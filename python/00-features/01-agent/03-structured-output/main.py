"""Get a validated Pydantic object back from an agent instead of prose.

Run:
    python main.py
"""

from pydantic import BaseModel, Field
from strands import Agent


class Ticket(BaseModel):
    """A support ticket parsed from a free-text customer message."""

    summary: str = Field(description="One-line summary of the problem")
    severity: str = Field(description="One of: low, medium, high, critical")
    component: str = Field(description="The product area affected")
    needs_escalation: bool = Field(description="True if a human must review this")


class Sentiment(BaseModel):
    """Sentiment of a customer message."""

    tone: str = Field(description="One of: calm, frustrated, angry")
    confidence: float = Field(description="Confidence between 0.0 and 1.0")


MESSAGE = (
    "I have been trying to export my billing report for three days and the "
    "download button does nothing. This is holding up our month-end close."
)


def section(number: int, title: str, setup: str) -> None:
    """Announce what is about to run and what was configured to make it run."""
    print(f"\n=== {number}. {title} ===")
    print(f"{setup}\n")


def field(label: str, value: object, note: str = "") -> None:
    """Print one aligned label/value pair, with an optional inline callout.

    Annotated values are short, so padding them to a fixed width lines the
    callouts up in their own column.
    """
    if note:
        print(f"  {label:<17}: {str(value):<11} <- {note}")
    else:
        print(f"  {label:<17}: {value}")


def main() -> None:
    # Declaring the output type on the constructor makes it the default for
    # every invocation of this agent.
    agent = Agent(
        system_prompt="You triage customer support messages.",
        structured_output_model=Ticket,
        callback_handler=None,
    )

    section(
        1,
        "Declared on the constructor",
        "structured_output_model=Ticket, so every call returns a Ticket.",
    )
    result = agent(MESSAGE)
    ticket = result.structured_output

    field("type", type(ticket).__name__, "a Ticket object, not a string")
    field("summary", ticket.summary)
    field("severity", ticket.severity)
    field("component", ticket.component)
    field("needs_escalation", ticket.needs_escalation, "a real bool, not the text 'True'")
    field("stop_reason", result.stop_reason, "not end_turn: this is a forced tool call")

    # The same keyword on the invocation overrides the constructor for that
    # call only.
    section(
        2,
        "Overridden for one call",
        "Same agent object, structured_output_model=Sentiment passed to this call.",
    )
    sentiment = agent(
        "Classify the tone of that message.",
        structured_output_model=Sentiment,
    ).structured_output

    field("type", type(sentiment).__name__, "different shape, agent not rebuilt")
    field("tone", sentiment.tone)
    field("confidence", sentiment.confidence)

    # If the override had mutated the agent, this call would return a Sentiment.
    section(
        3,
        "Constructor default survives",
        "Nothing passed to this call, so the constructor default applies again.",
    )
    again = agent("Triage this: the search box returns no results for any query.")

    field("type", type(again.structured_output).__name__, "step 2's override did not stick")
    field("severity", again.structured_output.severity)

    print("\nTakeaway: set the model once on the constructor for a fixed shape,")
    print("pass it per call to vary the shape without rebuilding the agent.")


if __name__ == "__main__":
    main()
