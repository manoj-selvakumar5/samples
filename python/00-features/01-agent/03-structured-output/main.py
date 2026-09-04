"""Turn free text into a validated Pydantic object with Strands Structured Output.

Run:
    python main.py
"""

import textwrap

from pydantic import BaseModel, Field
from strands import Agent


# Define the structure we want the agent to return.
# Strands uses this Pydantic model as the output schema and validates
# the model's response against it.
class Event(BaseModel):
    """One thing that happened during the incident."""

    time: str = Field(description="Clock time as written, such as 09:12")
    detail: str = Field(description="What happened, in a few words")


# Structured output can contain nested Pydantic models.
# Because `events` is list[Event], each item must match the Event schema.
class Incident(BaseModel):
    """A timeline reconstructed from an engineer's account of an outage."""

    events: list[Event] = Field(
        description="Everything that happened, in order"
    )
    resolved: bool = Field(
        description="True if service was restored"
    )


REPORT = (
    "We pushed the release at 09:12. By 09:20 error rates had tripled, so we "
    "paged the on-call. Rolled back at 09:41 and things were back to normal by 09:50."
)


def main() -> None:
    print("--- Input: one paragraph of free text ---")
    print(
        textwrap.indent(
            textwrap.fill(REPORT, width=84, break_on_hyphens=False),
            "  ",
        )
    )
    print()

    # Set Incident as the agent's default structured output type.
    # Each invocation of this agent will now try to return an Incident.
    agent = Agent(
        structured_output_model=Incident,
        callback_handler=None,
    )

    # Invoke the agent normally.
    # The validated Incident object is available on
    # `result.structured_output`.
    result = agent(REPORT)
    incident = result.structured_output

    print("--- Result: agent(REPORT).structured_output ---")

    # `incident.events` is now a normal Python list of Event objects.
    # There is no free-form response to parse into these fields ourselves.
    width = max(len(event.time) for event in incident.events)

    for event in incident.events:
        print(f"  {event.time:<{width}}  {event.detail}")

    print()

    # Structured output is not limited to copying text directly.
    # The model can also infer field values from the input.
    # Here, "back to normal" provides the evidence for `resolved=True`.
    print(f"resolved: {incident.resolved}")


if __name__ == "__main__":
    main()
