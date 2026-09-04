"""Construct an agent, give it one tool, invoke it, and read the result.

Run:
    python main.py
"""

from strands import Agent, tool


# The @tool decorator makes this function available to the agent as a tool.
# The docstring and type hints become the description and input schema that
# the model reads when it decides whether to call it.
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
    # `tools` is the list the agent is allowed to choose from. No model is
    # configured here, so the agent uses the SDK default; pass `model=` to
    # choose one.
    agent = Agent(
        system_prompt=(
            "You are a concise assistant. When asked to count words, use the "
            "word_count tool rather than counting yourself."
        ),
        tools=[word_count],
    )

    prompt = "How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?"
    print(f"Prompt: {prompt}\n")

    # Invoke the agent normally. The model decides whether to call word_count.
    # The system prompt asks it to, but nothing here forces the call.
    result = agent(prompt)

    # `result` is an AgentResult, not a string. Printing it renders the final
    # text, but the object also carries why the loop stopped and what it cost.
    # The first \n closes the model's streamed line, which does not end in one.
    print("\n\n--- AgentResult ---")
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
