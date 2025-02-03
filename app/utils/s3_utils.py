import boto3
import threading
import asyncio
from botocore.exceptions import NoCredentialsError
from app.config.settings import S3_CONFIG

def download_file_from_s3(bucket_name, s3_key, local_path, progress_callback=None):
    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_CONFIG["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=S3_CONFIG["AWS_SECRET_ACCESS_KEY"]
    )

    class ProgressPercentage:
        def __init__(self, filename, loop):
            self._filename = filename
            self._size = float(s3.head_object(Bucket=bucket_name, Key=s3_key)['ContentLength'])
            self._seen_so_far = 0
            self._lock = threading.Lock()
            self._loop = loop

        def __call__(self, bytes_amount):
            with self._lock:
                self._seen_so_far += bytes_amount
                percentage = (self._seen_so_far / self._size) * 100
                if progress_callback:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(self._seen_so_far, self._size),
                        self._loop
                    )

    try:
        s3.download_file(bucket_name, s3_key, local_path, Callback=ProgressPercentage(s3_key, asyncio.get_event_loop()))
        print(f"Downloaded {s3_key} to {local_path}")
    except NoCredentialsError:
        print("Credentials not available")

def upload_file_to_s3(bucket_name, s3_key, content):
    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_CONFIG["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=S3_CONFIG["AWS_SECRET_ACCESS_KEY"]
    )
    try:
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=content, ContentType='text/plain')
        print(f"Uploaded {s3_key} to {bucket_name}")
    except NoCredentialsError:
        print("Credentials not available")