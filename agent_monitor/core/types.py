"""
Core type definitions for Agent Monitor
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class TraceStatus(Enum):
    """Trace execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SpanType(Enum):
    """Types of spans"""
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    AGENT_STEP = "agent_step"
    CUSTOM = "custom"


@dataclass
class Span:
    """Represents a single operation within a trace"""
    id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    type: SpanType
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: TraceStatus = TraceStatus.RUNNING

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Cost tracking
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None

    def complete(self, end_time: datetime):
        """Mark span as completed"""
        self.end_time = end_time
        self.duration_ms = (end_time - self.start_time).total_seconds() * 1000
        self.status = TraceStatus.COMPLETED

    def fail(self, error: str, error_type: str, stack_trace: Optional[str] = None):
        """Mark span as failed"""
        self.error = error
        self.error_type = error_type
        self.stack_trace = stack_trace
        self.status = TraceStatus.FAILED
        if not self.end_time:
            self.end_time = datetime.utcnow()
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


@dataclass
class Trace:
    """Represents a complete execution trace"""
    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: TraceStatus = TraceStatus.RUNNING

    # Spans in this trace
    spans: List[Span] = field(default_factory=list)

    # Aggregated metrics
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    error_count: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span):
        """Add a span to this trace"""
        self.spans.append(span)
        self.total_tokens += span.input_tokens + span.output_tokens
        self.total_cost_usd += span.cost_usd
        if span.status == TraceStatus.FAILED:
            self.error_count += 1

    def complete(self, end_time: datetime):
        """Mark trace as completed"""
        self.end_time = end_time
        self.duration_ms = (end_time - self.start_time).total_seconds() * 1000
        self.status = TraceStatus.COMPLETED if self.error_count == 0 else TraceStatus.FAILED


@dataclass
class MetricsResult:
    """Result of a metrics query"""
    metric_name: str
    time_range: str
    data_points: List[Dict[str, Any]]
    aggregations: Dict[str, float] = field(default_factory=dict)

    def __repr__(self):
        return f"MetricsResult(metric={self.metric_name}, points={len(self.data_points)})"


@dataclass
class CostReport:
    """Cost analysis report"""
    time_range: str
    total_cost: float
    cost_per_day: float
    top_cost_task: Optional[str] = None
    top_cost_agent: Optional[str] = None

    # Breakdown by category
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_operation: Dict[str, float] = field(default_factory=dict)
    cost_by_agent: Dict[str, float] = field(default_factory=dict)

    # Token usage
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def __repr__(self):
        return f"CostReport(total=${self.total_cost:.2f}, tokens={self.total_tokens:,})"


@dataclass
class ErrorInfo:
    """Information about an error"""
    id: str
    timestamp: datetime
    trace_id: str
    span_id: str
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    replay_url: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    metric_name: str
    period: str

    # Latency percentiles
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float

    # Throughput
    requests_per_second: float
    total_requests: int

    # Success/Error rates
    success_rate: float
    error_rate: float

    def __repr__(self):
        return f"PerformanceMetrics(p50={self.p50_ms:.1f}ms, p95={self.p95_ms:.1f}ms, rps={self.requests_per_second:.1f})"
