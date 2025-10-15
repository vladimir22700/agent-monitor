"""
LangChain collector for Agent Monitor
"""

from datetime import datetime
from typing import Any

from ..core.types import Span, SpanType


class LangChainCollector:
    """Collector for LangChain agents"""

    def __init__(self, monitor: "AgentMonitor"):
        """Initialize collector"""
        self.monitor = monitor

    def wrap(self, agent: Any) -> Any:
        """Wrap LangChain agent"""
        # Wrap the run method
        original_run = agent.run if hasattr(agent, "run") else None
        original_invoke = agent.invoke if hasattr(agent, "invoke") else None

        if original_run:
            def monitored_run(*args, **kwargs):
                """Monitored version of run"""
                start_time = datetime.utcnow()

                try:
                    # Call original method
                    result = original_run(*args, **kwargs)

                    # Record telemetry
                    if self.monitor._current_trace_id:
                        trace = self.monitor._active_traces[self.monitor._current_trace_id]

                        span = Span(
                            id=f"span_{len(trace.spans)}",
                            trace_id=trace.id,
                            parent_id=None,
                            name="langchain.agent.run",
                            type=SpanType.AGENT_STEP,
                            start_time=start_time,
                            metadata={
                                "provider": "langchain",
                                "agent_type": type(agent).__name__
                            }
                        )

                        span.complete(datetime.utcnow())
                        trace.add_span(span)

                    return result

                except Exception as e:
                    # Record error
                    if self.monitor._current_trace_id:
                        trace = self.monitor._active_traces[self.monitor._current_trace_id]

                        span = Span(
                            id=f"span_{len(trace.spans)}",
                            trace_id=trace.id,
                            parent_id=None,
                            name="langchain.agent.run",
                            type=SpanType.AGENT_STEP,
                            start_time=start_time,
                            metadata={"provider": "langchain"}
                        )

                        span.fail(str(e), type(e).__name__)
                        trace.add_span(span)

                    raise

            agent.run = monitored_run

        if original_invoke:
            def monitored_invoke(*args, **kwargs):
                """Monitored version of invoke"""
                start_time = datetime.utcnow()

                try:
                    # Call original method
                    result = original_invoke(*args, **kwargs)

                    # Record telemetry
                    if self.monitor._current_trace_id:
                        trace = self.monitor._active_traces[self.monitor._current_trace_id]

                        span = Span(
                            id=f"span_{len(trace.spans)}",
                            trace_id=trace.id,
                            parent_id=None,
                            name="langchain.agent.invoke",
                            type=SpanType.AGENT_STEP,
                            start_time=start_time,
                            metadata={
                                "provider": "langchain",
                                "agent_type": type(agent).__name__
                            }
                        )

                        span.complete(datetime.utcnow())
                        trace.add_span(span)

                    return result

                except Exception as e:
                    # Record error
                    if self.monitor._current_trace_id:
                        trace = self.monitor._active_traces[self.monitor._current_trace_id]

                        span = Span(
                            id=f"span_{len(trace.spans)}",
                            trace_id=trace.id,
                            parent_id=None,
                            name="langchain.agent.invoke",
                            type=SpanType.AGENT_STEP,
                            start_time=start_time,
                            metadata={"provider": "langchain"}
                        )

                        span.fail(str(e), type(e).__name__)
                        trace.add_span(span)

                    raise

            agent.invoke = monitored_invoke

        return agent
