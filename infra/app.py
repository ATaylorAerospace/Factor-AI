#!/usr/bin/env python3
"""CDK application entry point for Factor infrastructure."""

import aws_cdk as cdk

from stacks.storage_stack import StorageStack
from stacks.auth_stack import AuthStack
from stacks.agentcore_stack import AgentCoreStack
from stacks.observability_stack import ObservabilityStack

app = cdk.App()

env = cdk.Environment(region="us-west-2")

storage = StorageStack(app, "FactorStorage", env=env)
auth = AuthStack(app, "FactorAuth", env=env)
agentcore = AgentCoreStack(
    app, "FactorAgentCore",
    env=env,
    storage_stack=storage,
    auth_stack=auth,
)
observability = ObservabilityStack(
    app, "FactorObservability",
    env=env,
    agentcore_stack=agentcore,
)

app.synth()
