"""
Basic example: Monitor OpenAI agents

This example shows how to wrap an OpenAI client for automatic monitoring.
"""

from agent_monitor import AgentMonitor
from openai import OpenAI


def main():
    """Run basic OpenAI monitoring example"""

    # Initialize monitor (uses local SQLite storage by default)
    monitor = AgentMonitor()

    # Wrap your OpenAI client
    client = monitor.wrap_openai(OpenAI())

    # Create a trace for your workflow
    with monitor.trace("example_workflow"):

        # Use OpenAI normally - automatically monitored!
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ]
        )

        print(f"Response: {response.choices[0].message.content}")

    # View metrics
    print(f"\n📊 Metrics:")
    print(f"Cost: ${monitor.get_cost():.4f}")
    print(f"Tokens: {monitor.get_tokens():,}")

    # Generate cost report
    report = monitor.cost_report(time_range="last_hour")
    print(f"\n💰 Cost Report:")
    print(f"Total Cost: ${report.total_cost:.4f}")
    print(f"Total Tokens: {report.total_tokens:,}")


if __name__ == "__main__":
    main()
