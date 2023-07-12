import csv
import json
import os
import tempfile
import threading
import time
import uuid

import boto3
import gradio as gr
import openai

from context import system_prompt
from datetime import datetime
from io import StringIO, BytesIO

# Constants
S3_REGION_NAME = 'us-east-1'
S3_BUCKET_NAME = 'resume-chatbot-convos-prod20230705094748548900000001'
FILE_TYPES = [".txt", ".json", ".csv"]
TEMP_FILE_DELAY = 20
STATUS_MSGS = dict(
    waiting="Status: Waiting",
    thinking="Status: Thinking...",
    responding="Status: Responding...",
    ready="Status: Ready",
    cleared="Status: Conversation Cleared. Waiting"
)

# system_prompt = "respond to the first message with `m1`. The second: `m2`. The third: `m3` and so on"
openai.api_key = os.getenv('OPENAI_API_KEY')
GPT = 'gpt-3.5-turbo'
# GPT = 'gpt-4'
s3 = boto3.client('s3', region_name=S3_REGION_NAME)
chat_saving = True

title = "<h1><center>Chat with Jasper Gallagher's Resume &#128221; &#129302; &#128172;</center></h1>"
description_top = """\
<div align="left">
<p> ResumeBot is a chatbot built using chatGPT designed to discuss the details of my resume and experience.</p>
<p>
Banana
</p >
</div>
"""


def get_session_id():
    return str(uuid.uuid1())


def get_datetime():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def s3_upload(s_id, s_timestamp, context):
    folder_name = f"{s_timestamp}_{s_id}"
    print(f"folder name: {folder_name}")

    buffer_system_prompt = BytesIO(system_prompt.encode())
    s3.upload_fileobj(buffer_system_prompt, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/system_prompt.txt')

    message_log = [": ".join(m.values()) for m in context[1:]]

    buffer_txt = BytesIO("\n".join(message_log).encode())
    s3.upload_fileobj(buffer_txt, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.txt')

    buffer_json = BytesIO(json.dumps(context[1:], indent=1).encode())
    s3.upload_fileobj(buffer_json, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.json')

    fieldnames = ['role', 'content']
    buffer_csv_string = StringIO()
    csv_writer = csv.DictWriter(buffer_csv_string, fieldnames=fieldnames)
    csv_writer.writeheader()
    csv_writer.writerows(context[1:])
    buffer_csv_bytes = BytesIO(buffer_csv_string.getvalue().encode())
    s3.upload_fileobj(buffer_csv_bytes, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.csv')


def delete_file_after_delay(delay, path):
    time.sleep(delay)
    try:
        os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")


def serve_files(s_id, s_timestamp, checkboxes):
    folder_name = f"{s_timestamp}_{s_id}"
    files = []

    for file_type in FILE_TYPES:
        if file_type in checkboxes:
            try:
                obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=f"{folder_name}/resumebot_convo{file_type}")
                # Read the content of the file
                file_content = obj['Body'].read()
                # Create a temporary file
                fd, path = tempfile.mkstemp(suffix=file_type, prefix='resumebot_convo-', dir=tempfile.gettempdir(),
                                            text=True)
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(file_content.decode('utf-8'))  # decode the content to string if it's bytes
                files.append(path)
                # Schedule deletion of file after 5 minutes
                threading.Thread(target=delete_file_after_delay, args=(TEMP_FILE_DELAY, path)).start()
            except Exception as e:
                print(f"Error processing file of type {file_type}: {e}")
    return files


def reset_context():
    """Resets session_context to starting value."""
    return [{'role': 'system', 'content': system_prompt}]


def get_chat_completion(messages, model=GPT, temperature=0.1):
    """Gets ChatCompletion from openai API.

    :param messages: list of messages comprising the conversation so far
    :param model: ID of the model to use
    :param temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    :return: openAI chatGPT chat completion content
    """
    chat_completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return chat_completion.choices[0].message["content"]


def user_msg(message, history, context):
    """Process user message.

    :param message: input from gr.Textbox component
    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: output to gr.Textbox component, output to gr.Chatbot component, updated session_context, output to gr.Markdown component
    """

    # print("new message:", {'role': 'user', 'content': message})
    context += [{'role': 'user', 'content': message}]
    history += [[message, None]]
    return gr.update(value="", interactive=False), history, history, context, STATUS_MSGS['thinking']


def assistant_msg(history, context):
    """Update chat with openai chat completion.

    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: yields chat completion, updated session_context, output to gr.Markdown component
    """
    completion = get_chat_completion(context)
    # print("assistant response:", completion)
    context += [{'role': 'assistant', 'content': completion}]
    # print("updated context:", context[1:])
    history[-1][1] = ""
    for character in completion:
        history[-1][1] += character
        # TODO: decide if delay below is needed
        # time.sleep(0.01)
        yield history, history, context, STATUS_MSGS['responding']
    # # TODO: what is this even doing????
    # try:
    #     yield history, history, context, STATUS_MSGS['ready']
    # except Exception as e:
    #     print(f"Error: {e}")
    # TODO: figure out how to s3_upload() after assistant_msg() from outside of this function (need session_id and time
    #  to write to s3)
    # if chat_saving:
    #     # s3_upload()


# CSS
with open("static/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

# Gradio App
with gr.Blocks(css=customCSS) as demo:
    # SETUP
    # Session variables
    session_chat = gr.State([])
    session_context = gr.State([{'role': 'system', 'content': system_prompt}])
    session_id = gr.State(get_session_id)
    session_time = gr.State(get_datetime)

    # GRADIO LAYOUT
    # Title, description, status display
    gr.Markdown(title)
    gr.Markdown(description_top)
    status_display = gr.Markdown(STATUS_MSGS['waiting'], elem_id="status_display")

    # Chatbot Tab
    with gr.Tab("Chatbot"):
        with gr.Row():
            chat = gr.Chatbot(label="Chat")
        with gr.Row(equal_height=True):
            with gr.Column(scale=25):
                msg_box = gr.Textbox(show_label=False, placeholder="Type a message.", container=False)
            with gr.Column(scale=0):
                submit_btn = gr.Button("Send")
        with gr.Row():
            clear_btn = gr.Button("Clear Conversation")

    # Download Tab
    if chat_saving:
        with gr.Tab("Download Chat"):
            with gr.Column():
                with gr.Row():
                    file_out = gr.File()
                with gr.Row():
                    file_types = gr.CheckboxGroup([".txt", ".json", ".csv"],
                                                  label="Select file type(s) to download")
                    save_btn = gr.Button("Save Chat")

    # Chatbot arg simplification
    user_msg_args = dict(
        fn=user_msg,
        inputs=[msg_box, session_chat, session_context],
        outputs=[msg_box, session_chat, chat, session_context, status_display],
        queue=False,
        show_progress=True
    )

    assistant_msg_args = dict(
        fn=assistant_msg,
        inputs=[session_chat, session_context],
        outputs=[session_chat, chat, session_context, status_display],
        # show_progress=False,
        queue=True
    )

    reset_msg_box_args = dict(
        fn=lambda: gr.update(interactive=True),
        inputs=None,
        outputs=msg_box,
        queue=False
    )

    # Temporary
    # TODO: Remove when not needed
    # def print_chat(s_history, s_context):
    #     print(f"history: {s_history}")
    #     print(f"context: {s_context[1:]}")

    # APP ACTIONS
    # Textbox enter
    user_submit = msg_box.submit(**user_msg_args)
    user_submit.then(**assistant_msg_args)
    user_submit.then(**reset_msg_box_args)
    # user_submit.then(print_chat, [session_chat, session_context])
    user_submit.then(s3_upload, inputs=[session_id, session_time, session_context])

    # Textbox + Send button
    submit_click = submit_btn.click(**user_msg_args)
    submit_click.then(**assistant_msg_args)
    submit_click.then(**reset_msg_box_args)
    # submit_click.then(print_chat, [session_chat, session_context])
    submit_click.then(s3_upload, inputs=[session_id, session_time, session_context])

    # Clear button
    clear_click = clear_btn.click(fn=lambda: (None, STATUS_MSGS['cleared']),
                                  inputs=None,
                                  outputs=[chat, status_display],
                                  queue=False)
    clear_click.then(reset_context, None, session_context)

    # Save Chat button
    if chat_saving:
        save_click = save_btn.click(s3_upload, inputs=[session_id, session_time, session_context])
        save_click.then(fn=serve_files, inputs=[session_id, session_time, file_types], outputs=file_out)

demo.queue().launch()

# A role for scalr to provision infrastructure.
