"""Cap what a single invocation may spend.

`limits` bounds one call to the agent. It takes three optional caps, is passed
to the invocation rather than the constructor, and never raises: the loop stops
between iterations and names the cap it tripped in `stop_reason`.

Run:
    python main.py
"""

from strands import Agent, tool
from strands.agent import AgentResult

LOG = [
    "09:12 deploy release=4.2 status=ok",
    "09:20 error_rate=3.1x threshold=1.0x alert=paged",
    "09:33 pool.active=512 pool.max=512 waiters=87",
    "09:41 rollback release=4.1 status=ok",
    "09:50 error_rate=0.9x status=recovered",
]


@tool
def read_line(number: int) -> str:
    """Read one line of the deployment log.

    Args:
        number: The 1-based line number.

    Returns:
        The log line, or a note that it does not exist.
    """
    if not 1 <= number <= len(LOG):
        return f"There is no line {number}. The log has {len(LOG)} lines."
    return LOG[number - 1]


SYSTEM = (
    "You are a log analysis assistant. Read one line at a time with the tool. "
    "Answer in plain sentences with no markdown formatting."
)

TASK = "Read the deployment log line by line, then say what caused the incident."


def spent(result: AgentResult) -> str:
    """Format what one invocation used, from the counters the caps read."""
    # The caps compare against the per-invocation counters. `accumulated_usage`
    # on the same metrics object is the agent's lifetime total, so on a reused
    # agent it is a different, larger number than the one being enforced.
    invocation = result.metrics.latest_agent_invocation
    usage = invocation.usage
    total = usage["inputTokens"] + usage["outputTokens"]
    return (f"{len(invocation.cycles)} turns, {usage['inputTokens']} in, "
            f"{usage['outputTokens']} out, {total} total")


def fresh() -> Agent:
    """A new agent, so each cap is measured from zero."""
    return Agent(system_prompt=SYSTEM, tools=[read_line], callback_handler=None)


def the_three_caps() -> None:
    """Each field of `Limits`, and the `stop_reason` it produces."""
    print("=== The three caps ===\n")
    for limits in ({"turns": 2}, {"total_tokens": 1500}, {"output_tokens": 48}):
        result = fresh()(TASK, limits=limits)
        print(f"  {str(limits):32s} -> {result.stop_reason:20s} {spent(result)}")
    print()


def caps_are_soft() -> None:
    """A cap is checked between iterations, so a run can finish past it."""
    print("=== Caps are soft ===\n")
    cap = 1500
    result = fresh()(TASK, limits={"total_tokens": cap})
    usage = result.metrics.latest_agent_invocation.usage
    total = usage["inputTokens"] + usage["outputTokens"]
    print(f"  asked for at most {cap} total tokens, used {total} ({result.stop_reason})")
    if result.stop_reason == "limit_total_tokens":
        # The check runs at the top of each loop iteration, never mid-call, so
        # the iteration that crosses the line still finishes. Treat a cap as a
        # circuit breaker rather than an accounting guarantee.
        print(f"  overshoot: {total - cap} tokens, spent by the turn that crossed the line\n")
    else:
        print("  the task finished before the cap was reached\n")


def priority() -> None:
    """When several caps would trip together, one of them is reported."""
    print("=== Priority when several trip at once ===\n")
    result = fresh()(TASK, limits={"turns": 1, "total_tokens": 1, "output_tokens": 1})
    # Fixed order: turns, then total_tokens, then output_tokens.
    print(f"  all three set to 1 -> {result.stop_reason}\n")


def rejected_and_ignored() -> None:
    """What a bad cap does, and what a misspelt one does."""
    print("=== Validation ===\n")
    for bad in (0, -1, 1.5, True, "3"):
        try:
            fresh()(TASK, limits={"turns": bad})
            print(f"  turns={bad!r:6} accepted")
        except TypeError as exc:
            # Validation runs before any model call, so a bad cap costs nothing.
            print(f"  turns={bad!r:6} TypeError: {exc}")

    # Only `turns`, `total_tokens` and `output_tokens` are read. Anything else is
    # not an error and not a cap: this run is uncapped.
    result = fresh()(TASK, limits={"turn": 1})
    print(f"\n  limits={{'turn': 1}} is a typo, not an error -> {result.stop_reason}, {spent(result)}\n")


def main() -> None:
    the_three_caps()
    caps_are_soft()
    priority()
    rejected_and_ignored()


if __name__ == "__main__":
    main()
