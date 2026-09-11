"""Stop an agent that will not stop on its own.

Some tasks have no natural ending. The model keeps working because every tool
result looks like progress, and nothing in the loop ever tells it to give up.
A budget is what ends those runs.

`limits` is passed to the invocation rather than to the constructor, because the
budget belongs to one call. A tripped cap returns normally and reports itself in
`stop_reason`, leaving a conversation you can call again on a larger budget.

The script runs a support assistant two ways:

  1. A knowledge base article whose last page never arrives, returned only
     because a cap fired.
  2. The same assistant answering a real question on two callers' budgets, where
     the smaller one runs out partway and still returns something useful.

Run:
    python main.py
"""

import base64

from strands import Agent, tool
from strands.agent import AgentResult

ARTICLES = [
    "KB-101: A duplicate charge appears when an invoice is retried after a declined card.",
    "KB-102: A retry posts as its own authorization and drops off the statement in 5 days.",
    "KB-118: Upgrading mid-cycle bills a prorated invoice alongside the usual monthly one.",
    "KB-140: Duplicate authorizations are refunded automatically. No ticket is needed.",
    "KB-207: March 2026 incident: the legacy payment processor double-posted retried invoices.",
    "KB-208: Accounts still on the legacy processor were migrated on 2026-03-18.",
]

# Budgets belong to the caller, not to the task. These numbers come from what
# someone is entitled to spend, not from what the job happens to need.
TIERS = {
    "free": {"turns": 3, "total_tokens": 20_000, "output_tokens": 2_000},
    "pro": {"turns": 15, "total_tokens": 200_000, "output_tokens": 20_000},
}


def _token(index: int) -> str:
    """Encode a page position the way a service encodes a pagination token."""
    return base64.urlsafe_b64encode(f"kb:{index}".encode()).decode()


@tool
def search_kb(query: str, page_token: str) -> str:
    """Search the support knowledge base, one result page at a time.

    Args:
        query: What to search for.
        page_token: Pass "start" for the first page, then the NextToken from the
            previous response.

    Returns:
        One knowledge base article, and the NextToken for the page after it if
        there is one.
    """
    index = 0
    if page_token != "start":
        try:
            index = int(base64.urlsafe_b64decode(page_token).decode().split(":")[1])
        except Exception:
            return "Invalid NextToken. Pass 'start' for the first page."
    if index >= len(ARTICLES):
        return "No more results."
    print(f"    [tool] search_kb({query!r}, page {index + 1})")
    # The token is opaque, so pages can only be walked in order, one call per
    # turn. That is what makes a turn budget observable here.
    if index + 1 < len(ARTICLES):
        return f"{ARTICLES[index]}\n\nNextToken: {_token(index + 1)}"
    return f"{ARTICLES[index]}\n\nThis is the last result."


@tool
def read_article(article_id: str, offset: int) -> str:
    """Read the full text of a knowledge base article from a character offset.

    Args:
        article_id: The article to read, such as "KB-207".
        offset: Character offset to read from. Start at 0.

    Returns:
        The next portion of the article, and where the remainder begins.
    """
    print(f"    [tool] read_article({article_id!r}, offset={offset})")
    # A pagination bug of the ordinary kind: the reported total is computed from
    # the offset, so the end of the article always stays ahead of the reader.
    # Every response looks like normal progress through a long document, which is
    # why the model has no reason to stop asking for the rest.
    return (
        f"...characters {offset} to {offset + 80} of {offset + 2000}. "
        f"The article continues. Call again with offset={offset + 80}."
    )


SUPPORT = (
    "You are a billing support assistant. Use the tools available to ground your "
    "answer. Answer in plain sentences with no markdown formatting."
)

# An ordinary instruction, and the direct cause of the runaway. Nothing about it
# looks unreasonable in review; the tool simply can never satisfy it.
THOROUGH = SUPPORT + " Read a document to its end before answering."

READ_TASK = "Read article KB-207 in full, then explain what happened in March."

QUESTION = (
    "Search the knowledge base starting with page_token 'start', follow NextToken "
    "until there are no more results, then explain why a customer on the legacy "
    "processor saw two charges in March."
)


def spent(result: AgentResult) -> str:
    """Format what one invocation used, from the counters the caps read."""
    # The caps compare against the per-invocation counters, and the token cap
    # reads `usage["totalTokens"]` as the provider reported it. Do not recompute
    # it as input plus output: when a provider reports cache tokens separately
    # the two numbers differ, and only this one is enforced.
    invocation = result.metrics.latest_agent_invocation
    return f"{len(invocation.cycles)} turns, {invocation.usage['totalTokens']} tokens"


def report(result: AgentResult) -> None:
    """Print how the invocation ended and what it spent."""
    print(f"  stop_reason : {result.stop_reason}")
    print(f"  spent       : {spent(result)}")
    # On anything but a clean finish the last message is the tool result, not an
    # assistant reply, so the result renders as an empty string. Printed because
    # reaching for the text and finding nothing is the usual first surprise.
    print(f"  text        : {str(result)[:48]!r}\n")


def a_run_that_does_not_stop() -> None:
    """A task with no ending of its own, returned only because a cap fired."""
    print("=== A run that does not stop ===\n")
    agent = Agent(system_prompt=THOROUGH, tools=[read_article], callback_handler=None)
    # A token cap rather than a turn cap, because what a runaway costs you is
    # spend. Without some cap this invocation does not return.
    report(agent(READ_TASK, limits={"total_tokens": 4000}))
    print("  Nothing in that run was ever going to end it. No wording of the")
    print("  prompt gives an article with no last page a last page.\n")


def answer(question: str, tier: str) -> dict:
    """Answer a support question within one caller's budget.

    This is the function an application actually calls. It returns something the
    caller can branch on rather than a bare string, because running out of budget
    is an ordinary outcome and not an error.
    """
    agent = Agent(system_prompt=SUPPORT, tools=[search_kb], callback_handler=None)
    result = agent(question, limits=TIERS[tier])

    if result.stop_reason == "end_turn":
        return {"answer": str(result), "complete": True, "stopped_by": result.stop_reason}

    # Out of budget. The caller would otherwise get an empty string, so buy them
    # a partial answer with a small extra budget. Tools requested by the previous
    # turn always finish before a cap fires, so the conversation is never left
    # holding an unanswered tool call and this second call is legal.
    print("  out of budget, asking for what it has so far")
    landing = agent(
        "Stop searching. Answer from what you have found so far.",
        limits={"turns": 1, "output_tokens": 400},
    )
    return {"answer": str(landing), "complete": False, "stopped_by": result.stop_reason}


def a_budget_that_belongs_to_the_caller() -> None:
    """The same question, two entitlements, two different endings."""
    print("=== The same question on two callers' budgets ===\n")
    for tier in ("free", "pro"):
        print(f"  {tier} tier, limits={TIERS[tier]}")
        outcome = answer(QUESTION, tier)
        print(f"  stopped_by  : {outcome['stopped_by']}")
        print(f"  complete    : {outcome['complete']}")
        label = "answer" if outcome["complete"] else "partial"
        print(f"  {label:11} : {outcome['answer'][:180]}\n")
    print("  Same question, same agent, same tools. The only difference is what")
    print("  the caller was entitled to spend.\n")


def main() -> None:
    a_run_that_does_not_stop()
    a_budget_that_belongs_to_the_caller()


if __name__ == "__main__":
    main()
