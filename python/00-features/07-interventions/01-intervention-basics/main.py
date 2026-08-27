"""Gate and rewrite what an agent does, using an intervention handler.

An intervention handler sits on the agent loop and returns an action at each
step it overrides: Proceed, Deny, Guide, or Transform.

Run:
    python main.py
"""

import re

from strands import Agent, tool
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent
from strands.interventions import Deny, InterventionHandler, Proceed, Transform

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
    # This never prints. The handler denies the call before the tool runs.
    print(f"  [tool] delete_customer({name!r}) ran")
    return f"deleted {name}"


def redact_emails(event: AfterToolCallEvent) -> None:
    """Rewrite the tool result in place, masking any email address."""
    for block in event.result.get("content", []):
        if "text" in block:
            block["text"] = EMAIL.sub("[redacted]", block["text"])


class Governance(InterventionHandler):
    """Blocks destructive tools and redacts PII from tool results.

    Lifecycle methods must be overridden at CLASS level. The framework inspects
    the class to decide which hooks to call, so assigning a function onto an
    instance is silently ignored.
    """

    name = "governance"

    DESTRUCTIVE = {"delete_customer"}

    def before_tool_call(self, event: BeforeToolCallEvent, **kwargs) -> Proceed | Deny:
        tool_name = event.tool_use["name"]
        if tool_name in self.DESTRUCTIVE:
            print(f"  [intervention] DENY {tool_name}")
            return Deny(reason="Deleting customer records requires a change ticket.")
        print(f"  [intervention] allow {tool_name}")
        return Proceed()

    def after_tool_call(self, event: AfterToolCallEvent, **kwargs) -> Proceed | Transform:
        rendered = str(event.result)
        if EMAIL.search(rendered):
            print(f"  [intervention] TRANSFORM {event.tool_use['name']} result, redacting email")
            return Transform(apply=redact_emails)
        return Proceed()


def main() -> None:
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

    print("\n--- Result ---")
    print(f"stop_reason : {result.stop_reason}")
    print(f"text        : {result}")

    # The email never reaches the model, because the transform rewrote the tool
    # result before it was appended to the conversation.
    transcript = str(agent.messages)
    print(f"\nemail in conversation history : {bool(EMAIL.search(transcript))}")
    print(f"'[redacted]' in history       : {'[redacted]' in transcript}")


if __name__ == "__main__":
    main()
