"""
Observability: OpenTelemetry + AWS CloudWatch via ADOT (AWS Distro for OpenTelemetry).
Call setup_telemetry() once at application startup.

Traces flow to CloudWatch → visible in CloudWatch ServiceLens and X-Ray.
Logs go to CloudWatch Logs via standard Python logging.
"""

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from config import APP_NAME, LOG_LEVEL


def setup_telemetry() -> trace.Tracer:
    # Standard Python logging — CloudWatch agent or Lambda picks this up automatically
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # OpenTelemetry → ADOT Collector → CloudWatch / X-Ray
    # ADOT Collector runs as a sidecar (EKS/ECS) or Lambda layer
    # Default OTLP gRPC endpoint: localhost:4317
    exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    return trace.get_tracer(APP_NAME)


def trace_agent_call(tracer: trace.Tracer, agent_name: str, user_id: str, session_id: str):
    """Context manager: wraps an agent invocation in a named trace span."""
    return tracer.start_as_current_span(
        f"agent.{agent_name}",
        attributes={
            "agent.name":   agent_name,
            "user.id":      user_id,
            "session.id":   session_id,
            "app.name":     APP_NAME,
            "cloud":        "aws",
        },
    )
