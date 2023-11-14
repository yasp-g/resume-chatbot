import os
import time
import openai
import requests
import socket
import urllib3

import gradio as gr

from .config import STATUS_MSGS

# Constants
GPT = 'gpt-4'
# GPT = 'gpt-3.5-turbo'
TEMP = 0.1


def user_msg(message, history, context):
    """Process user message.

    :param message: input from gr.Textbox component
    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: output to gr.Textbox component, output to gr.Chatbot component, updated session_context, output to gr.Markdown component
    """
    context += [{'role': 'user', 'content': message}]
    history += [[message, None]]
    return gr.update(value="", interactive=False), gr.update(interactive=False), history, history, context, STATUS_MSGS[
        'thinking']


def get_chat_completion(messages, model=GPT, temperature=TEMP):
    """Get chat completion from openai API.

    :param messages: list of messages comprising the conversation so far
    :param model: ID of the model to use
    :param temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    :return: openAI chatGPT chat completion content, error message if relevant
    """

    if not openai.api_key:
        openai.api_key = os.environ.get('OPENAI_API_KEY')

    if openai.api_key is None:
        # Handle the case where the environment variable is not set
        raise EnvironmentError("No OpenAI API key.")

    try:
        chat_completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return chat_completion.choices[0].message["content"], None, None

    # TODO: handle network errors better (maybe: remove message from context, remove from history when new message sent)
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError,
            requests.exceptions.ConnectionError, openai.error.APIConnectionError) as e:
        error_message = f"A network error occurred: {e}. Please try again."
        print(f"Network error occurred: {type(e).__name__}: {e}")
        return None, e, error_message

    except openai.error.InvalidRequestError as e:
        error_message = f"""
        Congratulations, your conversation with ResumeBot has reached OpenAI's token limit! \
        Future versions of ResumeBot will work around this constraint, but for now, this is the end of your conversation. \
        Simply refresh the page to start again if you'd like. I hope you had fun and come back soon :).
        """
        print(f"Request error occurred: {type(e).__name__}: {e}")
        # print(f"error message: {error_message}")
        return None, e, error_message

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}. Please try again."
        print(f"Unexpected error of type {type(e).__name__}: {e}")
        return None, e, error_message


def assistant_msg(chat_history, chat_context):
    """Update gradio chat with openai chat completion.

    :param chat_history: input from gr.Chatbot component
    :param chat_context: input from gr.State session_context component
    :return: yields chat completion, updated session_context, output to gr.Markdown component
    """
    completion, e, error_message = get_chat_completion(chat_context)

    if error_message:
        chat_context += [{'role': 'assistant', 'content': error_message}]
        chat_history[-1][1] = error_message
        msg_box_update = gr.update(value="", placeholder="Chat locked due to an error.", interactive=False)
        submit_btn_update = gr.update(interactive=False)
        yield chat_history, chat_history, chat_context, e, msg_box_update, submit_btn_update, STATUS_MSGS['error']

    else:
        chat_context += [{'role': 'assistant', 'content': completion}]
        chat_history[-1][1] = ""
        msg_box_update = gr.update(value="", interactive=True)
        submit_btn_update = gr.update(interactive=True)

        for character in completion:
            chat_history[-1][1] += character
            time.sleep(0.005)
            yield chat_history, chat_history, chat_context, e, msg_box_update, submit_btn_update, STATUS_MSGS[
                'responding']

        yield chat_history, chat_history, chat_context, e, msg_box_update, submit_btn_update, STATUS_MSGS['ready']
