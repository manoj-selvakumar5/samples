"""Turn a free-text report into a typed Python object you can walk.

Run:
    python main.py
"""

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

agent = Agent(
    structured_output_model=Incident,
    callback_handler=None,  # silence the streaming trace
)


def main() -> None:
    incident = agent(REPORT).structured_output

    print(f"type: {type(incident).__name__}, events: {len(incident.events)}")
    print(f"whole object: {incident}")

    # A list of objects. Iterate it directly; prose would need a parser first.
    for event in incident.events:
        print(f"{event.time}  {event.detail}")

    print(f"resolved: {incident.resolved}")


if __name__ == "__main__":
    main()


"""
type: Incident, events: 4
whole object: events=[Event(time='09:12', detail='Release pushed'), Event(time='09:20', detail='Error rates tripled, on-call paged'), Event(time='09:41', detail='Rollback performed'), Event(time='09:50', detail='Service returned to normal')] resolved=True
09:12  Release pushed
09:20  Error rates tripled, on-call paged
09:41  Rollback performed
09:50  Service returned to normal
resolved: True
"""
