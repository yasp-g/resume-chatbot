import logging
import os
import sys
import uuid

import gradio as gr

from datetime import datetime
from utils import aws, chatbot
from utils.config import STATUS_MSGS, SYSTEM_PROMPT, TITLE, SUB_TITLE, DESCRIPTION_TOP

from utils.timing_decorator import timing_decorator


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
aws.get_api_key()
aws.get_bucket_path()

logger.info(f"INSTANCE_NAME: {os.environ.get('INSTANCE_NAME')}")
logger.info(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
logger.info(f"OPENAI_API_KEY check: {bool(os.environ.get('OPENAI_API_KEY'))}")
logger.info(f"S3_BUCKET_NAME check: {bool(os.environ.get('S3_BUCKET_NAME'))}")


@timing_decorator
def serve_error(error):
    if error:
        return gr.Warning(f"{error}")


# CSS
with open("static/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

# GRADIO APP
with gr.Blocks(css=customCSS, theme="sudeepshouche/minimalist") as demo:
    # SETUP
    # Session variables
    S_client = gr.State(chatbot.create_openai_client)
    S_chat = gr.State([])
    S_context = gr.State([{'role': 'system', 'content': SYSTEM_PROMPT}])
    S_id = gr.State(lambda: str(uuid.uuid1()))
    S_time = gr.State(lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    S_error = gr.State()

    # GRADIO LAYOUT
    # Title, description, status display
    gr.Markdown(TITLE)
    gr.Markdown(SUB_TITLE)
    gr.Markdown(DESCRIPTION_TOP)
    status_display = gr.Markdown(STATUS_MSGS['waiting'], elem_id="status_display")

    # Chatbot Tab
    with gr.Tab("Chatbot"):
        # TODO: see whats best to do now that gr.Group() is depricated
        with gr.Group():
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
                with gr.Group(elem_id="download_files_container"):
                    with gr.Column(scale=1, min_width=480):
                        gr.Markdown("<center>Select file type(s) and click Save Chat</center>")
                        file_types = gr.CheckboxGroup([".txt", ".json", ".csv"], show_label=False, elem_id="file_types")
                        save_btn = gr.Button("Save Chat", scale=1, interactive=False, variant='primary',
                                             elem_id="save_files_inputs")
                file_out = gr.File(label="Saved File(s)", scale=2, min_width=480, interactive=False)

    server_name = gr.Markdown(f"Server: {os.getenv('INSTANCE_NAME')}", elem_id="server_name")

    # APP ACTIONS
    # Textbox enter
    msg_box.submit(  # take in user message
        fn=chatbot.user_msg,
        inputs=[msg_box,
                S_chat,
                S_context],
        outputs=[msg_box,
                 submit_btn,
                 S_chat,
                 chat,
                 S_context,
                 status_display],
        queue=True,
        api_name="usr_msg_submit"
        # show_progress=True
    ).then(  # get and serve chat completion
        fn=chatbot.assistant_msg,
        inputs=[S_client,
                S_chat,
                S_context,
                msg_box,
                submit_btn],
        outputs=[S_chat,
                 chat,
                 S_context,
                 S_error,
                 msg_box,
                 submit_btn,
                 status_display],
        queue=True,
        api_name="assistant_msg_submit",
        # show_progress=True
    ).then(  # upload chat to S3
        fn=aws.s3_upload,
        inputs=[S_id, S_time, S_context],
        api_name="s3_upload_submit"
    ).then(  # serve error if needed
        fn=serve_error,
        inputs=S_error,
        api_name="serve_error_submit"
    )

    # Textbox + Send button
    submit_btn.click(  # take in user message
        fn=chatbot.user_msg,
        inputs=[msg_box,
                S_chat,
                S_context],
        outputs=[msg_box,
                 submit_btn,
                 S_chat,
                 chat,
                 S_context,
                 status_display],
        queue=True,
        api_name="usr_msg_click"
        # show_progress=True
    ).then(  # get and serve chat completion
        fn=chatbot.assistant_msg,
        inputs=[S_client,
                S_chat,
                S_context,
                msg_box,
                submit_btn],
        outputs=[S_chat,
                 chat,
                 S_context,
                 S_error,
                 msg_box,
                 submit_btn,
                 status_display],
        queue=True,
        api_name="assistant_msg_click",
        # show_progress=True
    ).then(  # upload chat to S3
        fn=aws.s3_upload,
        inputs=[S_id, S_time, S_context],
        api_name="s3_upload_click"
    ).then(  # serve error if needed
        fn=serve_error,
        inputs=S_error,
        api_name="serve_error_click"
    )

    # TODO: Finish this / decide if even needed
    # Error info button
    # error_info_click = error_info_btn.click(fn=gr.Info(f"Session error bool: {session_error.value}"), inputs=None,
    #                                         outputs=None)

    # Clear button
    clear_btn.click(
        fn=lambda: (None, []),
        outputs=[chat, S_chat],
        queue=False,
        api_name="clear_chat"
    ).then(
        fn=lambda: gr.State(),
        outputs=S_error,
        api_name="clear_error"
    ).then(
        fn=lambda: gr.update(placeholder="Type a message.", interactive=True),
        outputs=msg_box,
        api_name="reset_msg_box"
    ).then(
        fn=lambda: gr.update(interactive=True),
        outputs=submit_btn,
        api_name="reset_submit_btn"
    ).then(
        fn=lambda: [{'role': 'system', 'content': SYSTEM_PROMPT}],
        outputs=S_context,
        api_name="reset_context"
    ).then(
        fn=lambda: (None, []),
        outputs=[file_out, file_types],
        api_name="reset_files"
    ).then(
        fn=lambda: STATUS_MSGS['cleared'],
        outputs=status_display,
        api_name="reset_status_msg"
    )

    # Save Chat button
    if chat_saving:
        file_types.input(fn=lambda types: gr.update(interactive=True) if any(types) else gr.update(interactive=False),
                         inputs=[file_types],
                         outputs=[save_btn])
        save_btn.click(fn=aws.serve_files, inputs=[S_id, S_time, file_types], outputs=file_out)

logger.info("Launching the app...")
demo.queue()  # concurrency_count=1)
try:
    if __name__ == "__main__":
        # demo.launch(share=True)  # for local
        demo.launch(server_name="0.0.0.0", server_port=8080, ssl_verify=False)  # for aws
except Exception as e:
    logger.error('An error occurred while launching the app:', exc_info=True)
