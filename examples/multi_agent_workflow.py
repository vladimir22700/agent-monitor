"""
Multi-agent workflow monitoring example

This example demonstrates monitoring a complex workflow with multiple agents
and nested operations.
"""

from agent_monitor import AgentMonitor
from openai import OpenAI


def classify_query(client, query: str) -> str:
    """Classify user query intent"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify this query as 'technical', 'sales', or 'support'."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content.strip().lower()


def handle_technical_query(client, query: str) -> str:
    """Handle technical queries"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a technical expert. Provide detailed technical answers."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content


def handle_sales_query(client, query: str) -> str:
    """Handle sales queries"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a sales representative. Be persuasive and helpful."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content


def main():
    """Run multi-agent workflow example"""

    # Initialize monitor
    monitor = AgentMonitor()

    # Wrap OpenAI client
    client = monitor.wrap_openai(OpenAI())

    # Example query
    query = "How does your API handle rate limiting?"

    # Create a trace for the entire workflow
    with monitor.trace("customer_support_workflow", metadata={"query": query}):

        # Step 1: Classify intent
        with monitor.span("classify_intent"):
            intent = classify_query(client, query)
            print(f"Classified as: {intent}")

        # Step 2: Route to appropriate handler
        with monitor.span(f"handle_{intent}_query"):
            if intent == "technical":
                response = handle_technical_query(client, query)
            elif intent == "sales":
                response = handle_sales_query(client, query)
            else:
                response = "Please contact support@example.com"

            print(f"\nResponse: {response}")

    # View complete workflow metrics
    print(f"\n📊 Workflow Metrics:")
    print(f"Total Cost: ${monitor.get_cost():.4f}")
    print(f"Total Tokens: {monitor.get_tokens():,}")

    # Get cost report
    report = monitor.cost_report(time_range="last_hour")
    print(f"\n💰 Cost Breakdown:")
    print(f"Total Spend: ${report.total_cost:.4f}")
    print(f"Average Cost per Day: ${report.cost_per_day:.4f}")

    # Find slow operations
    slow_ops = monitor.query(
        metric="latency",
        threshold=">1s",
        time_range="last_hour"
    )

    if slow_ops:
        print(f"\n⚠️  Found {len(slow_ops)} slow operations:")
        for op in slow_ops[:3]:
            print(f"  - {op['operation']}: {op['duration']:.1f}ms")


if __name__ == "__main__":
    main()
