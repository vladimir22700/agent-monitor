"""
Dashboard application for Agent Monitor
"""

from typing import Optional


class DashboardApp:
    """Web dashboard for Agent Monitor"""

    def __init__(self, monitor: "AgentMonitor", port: int = 3000):
        """Initialize dashboard"""
        self.monitor = monitor
        self.port = port

    def run(self):
        """Run the dashboard server"""
        print(f"Dashboard would run on http://localhost:{self.port}")
        print("Dashboard implementation coming soon!")
        print("\nFor now, you can:")
        print("1. Query metrics programmatically using monitor.get_metrics()")
        print("2. Generate cost reports using monitor.cost_report()")
        print("3. View errors using monitor.get_errors()")
