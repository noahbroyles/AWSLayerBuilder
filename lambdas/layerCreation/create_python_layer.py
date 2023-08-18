import os
import sys
import json
import time
import boto3
import shutil
import zipfile
import subprocess

from uuid import uuid4
from pathlib import Path
from base64 import b64decode
from botocore.client import Config


# Get environment variables
ARCHITECTURE = os.environ["ARCHITECTURE"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
PYTHON_VERSION_NAME = os.environ["PYTHON_VERSION_NAME"]

# Declare requirements file name standard
REQUIREMENTS_FILE_NAME = "requirements.txt"

# Create S3 client
s3 = boto3.client('s3', config=Config(signature_version='s3v4'))


def create_layer(event, context) -> dict:
    """
    This function is written to be called by API Gateway, with a base64-encoded JSON body.
    This function downloads all the requirements for a python layer, zips it up into a layer, and yeets it to S3.
    Then it returns the S3 download URL

    :param event: The AWS API Gateway Lambda Proxy event
    :param context: Nothing that anyone cares about
    :return: a response for API Gateway
    """
    # Get the body from the request
    body = json.loads(b64decode(event["body"]).decode())

    # Get the requirements
    requirements = body["requirements"]

    # Create the layer directory
    layer_name = body["layerName"]
    layer_directory = Path(f"/tmp/{layer_name}")
    os.mkdir(layer_directory)

    # Create the `python` directory inside the layer directory
    os.mkdir(layer_directory / 'python')

    # Create the requirements file
    with open(layer_directory / REQUIREMENTS_FILE_NAME, 'w') as rf:
        rf.write(requirements)

    # Install the requirements
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE_NAME, "-t", "python"], cwd=layer_directory)

    layer_zip_file = Path(f"/tmp/{layer_name}.zip")

    # Zip that shit up
    with zipfile.ZipFile(layer_zip_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for entry in (layer_directory / "python").rglob("*"):
            zip_file.write(entry, entry.relative_to(layer_directory))

    # Remove the layer directory
    shutil.rmtree(layer_directory, ignore_errors=True)

    # Yeet the layer zip file to S3
    layer_s3_key = f"{layer_name}-{PYTHON_VERSION_NAME}-{ARCHITECTURE}-{time.time()}.zip"
    with open(layer_zip_file, "rb") as lf:
        s3.upload_fileobj(
            lf,
            S3_BUCKET_NAME,
            layer_s3_key,
            ExtraArgs={
                "ContentType": "application/zip"
            }
        )

    # Generate an S3 pre-signed URL to download the layer
    layer_download_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": layer_s3_key
        },
        ExpiresIn=100,
        HttpMethod='GET'
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
            "layerDownloadUrl": layer_download_url
        })
    }
