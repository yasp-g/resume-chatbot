import csv
import json
import os
import requests
import tempfile
import threading
import time

import boto3

from botocore.exceptions import ClientError
from io import StringIO, BytesIO

import functools


def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__!r} executed in {(end_time - start_time):.4f}s")
        return result

    return wrapper

# CONSTANTS
S3_REGION_NAME = "us-east-1"
FILE_TYPES = [".txt", ".json", ".csv"]
TEMP_FILE_DELAY = 20

s3 = boto3.client('s3', region_name=S3_REGION_NAME)


@timing_decorator
def get_api_key():
    if not os.environ.get('OPENAI_API_KEY'):
        secret_name = "openai-api-key"
        region_name = "us-east-1"

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            raise e

        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        api_key = secret_dict['OPENAI_API_KEY']
        os.environ['OPENAI_API_KEY'] = api_key


# TODO: fork a branch and see if it's better to run get_bucket_path() in a gr.State() and declare
#  'S3_BUCKET_PATH' environment variable that way (probably eliminates needing to feed session_id
#  and s_timestamp into s3_upload() and serve_files() or the need for session_id and session_time
#  at all. Feels cleaner.
@timing_decorator
def get_bucket_path(s3_client=s3):
    if not os.environ.get('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = "Development"

    if not os.environ.get('S3_BUCKET_NAME') or os.environ.get('S3_BUCKET_PATH'):
        all_buckets = s3_client.list_buckets()
        for bucket in all_buckets['Buckets']:
            # if f"resume-chatbot-convos-{os.environ.get('ENVIRONMENT').lower()}" in bucket['Name']:
            if f"resume-chatbot-" in bucket['Name']:
                os.environ['S3_BUCKET_NAME'] = bucket['Name']
                os.environ['S3_BUCKET_PATH'] = f"convos/{os.environ.get('ENVIRONMENT').lower()}"
                break
        else:
            raise Exception("No matching S3 bucket found for the environment")


@timing_decorator
def s3_upload(s_id, s_timestamp, context):
    convo_path = f"{os.environ.get('S3_BUCKET_PATH')}/{s_timestamp}_{s_id}"

    # buffer_system_prompt = BytesIO(system_prompt.encode())
    buffer_system_prompt = BytesIO(context[0]['content'].encode())
    s3.upload_fileobj(buffer_system_prompt, Bucket=os.environ.get('S3_BUCKET_NAME'),
                      Key=f"{convo_path}/system_prompt.txt")

    message_log = [": ".join(m.values()) for m in context[1:]]

    buffer_txt = BytesIO("\n".join(message_log).encode())
    s3.upload_fileobj(buffer_txt, Bucket=os.environ.get('S3_BUCKET_NAME'), Key=f"{convo_path}/resumebot_convo.txt")

    buffer_json = BytesIO(json.dumps(context[1:], indent=2).encode())
    s3.upload_fileobj(buffer_json, Bucket=os.environ.get('S3_BUCKET_NAME'), Key=f"{convo_path}/resumebot_convo.json")

    fieldnames = ["role", "content"]
    buffer_csv_string = StringIO()
    csv_writer = csv.DictWriter(buffer_csv_string, fieldnames=fieldnames)
    csv_writer.writeheader()
    csv_writer.writerows(context[1:])
    buffer_csv_bytes = BytesIO(buffer_csv_string.getvalue().encode())
    s3.upload_fileobj(buffer_csv_bytes, Bucket=os.environ.get('S3_BUCKET_NAME'),
                      Key=f'{convo_path}/resumebot_convo.csv')


@timing_decorator
def delete_file_after_delay(delay, path):
    time.sleep(delay)
    try:
        os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")


@timing_decorator
def serve_files(s_id, s_timestamp, checkboxes):
    convo_path = f"{os.environ.get('S3_BUCKET_PATH')}/{s_timestamp}_{s_id}"
    files = []

    for file_type in FILE_TYPES:
        if file_type in checkboxes:
            try:
                # TODO: see if "resumebot_convo" can be changed to "resume-chatbot-convo"
                obj = s3.get_object(Bucket=os.environ.get('S3_BUCKET_NAME'),
                                    Key=f"{convo_path}/resumebot_convo{file_type}")
                # Read the content of the file
                file_content = obj['Body'].read()
                # Create a temporary file
                fd, path = tempfile.mkstemp(suffix=file_type, prefix="resumebot_convo-", dir=tempfile.gettempdir(),
                                            text=True)
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(file_content.decode('utf-8'))  # decode the content to string if it's bytes
                files.append(path)
                # Schedule deletion of file after 5 minutes
                threading.Thread(target=delete_file_after_delay, args=(TEMP_FILE_DELAY, path)).start()
            except Exception as e:
                print(f"Error processing file of type {file_type}: {e}")
    return files
