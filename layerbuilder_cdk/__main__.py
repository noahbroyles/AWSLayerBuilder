"""
This deploys the stack to AWS.
"""
import os
import aws_cdk as cdk

from secsie import parse_config_file
from .stacks.layer_stack import LayerStack


# Read the environment config from the file
environmental_config = parse_config_file("environment.conf")[
    "AWS-Deployment-Environment"
]
aws_environment = cdk.Environment(
    account=str(environmental_config["accountNumber"]),
    region=environmental_config["region"],
)

# Get the deployment environment from the ENV environment variable. If it doesn't exist, default to dev.
deployment_environment = os.environ.get("ENV", "dev").lower()

# Create the main CDK app
app = cdk.App()

# Layer stack
layer_stack = LayerStack(
    scope=app,
    construct_id="LayerBuilderStack",
    environment=deployment_environment,
    env=aws_environment,
)

# Synthesize the app
app.synth()
