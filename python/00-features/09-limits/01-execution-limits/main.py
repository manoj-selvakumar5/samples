"""Cap what a single invocation is allowed to spend.

A limit is a budget with a resumption story, not a kill switch. `limits` is
passed to the invocation rather than to the constructor, because the budget
belongs to one call.

The script reviews a contract twice:

  1. A search whose index never comes back, run under a policy that says to
     retry transient failures. Nothing in the loop will ever end it, so the cap
     is the only reason the call returns.
  2. A page-by-page read whose length is not knowable in advance. A small
     budget runs out partway, and a larger one then finishes the job.

Run:
    python main.py
"""

from strands import Agent, tool

# The contract, paged behind continuation tokens. A page names the token for the
# next one, so pages can only be fetched in order, one call at a time. The agent
# is never told how many there are.
PAGES = {
    "start": ("'Services' means the hosted analytics platform in Exhibit A.", "p-7f2"),
    "p-7f2": ("This agreement runs for twelve months from the effective date.", "p-3ba"),
    "p-3ba": ("Customer pays 4,000 USD monthly, due within 30 days of invoice.", "p-9c1"),
    "p-9c1": ("Vendor shall maintain 99.9% monthly uptime at the load balancer.", "p-2ee"),
    "p-2ee": ("Vendor shall report any security incident within 24 hours.", "p-8d4"),
    "p-8d4": ("Vendor shall retain audit logs for 24 months and produce them on request.", None),
}


@tool
def search_contract(term: str) -> str:
    """Search the contract text for a term.

    Args:
        term: The word or phrase to look for.

    Returns:
        Matching pages, or a message explaining why the search failed.
    """
    print(f"    [tool] search_contract({term!r}) -> index unavailable")
    # This tool never succeeds, and it fails the way a genuinely transient
    # failure fails. Paired with the retry policy below, no path through the
    # loop ends the run.
    return "Search index is rebuilding and returned no results. Retry the search."


@tool
def read_page(token: str) -> str:
    """Read one page of the contract.

    Args:
        token: The page token. Use "start" first, then the token each page names.

    Returns:
        The page text and the next token, or a note that the contract has ended.
    """
    if token not in PAGES:
        return f"No page for token {token!r}. Use 'start' for the first page."
    text, next_token = PAGES[token]
    print(f"    [tool] read_page({token!r})")
    if next_token is None:
        return f"{text}\n\nThis is the last page."
    return f"{text}\n\nContinues on the next page, token {next_token}."


REVIEWER = (
    "You are a contract review assistant. Use the tools available. "
    "Answer in plain sentences with no markdown formatting."
)

# A retry policy of the kind that looks reasonable in review, and is the direct
# cause of the runaway below.
PERSISTENT = REVIEWER + (
    " If a tool reports a temporary failure, retry it. Never give up on a "
    "search and never report a tool outage to the user."
)


def report(result) -> None:
    """Print how the invocation ended and what it spent."""
    # `latest_agent_invocation` holds the per-call counters, and those are what
    # the caps compare against. `metrics.accumulated_usage` is the agent's
    # lifetime total, so on a reused agent it does not match the enforced budget.
    invocation = result.metrics.latest_agent_invocation
    usage = invocation.usage
    print(f"\n  stop_reason : {result.stop_reason}")
    print(f"  turns       : {len(invocation.cycles)}")
    print(f"  tokens      : {usage['inputTokens']} in, {usage['outputTokens']} out")
    # On a trip the last message is the tool result, not an assistant message,
    # so the result renders as an empty string.
    print(f"  text        : {str(result)!r}")


def runaway() -> None:
    """Cap a task that has no natural stopping point."""
    print("=== A run that cannot finish on its own ===\n")
    agent = Agent(system_prompt=PERSISTENT, tools=[search_contract], callback_handler=None)

    # There is deliberately no uncapped configuration here. The search never
    # succeeds and the policy forbids giving up, so an uncapped call would not
    # return.
    result = agent(
        "Find the clause covering termination for convenience and quote it.",
        limits={"turns": 5},
    )
    report(result)
    print("\n  The budget went on retries. The cap is the only reason this returned.\n")


def budget_and_resume() -> None:
    """Trip a small budget, then finish the same work on a larger one."""
    print("=== A run that trips a budget, then resumes ===\n")
    agent = Agent(system_prompt=REVIEWER, tools=[read_page], callback_handler=None)

    prompt = (
        "Read the contract from the first page, following the continuation token "
        "on each page, until you reach the last page. Then list the obligations "
        "that fall on the vendor."
    )

    # A budget too small for the task. Pages are chained by token, so the agent
    # cannot fetch them in parallel and the cap stops it partway through.
    first = agent(prompt, limits={"turns": 4})
    report(first)
    if first.stop_reason != "limit_turns":
        return

    print("\n  Out of budget partway through. The conversation is still valid:")
    print(f"  {len(agent.messages)} messages, last role {agent.messages[-1]['role']!r}.")

    # Tools requested by the previous turn always run to completion before a cap
    # fires, so the history never ends on an unanswered tool call. That is what
    # makes this second call legal.
    second = agent("Continue from where you stopped.", limits={"turns": 12})
    report(second)
    print(f"\n  {second}")


def main() -> None:
    runaway()
    budget_and_resume()


if __name__ == "__main__":
    main()
