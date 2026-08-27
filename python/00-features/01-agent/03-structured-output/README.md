Part I - Build the agent

# Structured output

Get a validated Pydantic object back from an agent instead of prose.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `structured_output_model` | keyword on `strands.Agent` and on the invoke path |
| `AgentResult.structured_output` | the parsed, validated object |
| `BaseModel` | `pydantic.BaseModel` |

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
=== 1. Declared on the constructor ===
structured_output_model=Ticket, so every call returns a Ticket.

  type             : Ticket      <- a Ticket object, not a string
  summary          : Billing report export/download button is non-functional, blocking month-end close
  severity         : high
  component        : Billing
  needs_escalation : True        <- a real bool, not the text 'True'
  stop_reason      : tool_use    <- not end_turn: this is a forced tool call

=== 2. Overridden for one call ===
Same agent object, structured_output_model=Sentiment passed to this call.

  type             : Sentiment   <- different shape, agent not rebuilt
  tone             : frustrated
  confidence       : 0.92

=== 3. Constructor default survives ===
Nothing passed to this call, so the constructor default applies again.

  type             : Ticket      <- step 2's override did not stick
  severity         : high

Takeaway: set the model once on the constructor for a fixed shape,
pass it per call to vary the shape without rebuilding the agent.
```

## Note the following

- **`structured_output_model` works in two places**: on the `Agent` constructor, where it applies
  to every invocation, and on the invoke call, where it overrides the constructor for that call
  only. The third block of output confirms the constructor default survives an override.
- **`Agent.structured_output()` is deprecated.** The method still exists and still works, but it
  emits a `DeprecationWarning` directing you to pass `structured_output_model` into the invocation
  instead. Do not build new code on it.

  ```python
  # Deprecated
  ticket = agent.structured_output(Ticket, message)

  # Current
  ticket = agent(message, structured_output_model=Ticket).structured_output
  ```

- **`stop_reason` is `tool_use`, not `end_turn`.** Structured output is implemented as a forced
  tool call, so a run that succeeded reports the same stop reason as one that stopped to call a
  tool. This surprises people reading `stop_reason` to decide whether a run finished cleanly. See
  [`09-limits/02-stop-reasons`](../../09-limits/02-stop-reasons/).
- **`Field(description=...)` is the instruction the model receives.** The field descriptions are
  the only guidance it gets about what `severity` means, so constraints belong there rather than in
  the system prompt.

## Variations

- **See the forced tool call for yourself** by removing `callback_handler=None` from the `Agent`
  constructors. The default handler streams the loop, and the trace shows `Tool #1: Ticket`, the
  tool name being the Pydantic class name. It is set to `None` here only to keep the output legible.
- **Constrain values properly** with an `enum` or `Literal` type rather than describing the allowed
  values in prose, so Pydantic rejects anything off-list instead of passing it through.
- **Nest models** by declaring a field whose type is another `BaseModel`, for output that is not flat.
- **Add `structured_output_prompt=`** to steer extraction without touching the system prompt.
- **Return a list** by wrapping the item model in a container model with a `list[Item]` field.
- **Handle `StructuredOutputException`**, which is the failure mode this leaf does not provoke:

  ```python
  from strands.types.exceptions import StructuredOutputException

  try:
      ticket = agent(message, structured_output_model=Ticket).structured_output
  except StructuredOutputException:
      ...  # fall back to unstructured, or re-prompt
  ```

  The loop does not give up on the first miss. If the model replies with `end_turn` instead of
  calling the structured output tool, the SDK appends `structured_output_prompt` and retries once
  with the tool forced. Only if that forced attempt also comes back without a tool call does it
  raise, with the message `The model failed to invoke the structured output tool even after it was
  forced.` It bubbles up directly rather than being wrapped in an `EventLoopException`.

  This is a *model never called the tool* error. A Pydantic `ValidationError` is handled somewhere
  else entirely and never reaches you: the tool returns a result with `status: "error"` listing
  each bad field as `Field 'severity': <reason>`, and hands that back to the model so it can
  correct itself and retry. So a schema the model struggles to satisfy costs extra turns rather
  than raising, which is worth knowing when you are also setting `limits`.

## See also

- [`01-agent/01-first-agent`](../01-first-agent/) for the basic construct-and-invoke path.
- [`09-limits/02-stop-reasons`](../../09-limits/02-stop-reasons/) for why this leaf reports `tool_use`.

Verified against strands-agents 1.53.0 on 2026-08-26
