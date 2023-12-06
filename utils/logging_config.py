import json
import logging
import os
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'message': record.getMessage(),
            'name': record.name
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging():
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)


def startup_logging():
    setup_logging()
    logger = logging.getLogger()
    logger.info(f"INSTANCE_NAME: {os.environ.get('INSTANCE_NAME')}")
    logger.info(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    logger.info(f"OPENAI_API_KEY check: {bool(os.environ.get('OPENAI_API_KEY'))}")
    logger.info(f"S3_BUCKET_NAME check: {bool(os.environ.get('S3_BUCKET_NAME'))}")
