import aws_cdk as cdk

from pathlib import Path
from constructs import Construct
from aws_cdk.aws_apigateway import LambdaIntegration
from aws_cdk.aws_lambda import Runtime, Function, Architecture
from layerbuilder_cdk.types import LambdaArchitecture, PythonLambdaRuntime


# Declare various paths
repository_dir = Path(__file__).parent.parent.parent


class LayerStack(cdk.Stack):
    """
    This stack contains general resources which control the BestNest-Shopify integration.

    There are 3 possible deployments of this stack, one for dev, uat, and prod.
    """


    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        """
        Initialize the Layer stack.

        :param scope: The app to create the stack in
        :param construct_id: The name of the stack
        :param environment: The deployment environment for the current stack, either dev, uat, or prod.
        :param kwargs: Any additional keyword arguments
        """
        super().__init__(scope, f"{construct_id}-{environment}", **kwargs)  # The stack name is the name-environment
        self.dev_environment = environment

        ###################################################################
        #                       S3 LAYER BUCKET                           #
        ###################################################################
        self.layer_bucket = cdk.aws_s3.Bucket(
            self,
            f'layer-bucket-{self.dev_environment}',
            encryption=cdk.aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        ###################################################################
        #                  CREATE LAYER BUILDER LAMBDAS                   #
        ###################################################################
        # Create structures of all the supported architectures and python lambda runtimes. See https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
        lambda_architectures = {
            "ARM_64": LambdaArchitecture(architecture=Architecture.ARM_64, name="ARM_64"),  # type: ignore
            "X86_64": LambdaArchitecture(architecture=Architecture.X86_64, name="X86_64"),  # type: ignore
        }
        python_runtimes = {
            "python3.7": PythonLambdaRuntime(runtime=Runtime.PYTHON_3_7, name='python3.7', supported_architectures=[lambda_architectures["X86_64"]]),                                     # type: ignore
            "python3.8": PythonLambdaRuntime(runtime=Runtime.PYTHON_3_8, name='python3.8', supported_architectures=[lambda_architectures["ARM_64"], lambda_architectures["X86_64"]]),     # type: ignore
            "python3.9": PythonLambdaRuntime(runtime=Runtime.PYTHON_3_9, name='python3.9', supported_architectures=[lambda_architectures["ARM_64"], lambda_architectures["X86_64"]]),     # type: ignore
            "python3.10": PythonLambdaRuntime(runtime=Runtime.PYTHON_3_10, name='python3.10', supported_architectures=[lambda_architectures["ARM_64"], lambda_architectures["X86_64"]]),  # type: ignore
            "python3.11": PythonLambdaRuntime(runtime=Runtime.PYTHON_3_11, name='python3.11', supported_architectures=[lambda_architectures["ARM_64"], lambda_architectures["X86_64"]]),  # type: ignore
        }

        # Now build all the lambdas
        self.lambdas = {}
        for runtime_key, runtime in python_runtimes.items():
            for arch in runtime.supported_architectures:
                if self.lambdas.get(runtime_key) is not None:
                    self.lambdas[runtime_key][arch.name] = self.create_python_layer_builder(python_runtime=runtime, architecture=arch)
                else:
                    self.lambdas[runtime_key] = {
                        arch.name: self.create_python_layer_builder(python_runtime=runtime, architecture=arch)
                    }

        ###################################################################
        #                       API GATEWAY                               #
        ###################################################################
        # Layer Rest API
        layer_api = cdk.aws_apigateway.RestApi(
            self,
            f'layer-api-{environment}',
            deploy=True,
            deploy_options={
                "stage_name": "LayerAPI"
            },
            default_cors_preflight_options=cdk.aws_apigateway.CorsOptions(
                allow_origins=cdk.aws_apigateway.Cors.ALL_ORIGINS,      # type: ignore
                allow_methods=cdk.aws_apigateway.Cors.ALL_METHODS,      # type: ignore
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
                allow_credentials=True
            ),
        )
        
        # Create API resources for each Python version
        for python_version, arch_functions in self.lambdas.items():
            # Get the current runtime
            current_runtime: PythonLambdaRuntime = python_runtimes[python_version]
            # Create a resource for the python version
            python_version_resource = layer_api.root.add_resource(python_version)
            # Add a resource for each specific architecture
            for arch in current_runtime.supported_architectures:
                arch_resource = python_version_resource.add_resource(arch.name)
                # Add a method to create a layer with this specific version and architecture
                arch_resource.add_method(
                    'POST',
                    integration=LambdaIntegration(handler=arch_functions[arch.name])
                )

    def create_python_layer_builder(self, python_runtime: PythonLambdaRuntime, architecture: LambdaArchitecture) -> Function:
        """
        Create a lambda function for building a Python layer for a specific version of Python.

        :param python_runtime: The Python version of the layer builder
        :param architecture: The architecture of the lambda function
        :return: The created lambda function for building layers
        """
        # First we need to create the layer builder lambda
        layer_builder = Function(
            self,
            f'create-{python_runtime.name}-{architecture.name}-layer-{self.dev_environment}',
            code=cdk.aws_lambda.Code.from_asset((repository_dir / "lambdas" / "layerCreation").as_posix()),
            handler="create_python_layer.create_layer",
            runtime=python_runtime.runtime,
            architecture=architecture.architecture,
            timeout=cdk.Duration.minutes(5),
            memory_size=3008,
            ephemeral_storage_size=cdk.Size.gibibytes(8),
            environment={
                "S3_BUCKET_NAME": self.layer_bucket.bucket_name,
                "PYTHON_VERSION_NAME": python_runtime.name,
                "ARCHITECTURE": architecture.name
            }
        )

        # Grant the lambda permissions on the layer bucket
        self.layer_bucket.grant_read_write(layer_builder)

        # return the lambda
        return layer_builder
