Part II - Control the loop

# Stop a runaway agent

Bound what one invocation may spend, and stop it from outside when it will not stop itself.

Some tasks have no natural ending. The model keeps working because every tool result looks like
progress, and nothing in the loop ever tells it to give up. A budget is what ends those runs.

A cap belongs to one call rather than to the agent, so `limits` is passed at invocation time.
Nothing raises: the loop stops between iterations and reports the cap it tripped in `stop_reason`,
leaving a conversation you can call again on a larger budget.

## Teaches

| Symbol | Where it comes from |
|--------|---------------------|
| `Limits` | `strands.types.Limits`, a `TypedDict`, so a plain dict works and this script passes one |
| `limits=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async` |
| `cancel_signal=` | keyword on the same three paths, taking a `threading.Event` you own |
| `Agent.cancel()` | method, thread-safe, cancels whichever invocation is in flight |
| `result.metrics.latest_agent_invocation` | the per-call counters the caps compare against |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

## The three caps

`Limits` is a `TypedDict`, so a plain dict works. Every field is optional, and an omitted field
means no limit on that dimension.

| Field | Bounds | Trips with `stop_reason` |
|-------|--------|--------------------------|
| `turns` | Trips through the agent loop | `limit_turns` |
| `total_tokens` | Input plus output tokens | `limit_total_tokens` |
| `output_tokens` | Output tokens only | `limit_output_tokens` |

There is no time dimension, which is the first thing most readers come here looking for. A
wall-clock bound is cancellation, not a limit, and it reports `cancelled` rather than a `limit_*`
value.

## Two ways to cancel

| | Use when |
|---|---|
| `cancel_signal=` | You can create the `threading.Event` before the run starts, and hand it to a timer, a request lifecycle, or a disconnect handler |
| `agent.cancel()` | You hold the agent rather than a signal, such as in a web request handler or behind a Stop button |

**Neither is immediate.** The loop stops at the next cancellation-safe point, so a tool already
executing runs to completion first. In the script's output the tool's `returned` line appears after
the signal fired. Anything with a long-running tool should expect cancellation to take as long as
that tool does.

## Note the following

- **There is no cap unless you pass one.** An agent invoked without `limits` runs until the model
  decides it is finished, which for an unfinishable task is never.
- **The runaway here is a pagination bug, not a bad prompt.** The tool reports a total computed
  from the offset, so the end of the document always stays ahead of the reader. Every response
  looks like ordinary progress. This matters because the usual advice, write a better prompt, does
  not help: there is no wording that makes a never-ending document end.
- **A cap is a backstop, not a stopping mechanism.** It should fire on the run where the intended
  ending failed to arrive, not on the ordinary one. A budget that trips on a healthy run is too
  small, not well enforced.
- **Size the cap to what you will spend, not to what the task needs.** You rarely know a task's
  length in advance, which is the point of the third run in the script. Pick the number from the
  caller's allowance, let it trip, and raise it if the work was worth continuing.
- **A tripped limit is not an exception.** The invocation returns an `AgentResult` normally and the
  cap shows up in `stop_reason`. Code that assumes a returned result means a completed task will
  silently accept a truncated one.
- **After a cap trips, the result has no text.** `AgentResult.message` is the last message in the
  conversation, and on a trip that is the `user` message holding the tool result, not an assistant
  reply, so `str(result)` is the empty string. The work done so far is in `agent.messages`.
  Cancellation differs: it can land just after an assistant message, so a cancelled run often does
  carry text, and that text is still not an answer.
- **Branch on `stop_reason`, do not test it for equality with `end_turn`.** Only `end_turn` and
  `stop_sequence` mean the text is usable. A `limit_*` value means resume on a larger budget, which
  is what the third run in the script does. `cancelled` means the caller stopped it, so do not retry
  automatically. `guardrail_intervened` and `content_filtered` are terminal and should surface a
  refusal.
- **Nothing resumes on its own.** The conversation stays valid, but continuing is another ordinary
  call with a prompt. The history carries the context, so a short nudge is enough.
- **`agent.messages` stays reinvokable.** Tools requested by the previous turn run to completion
  before a cap fires, so the conversation is never left with a dangling tool call.
- **Read the per-invocation counters, not the lifetime ones.** The caps compare against
  `result.metrics.latest_agent_invocation.usage`. `result.metrics.accumulated_usage` is the agent's
  total across every call it has ever served.
- **A turn is a trip through the loop, not a model call.** One turn is one model call plus any tools
  it requested, however many of those run in parallel.
- **Caps are soft, and can be overshot.** They are checked at the top of each loop iteration, so a
  cap fires on the iteration *after* the one that crossed it.
- **Priority on a simultaneous trip is `turns`, then `total_tokens`, then `output_tokens`.**
- **Unknown keys are ignored silently.** `limits={"turn": 5}` is a typo, not an error, and applies
  no cap whatsoever.
- **Every cap must be a positive `int`.** Zero, a negative, a float, a string, and `True` all raise
  `TypeError` before any model call is made.
- **A token cap is a proxy for spend, not a measure of it.** The same token count costs very
  different amounts on different models, so a budget tuned for one model is wrong for the next.

## Variations

- **Derive the cap per request** from the caller's tier or remaining quota, since it is a per-call
  argument rather than agent configuration.
- **Cancel from a request handler** with `agent.cancel()`, which is thread-safe, when the signal
  comes from your own code rather than a timer.
- **Land gracefully instead of returning empty.** After a trip, call the agent again with a small
  budget and a prompt asking it to summarize what it has. The caller gets a partial answer rather
  than nothing.
- **Pass `limits` to `stream_async`** as well. The same keyword exists on all three invoke paths.

## See also

- [`07-interventions/01-intervention-basics`](../../07-interventions/01-intervention-basics/) for gating *what*
  the agent does rather than *how much*.

Verified against strands-agents 1.54.0 on 2026-09-09
