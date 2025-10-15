"""
Agent Monitor - Open-source observability for AI agents

Real-time tracing, metrics, cost tracking, and debugging for production AI agent systems.
Works with OpenAI, Claude, LangChain, and custom agents.
"""

from .core.monitor import AgentMonitor
from .core.config import Config, StorageConfig, DashboardConfig
from .core.types import MetricsResult, CostReport, Trace, Span

__version__ = "0.1.0"
__author__ = "Cognio AI Lab"
__email__ = "dev@cogniolab.com"

__all__ = [
    "AgentMonitor",
    "Config",
    "StorageConfig",
    "DashboardConfig",
    "MetricsResult",
    "CostReport",
    "Trace",
    "Span",
]
