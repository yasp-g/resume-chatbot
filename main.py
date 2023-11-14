import logging
import os
import sys
import uuid

import gradio as gr

from datetime import datetime
from utils import aws, chatbot
from utils.config import STATUS_MSGS, SYSTEM_PROMPT, TITLE, SUB_TITLE, DESCRIPTION_TOP

# LOGGING
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# SETUP
chat_saving = True
# logging_check = True
aws.get_bucket_path()
if not os.environ.get('OPENAI_API_KEY'):
    aws.get_api_key()

logger.info(f"INSTANCE_NAME: {os.environ.get('INSTANCE_NAME')}")
logger.info(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
logger.info(f"OPENAI_API_KEY check: {bool(os.environ.get('OPENAI_API_KEY'))}")
logger.info(f"S3_BUCKET_NAME check: {bool(os.environ.get('S3_BUCKET_NAME'))}")


def serve_error(error):
    # print("error warning", error)
    if error:
        return gr.Warning(f"{error}")


# CSS
with open("static/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

# GRADIO APP
with gr.Blocks(css=customCSS, theme="sudeepshouche/minimalist") as demo:
    # SETUP
    # Session variables
    session_chat = gr.State([])
    session_context = gr.State([{'role': 'system', 'content': SYSTEM_PROMPT}])
    session_id = gr.State(lambda: str(uuid.uuid1()))
    session_time = gr.State(lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    session_error = gr.State()

    # GRADIO LAYOUT
    # Title, description, status display
    gr.Markdown(TITLE)
    gr.Markdown(SUB_TITLE)
    gr.Markdown(DESCRIPTION_TOP)
    status_display = gr.Markdown(STATUS_MSGS['waiting'], elem_id="status_display")

    # Chatbot Tab
    with gr.Tab("Chatbot"):
        with gr.Box():
            chat = gr.Chatbot(label="Chat")
            with gr.Row(variant='panel', equal_height=False, elem_id='submit_button_container'):
                # TODO: check if container=False bug has been addressed
                msg_box = gr.Textbox(show_label=False, placeholder="Type a message.", scale=5, max_lines=10)
                submit_btn = gr.Button("Send", scale=1, variant='primary')
        clear_btn = gr.Button("Clear Conversation", variant='stop')
        # error_info_btn = gr.Button("Error Info")
        # chat_saving_check = gr.Checkbox(True, label="Chat Logging", visible=logging_check, interactive=True)

    # Download Tab
    if chat_saving:
        with gr.Tab("Download Chat"):
            with gr.Row():
                with gr.Box(elem_id="download_files_container"):
                    with gr.Column(scale=1, min_width=480):
                        gr.Markdown("<center>Select file type(s) and click Save Chat</center>")
                        file_types = gr.CheckboxGroup([".txt", ".json", ".csv"], show_label=False, elem_id="file_types")
                        save_btn = gr.Button("Save Chat", scale=1, interactive=False, variant='primary',
                                             elem_id="save_files_inputs")
                file_out = gr.File(label="Saved File(s)", scale=2, min_width=480, interactive=False)

    server_name = gr.Markdown(f"Server: {os.getenv('INSTANCE_NAME')}", elem_id="server_name")

    # CHATBOT ACTION ARGUMENTS
    user_msg_args = dict(
        fn=chatbot.user_msg,
        inputs=[msg_box,
                session_chat,
                session_context],
        outputs=[msg_box,
                 submit_btn,
                 session_chat,
                 chat,
                 session_context,
                 status_display],
        queue=True,
        show_progress=True
    )

    assistant_msg_args = dict(
        fn=chatbot.assistant_msg,
        inputs=[session_chat,
                session_context],
        outputs=[session_chat,
                 chat,
                 session_context,
                 session_error,
                 msg_box,
                 submit_btn,
                 status_display],
        # show_progress=True,
        queue=True
    )

    # APP ACTIONS
    # Textbox enter
    user_submit = msg_box.submit(**user_msg_args)
    user_submit.then(**assistant_msg_args)
    user_submit.then(fn=aws.s3_upload, inputs=[session_id, session_time, session_context])
    user_submit.then(fn=serve_error, inputs=session_error)

    # Textbox + Send button
    submit_click = submit_btn.click(**user_msg_args)
    submit_click.then(**assistant_msg_args)
    submit_click.then(fn=aws.s3_upload, inputs=[session_id, session_time, session_context])
    submit_click.then(fn=serve_error, inputs=session_error)

    # TODO: Finish this / decide if even needed
    # Error info button
    # error_info_click = error_info_btn.click(fn=gr.Info(f"Session error bool: {session_error.value}"), inputs=None,
    #                                         outputs=None)

    # Clear button
    clear_click = clear_btn.click(fn=lambda: (None, []),
                                  outputs=[chat, session_chat],
                                  queue=False)
    clear_click.then(fn=lambda: gr.State(), outputs=session_error)
    clear_click.then(fn=lambda: gr.update(placeholder="Type a message.", interactive=True), outputs=msg_box)
    clear_click.then(fn=lambda: gr.update(interactive=True), outputs=submit_btn)
    clear_click.then(fn=lambda: [{'role': 'system', 'content': SYSTEM_PROMPT}], outputs=session_context)
    clear_click.then(fn=lambda: (None, []), outputs=[file_out, file_types])
    clear_click.then(fn=lambda: STATUS_MSGS['cleared'], outputs=status_display)

    # Save Chat button
    if chat_saving:
        file_types.input(fn=lambda types: gr.update(interactive=True) if any(types) else gr.update(interactive=False),
                         inputs=[file_types],
                         outputs=[save_btn])
        save_btn.click(fn=aws.serve_files, inputs=[session_id, session_time, file_types], outputs=file_out)

logger.info("Launching the app...")
demo.queue(concurrency_count=1)
try:
    if __name__ == "__main__":
        # demo.launch(share=True)  # for local
        demo.launch(server_name="0.0.0.0", server_port=8080, ssl_verify=False)  # for aws
except Exception as e:
    logger.error('An error occurred while launching the app:', exc_info=True)
