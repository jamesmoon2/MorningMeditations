#!/usr/bin/env python3
"""
CDK app entry point for Daily Stoic Reflection service.

This file initializes the CDK app and creates the StoicStack.
"""

import aws_cdk as cdk
from infra.stoic_stack import StoicStack


# Create CDK app
app = cdk.App()

# Create the stack
StoicStack(
    app,
    "DailyStoicStack",
    env=cdk.Environment(
        # Use default account and region from AWS CLI config
        # Or specify explicitly:
        # account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        # region=os.environ.get("CDK_DEFAULT_REGION")
        region="us-east-1"  # Explicitly set region
    ),
    description="Daily Stoic reflection email service - generates and sends philosophical reflections",
    tags={
        "Project": "DailyStoicReflection",
        "ManagedBy": "CDK",
        "Environment": "Production"
    }
)

# Synthesize CloudFormation template
app.synth()
