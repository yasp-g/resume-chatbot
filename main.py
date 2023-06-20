import os
import csv
import json
from datetime import datetime
import gradio as gr
import openai
from context import system_prompt

# added a comment at the top about bananas
openai.api_key = os.getenv('OPENAI_API_KEY')
GPT = 'gpt-3.5-turbo'
# GPT = 'gpt-4'
chat_saving = True

title = "<h1><center>Chat with Jasper Gallagher's Resume &#128221; &#129302; &#128172;</center></h1>"
description_top = """\
<div align="left">
<p> ResumeBot is a chatbot built using chatGPT designed to discuss the details of Jasper Gallagher's resume. </p>
<p>
Banana
</p >
</div>
"""
status_msgs = dict(
    waiting="Status: Waiting",
    thinking="Status: Thinking...",
    responding="Status: Responding...",
    ready="Status: Ready",
    cleared="Status: Conversation Cleared. Waiting"
)


def make_dir():
    """Build directory for storing chat logs and update session_vars['path_filename']."""
    if not os.path.isdir("conversations"):
        os.mkdir("conversations")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"conversations/{now}"
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)
    session_vars['path_filename'] = f"{path}/resumebot_convo"


def save_chat():
    """Writes chat context to a .txt, .json and .csv file."""
    session_vars['message_log'] = [": ".join(m.values()) for m in session_vars['context'][1:]]

    with open(f"{session_vars['path_filename']}.txt", 'w') as f:
        f.write("\n".join(session_vars['message_log']))

    with open(f"{session_vars['path_filename']}.json", 'w') as f:
        json.dump(session_vars['context'][1:], f, indent=1)

    with open(f"{session_vars['path_filename']}.csv", 'w') as f:
        fieldnames = ['role', 'content']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in session_vars['context'][1:]:
            writer.writerow(d)


# TODO:
def get_files(checkboxes):
    """Retrieves chat log filenames as selected be checkboxes.

    :param checkboxes: list from gr.Checkboxes component
    :return: list of chat log filenames
    """
    files = []
    if ".txt" in checkboxes:
        files.append(f"{session_vars['path_filename']}.txt")
    if ".json" in checkboxes:
        files.append(f"{session_vars['path_filename']}.json")
    if ".csv" in checkboxes:
        files.append(f"{session_vars['path_filename']}.csv")
    return files


def reset_context():
    """Resets session_vars['context'] to starting value."""
    session_vars['context'] = [{'role': 'system', 'content': 'system_prompt'}]


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


def user_msg(message, history):
    """Process user message.

    :param message: input from gr.Textbox component
    :param history: input from gr.Chatbot component
    :return: output to gr.Textbox component, output to gr.Chatbot component, output to gr.Markdown component
    """
    session_vars['context'] += [{'role': 'user', 'content': message}]
    return gr.update(value="", interactive=False), history + [[message, None]], status_msgs['thinking']


def assistant_msg(history):
    """Update chat with openai chat completion.

    :param history: input from gr.Chatbot component
    :return: yields chat completion in single characters, output to gr.Markdown component
    """
    completion = get_chat_completion(session_vars['context'])
    session_vars['context'] += [{'role': 'assistant', 'content': completion}]
    history[-1][1] = ""
    for character in completion:
        history[-1][1] += character
        # time.sleep(0.01)
        yield history, status_msgs['responding']
    # TODO: ????
    try:
        yield history, status_msgs['ready']
    except Exception:
        pass

    if chat_saving:
        save_chat()


# CSS
with open("static/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

# TODO: how to do about launching unique sessions and logging chats without interference?
# Gradio App
with gr.Blocks(css=customCSS) as demo:
    # SETUP
    # Session variables
    session_vars = dict(
        context=[{'role': 'system', 'content': system_prompt}],
        message_log=[],
        path_filename="",
    )

    # Build logging directory
    if chat_saving:
        state = gr.State(make_dir)

    # GRADIO LAYOUT
    # Title, description, status display
    gr.Markdown(title)
    gr.Markdown(description_top)
    status_display = gr.Markdown(status_msgs['waiting'], elem_id="status_display")

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
        inputs=[msg_box, chat],
        outputs=[msg_box, chat, status_display],
        queue=False,
        show_progress=True
    )

    assistant_msg_args = dict(
        fn=assistant_msg,
        inputs=chat,
        outputs=[chat, status_display],
        # show_progress=False,
        queue=True
    )

    reset_msg_args = dict(
        fn=lambda: gr.update(interactive=True),
        inputs=None,
        outputs=msg_box,
        queue=False
    )


    def print_chat(chatbot):
        print(chatbot)


    # APP ACTIONS
    # Textbox enter
    user_submit = msg_box.submit(**user_msg_args)
    user_submit.then(**assistant_msg_args)
    user_submit.then(**reset_msg_args)
    user_submit.then(print_chat, chat)

    # Textbox + Send button
    submit_click = submit_btn.click(**user_msg_args)
    submit_click.then(**assistant_msg_args)
    submit_click.then(**reset_msg_args)
    submit_click.then(print_chat, chat)

    # Clear button
    clear_click = clear_btn.click(fn=lambda: (None, status_msgs['cleared']),
                                  inputs=None,
                                  outputs=[chat, status_display],
                                  queue=False)
    clear_click.then(reset_context)

    # Save Chat button
    if chat_saving:
        save_click = save_btn.click(save_chat)
        save_click.then(fn=get_files, inputs=file_types, outputs=file_out)

demo.queue().launch()

# A role for scalr to provision infrastructure.
