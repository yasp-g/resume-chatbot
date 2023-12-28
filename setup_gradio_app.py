import uuid
import os
import logging

import gradio as gr

from datetime import datetime
from utils import aws, chatbot
from utils.config import make_system_prompt, EN_TEXT, DE_TEXT, STATUS_MSGS
from utils.timing_decorator import timing_decorator

logger = logging.getLogger(__name__)


@timing_decorator
def serve_error(error):
    if error:
        return gr.Warning(f"{error}")


@timing_decorator
def files_selected_check(types, chat_content):
    if any(types):
        if not chat_content:
            return gr.update(value=None), gr.update(interactive=False), gr.update(visible=True)
        else:
            return types, gr.update(interactive=True), gr.update(visible=False)
    else:
        return types, gr.update(interactive=False), gr.update(visible=False)


@timing_decorator
def change_language(language):
    if language == "Deutsch":
        lang_dict = DE_TEXT
    else:
        lang_dict = EN_TEXT
    return (gr.update(value=lang_dict["title"]),
            gr.update(value=lang_dict["sub_title"]),
            gr.update(value=lang_dict["description_top"]),
            gr.update(value=lang_dict["description_bottom"]))

    # return gr.update(value=lang_dict["title"])


@timing_decorator
def context_langauge_update(language, context):
    if language == "Deutsch":
        new_context = {'role': 'system', 'content': "Your conversation will now be in German. From now on you are programed to speak German, and you will only respond in German. Even if the user responds in a different language, you will only respond in German."}
    else:
        new_context = {'role': 'system', 'content': "Your conversation will now be in English. From now on you are programed to speak English, and you will only respond in English. Even if the user responds in a different language, you will only respond in English."}
    # logger.info(f"new_context: {new_context}")
    context.append(new_context)
    # logger.info(f"context update: {context}")
    return context


def create_context(request: gr.Request):
    query_params = dict(request.query_params)
    company = query_params.get('comp', 'Machine Learning Company').replace("_", " ")
    role = query_params.get('role', 'Machine Learning Engineer').replace("_", " ")
    # logger.info(f"App Load Time: company: {company}, role: {role}")
    context = [{'role': 'system', 'content': make_system_prompt(company, role)}]
    logger.info(f"App Load Time: company: {context}")
    return context


@timing_decorator
def setup_gradio_app():
    # SETUP
    chat_saving = True
    # logging_check = True

    with open("static/custom.css", "r", encoding="utf-8") as f:
        custom_css = f.read()

    with gr.Blocks(title="ResumeBot by Jasper", css=custom_css, theme="sudeepshouche/minimalist@0.0.1") as demo:
        # SETUP
        # Session variables
        s_id = gr.State(lambda: str(uuid.uuid1()))
        s_time = gr.State(lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        s_chat = gr.State([])
        s_client = gr.State(chatbot.create_openai_client)
        # TODO: this is related to generating context at app load time. incomplete. never got a response in hugging face discord
        # context = demo.load(fn=create_context)
        s_context = gr.State([])
        s_error = gr.State("")

        # GRADIO LAYOUT
        # Title, description, status display
        title = gr.HTML(EN_TEXT["title"])
        with gr.Row():
            # gr.Markdown()
            # with gr.Group(elem_id='download_files_container'):
            with gr.Column():
                gr.HTML("<center>Select Langauge</center>", elem_id="file_types")
                language_radio = gr.Radio(["English", "Deutsch"], value="English", label="Select Language", container=False, scale=0, min_width=320, elem_id="file_types")
            # gr.Markdown()
        sub_title = gr.HTML(EN_TEXT["sub_title"])
        description_top = gr.HTML(EN_TEXT["description_top"])
        status_display = gr.HTML(STATUS_MSGS['waiting'], elem_id="status_display")

        # Chatbot Tab
        with gr.Group():
            chat = gr.Chatbot(label="ResumeBot", avatar_images=(None, "utils/images/favicon.ico"))
            with gr.Row(variant='panel', equal_height=True):  # , elem_id='submit_button_container'):
                # TODO: check if container=False bug has been addressed
                msg_box = gr.Textbox(max_lines=10,
                                     placeholder="Type a message.",
                                     info="If you're feeling stuck, just try \"hello\" :)",
                                     show_label=False,
                                     container=True,
                                     scale=5,
                                     min_width=320,
                                     elem_id='msg_box'
                                     )
                submit_btn = gr.Button("Send", scale=1, variant='primary', elem_id='submit_btn')
        clear_btn = gr.Button("Clear Conversation", variant='stop')
        # error_info_btn = gr.Button("Error Info")
        # chat_saving_check = gr.Checkbox(True, label="Chat Logging", visible=logging_check, interactive=True)

        # Download Tab
        if chat_saving:
            # with gr.Accordion("Download Chat", open=False):
            with gr.Row(elem_id='custom-row'):
                with gr.Group(elem_id='download_files_container'):
                    # TODO: is min_width still needed here with new custom.css styling?
                    with gr.Column(scale=1, min_width=1000):
                        gr.Markdown("<center>Select file type(s) and click Save Chat</center>")
                        file_types = gr.CheckboxGroup([".txt", ".json", ".csv"], show_label=False,
                                                      elem_id="file_types")
                        help_text = gr.Markdown("<center>Try having a convo first!</center>", visible=False)
                        save_btn = gr.Button("Save Chat", interactive=False, variant='primary', scale=1,
                                             elem_id='save_files_inputs')
                file_out_placeholder = gr.Markdown("")
                file_out = gr.File(label="Downloaded File(s)", scale=1, min_width=480, interactive=False, visible=False)

        description_bottom = gr.HTML(EN_TEXT["description_bottom"], elem_id="description_bottom")
        server_name = gr.Markdown(f"Server: {os.getenv('INSTANCE_NAME')}", elem_id="server_name")

        # APP ACTIONS
        # Textbox enter
        # TODO: Consider having the chatbot send first message
        msg_box.submit(  # take in user message
            fn=chatbot.user_msg,
            inputs=[msg_box,
                    s_chat,
                    s_context],
            outputs=[s_chat,
                     chat,
                     s_context,
                     msg_box,
                     submit_btn,
                     clear_btn,
                     status_display],
            queue=True,
            api_name="usr_msg_submit"
            # show_progress=True
        ).then(  # get and serve chat completion
            fn=chatbot.assistant_msg,
            inputs=[s_client,
                    s_chat,
                    s_context,
                    msg_box,
                    submit_btn,
                    clear_btn],
            outputs=[s_chat,
                     chat,
                     s_context,
                     s_error,
                     msg_box,
                     submit_btn,
                     clear_btn,
                     status_display],
            queue=True,
            api_name="assistant_msg_submit",
            # show_progress=True
        ).then(  # upload chat to S3
            fn=aws.s3_upload,
            inputs=[s_id,
                    s_time,
                    s_context],
            api_name="s3_upload_submit"
        ).then(  # serve error if needed
            fn=serve_error,
            inputs=s_error,
            api_name="serve_error_submit"
        )

        # Textbox + Send button
        submit_btn.click(  # take in user message
            fn=chatbot.user_msg,
            inputs=[msg_box,
                    s_chat,
                    s_context],
            outputs=[s_chat,
                     chat,
                     s_context,
                     msg_box,
                     submit_btn,
                     clear_btn,
                     status_display],
            queue=True,
            api_name="usr_msg_click"
            # show_progress=True
        ).then(  # get and serve chat completion
            fn=chatbot.assistant_msg,
            inputs=[s_client,
                    s_chat,
                    s_context,
                    msg_box,
                    submit_btn,
                    clear_btn],
            outputs=[s_chat,
                     chat,
                     s_context,
                     s_error,
                     msg_box,
                     submit_btn,
                     clear_btn,
                     status_display],
            queue=True,
            api_name="assistant_msg_click",
            # show_progress=True
        ).then(  # upload chat to S3
            fn=aws.s3_upload,
            inputs=[s_id,
                    s_time,
                    s_context],
            api_name="s3_upload_click"
        ).then(  # serve error if needed
            fn=serve_error,
            inputs=s_error,
            api_name="serve_error_click"
        )

        # TODO: Finish this / decide if even needed
        # Error info button
        # error_info_click = error_info_btn.click(fn=gr.Info(f"Session error bool: {session_error.value}"), inputs=None,
        #                                         outputs=None)

        # Language radio button
        language_radio.change(
            fn=change_language,
            inputs=language_radio,
            outputs=[title, sub_title, description_top, description_bottom],
            queue=True,
            show_progress="hidden"
        ).then(
            fn=context_langauge_update,
            inputs=[language_radio, s_context],
            outputs=[s_context],
            queue=True,
            show_progress="hidden"
        )

        # Clear button
        clear_btn.click(
            fn=lambda: (None, []),
            outputs=[chat, s_chat],
            queue=True,
            api_name="clear_chat"
        ).then(
            fn=lambda: "",
            outputs=s_error,
            api_name="clear_error"
        ).then(
            fn=lambda: gr.update(placeholder="Type a message.",
                                 interactive=True,
                                 info="If you're feeling stuck, just try \"hello\" :)."),
            outputs=msg_box,
            api_name="reset_msg_box"
        ).then(
            fn=lambda: gr.update(interactive=True),
            outputs=submit_btn,
            api_name="reset_submit_btn"
        ).then(
            fn=lambda: "",
            outputs=s_context,
            api_name="reset_context"
        ).then(
            fn=lambda: (None, []),
            outputs=[file_out, file_types],
            api_name="reset_files"
        ).then(
            fn=lambda: str(uuid.uuid1()),
            outputs=s_id,
            api_name="reset_uid"
        ).then(
            fn=lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            outputs=s_time,
            api_name="reset_timestamp"
        ).then(
            fn=lambda: STATUS_MSGS['cleared'],
            outputs=status_display,
            api_name="reset_status_msg"
        )

        # Save Chat button
        if chat_saving:
            file_types.input(
                fn=files_selected_check,
                inputs=[file_types, s_chat],
                outputs=[file_types, save_btn, help_text],
                show_progress="hidden"
            )
            save_btn.click(
                fn=lambda: gr.update(visible=False),
                outputs=file_out_placeholder,
                api_name="hide_file_out_placeholder"
            ).then(
                fn=lambda: gr.update(visible=True),
                outputs=file_out,
                show_progress="hidden",
                api_name="show_file_out"
            ).then(
                fn=aws.serve_files,
                inputs=[s_id, s_time, file_types],
                outputs=file_out,
                queue=True
            )

    return demo
