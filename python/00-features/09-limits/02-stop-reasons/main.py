"""Every way the agent loop can end, and how to tell them apart.

`stop_reason` is a twelve-value union, and this is the only place they are shown
as a set. The point is not that the values exist. It is that a returned
`AgentResult` does not mean a finished task, so the caller has to branch on how
the run ended. Each case below pairs a realistic ending with its recovery.

Run:
    python main.py
"""

import typing

from pydantic import BaseModel
from strands import Agent, tool
from strands.types.event_loop import StopReason
from strands.types.exceptions import MaxTokensReachedException

ALL_STOP_REASONS = sorted(typing.get_args(StopReason))

# What a caller should do with each ending. This is the table worth copying into
# real code: only the first two rows mean the text can be used as it stands.
ACTIONS = {
    "end_turn": "use the answer",
    "stop_sequence": "use the answer; the sequence was consumed",
    "tool_use": "read result.structured_output, not the text",
    "max_tokens": "raise the ceiling and reinvoke; the partial message is kept",
    "limit_turns": "raise the budget and reinvoke to continue",
    "limit_total_tokens": "raise the budget and reinvoke to continue",
    "limit_output_tokens": "raise the budget and reinvoke to continue",
    "cancelled": "the caller stopped this run; do not retry automatically",
    "checkpoint": "persist and resume later",
    "interrupt": "answer the interrupt and resume",
    "guardrail_intervened": "terminal; surface a refusal rather than retrying",
    "content_filtered": "terminal; surface a refusal rather than retrying",
}

# Values this script does not reach, and the mechanism that produces each one.
NOT_DEMONSTRATED = {
    "cancelled": "agent.cancel()",
    "checkpoint": "checkpointing=True",
    "content_filtered": "provider-side content filtering",
    "guardrail_intervened": "Amazon Bedrock Guardrails",
    "interrupt": "an intervention raising an interrupt",
}

SEEN: set[str] = set()
REPORT = (
    "At 09:12 we pushed release 4.2. By 09:20 error rates had tripled and the "
    "on-call engineer was paged. We rolled back at 09:41 and the service was "
    "healthy again by 09:50."
)

PARAGRAPHS = [
    "Release 4.2 shipped a change to the connection pool.",
    "The pool leaked handles under retry, exhausting the limit in eight minutes.",
    "Rolling back restored the previous settings and the leak stopped.",
]

QUIET = "Answer plainly with no markdown. Call tools silently without commentary."
READ_PROMPT = (
    "Read the write-up one paragraph at a time, starting at paragraph 1, and "
    "explain what caused the outage."
)


class Incident(BaseModel):
    """A structured summary of an incident report."""

    summary: str
    resolved: bool


@tool
def read_paragraph(number: int) -> str:
    """Read one numbered paragraph of the incident write-up.

    Args:
        number: The 1-based paragraph number.

    Returns:
        The paragraph text, or a note that it does not exist.
    """
    if not 1 <= number <= len(PARAGRAPHS):
        return f"There is no paragraph {number}."
    return PARAGRAPHS[number - 1]


def show(label: str, stop_reason: str, expected: str) -> None:
    """Print how one run ended and what the caller should do about it."""
    SEEN.add(stop_reason)
    mark = "" if stop_reason == expected else f"  UNEXPECTED (wanted {expected})"
    print(f"  {label:24s} -> {stop_reason:20s} {ACTIONS[stop_reason]}{mark}")


def main() -> None:
    # end_turn: the model finished on its own. The only ending whose text can be
    # used without further thought.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    show("plain question", agent(f"Summarize in one sentence: {REPORT}").stop_reason, "end_turn")

    # tool_use: structured output is a forced tool call, so a successful
    # structured response reports tool_use rather than end_turn. Code that treats
    # end_turn as the only success value misclassifies every one of these.
    agent = Agent(system_prompt=QUIET, structured_output_model=Incident, callback_handler=None)
    show("structured extraction", agent(f"Extract from: {REPORT}").stop_reason, "tool_use")

    # max_tokens: the provider's own output ceiling, and the exception to the
    # pattern. It raises rather than returning, because a truncated message is
    # not something you should mistake for an answer by forgetting to check a
    # field. The partial message stays in the conversation, so raising the
    # ceiling and reinvoking picks up from there.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    agent.model.update_config(max_tokens=16)
    try:
        show("model max_tokens=16", agent("Why do pools leak handles?").stop_reason, "max_tokens")
    except MaxTokensReachedException:
        SEEN.add("max_tokens")
        print(f"  {'model max_tokens=16':24s} -> raised MaxTokensReachedException")
        agent.model.update_config(max_tokens=2048)
        print(f"  {'  after raising it':24s} -> {agent('Continue.').stop_reason:20s} recovered")

    # stop_sequence: the model emitted a configured stop string. Useful as a
    # delimiter when you want one section rather than a whole document. The
    # sequence itself is consumed and does not appear in the text.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    agent.model.update_config(stop_sequences=["## Timeline"])
    prompt = f"Write a summary section, then a '## Timeline' section, for: {REPORT}"
    show("stop at a delimiter", agent(prompt).stop_reason, "stop_sequence")

    # The three limit_* values. A budget too small for the task ends the run
    # partway, and the conversation stays valid so it can be continued.
    for label, limits, expected in [
        ("budget: turns", {"turns": 2}, "limit_turns"),
        ("budget: total tokens", {"total_tokens": 1500}, "limit_total_tokens"),
        ("budget: output tokens", {"output_tokens": 64}, "limit_output_tokens"),
    ]:
        agent = Agent(system_prompt=QUIET, tools=[read_paragraph], callback_handler=None)
        show(label, agent(READ_PROMPT, limits=limits).stop_reason, expected)

    print(f"\n--- Coverage: {len(SEEN)} of {len(ALL_STOP_REASONS)} ---")
    for value in ALL_STOP_REASONS:
        state = "[demonstrated]" if value in SEEN else "[not here]    "
        detail = ACTIONS[value] if value in SEEN else NOT_DEMONSTRATED[value]
        print(f"  {state} {value:22s} {detail}")


if __name__ == "__main__":
    main()
