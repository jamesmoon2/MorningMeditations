"""
AWS CDK Stack definition for Daily Stoic Reflection service.

Defines all AWS infrastructure: Lambda, S3, EventBridge, and IAM permissions.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_apigateway as apigateway,
    CfnOutput
)
from constructs import Construct


class StoicStack(Stack):
    """CDK Stack for Daily Stoic Reflection email service."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get context values from cdk.json
        anthropic_api_key = self.node.try_get_context("anthropic_api_key")
        sender_email = self.node.try_get_context("sender_email")

        if not anthropic_api_key or anthropic_api_key == "REPLACE_WITH_YOUR_ANTHROPIC_API_KEY":
            print("WARNING: ANTHROPIC_API_KEY not set in cdk.json context")

        # ===== S3 Bucket for State Management =====
        bucket = s3.Bucket(
            self, "StoicBucket",
            bucket_name=None,  # Auto-generate unique name
            versioned=True,  # Enable versioning for safety
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,  # Keep bucket if stack is deleted
            auto_delete_objects=False  # Don't auto-delete on stack deletion
        )

        # ===== Lambda Function =====
        lambda_fn = lambda_.Function(
            self, "DailyStoicSender",
            function_name="DailyStoicSender",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_linux"),
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "SENDER_EMAIL": sender_email or "reflections@jamescmooney.com",
                "ANTHROPIC_API_KEY": anthropic_api_key or "MISSING_API_KEY",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Generates and sends daily stoic reflections via email"
        )

        # Grant Lambda permissions to read/write S3 bucket
        bucket.grant_read_write(lambda_fn)

        # Grant Lambda permissions to send emails via SES
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail"
                ],
                resources=["*"]  # SES doesn't support resource-level permissions for these actions
            )
        )

        # ===== EventBridge Rule (Daily Trigger) =====
        # Schedule: 6 AM Pacific Time
        # PST (UTC-8): 6 AM PST = 14:00 UTC
        # PDT (UTC-7): 6 AM PDT = 13:00 UTC
        # Using 14:00 UTC for consistent 6 AM PST (will be 7 AM during PDT)
        # Adjust to 13:00 UTC if you prefer 6 AM PDT (will be 5 AM during PST)

        rule = events.Rule(
            self, "DailyTrigger",
            rule_name="DailyStoicTrigger",
            description="Triggers daily stoic reflection at 6 AM PT",
            schedule=events.Schedule.cron(
                minute="0",
                hour="14",  # 6 AM PST / 7 AM PDT
                month="*",
                week_day="*",
                year="*"
            ),
            enabled=True
        )

        # Add Lambda as target
        rule.add_target(targets.LambdaFunction(lambda_fn))

        # ===== API Lambda Function =====
        api_lambda_fn = lambda_.Function(
            self, "ReflectionApiHandler",
            function_name="ReflectionApiHandler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="api_handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_linux"),
            timeout=Duration.seconds(10),
            memory_size=128,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="API handler for serving daily stoic reflections"
        )

        # Grant API Lambda read-only access to S3 bucket
        bucket.grant_read(api_lambda_fn)

        # ===== API Gateway =====
        api = apigateway.RestApi(
            self, "ReflectionApi",
            rest_api_name="Morning Reflections API",
            description="Public API for accessing daily stoic reflections",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_burst_limit=10,  # Max concurrent requests
                throttling_rate_limit=5,    # Requests per second
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "OPTIONS"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
                max_age=Duration.hours(1)
            ),
            endpoint_types=[apigateway.EndpointType.REGIONAL]
        )

        # Create Lambda integration
        api_integration = apigateway.LambdaIntegration(
            api_lambda_fn,
            proxy=True,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                )
            ]
        )

        # Create /reflection resource
        reflection_resource = api.root.add_resource("reflection")

        # Add /reflection/today endpoint
        today_resource = reflection_resource.add_resource("today")
        today_resource.add_method(
            "GET",
            api_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # Add /reflection/{date} endpoint
        date_resource = reflection_resource.add_resource("{date}")
        date_resource.add_method(
            "GET",
            api_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # ===== CloudFormation Outputs =====
        CfnOutput(
            self, "BucketName",
            value=bucket.bucket_name,
            description="S3 bucket name for state files",
            export_name=f"{self.stack_name}-BucketName"
        )

        CfnOutput(
            self, "LambdaFunctionName",
            value=lambda_fn.function_name,
            description="Lambda function name",
            export_name=f"{self.stack_name}-LambdaFunctionName"
        )

        CfnOutput(
            self, "LambdaFunctionArn",
            value=lambda_fn.function_arn,
            description="Lambda function ARN",
            export_name=f"{self.stack_name}-LambdaFunctionArn"
        )

        CfnOutput(
            self, "EventRuleName",
            value=rule.rule_name,
            description="EventBridge rule name",
            export_name=f"{self.stack_name}-EventRuleName"
        )

        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name=f"{self.stack_name}-ApiUrl"
        )

        CfnOutput(
            self, "ApiTodayEndpoint",
            value=f"{api.url}reflection/today",
            description="Endpoint for today's reflection",
            export_name=f"{self.stack_name}-ApiTodayEndpoint"
        )

        CfnOutput(
            self, "ApiDateEndpoint",
            value=f"{api.url}reflection/{{date}}",
            description="Endpoint for specific date reflection (replace {{date}} with YYYY-MM-DD)",
            export_name=f"{self.stack_name}-ApiDateEndpoint"
        )

        # Store references for potential use
        self.bucket = bucket
        self.lambda_function = lambda_fn
        self.event_rule = rule
        self.api_lambda_function = api_lambda_fn
        self.api = api
