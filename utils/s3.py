import csv
import json
import os
import tempfile
import threading
import time

import boto3

from io import StringIO, BytesIO

# Constants
S3_REGION_NAME = 'us-east-1'
S3_BUCKET_NAME = 'resume-chatbot-convos-production-20230728092902822500000002'
FILE_TYPES = [".txt", ".json", ".csv"]
TEMP_FILE_DELAY = 20

s3 = boto3.client('s3', region_name=S3_REGION_NAME)


def upload(s_id, s_timestamp, context):
    folder_name = f"{s_timestamp}_{s_id}"

    # buffer_system_prompt = BytesIO(system_prompt.encode())
    buffer_system_prompt = BytesIO(context[0]['content'].encode())
    s3.upload_fileobj(buffer_system_prompt, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/system_prompt.txt')

    message_log = [": ".join(m.values()) for m in context[1:]]

    buffer_txt = BytesIO("\n".join(message_log).encode())
    s3.upload_fileobj(buffer_txt, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.txt')

    buffer_json = BytesIO(json.dumps(context[1:], indent=1).encode())
    s3.upload_fileobj(buffer_json, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.json')

    fieldnames = ['role', 'content']
    buffer_csv_string = StringIO()
    csv_writer = csv.DictWriter(buffer_csv_string, fieldnames=fieldnames)
    csv_writer.writeheader()
    csv_writer.writerows(context[1:])
    buffer_csv_bytes = BytesIO(buffer_csv_string.getvalue().encode())
    s3.upload_fileobj(buffer_csv_bytes, Bucket=S3_BUCKET_NAME, Key=f'{folder_name}/resumebot_convo.csv')


def delete_file_after_delay(delay, path):
    time.sleep(delay)
    try:
        os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")


def serve_files(s_id, s_timestamp, checkboxes):
    folder_name = f"{s_timestamp}_{s_id}"
    files = []

    for file_type in FILE_TYPES:
        if file_type in checkboxes:
            try:
                obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=f"{folder_name}/resumebot_convo{file_type}")
                # Read the content of the file
                file_content = obj['Body'].read()
                # Create a temporary file
                fd, path = tempfile.mkstemp(suffix=file_type, prefix='resumebot_convo-', dir=tempfile.gettempdir(),
                                            text=True)
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(file_content.decode('utf-8'))  # decode the content to string if it's bytes
                files.append(path)
                # Schedule deletion of file after 5 minutes
                threading.Thread(target=delete_file_after_delay, args=(TEMP_FILE_DELAY, path)).start()
            except Exception as e:
                print(f"Error processing file of type {file_type}: {e}")
    return files
