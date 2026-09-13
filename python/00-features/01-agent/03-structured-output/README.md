Part I - Build the agent

# Extract a typed object from free text with structured output

## Overview

An agent's default answer is prose. That is the right shape when a person reads it and the wrong
shape when code has to act on it. A paragraph that happens to mention four timestamps is not a list
you can iterate, sort, or store, and turning it into one means writing a parser against wording the
model is free to vary from run to run.

In this tutorial, an engineer's account of an outage goes in as one paragraph of free text and a
timeline comes back as a Python object: a list of `Event` values, plus a boolean saying whether
service was restored.

Structured output removes the parsing step. You declare the shape you want as a Pydantic model, pass
it as `structured_output_model`, and read the result off `AgentResult.structured_output`. What comes
back is a real object, not a string that looks like one.

`structured_output_model` can be set on the `Agent`, where it applies to every call, or passed for a
single invocation. This tutorial sets it on the agent.

---

## What you will learn

- how to declare an output shape as a Pydantic model and read it back as a validated object
- how field descriptions and the class docstring become the instructions the model receives
- why a successful structured run reports `stop_reason` as `tool_use` rather than `end_turn`
- why validation failure and extraction failure are different outcomes, and which one raises

---

## How structured output works

The Pydantic model is not inspected after the fact. It travels with the request:

```text
Incident (Pydantic model)
      │
      │ field names, types, descriptions, and the class docstring
      ▼
Model call  ◄────  REPORT (free text)
      │
      │ the model supplies a value for every field
      ▼
Validate against Incident
      │
      ├── a field does not fit ──► errors go back to the model,
      │                            which gets another attempt
      ▼
AgentResult.structured_output
      = Incident(events=[...], resolved=True)
```

The important detail is **where validation sits**: before your code runs, not after. By the time an
object reaches `structured_output` it has already been constructed as an `Incident`, so there is
nothing to parse and nothing to check by hand.

What the schema does not pin down is size. A list field says what each item must look like, not how
many items there are:

```text
one paragraph of prose
          │
          ▼
events: list[Event]
          │
          ├── Event(time="09:12", detail=...)
          ├── Event(time="09:20", detail=...)
          ├── Event(time="09:41", detail=...)
          └── Event(time="09:50", detail=...)
```

The model decides how many events the report contains. That is why this tutorial nests `Event`
inside `Incident` rather than declaring four scalar timestamp fields: a flat model with a known set
of fields cannot show that behavior.

---

## Prerequisites and setup

Before starting, make sure you have:

- Python 3.10 or later
- AWS credentials configured
- access to a supported model in Amazon Bedrock

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the tutorial

```bash
python main.py
```

The script runs one scenario.

### 1. Reconstruct a timeline from a free-text report

`REPORT` is a single paragraph written the way an engineer would write it. The wanted shape is
declared as two Pydantic models, the inner one describing a single moment and the outer one
describing the whole incident:

```python
class Event(BaseModel):
    """One thing that happened during the incident."""

    time: str = Field(description="Clock time as written, such as 09:12")
    detail: str = Field(description="What happened, in a few words")


class Incident(BaseModel):
    """A timeline reconstructed from an engineer's account of an outage."""

    events: list[Event] = Field(
        description="Everything that happened, in order"
    )
    resolved: bool = Field(
        description="True if service was restored"
    )
```

`Incident` is then set as the agent's output model, and the agent is invoked normally:

```python
agent = Agent(
    structured_output_model=Incident,
    callback_handler=None,
)

result = agent(REPORT)
incident = result.structured_output
```

`incident.events` is an ordinary Python list of `Event` objects, so the script can measure the
widest timestamp and print an aligned table. Against a paragraph of prose that would have meant
writing a parser first. This is what structured output buys that a well-worded prompt does not.

### Expected output

Output varies because the model chooses the wording of the free-text fields. An abbreviated run:

```text
--- Input: one paragraph of free text ---
  We pushed the release at 09:12. By 09:20 error rates had tripled, so we paged the
  on-call. Rolled back at 09:41 and things were back to normal by 09:50.

--- Result: agent(REPORT).structured_output ---
  09:12  <what happened>
  09:20  <what happened>
  09:41  <what happened>
  09:50  <what happened>

resolved: True
```

**In this example**, both halves are printed so that the terminal explains itself. Without the input
echoed, the timestamps would appear from nowhere and you could not tell extraction from invention.
The number of rows is not fixed either, so seeing the source paragraph is what makes the
segmentation legible.

`resolved` is inferred rather than copied. The report never says the incident was resolved. "Back to
normal by 09:50" implies it, and the field description tells the model what the flag means.

---

## Understanding structured output

### What the model is asked to produce

Three things in the class reach the model:

- each field's name and type
- each `Field(description=...)`
- the class docstring, which describes the object as a whole

Descriptions are therefore instructions, not comments. `Field(description="True if service was
restored")` is the reason `resolved` comes back as a boolean judgement rather than a quotation, and
`Field(description="Clock time as written, such as 09:12")` is the reason the times are not
reformatted.

`Incident.model_fields` holds those descriptions at runtime if you want to see exactly what the
model was told.

### What comes back

`AgentResult.structured_output` holds a validated instance, or `None`:

```python
result = agent(REPORT)
incident = result.structured_output

type(incident).__name__   # 'Incident'
incident.events[0].time   # '09:12'
incident.resolved         # True
```

It is only ever set from an instance that already passed validation, so a call that returned an
object has produced an `Incident`. Nested models are real objects too: every item in
`incident.events` is an `Event`, not a dictionary.

`str(result)` and `print(result)` return the object as JSON rather than the message text whenever
structured output is present.

### Where to set the output model

On the `Agent`, as this tutorial does, where it applies to every call. Or on a single call, where it
overrides the agent's setting for that call only and leaves the agent unchanged:

```python
agent = Agent(structured_output_model=Incident)

agent(report).structured_output                                  # Incident
agent(other, structured_output_model=Summary).structured_output  # Summary
agent(third).structured_output                                   # Incident again
```

The keyword is accepted by `__call__`, `invoke_async`, and `stream_async`, alongside
`structured_output_prompt`. That second keyword replaces the default message Strands sends to ask
for the object again when a response came back as prose instead, which is `"You must format the
previous response as structured output."` Use it to steer extraction without touching the system
prompt.

### Why a successful run reports `tool_use`

The model returns the object by requesting it, so the run reports:

```text
stop_reason = "tool_use"
```

A run that succeeded therefore carries the same stop reason as one that paused to call a tool. Code
that treats `end_turn` as the only success value will misclassify every structured response. Branch
on `structured_output` being present instead.

### When validation fails

A Pydantic `ValidationError` does not reach your code. The failing fields are named back to the
model, which gets another attempt at them.

The practical consequence is that a schema the model struggles to satisfy costs extra turns rather
than raising. That matters when you are also setting `limits`, because those turns spend the same
budget as useful work.

### When no object comes back

Two outcomes are worth telling apart, and only one of them raises.

If the model will not produce the object at all, the call raises `StructuredOutputException`:

```python
from strands.types.exceptions import StructuredOutputException

try:
    incident = agent(report, structured_output_model=Incident).structured_output
except StructuredOutputException:
    ...  # fall back to unstructured, or re-prompt
```

If the invocation instead ends some other way before an object exists, by reaching a cap in `limits`
for example, nothing is raised and `structured_output` is left as `None`. That is the one case where
checking for `None` before using the result earns its place. See
[09-limits/01-stop-a-runaway-agent](../../09-limits/01-stop-a-runaway-agent/).

---

## Designing the output model

Prose in a `description` is guidance. A type is enforcement. When a constraint actually matters,
express it in the type rather than in words:

| Requirement                               | Express it as                            |
|:------------------------------------------|:-----------------------------------------|
| one of a fixed set of values              | `Literal["low", "high"]` or an `Enum`    |
| a number inside a range                   | `Field(ge=0, le=1)`                      |
| a value that may be absent from the input | `Optional[str]` with a default           |
| a repeated sub-structure                  | a nested `BaseModel`, as `Event` is here |

Nesting is not limited to one level. Giving `Event` a field whose type is another `BaseModel` works
the same way `Incident` nests `Event`.

Rely on the schema, not on the exact strings. Field names, types, and list membership are
guaranteed by validation. The wording inside a free-text field belongs to the model and can move
between runs of the same input, so assert on shape in tests and treat the prose inside as prose.

Keep the schema no wider than what the caller needs. Every field is one more thing the model has to
get right, and a field with no grounding in the input is a field it will guess at.

---

## Structured output versus asking for JSON in the prompt

A prompt can ask for JSON, and a capable model will often produce something close to it. The
difference is what you are holding afterwards.

Prompted JSON arrives as text, so parsing and validation are your job, and a response that drifts
from the requested shape fails somewhere inside your own code. With `structured_output_model` the
shape travels with the request and validation happens before the result reaches you, so a drifting
response becomes another attempt by the model or a raised exception rather than a `KeyError` three
lines later.

Structured output also composes with the rest of an agent run. The declared object is what ends the
loop, so the agent can call ordinary tools first and still return an `Incident` at the end.

---

## Additional resources

- [Structured Output](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/)
- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/)
- [`01-agent/01-first-agent`](../01-first-agent/) for the plain construct-and-invoke path with no
  schema.
