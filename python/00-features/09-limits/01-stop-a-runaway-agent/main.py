"""Stop an agent that will not stop on its own.

Some tasks have no natural ending. The model keeps working because every tool
result looks like progress, and nothing in the loop ever tells it to give up.
A budget is what ends those runs.

`limits` is passed to the invocation rather than to the constructor, because the
budget belongs to one call. A tripped cap returns normally and reports itself in
`stop_reason`, leaving a conversation you can call again on a larger budget.

The script runs a contract review three ways:

  1. A search that can never satisfy its own success criterion, stopped by each
     of the three caps in turn.
  2. The same run stopped from outside, by a deadline and by `agent.cancel()`,
     which is the only way to bound wall-clock time.
  3. A page-by-page read that runs out of budget partway and finishes on a
     second call.

Run:
    python main.py
"""

import base64
import threading
import time

from strands import Agent, tool
from strands.agent import AgentResult

CLAUSES = [
    "'Services' means the hosted analytics platform described in Exhibit A.",
    "This agreement runs for twelve months from the effective date.",
    "Customer pays 4,000 USD monthly, due within 30 days of invoice.",
    "Vendor shall maintain 99.9% monthly uptime at the load balancer.",
    "Vendor shall report any security incident within 24 hours.",
    "Vendor shall retain audit logs for 24 months and produce them on request.",
]


def _token(index: int) -> str:
    """Encode a page position the way a service encodes a pagination token."""
    return base64.urlsafe_b64encode(f"clause:{index}".encode()).decode()


@tool
def read_clause_text(offset: int) -> str:
    """Read the termination clause, starting at a character offset.

    Args:
        offset: Character offset to read from. Start at 0.

    Returns:
        The next portion of the clause, and where the remainder begins.
    """
    print(f"    [tool] read_clause_text(offset={offset}) ...")
    time.sleep(1.0)
    print(f"    [tool] read_clause_text(offset={offset}) returned")
    # A pagination bug of the ordinary kind: the reported total is computed from
    # the offset, so the end of the document always stays ahead of the reader.
    # Every response looks like normal progress through a long clause, which is
    # why the model has no reason to stop asking for the rest. No prompt makes
    # this terminate.
    return (
        f"...characters {offset} to {offset + 80} of {offset + 2000}. "
        f"The clause continues. Call again with offset={offset + 80}."
    )


@tool
def list_clauses(next_token: str) -> str:
    """List contract clauses one page at a time.

    Args:
        next_token: Pass "start" for the first page, then the NextToken from the
            previous response.

    Returns:
        One clause, and the NextToken for the page after it if there is one.
    """
    index = 0
    if next_token != "start":
        try:
            index = int(base64.urlsafe_b64decode(next_token).decode().split(":")[1])
        except Exception:
            return "Invalid NextToken. Pass 'start' for the first page."
    if index >= len(CLAUSES):
        return "No more clauses."
    print(f"    [tool] list_clauses(page {index + 1})")
    # The token is opaque, so the pages can only be walked in order, one call per
    # turn. That is what makes a turn budget observable here.
    if index + 1 < len(CLAUSES):
        return f"{CLAUSES[index]}\n\nNextToken: {_token(index + 1)}"
    return f"{CLAUSES[index]}\n\nThis is the last clause."


REVIEWER = (
    "You are a contract review assistant. Use the tools available. "
    "Answer in plain sentences with no markdown formatting."
)

# An ordinary instruction, and the direct cause of the runaway. Nothing about it
# looks unreasonable in review; the tool simply can never satisfy it.
WHOLE = REVIEWER + " Read a document to its end before answering."

READ_CLAUSE = "Read the termination for convenience clause in full and summarize it."


def report(result: AgentResult) -> None:
    """Print how the invocation ended and what it spent."""
    # `latest_agent_invocation` holds the per-call counters, and those are what
    # the caps compare against. `metrics.accumulated_usage` is the agent's
    # lifetime total, so on a reused agent it does not match the enforced budget.
    invocation = result.metrics.latest_agent_invocation
    usage = invocation.usage
    print(f"  stop_reason : {result.stop_reason}")
    print(f"  spent       : {len(invocation.cycles)} turns, "
          f"{usage['inputTokens']} in, {usage['outputTokens']} out")
    # On anything but a clean finish the last message is the tool result, not an
    # assistant reply, so the result renders as an empty string. Printed because
    # reaching for the text and finding nothing is the usual first surprise.
    print(f"  text        : {str(result)[:48]!r}\n")


def three_caps() -> None:
    """Stop the same unfinishable run on each of the three budget dimensions."""
    print("=== A run that cannot finish, stopped three ways ===\n")
    for limits in ({"turns": 4}, {"total_tokens": 3000}, {"output_tokens": 200}):
        print(f"  limits={limits}")
        agent = Agent(system_prompt=WHOLE, tools=[read_clause_text], callback_handler=None)
        report(agent(READ_CLAUSE, limits=limits))
    print("  Every one of those returned only because a cap fired. The task had")
    print("  no ending of its own.\n")


def cancel_from_outside() -> None:
    """Stop a run from outside. `Limits` counts turns and tokens, never seconds."""
    print("=== Stopping from outside ===\n")

    # A `cancel_signal` is an ordinary threading.Event that you create before the
    # run starts and can hand to anything: a timer, a request lifecycle, a client
    # disconnect handler. This is the wall-clock timeout `Limits` cannot express.
    print("  cancel_signal, deadline at 2.5s")
    agent = Agent(system_prompt=WHOLE, tools=[read_clause_text], callback_handler=None)
    deadline = threading.Event()
    threading.Timer(2.5, lambda: (print("    [signal] deadline reached"), deadline.set())).start()
    # The turn cap stays on as a backstop, so this returns even if the signal
    # never arrives.
    report(agent(READ_CLAUSE, cancel_signal=deadline, limits={"turns": 30}))

    # `agent.cancel()` is thread-safe and targets whichever invocation is in
    # flight. Use it when you hold the agent rather than a signal, for example
    # from a web request handler or a Stop button.
    print("  agent.cancel() from another thread at 2.5s")
    agent = Agent(system_prompt=WHOLE, tools=[read_clause_text], callback_handler=None)
    threading.Timer(2.5, lambda: (print("    [signal] cancel() called"), agent.cancel())).start()
    report(agent(READ_CLAUSE, limits={"turns": 30}))

    print("  Neither is immediate. The loop stops at the next cancellation-safe")
    print("  point, so a tool already executing runs to completion first: the")
    print("  'returned' line above appears after the signal.\n")


def budget_and_resume() -> None:
    """Trip a budget partway through real work, then finish on a larger one."""
    print("=== A budget that runs out, and the call that finishes the job ===\n")
    agent = Agent(system_prompt=REVIEWER, tools=[list_clauses], callback_handler=None)

    prompt = (
        "List every clause in the contract, starting with next_token 'start' and "
        "following NextToken until there are no more, then say which obligations "
        "fall on the vendor."
    )

    # You rarely know how long a task is in advance, so size the cap to what you
    # are willing to spend rather than to what the job needs. This one is a
    # low-tier caller's allowance, and the contract is longer than it.
    first = agent(prompt, limits={"turns": 4})
    report(first)
    if first.stop_reason != "limit_turns":
        return

    print(f"  Out of budget partway through. The conversation is intact: "
          f"{len(agent.messages)} messages, last role {agent.messages[-1]['role']!r}.")
    print("  Nothing resumes on its own. You call the agent again.\n")

    # Tools requested by the previous turn always run to completion before a cap
    # fires, so the history never ends on an unanswered tool call. That is what
    # makes this second call legal. It needs a prompt like any other call; the
    # history carries the context, so a short nudge is enough.
    report(agent("Continue from where you stopped.", limits={"turns": 15}))


def main() -> None:
    three_caps()
    cancel_from_outside()
    budget_and_resume()


if __name__ == "__main__":
    main()
