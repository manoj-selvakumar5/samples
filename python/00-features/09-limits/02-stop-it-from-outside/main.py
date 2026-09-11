"""Stop an invocation from outside it, and make the stop actually feel fast.

`Limits` counts turns and tokens, never seconds, so a deadline or a Stop button
is cancellation rather than a limit. Two mechanisms do it and both report a
`stop_reason` of `cancelled`.

Neither is immediate. The loop stops at the next cancellation-safe point, and a
tool already executing runs to completion first, which is what makes a Stop
button feel broken. The last section fixes that: a tool can be handed the same
signal and give up on its own.

The script runs a support assistant three ways:

  1. A client disconnect, expressed as a `cancel_signal` the caller owns.
  2. A Stop button, expressed as `agent.cancel()` from another thread, followed
     by an ordinary question to the same agent.
  3. The same disconnect, at the same point, against a tool that watches the
     signal instead of ignoring it.

Run:
    python main.py
"""

import threading
import time

from strands import Agent, ToolContext, tool
from strands.agent import AgentResult

THREAD = [
    "customer: I was charged twice on 12 March and once more on 14 March.",
    "agent: Thanks, pulling up the invoice history for that period now.",
    "agent: I see three authorizations against the card ending 4471.",
    "customer: Only one of them should have gone through.",
    "agent: Two of the three are retries of the same declined invoice.",
    "agent: Retries post separately and drop off the statement within 5 days.",
    "customer: Nothing has dropped off and it has been three weeks.",
    "agent: That matches the March legacy-processor incident. Escalating.",
]

# The upstream this stands in for is slow, which is the ordinary case and the
# reason cancellation is visible at all here.
FETCH_SECONDS = 1.5
STEP_SECONDS = 0.1

# The caller's event, and the fetch it is fired during. Firing from inside the
# tool is both the realistic case, since a client goes away mid-request rather
# than on a schedule, and the only way to cancel the two timed runs below at
# exactly the same point so their delays can be compared. ARMED is set only for
# those runs, so the Stop button section is left to its own timer.
DISCONNECT = threading.Event()
ARMED = threading.Event()
FIRED: dict[str, float] = {}
DISCONNECT_DURING = 3


def _client_disconnects() -> None:
    """Stand in for the caller going away while a fetch is in flight."""
    ARMED.clear()
    FIRED["at"] = time.monotonic()
    print("    [signal] client disconnected")
    DISCONNECT.set()


@tool
def fetch_message(number: int) -> str:
    """Fetch one message from the support ticket thread.

    Args:
        number: The 1-based message number.

    Returns:
        The message text, or a note that it does not exist.
    """
    print(f"    [tool] fetch_message({number}) started")
    if number == DISCONNECT_DURING and ARMED.is_set():
        _client_disconnects()
    # One uninterruptible call. Nothing here is watching for a cancellation, so
    # once this starts, the run cannot end before it does.
    time.sleep(FETCH_SECONDS)
    print(f"    [tool] fetch_message({number}) returned")
    return THREAD[number - 1] if 1 <= number <= len(THREAD) else "No such message."


@tool(context=True)
def fetch_message_promptly(number: int, tool_context: ToolContext) -> str:
    """Fetch one message from the support ticket thread, giving up if cancelled.

    Args:
        number: The 1-based message number.

    Returns:
        The message text, or a note that the fetch was abandoned.
    """
    print(f"    [tool] fetch_message_promptly({number}) started")
    if number == DISCONNECT_DURING and ARMED.is_set():
        _client_disconnects()
    # `context=True` places a ToolContext in the named parameter. Its
    # `cancel_signal` is the same event the agent is watching, so polling it
    # between steps is what turns a stop that waits out the fetch into one that
    # does not. A tool that never looks at it runs to completion, as the one
    # above does.
    for _ in range(int(FETCH_SECONDS / STEP_SECONDS)):
        if tool_context.cancel_signal.is_set():
            print(f"    [tool] fetch_message_promptly({number}) abandoned")
            return "Abandoned: the run was cancelled."
        time.sleep(STEP_SECONDS)
    print(f"    [tool] fetch_message_promptly({number}) returned")
    return THREAD[number - 1] if 1 <= number <= len(THREAD) else "No such message."


SUPPORT = (
    "You are a billing support assistant. Read the ticket thread with the fetch "
    "tool, starting at message 1. Answer in plain sentences with no markdown."
)

TASK = "Read the ticket thread and summarize what the customer is disputing."


def support_agent(fetch_tool: object) -> Agent:
    """A fresh assistant over one of the two fetch tools."""
    return Agent(system_prompt=SUPPORT, tools=[fetch_tool], callback_handler=None)


def report(result: AgentResult, fired_at: float | None) -> float:
    """Print how the invocation ended, and how long after the signal it returned.

    Returns the delay in seconds, or 0.0 if the signal never fired.
    """
    if fired_at is None:
        print(f"  {result.stop_reason}, but the run ended before the signal\n")
        return 0.0
    delay = time.monotonic() - fired_at
    print(f"  stop_reason : {result.stop_reason}")
    print(f"  returned    : {delay:.1f}s after the signal\n")
    return delay


def run_until_disconnected(fetch_tool: object) -> float:
    """Invoke the assistant with a `cancel_signal`, cancelled during one fetch."""
    # The event is reusable but stays set once fired, so clear it before handing
    # it to another invocation.
    DISCONNECT.clear()
    FIRED.clear()
    ARMED.set()
    # Anything can own this event: a request lifecycle, a websocket disconnect
    # handler, a timer. It exists before the invocation, which is what makes it
    # usable as a deadline. `Limits` has no time dimension to express one.
    result = support_agent(fetch_tool)(TASK, cancel_signal=DISCONNECT)
    return report(result, FIRED.get("at"))


def a_client_disconnect() -> float:
    """A `cancel_signal` the caller creates before the run starts."""
    print("=== A client disconnect ===\n")
    return run_until_disconnected(fetch_message)


def a_stop_button() -> None:
    """`agent.cancel()`, thread-safe, aimed at the invocation in flight."""
    print("=== A Stop button ===\n")
    agent = support_agent(fetch_message)

    def fire() -> None:
        print("    [signal] cancel() called")
        # Safe to call from any thread: a request handler, a background task, a
        # UI button. It targets whichever invocation is currently running, so it
        # does nothing useful when no run is in progress.
        agent.cancel()

    timer = threading.Timer(5.0, fire)
    timer.daemon = True
    timer.start()
    try:
        result = agent(TASK)
    finally:
        # Stop a timer that has not fired yet, so it cannot reach a later run.
        timer.cancel()
    # No delay is reported here. Where this lands depends on whether a fetch
    # happened to be in flight, and the section below times that deliberately.
    print(f"  stop_reason : {result.stop_reason}\n")

    # Cancelling does not invalidate the history, so the same agent can be
    # invoked again. A cancelled run is a pause you chose, not a broken one.
    followup = agent("Never mind the thread. In one sentence, what is a chargeback?")
    print(f"  called again -> {followup.stop_reason}: {followup}\n")


def a_tool_that_cooperates(baseline: float) -> None:
    """The same disconnect, at the same fetch, against a cooperative tool."""
    print("=== A tool that cooperates ===\n")
    cooperative = run_until_disconnected(fetch_message_promptly)
    if not (baseline and cooperative):
        return
    print(f"  a tool that ignores the signal : {baseline:.1f}s after it")
    print(f"  a tool that polls the signal   : {cooperative:.1f}s after it")
    print("  Same mechanism, same cancellation point. The loop behaved identically")
    print("  in both runs; the difference is entirely in whether the tool looked.\n")


def main() -> None:
    ignored = a_client_disconnect()
    a_stop_button()
    a_tool_that_cooperates(ignored)


if __name__ == "__main__":
    main()
