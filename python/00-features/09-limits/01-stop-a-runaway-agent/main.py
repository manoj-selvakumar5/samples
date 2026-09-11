"""Bound one agent invocation with execution limits.

Some agent tasks have no reliable natural stopping point. `limits` lets the
caller cap the turns or tokens that one invocation may consume.

When a limit is reached the agent returns normally and reports the reason in
`result.stop_reason`. The conversation stays valid and can be invoked again.

The script shows:

  1. A runaway tool loop stopped by a token budget.
  2. The same task run on two different callers' budgets.

Run:
    python main.py
"""

import base64

from strands import Agent, tool
from strands.agent import AgentResult
from strands.types import Limits

ARTICLES = [
    "KB-101: A duplicate charge appears when an invoice is retried after a declined card.",
    "KB-102: A retry posts as its own authorization and drops off the statement in 5 days.",
    "KB-118: Upgrading mid-cycle bills a prorated invoice alongside the usual monthly one.",
    "KB-140: Duplicate authorizations are refunded automatically. No ticket is needed.",
    "KB-207: March 2026 incident: the legacy payment processor double-posted retried invoices.",
    "KB-208: Accounts still on the legacy processor were migrated on 2026-03-18.",
]

# Turn budget by plan tier.
TIERS = {
    "free": {"turns": 3},
    "pro": {"turns": 10},
}


def _cursor(index: int) -> str:
    """Encode a page position as an opaque pagination token."""
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
    # The cursor is opaque, so pages can only be walked in order, one per call.
    if index + 1 < len(ARTICLES):
        return f"{ARTICLES[index]}\n\nNextToken: {_cursor(index + 1)}"
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
    # Deliberate bug: the reported total is derived from the offset, so the end
    # of the article always stays ahead of the reader and this never terminates.
    return (
        f"...characters {offset} to {offset + 80} of {offset + 2000}. "
        f"The article continues. Call again with offset={offset + 80}."
    )


SUPPORT = (
    "You are a billing support assistant. Use the tools available to ground your "
    "answer. Answer in plain sentences with no markdown formatting."
)

# Combined with read_article, this instruction can never be satisfied.
THOROUGH = SUPPORT + " Read a document to its end before answering."

READ_TASK = "Read article KB-207 in full, then explain what happened in March."

QUESTION = (
    "Search the knowledge base starting with page_token 'start', follow NextToken "
    "until there are no more results, then explain why a customer on the legacy "
    "processor saw two charges in March."
)


def spent(result: AgentResult) -> str:
    """Format the budget counters this invocation used."""
    # The caps compare against these per-invocation counters, not
    # `metrics.accumulated_usage`, which is the agent's lifetime total.
    invocation = result.metrics.latest_agent_invocation
    return f"{len(invocation.cycles)} turns, {invocation.usage['totalTokens']} tokens"


def report(result: AgentResult) -> None:
    """Print how the invocation ended and what it spent."""
    print(f"  stop_reason : {result.stop_reason}")
    print(f"  spent       : {spent(result)}")
    # After a limit fires the last message is a tool result, not an assistant
    # reply, so this renders as an empty string.
    print(f"  text        : {str(result)[:48]!r}\n")


def summarize_incident(budget: Limits) -> AgentResult:
    """Summarize the March billing incident from the knowledge base article."""
    agent = Agent(system_prompt=THOROUGH, tools=[read_article], callback_handler=None)
    return agent(READ_TASK, limits=budget)


def answer(question: str, tier: str) -> dict:
    """Answer a support question within one caller's budget.

    Returns a result the caller can branch on: reaching a limit is an ordinary
    outcome, not an error.
    """
    agent = Agent(system_prompt=SUPPORT, tools=[search_kb], callback_handler=None)
    result = agent(question, limits=TIERS[tier])

    if result.stop_reason == "end_turn":
        return {"answer": str(result), "complete": True, "stopped_by": result.stop_reason}

    # Tools from the last turn have already completed, so the history is valid
    # and the agent can be invoked again. One more turn, and no more searching.
    print("  out of budget, asking for what it has so far")
    landing = agent(
        "Stop searching. Answer from what you have found so far.",
        limits={"turns": 1, "output_tokens": 400},
    )
    return {"answer": str(landing), "complete": False, "stopped_by": result.stop_reason}


def main() -> None:
    print("=== A loop with no natural ending ===\n")
    # A token cap rather than a turn cap, because what a runaway costs is spend.
    report(summarize_incident({"total_tokens": 4000}))
    print("  The agent stopped because the budget ran out, not because the")
    print("  document ended. No wording of the prompt supplies that ending.\n")

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


if __name__ == "__main__":
    main()
