"""AgentCore stack — Bedrock AgentCore configuration for Factor."""

from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_lambda as lambda_,
)


class AgentCoreStack(cdk.Stack):
    """AgentCore Runtime, Gateway, and Memory configuration."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        storage_stack,
        auth_stack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.agent_role = iam.Role(
            self, "AgentRole",
            role_name="factor-agent-role",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
            ],
        )

        storage_stack.documents_bucket.grant_read_write(self.agent_role)
        storage_stack.sessions_table.grant_read_write_data(self.agent_role)

        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        )

        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:GetUser",
                    "cognito-idp:AdminGetUser",
                ],
                resources=[auth_stack.user_pool.user_pool_arn],
            )
        )

        cdk.CfnOutput(self, "AgentRoleArn", value=self.agent_role.role_arn)
