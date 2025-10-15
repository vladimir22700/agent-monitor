"""
Core AgentMonitor class - Main entry point for monitoring
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List
from contextlib import contextmanager

from .config import Config, StorageConfig, DashboardConfig
from .types import Trace, Span, TraceStatus, SpanType, MetricsResult, CostReport, ErrorInfo
from ..storage.storage import Storage
from ..storage.sqlite_storage import SQLiteStorage


class AgentMonitor:
    """
    Main monitoring class for AI agents

    Usage:
        monitor = AgentMonitor(api_key="...")
        client = monitor.wrap_openai(OpenAI())
        # Use client normally - automatically monitored!
    """

    def __init__(self, config: Optional[Config] = None, api_key: Optional[str] = None):
        """
        Initialize Agent Monitor

        Args:
            config: Configuration object
            api_key: API key for Agent Monitor cloud (optional)
        """
        self.config = config or Config()
        if api_key:
            self.config.api_key = api_key

        # Initialize storage
        self.storage: Storage = self._init_storage()

        # Active traces
        self._active_traces: Dict[str, Trace] = {}
        self._current_trace_id: Optional[str] = None

        # Metrics cache
        self._metrics_cache: List[Dict[str, Any]] = []

    def _init_storage(self) -> Storage:
        """Initialize storage backend"""
        storage_config = self.config.storage
        if storage_config.type.value == "sqlite":
            return SQLiteStorage(storage_config.get_connection_url())
        else:
            # For now, default to SQLite
            return SQLiteStorage("sqlite:///agent_monitor.db")

    # Client wrappers
    def wrap_openai(self, client: Any) -> Any:
        """
        Wrap OpenAI client for automatic monitoring

        Args:
            client: OpenAI client instance

        Returns:
            Wrapped client with monitoring
        """
        from ..collectors.openai_collector import OpenAICollector
        collector = OpenAICollector(self)
        return collector.wrap(client)

    def wrap_anthropic(self, client: Any) -> Any:
        """
        Wrap Anthropic client for automatic monitoring

        Args:
            client: Anthropic client instance

        Returns:
            Wrapped client with monitoring
        """
        from ..collectors.anthropic_collector import AnthropicCollector
        collector = AnthropicCollector(self)
        return collector.wrap(client)

    def wrap_langchain(self, agent: Any) -> Any:
        """
        Wrap LangChain agent for automatic monitoring

        Args:
            agent: LangChain AgentExecutor instance

        Returns:
            Wrapped agent with monitoring
        """
        from ..collectors.langchain_collector import LangChainCollector
        collector = LangChainCollector(self)
        return collector.wrap(agent)

    # Tracing API
    @contextmanager
    def trace(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a trace context for monitoring a workflow

        Usage:
            with monitor.trace("customer_support_workflow"):
                # Your agent code here
                pass

        Args:
            name: Name of the trace
            metadata: Optional metadata dictionary
        """
        trace_id = str(uuid.uuid4())
        trace = Trace(
            id=trace_id,
            name=name,
            start_time=datetime.utcnow(),
            metadata=metadata or {}
        )

        self._active_traces[trace_id] = trace
        previous_trace_id = self._current_trace_id
        self._current_trace_id = trace_id

        try:
            yield trace
            trace.complete(datetime.utcnow())
        except Exception as e:
            trace.status = TraceStatus.FAILED
            trace.complete(datetime.utcnow())
            raise
        finally:
            self._current_trace_id = previous_trace_id
            self.storage.save_trace(trace)
            del self._active_traces[trace_id]

    @contextmanager
    def span(self, name: str, span_type: SpanType = SpanType.CUSTOM, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a span within a trace

        Usage:
            with monitor.span("classify_intent"):
                # Your code here
                pass

        Args:
            name: Name of the span
            span_type: Type of span (LLM_CALL, TOOL_CALL, etc.)
            metadata: Optional metadata dictionary
        """
        if not self._current_trace_id:
            # No active trace, create one automatically
            with self.trace(name, metadata):
                yield None
            return

        trace = self._active_traces[self._current_trace_id]
        span_id = str(uuid.uuid4())

        span = Span(
            id=span_id,
            trace_id=trace.id,
            parent_id=None,  # Could track parent span in future
            name=name,
            type=span_type,
            start_time=datetime.utcnow(),
            metadata=metadata or {}
        )

        try:
            yield span
            span.complete(datetime.utcnow())
        except Exception as e:
            span.fail(
                error=str(e),
                error_type=type(e).__name__,
                stack_trace=None  # Could capture full stack trace
            )
            raise
        finally:
            trace.add_span(span)

    # Metrics API
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a custom metric

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for filtering
        """
        metric = {
            "name": name,
            "value": value,
            "timestamp": datetime.utcnow(),
            "tags": tags or {}
        }
        self._metrics_cache.append(metric)

        if len(self._metrics_cache) >= self.config.batch_size:
            self._flush_metrics()

    def _flush_metrics(self):
        """Flush metrics cache to storage"""
        if self._metrics_cache:
            self.storage.save_metrics(self._metrics_cache)
            self._metrics_cache.clear()

    # Query API
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        time_range: str = "last_hour",
        **filters
    ) -> MetricsResult:
        """
        Query metrics

        Args:
            metric_name: Name of metric to query
            time_range: Time range (last_hour, last_day, last_week, etc.)
            **filters: Additional filters

        Returns:
            MetricsResult with data points and aggregations
        """
        return self.storage.query_metrics(metric_name, time_range, filters)

    def cost_report(
        self,
        time_range: str = "last_7_days",
        group_by: Optional[str] = None
    ) -> CostReport:
        """
        Generate cost report

        Args:
            time_range: Time range for report
            group_by: Group costs by (task_type, agent, model, etc.)

        Returns:
            CostReport with cost breakdowns
        """
        return self.storage.generate_cost_report(time_range, group_by)

    def get_errors(
        self,
        limit: int = 10,
        time_range: str = "last_hour"
    ) -> List[ErrorInfo]:
        """
        Get recent errors

        Args:
            limit: Maximum number of errors to return
            time_range: Time range to search

        Returns:
            List of ErrorInfo objects
        """
        return self.storage.get_errors(limit, time_range)

    def query(
        self,
        metric: str,
        threshold: Optional[str] = None,
        time_range: str = "last_hour"
    ) -> List[Dict[str, Any]]:
        """
        Query operations by metric threshold

        Args:
            metric: Metric to query (latency, cost, tokens, etc.)
            threshold: Threshold filter (e.g., ">5s", "<0.01")
            time_range: Time range to search

        Returns:
            List of operations matching criteria
        """
        return self.storage.query_operations(metric, threshold, time_range)

    # Simple getters for quick access
    def get_cost(self) -> float:
        """Get total cost for current session"""
        if self._current_trace_id and self._current_trace_id in self._active_traces:
            return self._active_traces[self._current_trace_id].total_cost_usd
        return 0.0

    def get_tokens(self) -> int:
        """Get total tokens for current session"""
        if self._current_trace_id and self._current_trace_id in self._active_traces:
            return self._active_traces[self._current_trace_id].total_tokens
        return 0

    # Dashboard control
    def serve(self, port: Optional[int] = None):
        """
        Start the web dashboard

        Args:
            port: Port to run dashboard on (default from config)
        """
        from ..dashboard.app import DashboardApp

        dashboard_port = port or self.config.dashboard.port
        app = DashboardApp(self, port=dashboard_port)
        app.run()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - flush any pending data"""
        self._flush_metrics()
