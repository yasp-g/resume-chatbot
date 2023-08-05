import os
import time
import openai
import gradio as gr
from .config import STATUS_MSGS

openai.api_key = os.getenv('OPENAI_API_KEY')

# Constants
GPT = 'gpt-3.5-turbo'
TEMP = 0.1


# GPT = 'gpt-4'


def user_msg(message, history, context):
    """Process user message.

    :param message: input from gr.Textbox component
    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: output to gr.Textbox component, output to gr.Chatbot component, updated session_context, output to gr.Markdown component
    """
    context += [{'role': 'user', 'content': message}]
    history += [[message, None]]
    return gr.update(value="", interactive=False), history, history, context, STATUS_MSGS['thinking']


def get_chat_completion(messages, model=GPT, temperature=TEMP):
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


def assistant_msg(history, context):
    """Update chat with openai chat completion.

    :param history: input from gr.Chatbot component
    :param context: input from gr.State session_context component
    :return: yields chat completion, updated session_context, output to gr.Markdown component
    """
    # while history[-1][1] is None:
    #     time.sleep(0.1)
    completion = get_chat_completion(context)
    context += [{'role': 'assistant', 'content': completion}]
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
    # TODO: figure out how to s3.s3_upload() after assistant_msg() from outside of this function (need session_id and
    #  time to write to s3) (if this is even needed??)
    # if chat_saving:
    #     # s3.s3_upload()
