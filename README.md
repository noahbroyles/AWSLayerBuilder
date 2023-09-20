# AWSLayerBuilder

This is a dope tool to build lambda layers for AWS. Currently, it only works to build Python layers. 
Considering how much free time I have, it might always be that way.

## How to use
You can use the existing API deployment available at https://op71hud2zj.execute-api.us-east-2.amazonaws.com/LayerAPI, or 
create your own instance of the layer builder API via the AWS CDK.

1. To use the existing layer builder API, use the example at [`createALayer.py`](https://github.com/noahbroyles/AWSLayerBuilder/blob/master/createALayer.py).
2. To create a deployment of the layer builder in your own AWS account, clone the repo and create the following `environment.conf` file:
```ini
[AWS-Deployment-Environment]
    accountNumber = your_account_number
    region = us-east-2  # can be whichever region you prefer
```

Then run the following commands:
```console
# Install the requirements
python3 -m pip install -r requirements.txt

# Deploy the layer builder CDK stack
cdk deploy --all --require-approval never
```

You should see a new CloudFormation stack called `LayerBuilderStack-dev`. If you want to deploy a prod stack, just sent the environment variable `ENV` to `prod`.
All this does is change the environment prefix in the stack name, so the stack would be `LayerBuilderStack-prod`.
