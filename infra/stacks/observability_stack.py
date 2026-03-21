"""Observability stack — CloudWatch dashboards and alarms for Factor."""

from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
)


class ObservabilityStack(cdk.Stack):
    """CloudWatch dashboards, log groups, and alarms for Factor agents."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agentcore_stack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.log_group = logs.LogGroup(
            self, "AgentLogGroup",
            log_group_name="/factor/agents",
            retention=logs.RetentionDays.THIRTY_DAYS,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.dashboard = cloudwatch.Dashboard(
            self, "FactorDashboard",
            dashboard_name="factor-agents",
        )

        self.dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown="# Factor Agent Dashboard\nMonitoring for the Factor agentic AI system.",
                width=24,
                height=2,
            ),
        )

        self.dashboard.add_widgets(
            cloudwatch.LogQueryWidget(
                title="Agent Errors (Last 24h)",
                log_group_names=[self.log_group.log_group_name],
                query_lines=[
                    "fields @timestamp, @message",
                    "filter @message like /ERROR/",
                    "sort @timestamp desc",
                    "limit 20",
                ],
                width=12,
                height=6,
            ),
            cloudwatch.LogQueryWidget(
                title="Agent Activity (Last 24h)",
                log_group_names=[self.log_group.log_group_name],
                query_lines=[
                    "fields @timestamp, @message",
                    "filter @message like /Created|Completed|Started/",
                    "sort @timestamp desc",
                    "limit 20",
                ],
                width=12,
                height=6,
            ),
        )

        cdk.CfnOutput(self, "LogGroupName", value=self.log_group.log_group_name)
        cdk.CfnOutput(self, "DashboardName", value=self.dashboard.dashboard_name)
