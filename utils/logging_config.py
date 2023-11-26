import logging
import os
import sys


def setup_logging():
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def startup_logging():
    setup_logging()
    logger = logging.getLogger()
    logger.info(f"INSTANCE_NAME: {os.environ.get('INSTANCE_NAME')}")
    logger.info(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    logger.info(f"OPENAI_API_KEY check: {bool(os.environ.get('OPENAI_API_KEY'))}")
    logger.info(f"S3_BUCKET_NAME check: {bool(os.environ.get('S3_BUCKET_NAME'))}")
