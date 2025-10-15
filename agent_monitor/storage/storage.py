"""
Abstract storage interface for Agent Monitor
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..core.types import Trace, MetricsResult, CostReport, ErrorInfo


class Storage(ABC):
    """Abstract storage interface"""

    @abstractmethod
    def save_trace(self, trace: Trace) -> None:
        """Save a trace to storage"""
        pass

    @abstractmethod
    def save_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """Save metrics batch to storage"""
        pass

    @abstractmethod
    def query_metrics(
        self,
        metric_name: Optional[str],
        time_range: str,
        filters: Dict[str, Any]
    ) -> MetricsResult:
        """Query metrics from storage"""
        pass

    @abstractmethod
    def generate_cost_report(
        self,
        time_range: str,
        group_by: Optional[str]
    ) -> CostReport:
        """Generate cost report"""
        pass

    @abstractmethod
    def get_errors(self, limit: int, time_range: str) -> List[ErrorInfo]:
        """Get recent errors"""
        pass

    @abstractmethod
    def query_operations(
        self,
        metric: str,
        threshold: Optional[str],
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Query operations by metric"""
        pass
