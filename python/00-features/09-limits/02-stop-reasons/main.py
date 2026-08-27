"""Every way the agent loop can end, and how to tell them apart.

`stop_reason` is a twelve-value union. Every Part II feature produces one of
these values, and this is the only place they are shown as a set.

Run:
    python main.py
"""

import typing

from pydantic import BaseModel
from strands import Agent, tool
from strands.types.event_loop import StopReason
from strands.types.exceptions import MaxTokensReachedException

ALL_STOP_REASONS = sorted(typing.get_args(StopReason))

# Reachable from the areas built so far. The rest are listed in the README
# alongside the area that will own them.
NOT_DEMONSTRATED = {
    "cancelled": "agent.cancel(), a later 09-limits/ leaf",
    "checkpoint": "checkpointing=True, a later 10-sessions/ leaf",
    "content_filtered": "provider-side content filtering",
    "guardrail_intervened": "Amazon Bedrock Guardrails, a later 09-limits/ leaf",
    "interrupt": "an intervention raising an interrupt, a later 07-interventions/ leaf",
}


class Answer(BaseModel):
    """A short factual answer."""

    text: str


@tool
def next_number(n: int) -> int:
    """Return the number that follows n.

    Args:
        n: The current number.

    Returns:
        n plus one.
    """
    return n + 1


COUNT_PROMPT = (
    "Start at 1 and call next_number one step at a time until you reach 6. "
    "Call the tool once per step, silently, with no commentary."
)

QUIET = (
    "Answer plainly with no markdown. Call tools silently without commentary."
)


def show(label: str, result, expected: str) -> None:
    got = result.stop_reason
    mark = "OK" if got == expected else f"UNEXPECTED (wanted {expected})"
    print(f"  {label:22s} -> {got:20s} {mark}")


def main() -> None:
    seen = {}

    # end_turn: the model finished on its own.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    r = agent("Name the capital of Japan.")
    show("plain question", r, "end_turn")
    seen["end_turn"] = "model finished on its own"

    # tool_use: structured output is a forced tool call, so a successful
    # structured response reports tool_use rather than end_turn.
    agent = Agent(system_prompt=QUIET, structured_output_model=Answer, callback_handler=None)
    r = agent("Name the capital of Japan.")
    show("structured output", r, "tool_use")
    seen["tool_use"] = "loop ended on a tool call, including structured output"

    # max_tokens: the provider's own output ceiling. This one does NOT come
    # back as a stop_reason. The loop raises instead, because a truncated
    # message is not a result you should accidentally treat as an answer.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    agent.model.update_config(max_tokens=16)
    try:
        r = agent("Explain how a jet engine works.")
        show("model max_tokens=16", r, "max_tokens")
    except MaxTokensReachedException:
        print(f"  {'model max_tokens=16':22s} -> raised MaxTokensReachedException")
    seen["max_tokens"] = "provider output ceiling, raised as an exception"

    # stop_sequence: the model emitted a configured stop string.
    agent = Agent(system_prompt=QUIET, callback_handler=None)
    agent.model.update_config(stop_sequences=["4"])
    r = agent("Count from 1 to 9, separated by spaces.")
    show("stop_sequences=['4']", r, "stop_sequence")
    seen["stop_sequence"] = "model emitted a configured stop string"

    # The three limit_* values, all from the `limits` argument.
    for label, limits, expected in [
        ("limits turns=3", {"turns": 3}, "limit_turns"),
        ("limits total_tokens=2000", {"total_tokens": 2000}, "limit_total_tokens"),
        ("limits output_tokens=64", {"output_tokens": 64}, "limit_output_tokens"),
    ]:
        agent = Agent(system_prompt=QUIET, tools=[next_number], callback_handler=None)
        r = agent(COUNT_PROMPT, limits=limits)
        show(label, r, expected)
        seen[expected] = f"the {list(limits)[0]} cap in `limits`"

    print(f"\n--- Coverage: {len(seen)} of {len(ALL_STOP_REASONS)} ---")
    for value in ALL_STOP_REASONS:
        if value in seen:
            print(f"  [demonstrated] {value:22s} {seen[value]}")
        else:
            print(f"  [not here]     {value:22s} {NOT_DEMONSTRATED[value]}")


if __name__ == "__main__":
    main()
