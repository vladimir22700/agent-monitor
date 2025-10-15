"""
SQLite storage implementation for Agent Monitor
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .storage import Storage
from ..core.types import Trace, Span, MetricsResult, CostReport, ErrorInfo, TraceStatus


class SQLiteStorage(Storage):
    """SQLite storage backend"""

    def __init__(self, connection_string: str):
        """Initialize SQLite storage"""
        # Remove sqlite:/// prefix
        db_path = connection_string.replace("sqlite:///", "")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Traces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_ms REAL,
                status TEXT NOT NULL,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                error_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)

        # Spans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                parent_id TEXT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_ms REAL,
                status TEXT NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                error TEXT,
                error_type TEXT,
                stack_trace TEXT,
                metadata TEXT,
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            )
        """)

        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                tags TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics(name, timestamp)")

        self.conn.commit()

    def save_trace(self, trace: Trace) -> None:
        """Save a trace to storage"""
        cursor = self.conn.cursor()

        # Save trace
        cursor.execute("""
            INSERT INTO traces (id, name, start_time, end_time, duration_ms, status,
                               total_tokens, total_cost_usd, error_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace.id,
            trace.name,
            trace.start_time,
            trace.end_time,
            trace.duration_ms,
            trace.status.value,
            trace.total_tokens,
            trace.total_cost_usd,
            trace.error_count,
            json.dumps(trace.metadata)
        ))

        # Save spans
        for span in trace.spans:
            cursor.execute("""
                INSERT INTO spans (id, trace_id, parent_id, name, type, start_time, end_time,
                                  duration_ms, status, input_tokens, output_tokens, cost_usd,
                                  error, error_type, stack_trace, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                span.id,
                span.trace_id,
                span.parent_id,
                span.name,
                span.type.value,
                span.start_time,
                span.end_time,
                span.duration_ms,
                span.status.value,
                span.input_tokens,
                span.output_tokens,
                span.cost_usd,
                span.error,
                span.error_type,
                span.stack_trace,
                json.dumps(span.metadata)
            ))

        self.conn.commit()

    def save_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """Save metrics batch to storage"""
        cursor = self.conn.cursor()

        for metric in metrics:
            cursor.execute("""
                INSERT INTO metrics (name, value, timestamp, tags)
                VALUES (?, ?, ?, ?)
            """, (
                metric["name"],
                metric["value"],
                metric["timestamp"],
                json.dumps(metric["tags"])
            ))

        self.conn.commit()

    def query_metrics(
        self,
        metric_name: Optional[str],
        time_range: str,
        filters: Dict[str, Any]
    ) -> MetricsResult:
        """Query metrics from storage"""
        cursor = self.conn.cursor()

        # Parse time range
        end_time = datetime.utcnow()
        start_time = self._parse_time_range(time_range, end_time)

        # Build query
        query = "SELECT name, value, timestamp FROM metrics WHERE timestamp >= ? AND timestamp <= ?"
        params = [start_time, end_time]

        if metric_name:
            query += " AND name = ?"
            params.append(metric_name)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        data_points = [
            {"name": row[0], "value": row[1], "timestamp": row[2]}
            for row in rows
        ]

        # Calculate aggregations
        values = [row[1] for row in rows]
        aggregations = {}
        if values:
            aggregations = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
                "count": len(values)
            }

        return MetricsResult(
            metric_name=metric_name or "all",
            time_range=time_range,
            data_points=data_points,
            aggregations=aggregations
        )

    def generate_cost_report(
        self,
        time_range: str,
        group_by: Optional[str]
    ) -> CostReport:
        """Generate cost report"""
        cursor = self.conn.cursor()

        end_time = datetime.utcnow()
        start_time = self._parse_time_range(time_range, end_time)

        # Get total costs
        cursor.execute("""
            SELECT
                SUM(total_cost_usd) as total_cost,
                SUM(total_tokens) as total_tokens
            FROM traces
            WHERE start_time >= ? AND start_time <= ?
        """, (start_time, end_time))

        row = cursor.fetchone()
        total_cost = row[0] or 0.0
        total_tokens = row[1] or 0

        # Calculate days
        days = (end_time - start_time).days or 1
        cost_per_day = total_cost / days

        return CostReport(
            time_range=time_range,
            total_cost=total_cost,
            cost_per_day=cost_per_day,
            total_tokens=total_tokens,
            input_tokens=0,  # Could track separately
            output_tokens=0
        )

    def get_errors(self, limit: int, time_range: str) -> List[ErrorInfo]:
        """Get recent errors"""
        cursor = self.conn.cursor()

        end_time = datetime.utcnow()
        start_time = self._parse_time_range(time_range, end_time)

        cursor.execute("""
            SELECT id, trace_id, start_time, error, error_type, stack_trace
            FROM spans
            WHERE status = 'failed' AND start_time >= ? AND start_time <= ?
            ORDER BY start_time DESC
            LIMIT ?
        """, (start_time, end_time, limit))

        rows = cursor.fetchall()

        return [
            ErrorInfo(
                id=row[0],
                trace_id=row[1],
                span_id=row[0],
                timestamp=datetime.fromisoformat(row[2]),
                message=row[3] or "Unknown error",
                error_type=row[4] or "Error",
                stack_trace=row[5]
            )
            for row in rows
        ]

    def query_operations(
        self,
        metric: str,
        threshold: Optional[str],
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Query operations by metric"""
        cursor = self.conn.cursor()

        end_time = datetime.utcnow()
        start_time = self._parse_time_range(time_range, end_time)

        # Simple implementation - could be enhanced
        cursor.execute("""
            SELECT id, trace_id, name, duration_ms, cost_usd
            FROM spans
            WHERE start_time >= ? AND start_time <= ?
            ORDER BY duration_ms DESC
            LIMIT 100
        """, (start_time, end_time))

        rows = cursor.fetchall()

        return [
            {
                "span_id": row[0],
                "trace_id": row[1],
                "operation": row[2],
                "duration": row[3],
                "cost": row[4],
                "trace_url": f"/trace/{row[1]}"
            }
            for row in rows
        ]

    def _parse_time_range(self, time_range: str, end_time: datetime) -> datetime:
        """Parse time range string to start datetime"""
        ranges = {
            "last_hour": timedelta(hours=1),
            "last_day": timedelta(days=1),
            "last_7_days": timedelta(days=7),
            "last_week": timedelta(weeks=1),
            "last_month": timedelta(days=30)
        }

        delta = ranges.get(time_range, timedelta(hours=1))
        return end_time - delta
