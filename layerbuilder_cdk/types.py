from typing import List
from dataclasses import dataclass
from aws_cdk.aws_lambda import Runtime, Architecture


@dataclass
class LambdaArchitecture:
    name: str
    architecture: Architecture


@dataclass
class PythonLambdaRuntime:
    name: str
    runtime: Runtime
    supported_architectures: List[LambdaArchitecture]
