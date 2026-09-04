Part I - Build the agent

# Structured output

Turn a free-text report into a typed Python object you can walk.

Declare the shape you want as a Pydantic model, pass it as `structured_output_model`, and read the
result off `AgentResult.structured_output`. What comes back is a real object, not a string that
looks like one.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `structured_output_model` | keyword on `strands.Agent` and on the invoke path |
| `AgentResult.structured_output` | the parsed, validated object |
| `BaseModel` | `pydantic.BaseModel` |
| `Field` | `pydantic.Field`, whose `description` reaches the model |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Output

```
type: Incident, events: 4
whole object: events=[Event(time='09:12', detail='Release pushed'), Event(time='09:20', detail='Error rates tripled, on-call paged'), Event(time='09:41', detail='Rollback performed'), Event(time='09:50', detail='Service returned to normal')] resolved=True
09:12  Release pushed
09:20  Error rates tripled, on-call paged
09:41  Rollback performed
09:50  Service returned to normal
resolved: True
```

## Note the following

- **The first line is the proof.** `type: Incident, events: 4` says the result is an `Incident`
  object, not text that resembles one, and that the list length came from the model rather than
  from the schema. Everything below it follows from that.
- **The loop is the point.** `incident.events` is a list of `Event` objects, so you can iterate it,
  sort it, or render each entry separately. Against a paragraph of prose you would be writing a
  parser first. This is what structured output buys you that a well-worded prompt does not.
- **The list length is not fixed.** Nothing tells the model how many events to produce; it segments
  the report itself. A flat model with a known set of fields cannot demonstrate this, which is why
  the example nests `Event` inside `Incident` rather than using four scalar fields.
- **`resolved` is inferred, not extracted.** The report never says the incident was resolved. "Back
  to normal by 09:50" implies it, and the field description tells the model what the flag means.
- **`Field(description=...)` is the instruction the model receives**, and the model's docstring
  becomes the description of the tool the SDK builds from it. Both are shipped to the model, so
  neither is decoration.
- **`stop_reason` is `tool_use`, not `end_turn`.** Structured output is implemented as a forced tool
  call, so a run that succeeded reports the same stop reason as one that paused to call a tool. Code
  that treats `end_turn` as the only success value will misclassify every structured response.
- **`structured_output_model` works in two places.** On the `Agent`, as here, where it applies to
  every call. Or on a single call, where it overrides the agent's setting for that call only and
  leaves the agent unchanged:

  ```python
  agent = Agent(structured_output_model=Incident)

  agent(report).structured_output                                  # Incident
  agent(other, structured_output_model=Summary).structured_output  # Summary
  agent(third).structured_output                                   # Incident again
  ```

- **The wording varies, the shape does not.** Across repeated runs this report consistently produced
  four events at the same four timestamps; only the phrasing of `detail` moved, for example
  `Rollback initiated` against `Rollback performed`. Expect your run to match the structure above
  rather than the exact strings.

## Variations

- **Constrain a field to a fixed set** with `Literal["low", "high"]` or an `Enum`, so Pydantic
  rejects anything off-list rather than passing it through. Prose in a `description` is guidance;
  a type is enforcement.
- **Bound a number** with `Field(ge=0, le=1)` rather than describing the range in words.
- **Make a field optional** with `Optional[str]` and a default, for data that may not be in the
  input at all.
- **Nest one level deeper** by giving `Event` a field whose type is another `BaseModel`.
- **Add `structured_output_prompt=`** to steer extraction without touching the system prompt.
- **See the forced tool call for yourself** by removing `callback_handler=None`. The default handler
  streams the loop and the trace shows `Tool #1: Incident`, the tool name being the Pydantic class
  name.
- **Handle `StructuredOutputException`**, the failure mode this leaf does not provoke:

  ```python
  from strands.types.exceptions import StructuredOutputException

  try:
      incident = agent(report, structured_output_model=Incident).structured_output
  except StructuredOutputException:
      ...  # fall back to unstructured, or re-prompt
  ```

  The loop does not give up on the first miss. If the model replies with `end_turn` instead of
  calling the structured output tool, the SDK appends `structured_output_prompt` and retries once
  with the tool forced. Only if that forced attempt also comes back without a tool call does it
  raise.

  That is a *model never called the tool* error. A Pydantic `ValidationError` is handled elsewhere
  and never reaches you: the tool returns a result with `status: "error"` listing each bad field,
  and hands it back to the model to correct itself. So a schema the model struggles to satisfy costs
  extra turns rather than raising, which matters when you are also setting `limits`.

## See also

- [`01-agent/01-first-agent`](../01-first-agent/) for the basic construct-and-invoke path.
- [`09-limits/02-stop-reasons`](../../09-limits/02-stop-reasons/) for why this leaf reports `tool_use`.

Verified against strands-agents 1.54.0 on 2026-09-03
