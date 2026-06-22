"""
Observability: OpenTelemetry + AWS CloudWatch via ADOT (AWS Distro for OpenTelemetry).

Call setup_telemetry() once at application startup (module level in main.py).
Subsequent calls are safe — the function is idempotent.

Traces flow: app -> OTLP -> ADOT Collector -> CloudWatch / X-Ray
Logs flow:   app -> Python logging -> CloudWatch Logs (via log agent or Lambda)

ADOT Collector runs as:
  - ECS/EKS: a sidecar container (public.ecr.aws/aws-observability/aws-otel-collector)
  - Lambda:  an AWS-managed Lambda layer
  - Local:   not required; spans are sent but collector may not be running
"""

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from config import APP_NAME, LOG_LEVEL

_tracer: trace.Tracer | None = None


def setup_telemetry() -> trace.Tracer:
    """Initialize structured logging and OpenTelemetry tracing. Safe to call multiple times.

    Returns:
        A named OpenTelemetry Tracer for the application.
    """
    global _tracer
    if _tracer is not None:
        return _tracer

    # Structured logging — picked up by CloudWatch Logs agent or Lambda runtime
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # OpenTelemetry -> ADOT Collector -> CloudWatch / X-Ray
    # Default OTLP gRPC endpoint: localhost:4317 (ADOT sidecar)
    exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _tracer = trace.get_tracer(APP_NAME)
    return _tracer


def trace_agent_call(tracer: trace.Tracer, agent_name: str, user_id: str, session_id: str):
    """Context manager: wraps an agent invocation in a named trace span."""
    return tracer.start_as_current_span(
        f"agent.{agent_name}",
        attributes={
            "agent.name": agent_name,
            "user.id":    user_id,
            "session.id": session_id,
            "app.name":   APP_NAME,
            "cloud":      "aws",
        },
    )
