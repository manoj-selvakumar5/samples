"""Construct an agent, give it one tool, invoke it, and read the result.

Run:
    python main.py
"""

from strands import Agent, tool


@tool
def word_count(text: str) -> int:
    """Count the words in a block of text.

    Args:
        text: The text to count words in.

    Returns:
        The number of whitespace-separated words.
    """
    print(f"  [tool] word_count called with {len(text)} characters")
    return len(text.split())


def main() -> None:
    # No model is configured, so the agent uses the SDK default.
    agent = Agent(
        system_prompt=(
            "You are a concise assistant. When asked to count words, use the "
            "word_count tool rather than counting yourself."
        ),
        tools=[word_count],
    )

    prompt = "How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?"
    print(f"Prompt: {prompt}\n")

    result = agent(prompt)

    # `result` is an AgentResult, not a string. Printing it renders the final
    # text, but the object also carries why the loop stopped and what it cost.
    print("\n--- AgentResult ---")
    print(f"stop_reason : {result.stop_reason}")
    print(f"text        : {result}")

    # `message` is the raw final message, a dict with role and content blocks.
    print(f"role        : {result.message['role']}")
    print(f"blocks      : {len(result.message['content'])}")

    usage = result.metrics.accumulated_usage
    print(f"tokens      : {usage['inputTokens']} in, {usage['outputTokens']} out")

    # Tool calls are recorded per tool name, so you can see the loop actually
    # routed through word_count rather than the model guessing an answer.
    for name, metrics in result.metrics.tool_metrics.items():
        print(f"tool calls  : {name} x{metrics.call_count}")


if __name__ == "__main__":
    main()
