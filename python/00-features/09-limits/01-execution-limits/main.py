"""Cap what a single invocation is allowed to spend.

`limits` is passed to the invocation, not to the constructor, because the
budget belongs to one call rather than to the agent.

Run:
    python main.py

The script runs four configurations against the same prompt and pauses between
them, so you can compare how each one ended.
"""

import sys

from strands import Agent, tool


@tool
def next_number(n: int) -> int:
    """Return the number that follows n.

    Args:
        n: The current number.

    Returns:
        n plus one.
    """
    print(f"    [tool] next_number({n}) -> {n + 1}")
    return n + 1


PROMPT = (
    "Start at 1 and call next_number one step at a time until you reach 6. "
    "Call the tool once per step. Then state the final number."
)


def pause() -> None:
    """Wait for Enter between runs, when there is a terminal to read from."""
    if not sys.stdin.isatty():
        # Started without a terminal on stdin, so there is nobody to press
        # Enter. Say so rather than appearing to ignore the pause.
        print("[no terminal on stdin, continuing without pausing]\n")
        return
    try:
        input("[Enter] next configuration, or Ctrl-C to stop ")
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    print()


def run(label: str, limits: dict | None) -> None:
    """Invoke a fresh agent with the given limits and report how it ended."""
    agent = Agent(
        system_prompt=(
            "You are a counting assistant. Call the tool silently without "
            "commentary between calls. Do not use markdown. When finished, "
            "reply with one short plain sentence."
        ),
        tools=[next_number],
    )
    print(f"--- {label} ---")
    result = agent(PROMPT, limits=limits)
    usage = result.metrics.accumulated_usage
    print(f"\n  stop_reason  : {result.stop_reason}")
    print(f"  tokens       : {usage['inputTokens']} in, {usage['outputTokens']} out")
    print()


def main() -> None:
    # No limits. The loop runs until the model decides it is finished.
    run("limits=None", None)
    pause()

    # Cap the number of trips through the loop. Tools requested by the previous
    # turn still run to completion, so the counting stops mid-task rather than
    # leaving a dangling tool call.
    run("limits={'turns': 3}", {"turns": 3})
    pause()

    # Cap total tokens for this invocation, input plus output.
    run("limits={'total_tokens': 2000}", {"total_tokens": 2000})
    pause()

    # Caps compose. When several would trip at once the priority is
    # turns, then total_tokens, then output_tokens.
    run(
        "limits={'turns': 2, 'total_tokens': 5000}",
        {"turns": 2, "total_tokens": 5000},
    )


if __name__ == "__main__":
    main()
