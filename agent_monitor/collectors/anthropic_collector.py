"""
Anthropic (Claude) collector for Agent Monitor
"""

from datetime import datetime
from typing import Any

from ..core.types import Span, SpanType


class AnthropicCollector:
    """Collector for Anthropic/Claude clients"""

    # Pricing per 1M tokens (approximate)
    MODEL_PRICING = {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet": {"input": 3.0, "output": 15.0}
    }

    def __init__(self, monitor: "AgentMonitor"):
        """Initialize collector"""
        self.monitor = monitor

    def wrap(self, client: Any) -> Any:
        """Wrap Anthropic client"""
        # Wrap the messages.create method
        original_create = client.messages.create

        def monitored_create(*args, **kwargs):
            """Monitored version of create"""
            start_time = datetime.utcnow()

            # Extract model
            model = kwargs.get("model", args[0] if args else "unknown")

            # Create span name
            span_name = f"anthropic.messages.{model}"

            try:
                # Call original method
                response = original_create(*args, **kwargs)

                # Extract token usage
                usage = response.usage if hasattr(response, "usage") else None
                input_tokens = usage.input_tokens if usage else 0
                output_tokens = usage.output_tokens if usage else 0

                # Calculate cost
                cost = self._calculate_cost(model, input_tokens, output_tokens)

                # Record telemetry
                if self.monitor._current_trace_id:
                    trace = self.monitor._active_traces[self.monitor._current_trace_id]

                    span = Span(
                        id=f"span_{len(trace.spans)}",
                        trace_id=trace.id,
                        parent_id=None,
                        name=span_name,
                        type=SpanType.LLM_CALL,
                        start_time=start_time,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=cost,
                        metadata={
                            "model": model,
                            "provider": "anthropic"
                        }
                    )

                    span.complete(datetime.utcnow())
                    trace.add_span(span)

                return response

            except Exception as e:
                # Record error
                if self.monitor._current_trace_id:
                    trace = self.monitor._active_traces[self.monitor._current_trace_id]

                    span = Span(
                        id=f"span_{len(trace.spans)}",
                        trace_id=trace.id,
                        parent_id=None,
                        name=span_name,
                        type=SpanType.LLM_CALL,
                        start_time=start_time,
                        metadata={"model": model, "provider": "anthropic"}
                    )

                    span.fail(str(e), type(e).__name__)
                    trace.add_span(span)

                raise

        # Replace the method
        client.messages.create = monitored_create

        return client

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        # Find matching model pricing
        pricing = None
        for model_key, model_pricing in self.MODEL_PRICING.items():
            if model.startswith(model_key):
                pricing = model_pricing
                break

        if not pricing:
            pricing = {"input": 3.0, "output": 15.0}  # Default to Sonnet pricing

        # Cost is per 1M tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
