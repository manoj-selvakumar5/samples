"""Stop an invocation from outside it.

`Limits` counts turns and tokens, never seconds, so a deadline or a Stop button
is cancellation rather than a limit. Two mechanisms do it, and neither takes
effect immediately.

Run:
    python main.py
"""

import threading
import time

from strands import Agent, tool
from strands.agent import AgentResult

LOG = [f"line {n}" for n in range(1, 40)]


@tool
def read_line(number: int) -> str:
    """Read one line of a long log.

    Args:
        number: The 1-based line number.

    Returns:
        The log line.
    """
    print(f"    [tool] read_line({number}) started")
    # A deliberately slow tool, so a cancellation can arrive while it is running
    # and the timing is visible in the output.
    time.sleep(1.5)
    print(f"    [tool] read_line({number}) returned")
    return LOG[number - 1] if 1 <= number <= len(LOG) else "No such line."


SYSTEM = (
    "You are a log analysis assistant. Read one line at a time with the tool. "
    "Answer in plain sentences with no markdown formatting."
)

TASK = "Read the log one line at a time from line 1 and summarize what it contains."


def agent() -> Agent:
    """A fresh agent for each demonstration."""
    return Agent(system_prompt=SYSTEM, tools=[read_line], callback_handler=None)


def report(label: str, result: AgentResult, started: float) -> None:
    """Print how the invocation ended, and how long after the signal."""
    print(f"  {label}: {result.stop_reason}, returned {time.monotonic() - started:.1f}s "
          f"after the signal\n")


def by_signal() -> None:
    """A `threading.Event` the caller creates before the run starts."""
    print("=== cancel_signal ===\n")
    deadline = threading.Event()
    fired = {}

    def fire() -> None:
        fired["at"] = time.monotonic()
        print("    [signal] deadline reached")
        deadline.set()

    threading.Timer(3.5, fire).start()
    # Anything can own this event: a timer, a request lifecycle, a websocket
    # disconnect handler. It exists before the invocation, which is what makes
    # it usable as a deadline.
    result = agent()(TASK, cancel_signal=deadline)
    report("cancel_signal", result, fired["at"])


def by_method() -> None:
    """`agent.cancel()`, thread-safe, aimed at the invocation in flight."""
    print("=== agent.cancel() ===\n")
    running = agent()
    fired = {}

    def fire() -> None:
        fired["at"] = time.monotonic()
        print("    [signal] cancel() called")
        # Safe to call from any thread: a request handler, a background task, a
        # UI button. It targets whichever invocation is currently running.
        running.cancel()

    threading.Timer(3.5, fire).start()
    result = running(TASK)
    report("agent.cancel()", result, fired["at"])


def not_immediate() -> None:
    """Cancellation lands at the next safe point, not mid-tool."""
    print("=== What 'cancelled' does not mean ===\n")
    # The loop checks for cancellation at fixed safe points: while the model
    # response streams, before tools execute, during an MCP tool call, and after
    # tools execute before the next model call. Which one you hit depends on
    # where the run happened to be, so the delay varies between the two runs
    # above. If the signal lands while tools are running, every tool already in
    # flight finishes first, which is why their 'returned' lines print after it.
    print("  Cancellation is checked at safe points, not preempted. Depending on")
    print("  where the run was, it lands during model streaming, before tools run,")
    print("  or after tools finish. Tools already executing always complete, so a")
    print("  run holding a slow tool takes at least that long to stop.\n")


def afterwards() -> None:
    """A cancelled conversation is still valid, so the agent can be called again."""
    print("=== After a cancellation ===\n")
    running = agent()
    threading.Timer(3.5, running.cancel).start()
    first = running(TASK)
    print(f"  cancelled after {len(running.messages)} messages, "
          f"last role {running.messages[-1]['role']!r}")
    # Nothing about cancelling invalidates the history, so the same agent can be
    # invoked again. Cancellation is a pause you chose, not a broken run.
    second = running("Never mind the log. What is 2 + 2?")
    print(f"  called again -> {second.stop_reason}: {second}")


def main() -> None:
    by_signal()
    by_method()
    not_immediate()
    afterwards()


if __name__ == "__main__":
    main()
