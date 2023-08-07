import uuid
import logging
import os
import sys

import gradio as gr

from datetime import datetime
from utils import s3, chatbot
from utils.config import STATUS_MSGS, SYSTEM_PROMPT, TITLE, SUB_TITLE, DESCRIPTION_TOP

# TODO: delete utils.context (moved it into config.py)

chat_saving = True
print("API_KEY:", bool(os.environ.get("API_KEY")))

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# CSS
with open("static/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

# Gradio App
with gr.Blocks(css=customCSS) as demo:
    # SETUP
    # Session variables
    session_chat = gr.State([])
    session_context = gr.State([{'role': 'system', 'content': SYSTEM_PROMPT}])
    session_id = gr.State(lambda: str(uuid.uuid1()))
    session_time = gr.State(lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    # GRADIO LAYOUT
    # Title, description, status display
    gr.Markdown(TITLE)
    gr.Markdown(SUB_TITLE)
    gr.Markdown(DESCRIPTION_TOP)
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
                    file_types = gr.CheckboxGroup([".txt", ".json", ".csv"],
                                                  label="Select file type(s) to download")
                    save_btn = gr.Button("Save Chat")
                with gr.Row():
                    file_out = gr.File(label="File(s)")

    server_name = gr.Markdown(f"Server: {os.getenv('INSTANCE_NAME')}", elem_id="server_name")

    # Chatbot arg simplification
    user_msg_args = dict(
        fn=chatbot.user_msg,
        inputs=[msg_box, session_chat, session_context],
        outputs=[msg_box, session_chat, chat, session_context, status_display],
        queue=True,
        show_progress=True
    )

    assistant_msg_args = dict(
        fn=chatbot.assistant_msg,
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
    user_submit.then(fn=s3.upload, inputs=[session_id, session_time, session_context])

    # Textbox + Send button
    submit_click = submit_btn.click(**user_msg_args)
    submit_click.then(**assistant_msg_args)
    submit_click.then(**reset_msg_box_args)
    # submit_click.then(print_chat, [session_chat, session_context])
    submit_click.then(fn=s3.upload, inputs=[session_id, session_time, session_context])

    # Clear button
    clear_click = clear_btn.click(fn=lambda: (None, [], STATUS_MSGS['cleared']),
                                  inputs=None,
                                  outputs=[chat, session_chat, status_display],
                                  queue=False)
    clear_click.then(fn=lambda: [{'role': 'system', 'content': SYSTEM_PROMPT}], inputs=None, outputs=session_context)
    clear_click.then(fn=lambda: (None, []), inputs=None, outputs=[file_out, file_types])

    # Save Chat button
    if chat_saving:
        save_click = save_btn.click(fn=s3.serve_files, inputs=[session_id, session_time, file_types], outputs=file_out)

logger.info('Launching the app...')
try:
    # demo.queue().launch() # for local
    demo.queue().launch(server_name="0.0.0.0", server_port=8080, ssl_verify=False)
except Exception as e:
    logger.error('An error occurred while launching the app:', exc_info=True)
