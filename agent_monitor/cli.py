"""
Command-line interface for Agent Monitor
"""

import argparse
from .core.monitor import AgentMonitor


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Agent Monitor - Observability for AI agents"
    )

    parser.add_argument(
        "command",
        choices=["serve", "version"],
        help="Command to run"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for dashboard (default: 3000)"
    )

    args = parser.parse_args()

    if args.command == "version":
        from . import __version__
        print(f"Agent Monitor v{__version__}")

    elif args.command == "serve":
        print(f"Starting Agent Monitor dashboard on port {args.port}...")
        monitor = AgentMonitor()
        monitor.serve(port=args.port)


if __name__ == "__main__":
    main()
