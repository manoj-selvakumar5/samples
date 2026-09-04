"""Turn a free-text report into a typed Python object you can walk.

Run:
    python main.py
"""

import textwrap

from pydantic import BaseModel, Field
from strands import Agent


class Event(BaseModel):
    """One thing that happened during the incident."""

    time: str = Field(description="Clock time as written, such as 09:12")
    detail: str = Field(description="What happened, in a few words")


class Incident(BaseModel):
    """A timeline reconstructed from an engineer's account of an outage."""

    events: list[Event] = Field(description="Everything that happened, in order")
    resolved: bool = Field(description="True if service was restored")


REPORT = (
    "We pushed the release at 09:12. By 09:20 error rates had tripled, so we "
    "paged the on-call. Rolled back at 09:41 and things were back to normal by 09:50."
)


def main() -> None:
    print("--- Input ---")
    # break_on_hyphens=False keeps "on-call" off the end of a line.
    print(textwrap.indent(textwrap.fill(REPORT, width=84, break_on_hyphens=False), "  "))
    print()

    agent = Agent(structured_output_model=Incident, callback_handler=None)
    incident = agent(REPORT).structured_output

    print("--- Result ---")

    # A list of objects, so it iterates, sorts, and renders like any other list.
    # Times are padded to the widest one rather than assumed to be equal width.
    width = max(len(event.time) for event in incident.events)
    for event in incident.events:
        print(f"  {event.time:<{width}}  {event.detail}")
    print()

    print(f"resolved: {incident.resolved}")


if __name__ == "__main__":
    main()
