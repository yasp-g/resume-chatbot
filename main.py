import logging
import os

from dotenv import load_dotenv
from utils.logging_config import setup_logging, startup_logging
from utils.aws import get_api_key, get_bucket_path
from setup_gradio_app import setup_gradio_app

load_dotenv()

def main():
    setup_logging()
    get_api_key()
    get_bucket_path()
    startup_logging()
    demo = setup_gradio_app()
    demo.queue()  # concurrency_count=1)

    mode = os.getenv('LAUNCH_MODE')
    icon_path = "static/favicon.ico"
    auths = os.getenv('AUTHS')

    if mode == "AWS":
        logging.info(f"Launch mode: {mode}")
        demo.launch(  # for aws
            share=False,
            # max_threads=1,
            server_name="0.0.0.0",
            server_port=8080,
            ssl_verify=False,
            favicon_path=icon_path,
            auth=auths
        )
    elif mode == "PI":
        logging.info(f"Launch mode: {mode}")
        demo.launch( # for Raspberry Pi
            share=False,
            # max_threads=1,
            server_name="0.0.0.0",
            server_port=7860,
            ssl_verify=False,
            favicon_path=icon_path,
            auth=auths
        )
    else:
        logging.info("Launch mode: LOCAL"),
        demo.launch( # for local
            share=True,
            favicon_path=icon_path,
            auth=auths
        )  


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error('An error occurred while launching the app:', exc_info=e)

# http://127.0.0.1:7860/?comp=Example_Corp&role=Data_Scientist
