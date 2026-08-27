Part II - Control the loop

# Intervention basics

Gate and rewrite what an agent does, using an intervention handler.

An intervention handler sits on the agent loop and returns an action at each step it overrides.
This leaf blocks a destructive tool and redacts an email address out of a tool result before the
model ever sees it.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `InterventionHandler` | `strands.interventions.InterventionHandler` |
| `Proceed` | `strands.interventions.Proceed` |
| `Deny` | `strands.interventions.Deny` |
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

## Output

```
Prompt: Look up the customer Dana Reyes, then delete their record.

I'll start by looking up Dana Reyes's record right away!
Tool #1: lookup_customer
  [intervention] allow lookup_customer
  [tool] lookup_customer('Dana Reyes') ran
  [intervention] TRANSFORM lookup_customer result, redacting email
I found Dana Reyes's record. Now I'll proceed to delete it.
Tool #2: delete_customer
  [intervention] DENY delete_customer
The deletion was denied because deleting customer records requires a change ticket to be submitted first. Please create a change ticket and try again once it has been approved.
--- Result ---
stop_reason : end_turn
text        : The deletion was denied because deleting customer records requires a change ticket to be submitted first. Please create a change ticket and try again once it has been approved.


email in conversation history : False
'[redacted]' in history       : True
```

`[tool] delete_customer(...) ran` never appears, because the handler blocked the call before the
tool function was entered.

## The four actions

| Action | Effect | Valid on |
|--------|--------|----------|
| `Proceed()` | Allow the step unchanged | every hook |
| `Deny(reason=...)` | Block the step. The reason is handed to the model as the cancellation message | `before_invocation`, `before_model_call`, `before_tool_call` |
| `Guide(feedback=...)` | Let the step run, but inject feedback to steer the model | `before_invocation`, `before_model_call`, `before_tool_call`, `after_model_call` |
| `Transform(apply=fn)` | Run `fn(event)` to mutate the event in place | every hook |

`Confirm(prompt=...)` is a fifth action, valid only on `before_tool_call`. It requests human
approval, which is what [`03-human-in-the-loop`](../03-human-in-the-loop/) is built on.

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
- **`Deny` is not an exception.** The loop continues, and the model is told the call was refused
  along with your reason, so it can explain itself or choose another path. The output above shows
  the model relaying the change-ticket requirement to the user.
- **The `reason` text reaches the model**, so write it as an instruction rather than as a log line.
- **`Transform` mutates the event in place** and returns nothing. Rewriting `event.result` in
  `after_tool_call` happens before the result is appended to the conversation, which is why the
  email is absent from `agent.messages` entirely rather than merely hidden from the final answer.
- **Only override the hooks you need.** Unoverridden hooks are not called at all.

## Variations

- **Return `Guide(feedback=...)`** instead of `Deny` when you want the model corrected rather than
  blocked, for example steering it toward a read-only tool.
- **Deny at the invocation level** by overriding `before_invocation`, which rejects the request
  before a single model call is billed.
- **Stack handlers** by passing several to `interventions=[...]`. They run in order.
- **Go async** by declaring any lifecycle method `async def`, for example to call an external
  authorization service.

## See also

- [`07-interventions/03-human-in-the-loop`](../03-human-in-the-loop/) for the vended handler that asks a person.
- [`09-limits/01-execution-limits`](../../09-limits/01-execution-limits/) for capping cost rather than gating behavior.

Verified against strands-agents 1.53.0 on 2026-08-26
