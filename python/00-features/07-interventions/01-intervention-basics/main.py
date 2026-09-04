"""Gate and rewrite what an agent does, using an intervention handler.

An intervention handler sits on the agent loop and returns a typed action at
each step it overrides. This script uses three of them: Proceed, Confirm, and
Transform. The README lists the full set and where each one is valid.

Run:
    python main.py

The script asks for approval on stdin before the destructive tool runs. Approve
with 'y', reject with anything else.
"""

import json
import re

from strands import Agent, tool
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent
from strands.interventions import Confirm, InterventionHandler, Proceed, Transform

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


@tool
def lookup_customer(name: str) -> str:
    """Look up a customer record by name.

    Args:
        name: The customer's full name.

    Returns:
        The customer record as text.
    """
    print(f"  [tool] lookup_customer({name!r}) ran")
    return f"name={name} plan=enterprise email=dana.reyes@example.com"


@tool
def delete_customer(name: str) -> str:
    """Permanently delete a customer record.

    Args:
        name: The customer's full name.

    Returns:
        Confirmation that the record was deleted.
    """
    # This prints only if you approve the call at the prompt.
    print(f"  [tool] delete_customer({name!r}) ran")
    return f"deleted {name}"


# The callable handed to `Transform(apply=...)` below. It receives the event and
# mutates it in place; the return value is not used.
def redact_emails(event: AfterToolCallEvent) -> None:
    """Rewrite the tool result in place, masking any email address."""
    for block in event.result.get("content", []):
        if "text" in block:
            block["text"] = EMAIL.sub("[redacted]", block["text"])


class Governance(InterventionHandler):
    """Asks before destructive tools, and redacts PII from tool results.

    Override only the lifecycle methods you need. The ones you leave alone are
    not called.
    """

    # Required on every handler, and unique across the handlers on one agent.
    name = "governance"

    NEEDS_APPROVAL = {"delete_customer"}

    def before_tool_call(self, event: BeforeToolCallEvent, **kwargs) -> Proceed | Confirm:
        tool_name = event.tool_use["name"]
        if tool_name in self.NEEDS_APPROVAL:
            # Ask the person here, then hand the answer to Confirm as
            # `response`. Confirm scores it with its `evaluate` function, which
            # accepts 'y' or 'yes' and rejects everything else, including an
            # empty line.
            answer = input(f"  [intervention] CONFIRM run {tool_name}? (y/n) ")
            # On a rejection the model is sent "CONFIRMATION_FAILED: <prompt>",
            # so write `prompt` as a statement about the policy. Phrase it as a
            # question and the model will relay that question back to the user
            # instead of reporting that the call was refused.
            return Confirm(
                prompt="A human reviewer declined this deletion. Do not retry it.",
                response=answer,
            )
        print(f"  [intervention] allow {tool_name}")
        # Proceed allows the step unchanged.
        return Proceed()

    def after_tool_call(self, event: AfterToolCallEvent, **kwargs) -> Proceed | Transform:
        rendered = str(event.result)
        if EMAIL.search(rendered):
            print(f"  [intervention] TRANSFORM {event.tool_use['name']} result, redacting email")
            # Strands calls redact_emails(event) before the result is appended
            # to the conversation, so the model never sees the raw email.
            return Transform(apply=redact_emails)
        return Proceed()


def main() -> None:
    # `interventions` takes handler instances. They run in the order given, so
    # a later handler sees what an earlier one transformed.
    agent = Agent(
        system_prompt=(
            "You are a customer operations assistant. Use the tools available. "
            "Answer in one or two plain sentences, with no markdown formatting."
        ),
        tools=[lookup_customer, delete_customer],
        interventions=[Governance()],
    )

    prompt = "Look up the customer Dana Reyes, then delete their record."
    print(f"Prompt: {prompt}\n")

    result = agent(prompt)

    print("\n\n--- Result ---")
    print(f"stop_reason : {result.stop_reason}")
    print(f"text        : {result}")

    # The transform rewrote the tool result before it was appended, so the
    # email is absent from the conversation itself, not merely from the answer.
    print("\n--- agent.messages ---")
    print(json.dumps(agent.messages, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
