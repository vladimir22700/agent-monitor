"""
Configuration classes for Agent Monitor
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class StorageType(Enum):
    """Supported storage backends"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MEMORY = "memory"


class ExporterType(Enum):
    """Supported metric exporters"""
    PROMETHEUS = "prometheus"
    JAEGER = "jaeger"
    OTLP = "otlp"


@dataclass
class StorageConfig:
    """Storage configuration"""
    type: StorageType = StorageType.SQLITE
    connection_string: str = "sqlite:///agent_monitor.db"

    # PostgreSQL specific
    host: str = "localhost"
    port: int = 5432
    database: str = "agent_monitor"
    username: Optional[str] = None
    password: Optional[str] = None

    # Performance
    pool_size: int = 10
    max_overflow: int = 20

    def get_connection_url(self) -> str:
        """Get database connection URL"""
        if self.type == StorageType.SQLITE:
            return self.connection_string
        elif self.type == StorageType.POSTGRESQL:
            if self.connection_string != "sqlite:///agent_monitor.db":
                return self.connection_string

            auth = ""
            if self.username and self.password:
                auth = f"{self.username}:{self.password}@"
            return f"postgresql://{auth}{self.host}:{self.port}/{self.database}"
        else:
            return "memory://"


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    enabled: bool = True
    host: str = "localhost"
    port: int = 3000

    # Authentication
    auth_enabled: bool = False
    auth_type: str = "basic"  # basic, oauth, jwt

    # Features
    real_time_updates: bool = True
    update_interval_ms: int = 1000


@dataclass
class ExporterConfig:
    """Metrics exporter configuration"""
    type: ExporterType
    enabled: bool = True

    # Prometheus
    prometheus_port: int = 9090

    # Jaeger
    jaeger_endpoint: str = "http://localhost:14268"

    # OTLP
    otlp_endpoint: str = "http://localhost:4317"


@dataclass
class AlertConfig:
    """Alert configuration"""
    name: str
    condition: str  # e.g., "cost_per_hour > 10.0"
    channels: list = field(default_factory=list)  # email, slack, pagerduty
    enabled: bool = True
    cooldown_minutes: int = 15


@dataclass
class Config:
    """Main configuration for Agent Monitor"""

    # API configuration
    api_key: Optional[str] = None

    # Storage
    storage: StorageConfig = field(default_factory=StorageConfig)

    # Dashboard
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)

    # Exporters
    exporters: list[ExporterConfig] = field(default_factory=list)

    # Alerts
    alerts: list[AlertConfig] = field(default_factory=list)

    # Sampling
    sample_rate: float = 1.0  # 1.0 = 100% sampling

    # Features
    tracing_enabled: bool = True
    metrics_enabled: bool = True
    cost_tracking_enabled: bool = True

    # Performance
    batch_size: int = 100
    flush_interval_seconds: int = 10

    # Additional settings
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create config from dictionary"""
        return cls(**config_dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load config from YAML file"""
        import yaml
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
