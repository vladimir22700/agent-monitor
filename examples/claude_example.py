"""
Claude (Anthropic) monitoring example

This example shows how to monitor Claude API calls.
"""

from agent_monitor import AgentMonitor
from anthropic import Anthropic


def main():
    """Run Claude monitoring example"""

    # Initialize monitor
    monitor = AgentMonitor()

    # Wrap Anthropic client
    client = monitor.wrap_anthropic(Anthropic())

    # Create a trace
    with monitor.trace("claude_workflow"):

        # Use Claude normally - automatically tracked!
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "Explain quantum computing in simple terms."}
            ]
        )

        print(f"Response: {response.content[0].text}")

    # View metrics
    print(f"\n📊 Metrics:")
    print(f"Cost: ${monitor.get_cost():.4f}")
    print(f"Tokens: {monitor.get_tokens():,}")


if __name__ == "__main__":
    main()
