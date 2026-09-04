Part II - Control the loop

# Execution limits

Cap what a single invocation is allowed to spend.

A limit is a budget with a resumption story, not a kill switch. The cap belongs to one call rather
than to the agent, so `limits` is passed at invocation time. Nothing raises: the loop stops between
iterations and reports the cap it tripped in `stop_reason`, leaving a conversation you can call
again on a larger budget.

This leaf reviews a contract twice. The first run searches an index that never comes back, under a
policy that says to retry transient failures, so nothing in the loop will ever end it. The second
run reads the contract page by page, runs out of budget partway, and finishes on a second call.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `Limits` | `strands.types.Limits` |
| `limits=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async` |
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

## Note the following

- **There is no cap unless you pass one.** An agent invoked without `limits` runs until the model
  decides it is finished. That is fine for a task with a natural stopping point and unbounded for
  one without, which is what the first run in this script demonstrates.
- **A cap is a backstop, not a stopping mechanism.** It should fire on the run where the intended
  ending failed to arrive, not on the ordinary one. A budget that trips on a healthy run is too
  small, not well enforced.
- **`limits` goes on the invocation, not the constructor.** The budget belongs to one call. Counters
  are not cumulative across reuses of the same agent, so a second `agent(...)` starts from zero.
  That is what makes the resume in this script work.
- **A tripped limit is not an exception.** The invocation returns an `AgentResult` normally and the
  cap shows up in `stop_reason`. Code that assumes a returned result means a completed task will
  silently accept a truncated one, so check `stop_reason`.
- **After a trip, the result has no text.** `AgentResult.message` is the last message in the
  conversation, and on a trip that is the `user` message holding the tool result, not an assistant
  reply. `str(result)` is therefore the empty string. The work done so far is in `agent.messages`.
- **`structured_output` is `None` after a trip**, even with `structured_output_model` set. Check
  `stop_reason` before trusting it. `Agent.structured_output()` takes no `limits` argument at all;
  the supported route is `agent(..., structured_output_model=Out, limits={...})`.
- **Read the per-invocation counters, not the lifetime ones.** The caps compare against
  `result.metrics.latest_agent_invocation.usage`. `result.metrics.accumulated_usage` is the agent's
  total across every call it has ever served, so on a reused agent it is a larger number than the
  one being enforced.
- **A turn is a trip through the loop, not a model call.** One turn is one model call plus any tools
  it requested, however many of those run in parallel. Some turns skip the model entirely, such as
  an interrupt being replayed, and still count.
- **Caps are soft, and can be overshot.** They are checked at the top of each loop iteration, so a
  cap fires on the iteration *after* the one that crossed it. Treat the number as a circuit breaker,
  not an accounting guarantee.
- **`agent.messages` stays reinvokable.** Tools requested by the previous turn run to completion
  before a cap fires, so the conversation is never left with a dangling tool call.
- **Priority on a simultaneous trip is `turns`, then `total_tokens`, then `output_tokens`.**
- **Unknown keys are ignored silently.** `limits={"turn": 5}` is a typo, not an error, and applies
  no cap whatsoever. Only `turns`, `total_tokens`, and `output_tokens` are read.
- **Every cap must be a positive `int`.** Zero, a negative, a float, a string, and `True` all raise
  `TypeError` before any model call is made.
- **A token cap is a proxy for spend, not a measure of it.** The same token count costs very
  different amounts on different models, so a budget tuned for one model is wrong for the next.

## Variations

- **Cap output only** with `{"output_tokens": 500}`, when input size is fixed but you want to stop a
  model that has started rambling.
- **Derive the cap per request** from the caller's tier or remaining quota, since it is a per-call
  argument rather than agent configuration.
- **Land gracefully instead of returning empty.** After a trip, call the agent again with a small
  budget and a prompt asking it to summarize what it has so far. The caller gets a partial answer
  rather than nothing, which is usually what a product needs.
- **Cap a wall clock** with `Agent.cancel()` and the `cancel_signal` argument. `Limits` has no time
  dimension, and cancellation reports `stop_reason` of `cancelled`.
- **Pass `limits` to `stream_async`** as well. The same keyword exists on all three invoke paths.

## See also

- [`09-limits/02-stop-reasons`](../02-stop-reasons/) for the full set of twelve ways a run can end.
- [`07-interventions/01-intervention-basics`](../../07-interventions/01-intervention-basics/) for gating *what*
  the agent does rather than *how much*.

Verified against strands-agents 1.54.0 on 2026-09-04
