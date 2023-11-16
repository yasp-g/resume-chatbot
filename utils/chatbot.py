import logging
import openai
import os
import requests
import socket
import time
import urllib3

import gradio as gr

from openai import OpenAI
from .config import STATUS_MSGS
from .timing_decorator import timing_decorator

# SETUP
logger = logging.getLogger()
logger.info(f"initial api key check: {bool(os.environ.get('OPENAI_API_KEY'))}")
GPT = 'gpt-4'
# GPT = 'gpt-3.5-turbo'
TEMP = 0.1


# TODO: decide if this is needed
@timing_decorator
def warm_up_api(client):
    logger.info(f"warmup check: {bool(os.environ.get('OPENAI_API_KEY'))}")
    # if not client.api_key:
    #     client.api_key = os.environ.get('OPENAI_API_KEY')
    # if OpenAI.api_key is None:
    #     raise EnvironmentError("No OpenAI API key.")
    # if not os.environ.get('OPENAI_API_KEY'):
    #     raise EnvironmentError("No OpenAI API key.")

    try:
        client.chat.completions.create(
            model=GPT,  # Use an appropriate model
            messages=[{"role": "system", "content": "You are a helpful assistant."}],
            temperature=0
        )
        logger.info("API warm-up call completed.")
    except Exception as e:
        logger.info(f"API warm-up call failed: {e}")


@timing_decorator
def create_openai_client():
    # api_key = os.environ.get('OPENAI_API_KEY')
    if os.environ.get('OPENAI_API_KEY') is None:
        raise EnvironmentError("No OpenAI API key.")

    client = OpenAI()  # api_key=api_key)
    warm_up_api(client)

    return client


@timing_decorator
def user_msg(message, history, context):
    """Process user message.

    :param message: input from gr.Textbox component
    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: output to gr.Textbox component, output to gr.Chatbot component, updated session_context, output to gr.Markdown component
    """
    logger.info("---NEW MESSAGE---")
    context += [{'role': 'user', 'content': message}]
    history += [[message, None]]
    return gr.update(value="", interactive=False), gr.update(interactive=False), history, history, context, STATUS_MSGS[
        'thinking']


@timing_decorator
def get_chat_completion(client, messages, model=GPT, temperature=TEMP):
    """Get chat completion from openai API.

    :param client: OpenAI client
    :param messages: list of messages comprising the conversation so far
    :param model: ID of the model to use
    :param temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    :return: openAI chatGPT chat completion content, error message if relevant
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return completion.choices[0].message.content, None, None

    # TODO: handle network errors better (maybe: remove message from context, remove from history when new message sent)
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError,
            requests.exceptions.ConnectionError, openai.APIConnectionError) as e:
        error_message = f"A network error occurred: {e}. Please try again by refreshing the page."
        logger.error(f"Network error occurred: {type(e).__name__}: {e}")
        return None, e, error_message

    except openai.RateLimitError as e:
        error_message = f"""
        Congratulations, your conversation with ResumeBot has reached OpenAI's token limit! \
        Future versions of ResumeBot will work around this constraint, but for now, this is the end of your conversation. \
        Simply refresh the page to start again if you'd like. I hope you had fun and come back soon :).
        """
        logger.error(f"Request error occurred: {type(e).__name__}: {e}")
        # print(f"error message: {error_message}")
        return None, e, error_message

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}. Please try again by refreshing the page."
        logger.error(f"Unexpected error of type {type(e).__name__}: {e}")
        return None, e, error_message


# @timing_decorator
def assistant_msg(client, chat_history, chat_context):
    """Update gradio chat with openai chat completion.

    :param client: OpenAI client
    :param chat_history: input from gr.Chatbot component
    :param chat_context: input from gr.State session_context component
    :return: yields chat completion, updated session_context, output to gr.Markdown component
    """
    start_time = time.time()  # Start timing here
    completion, e, error_message = get_chat_completion(client, chat_context)

    if error_message:
        chat_context += [{'role': 'assistant', 'content': error_message}]
        chat_history[-1][1] = error_message
        msg_box_update = gr.update(value="", placeholder="Chat locked due to an error.", interactive=False)
        submit_btn_update = gr.update(interactive=False)
        end_time = time.time()  # End timing before yielding
        logger.info(f"Function `assistant_msg` executed in {(end_time - start_time):.4f}s with error")
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

        end_time = time.time()  # End timing after the loop
        logger.info(f"Function `assistant_msg` executed in {(end_time - start_time):.4f}s with error")
        yield chat_history, chat_history, chat_context, e, msg_box_update, submit_btn_update, STATUS_MSGS['ready']
