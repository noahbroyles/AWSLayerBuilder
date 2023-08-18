"""
Use this script to generate and download a layer with the requirements you specify.
"""
import json
import requests

from base64 import b64encode

python_version = 'python3.10'
architecture = 'X86_64'
layer_name = "CommonPythonModules"
requirements = """
twilio~=7.3.0
google~=3.0.0
requests~=2.23.0
pymssql~=2.2.8
addict==2.4.0
secsie-conf==3.1.1
boto3>=1.26
"""

b64_body = b64encode(
    json.dumps(
        {
            "requirements": requirements,
            "layerName": layer_name,
        }
    ).encode()
).decode()


LAYER_API_URL = 'https://op71hud2zj.execute-api.us-east-2.amazonaws.com/LayerAPI'

response = requests.post(
    f"{LAYER_API_URL}/{python_version}/{architecture}",
    data=b64_body
).json()

print(f'You can download your layer at {response["layerDownloadUrl"]}')
