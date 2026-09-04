Part II - Control the loop

# Intervention basics

Gate and rewrite what an agent does, using an intervention handler.

An intervention handler sits on the agent loop and returns an action at each step it overrides.
This leaf asks a person before a destructive tool runs, and redacts an email address out of a tool
result before the model ever sees it.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `InterventionHandler` | `strands.interventions.InterventionHandler` |
| `Proceed` | `strands.interventions.Proceed` |
| `Confirm` | `strands.interventions.Confirm` |
| `Transform` | `strands.interventions.Transform` |
| `interventions=` | keyword on `strands.Agent` |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

The script asks for approval on stdin before `delete_customer` runs. Approve with `y`, reject with
anything else.

## The five actions

| Action | Effect | Valid on |
|--------|--------|----------|
| `Proceed()` | Allow the step unchanged | every hook |
| `Deny(reason=...)` | Block the step. The reason is handed to the model as the cancellation message | `before_invocation`, `before_model_call`, `before_tool_call` |
| `Guide(feedback=...)` | Let the step run, but inject feedback to steer the model | `before_invocation`, `before_model_call`, `before_tool_call`, `after_model_call` |
| `Confirm(prompt=...)` | Request human approval before the step runs | `before_tool_call` |
| `Transform(apply=fn)` | Run `fn(event)` to mutate the event in place | every hook |

`Confirm` is what [`03-human-in-the-loop`](../03-human-in-the-loop/) is built on.

## Note the following

- **Override lifecycle methods at class level.** The framework inspects the class to decide which
  hooks to call. Assigning a function onto an instance is silently ignored, and the handler simply
  never fires.

  ```python
  # Works
  class Governance(InterventionHandler):
      name = "governance"
      def before_tool_call(self, event, **kwargs): ...

  # Silently does nothing
  handler = Governance()
  handler.before_tool_call = my_function
  ```

- **A `name` attribute is required** on the subclass.
- **Collect the answer yourself, then hand it to `Confirm` as `response`.** With a `response` set,
  the agent evaluates it inline and never pauses the loop. Leave `response` unset and `Confirm`
  instead breaks out of the loop to wait for an external resume, which is what a web UI would use.
- **`prompt` is written for the model, not only for the person.** On a rejection the tool result
  becomes `CONFIRMATION_FAILED: <prompt>`, so a `prompt` phrased as a question ("Run
  delete_customer?") comes back to the model as a question and it will relay that question to the
  user instead of reporting the refusal. Write it as a statement about the policy. Ask the person
  with your own `input()` string.
- **`Confirm` scores the answer with `evaluate`.** The default accepts `True`, `'y'`, or `'yes'`,
  case-insensitive and trimmed, and rejects everything else. An empty line is a rejection, so the
  gate fails closed.
- **A rejection is not an exception.** The tool is cancelled, the loop continues, and the model is
  told the call was not approved, so it can explain itself and finish its turn normally.
  `stop_reason` is `end_turn`, not an error.
- **`Transform` mutates the event in place** and returns nothing. Rewriting `event.result` in
  `after_tool_call` happens before the result is appended to the conversation, which is why the
  email is absent from `agent.messages` entirely rather than merely hidden from the final answer.
- **Only override the hooks you need.** Unoverridden hooks are not called at all.
- **Printing the conversation is yours to write.** `Message` is a plain `TypedDict`, so
  `print(agent.messages)` and `json.dumps(agent.messages, indent=4)` are both faithful but bury the
  content blocks in per-message `tracking_id` and `metadata`. Walking the blocks yourself also
  sidesteps the `TypeError` that `json.dumps` raises on a history holding binary blocks.

## Variations

- **Return `Deny(reason=...)`** instead of `Confirm` when a tool should never run and there is
  nothing to ask, for example when policy requires a change ticket. The reason reaches the model,
  so write it as an instruction rather than as a log line.
- **Return `Guide(feedback=...)`** when you want the model corrected rather than blocked, for
  example steering it toward a read-only tool.
- **Deny at the invocation level** by overriding `before_invocation`, which rejects the request
  before a single model call is billed.
- **Stack handlers** by passing several to `interventions=[...]`. They run in order.
- **Go async** by declaring any lifecycle method `async def`, for example to call an external
  authorization service.

## See also

- [`07-interventions/03-human-in-the-loop`](../03-human-in-the-loop/) for the vended `HumanInTheLoop`
  handler, which wraps this same `Confirm` plumbing and, unlike the inline gate here, pauses the run
  so the decision can be answered from somewhere other than this terminal.
- [`09-limits/01-execution-limits`](../../09-limits/01-execution-limits/) for capping cost rather than gating behavior.

Verified against strands-agents 1.54.0 on 2026-09-04
