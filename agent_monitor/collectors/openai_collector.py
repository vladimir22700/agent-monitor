"""
OpenAI collector for Agent Monitor
"""

from datetime import datetime
from typing import Any, Optional
import inspect

from ..core.types import Span, SpanType, TraceStatus


class OpenAICollector:
    """Collector for OpenAI clients"""

    # Pricing per 1M tokens (approximate, may need updates)
    MODEL_PRICING = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6}
    }

    def __init__(self, monitor: "AgentMonitor"):
        """Initialize collector"""
        self.monitor = monitor

    def wrap(self, client: Any) -> Any:
        """Wrap OpenAI client"""
        # Wrap the chat.completions.create method
        original_create = client.chat.completions.create

        def monitored_create(*args, **kwargs):
            """Monitored version of create"""
            start_time = datetime.utcnow()

            # Extract model
            model = kwargs.get("model", args[0] if args else "unknown")

            # Create span
            span_name = f"openai.chat.{model}"

            try:
                # Call original method
                response = original_create(*args, **kwargs)

                # Extract token usage
                usage = response.usage if hasattr(response, "usage") else None
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0

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
                            "provider": "openai"
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
                        metadata={"model": model, "provider": "openai"}
                    )

                    span.fail(str(e), type(e).__name__)
                    trace.add_span(span)

                raise

        # Replace the method
        client.chat.completions.create = monitored_create

        return client

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        # Find matching model pricing (handle versioned models)
        pricing = None
        for model_key, model_pricing in self.MODEL_PRICING.items():
            if model.startswith(model_key):
                pricing = model_pricing
                break

        if not pricing:
            pricing = {"input": 1.0, "output": 2.0}  # Default

        # Cost is per 1M tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
