# Gate and rewrite agent actions with intervention handlers

## Overview

An agent that has tools can call any of them, with whatever arguments it chooses. Usually that is
the point. But some tools delete records, move money, or send mail, and some tool results carry data
the model should never be shown in the first place. Neither concern belongs inside the tool
function: the tool should not have to know who is allowed to call it.

In this tutorial, a customer operations agent is asked to look up a customer and then delete their
record. Two things have to happen before that request is allowed to run to completion. A person has
to approve the deletion, and the email address in the lookup result has to be removed before the
model sees it.

An intervention handler does both. It is a class you subclass from `InterventionHandler`, overriding
only the lifecycle methods you care about, and each override returns a typed action saying what
should happen at that step: allow it, block it, steer it, ask a person, or rewrite it. Handlers are
passed to the `Agent` constructor through `interventions=`, so they apply to every invocation of
that agent rather than to one call.

---

## What you will learn

- how to require human approval before one specific tool runs
- how to rewrite a tool result before the model or the conversation history ever sees it
- why a blocked tool is a normal outcome rather than an exception
- how to choose between blocking, steering, and asking

---

## Prerequisites and setup

Before starting, make sure you have:

- Python 3.10 or later
- AWS credentials configured
- access to a supported model in Amazon Bedrock
- an interactive terminal, because this script reads the approval from stdin

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the tutorial

```bash
python main.py
```

The script sends one task through two intervention points, and pauses at the first one for an answer
on stdin. Approve the deletion with `y`; anything else rejects it.

### 1. Ask a person before a destructive tool runs

`before_tool_call` fires for every tool the model requests, so the handler decides per tool name. It
collects the answer itself and hands that answer to `Confirm` as `response`:

```python
NEEDS_APPROVAL = {"delete_customer"}

def before_tool_call(self, event: BeforeToolCallEvent, **kwargs) -> Proceed | Confirm:
    tool_name = event.tool_use["name"]
    if tool_name in self.NEEDS_APPROVAL:
        answer = input(f"  [intervention] CONFIRM run {tool_name}? (y/n) ")
        return Confirm(
            prompt="A human reviewer declined this deletion. Do not retry it.",
            response=answer,
        )
    print(f"  [intervention] allow {tool_name}")
    return Proceed()
```

`lookup_customer` is not in `NEEDS_APPROVAL`, so it gets a `Proceed()` and runs unchanged.
`delete_customer` is, so the run stops at the prompt and waits.

### 2. Redact PII out of a tool result

`lookup_customer` returns an email address. `after_tool_call` catches the result on its way into the
conversation and returns a `Transform` carrying the function that rewrites it:

```python
def after_tool_call(self, event: AfterToolCallEvent, **kwargs) -> Proceed | Transform:
    rendered = str(event.result)
    if EMAIL.search(rendered):
        print(f"  [intervention] TRANSFORM {event.tool_use['name']} result, redacting email")
        return Transform(apply=redact_emails)
    return Proceed()
```

`redact_emails` receives the event and edits it in place. Nothing is returned:

```python
def redact_emails(event: AfterToolCallEvent) -> None:
    """Rewrite the tool result in place, masking any email address."""
    for block in event.result.get("content", []):
        if "text" in block:
            block["text"] = EMAIL.sub("[redacted]", block["text"])
```

<details>
<summary><b>Expected output</b></summary>

Output varies because the model's wording is not deterministic. An abbreviated run, rejecting the
deletion:

```text
Prompt: Look up the customer Dana Reyes, then delete their record.

<the model says what it is about to do>
Tool #1: lookup_customer
  [intervention] allow lookup_customer
  [tool] lookup_customer('Dana Reyes') ran
  [intervention] TRANSFORM lookup_customer result, redacting email
<the model says what it is about to do>
Tool #2: delete_customer
  [intervention] CONFIRM run delete_customer? (y/n) n
<the model reports that the deletion was declined>

--- Result ---
stop_reason : end_turn
text        : <the model reports that the deletion was declined>


--- agent.messages ---
[0] user
      text       : Look up the customer Dana Reyes, then delete their record.
[1] assistant
      text       : <the model says what it is about to do>
      toolUse    : lookup_customer {"name": "Dana Reyes"}
[2] user
      toolResult : success
                   name=Dana Reyes plan=enterprise email=[redacted]
[3] assistant
      text       : <the model says what it is about to do>
      toolUse    : delete_customer {"name": "Dana Reyes"}
[4] user
      toolResult : error
                   CONFIRMATION_FAILED: A human reviewer declined this deletion. Do not retry
                   it.
[5] assistant
      text       : <the model reports that the deletion was declined>
```

Two absences are the result. There is no `[tool] delete_customer(...) ran` line, because the tool
function was never entered. And message `[2]` already reads `email=[redacted]`, because the
transform ran before that message was appended, so the raw address is not in the history at all.

**In this example**, the `<the model says what it is about to do>` lines and the `Tool #N:` lines
come from the SDK's default callback handler streaming the model's output, not from the script's own
`print` calls. The typed `n` appears on the same line as the `(y/n)` prompt because `input()` writes
its prompt without a trailing newline.

</details>

---

## How an intervention handler sits in the agent loop

A handler is not a wrapper around your tool functions. It sits in the gaps the agent loop leaves
between deciding to call a tool and recording what that tool returned:

```text
Model returns a tool request
        │
        ▼
  before_tool_call ──► Deny, or a Confirm that was rejected
        │                        │
        │ Proceed                └──► the tool never executes
        ▼
  Tool executes
        │
        ▼
  after_tool_call  ──► Transform(apply=fn) rewrites event.result in place
        │
        ▼
  Tool result appended to agent.messages
        │
        ▼
  Next model call reads it
```

Both placements carry their weight. `before_tool_call` runs after the model has asked for the tool
but before any tool code runs, so blocking there means the side effect never happens at all.
`after_tool_call` runs after the tool returns but before its result is appended to the conversation,
so rewriting there takes the data out of the history rather than hiding it from the final answer.

Blocking a tool does not raise. The cancellation becomes an ordinary tool result, which the model
reads and responds to:

```text
Confirm rejected
        │
        ▼
toolResult status  = "error"
toolResult content = "CONFIRMATION_FAILED: <your prompt>"
        │
        ▼
Model reads the refusal and finishes its turn
        │
        ▼
stop_reason = "end_turn"
```

---

## Understanding intervention handlers

<details>
<summary><b>The five actions</b></summary>

Every lifecycle override returns one of five actions, all importable from `strands.interventions`:

| Action                | Effect                                                              | Valid on                                                                         |
|:----------------------|:--------------------------------------------------------------------|:---------------------------------------------------------------------------------|
| `Proceed()`           | Allow the step unchanged                                            | every hook                                                                       |
| `Deny(reason=...)`    | Block the step. The reason becomes the model's cancellation message | `before_invocation`, `before_model_call`, `before_tool_call`                     |
| `Guide(feedback=...)` | Inject feedback to steer the model                                  | `before_invocation`, `before_model_call`, `before_tool_call`, `after_model_call` |
| `Confirm(prompt=...)` | Request human approval before the step runs                         | `before_tool_call`                                                               |
| `Transform(apply=fn)` | Run `fn(event)` to mutate the event in place                        | every hook                                                                       |

Returning an action on a hook it is not valid for is not an error. The action has no effect and a
warning is logged.

`Guide` is the one action whose effect depends on where it is returned. On `before_model_call` the
feedback is appended as a user message and the model call goes ahead. On `after_model_call` the
model's response is discarded and the model retries with the feedback. On `before_invocation` and
`before_tool_call` the step is cancelled and the feedback becomes its cancellation message, so there
`Guide` steers by refusing rather than by letting the step run.

</details>

<details>
<summary><b>Declaring a handler</b></summary>

```python
from strands.interventions import Confirm, InterventionHandler, Proceed, Transform


class Governance(InterventionHandler):
    name = "governance"

    def before_tool_call(self, event: BeforeToolCallEvent, **kwargs) -> Proceed | Confirm:
        ...
```

A `name` attribute is required on the subclass, and it has to be unique across the handlers on one
agent.

Override the lifecycle methods at class level. The framework inspects the class to decide which
hooks to register, so assigning a function onto an instance is silently ignored and the handler
simply never fires:

```python
# Works
class Governance(InterventionHandler):
    name = "governance"
    def before_tool_call(self, event, **kwargs): ...

# Silently does nothing
handler = Governance()
handler.before_tool_call = my_function
```

Override only the hooks you need. Hooks you leave alone are not called at all.

</details>

<details>
<summary><b>Two ways to answer a `Confirm`</b></summary>

`Confirm` behaves differently depending on whether you supply `response`:

```text
Confirm(prompt=..., response=answer)  ──► scored inline, the loop never pauses
Confirm(prompt=...)                   ──► the loop stops, stop_reason = "interrupt",
                                          and you resume the agent with the answer later
```

This tutorial collects the answer with its own `input()` call and passes it as `response`, which
keeps the whole exchange in one terminal. Leaving `response` unset is what a web UI or a review
queue wants, because the decision can then be answered from somewhere other than this process. The
vended `HumanInTheLoop` handler in [`03-human-in-the-loop`](../03-human-in-the-loop/) is built on
that second mode.

</details>

<details>
<summary><b>How `Confirm` scores the answer</b></summary>

`Confirm` does not compare the answer itself. It passes the answer to its `evaluate` function, and
the default accepts `True`, `'y'`, or `'yes'`, case-insensitive and trimmed, rejecting everything
else. An empty line is therefore a rejection, so the gate fails closed. Pass your own callable as
`evaluate=` for a different policy.

</details>

<details>
<summary><b>Write the `prompt` for the model, not only for the person</b></summary>

This is the easiest part to get wrong. On a rejection the tool result carries the literal text
`CONFIRMATION_FAILED: <prompt>`, so `prompt` is something the model reads. A `prompt` phrased as a
question ("Run delete_customer?") arrives at the model as a question, and the model will relay that
question to the user instead of reporting the refusal.

Write it as a statement about the policy, and ask the person with your own `input()` string:

```python
return Confirm(
    prompt="A human reviewer declined this deletion. Do not retry it.",
    response=answer,
)
```

</details>

<details>
<summary><b>What `Transform` can and cannot do</b></summary>

`Transform(apply=fn)` calls `fn(event)` and ignores whatever `fn` returns, so `fn` has to mutate the
event rather than build a new one. Later handlers on the same event see the mutation.

Apart from `Proceed`, which does nothing by design, `Transform` is the only action valid on all five
hooks. That makes it the way to reach content on the `after_*` hooks, where blocking is no longer an
option.

</details>

<details>
<summary><b>Printing the conversation is yours to write</b></summary>

The SDK ships no conversation pretty-printer, which is why `main.py` carries its own `print_history`
helper. `agent.messages` is plain Python data, so `print(agent.messages)` and
`json.dumps(agent.messages, indent=4)` are both faithful, but they bury the content blocks under the
per-message `tracking_id` and `metadata` fields. Walking the blocks yourself also sidesteps the
`TypeError` that `json.dumps` raises on a history holding binary content blocks, such as an image or
a document.

</details>

---

## Choosing where to intervene

<details>
<summary><b>Which action fits a decision, how handlers compose, and when to go async</b></summary>

`Confirm` is the right action only when there is a decision left for a person to make. When the
answer is already known, a cheaper action fits better:

- **`Deny(reason=...)`** when a tool must never run and there is nothing to ask, for example when
  policy requires a change ticket first. The reason reaches the model as `DENIED: <reason>`, so
  write it as an instruction rather than as a log line.
- **`Guide(feedback=...)`** when you want the model corrected rather than stopped, for example
  steered toward a read-only tool. On `after_model_call` a `Guide` triggers a model retry and the
  framework imposes no retry cap, so a handler that guides there must count its own retries and
  escalate to `Deny`.
- **`before_invocation`** when the whole request should be rejected. It fires before any model call
  is made, so nothing is spent on the attempt.

Handlers compose. Pass several to `interventions=[...]` and they are evaluated in registration order
at each lifecycle event, so a later handler sees what an earlier one transformed. Put the cheap
local checks first and the expensive ones last.

Any lifecycle method may be declared `async def`, which is what you want when the decision depends
on an external authorization service rather than on a local rule:

```python
class RemoteAuth(InterventionHandler):
    name = "remote-auth"

    async def before_tool_call(self, event, **kwargs):
        if await is_allowed(event.tool_use):
            return Proceed()
        return Deny(reason="The authorization service refused this call. Do not retry it.")
```

</details>

---

## Gating behavior versus capping cost

<details>
<summary><b>When you want an invocation limit instead of a handler</b></summary>

Interventions decide **what** an agent may do. They do not decide **how much** of it the agent may
do. A handler that approves every tool call will still approve the hundredth one.

If the requirement is:

> This request may not spend more than ten turns.

that is an invocation-limit problem rather than an intervention problem. Limits are passed per call
and reported through `stop_reason` values such as `limit_turns`. See
[01-stop-a-runaway-agent](../../09-limits/01-stop-a-runaway-agent/).

The two compose cleanly: a handler gates the individual step, and a limit bounds the run containing
it.

</details>

---

## Additional resources

- [Interventions](https://strandsagents.com/docs/user-guide/concepts/agents/interventions/), the
  reference for handlers and actions.
- [Hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/), the lifecycle event
  system that interventions are layered on.
- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/)
