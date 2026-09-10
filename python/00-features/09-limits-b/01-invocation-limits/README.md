Part II - Control the loop

# Invocation limits

Cap what a single invocation may spend.

`limits` takes three optional caps, is passed to the invocation rather than the constructor, and
never raises. The loop stops between iterations and names the cap it tripped in `stop_reason`.

## Teaches

| Symbol | Where it comes from |
|--------|---------------------|
| `Limits` | `strands.types.Limits`, a `TypedDict`, so a plain dict works and this script passes one |
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

Every field is optional, and an omitted field means no limit on that dimension.

| Field | Bounds | Trips with `stop_reason` |
|-------|--------|--------------------------|
| `turns` | Trips through the agent loop | `limit_turns` |
| `total_tokens` | Input plus output tokens | `limit_total_tokens` |
| `output_tokens` | Output tokens only | `limit_output_tokens` |

There is no time dimension. Bounding wall-clock time is cancellation, not a limit. See
[`02-cancellation`](../02-cancellation/).

## Note the following

- **The cap belongs to the call, not the agent.** Counters are not cumulative across reuses, so a
  second `agent(...)` starts from zero. That is what makes a tripped run resumable on a larger
  budget.
- **A tripped limit is not an exception.** The invocation returns an `AgentResult` normally and the
  cap shows up in `stop_reason`, so code that assumes a returned result means a completed task will
  silently accept a truncated one.
- **Caps are soft.** They are checked at the top of each loop iteration, never mid-call, so the
  iteration that crosses the line still finishes. The script asks for at most 1500 total tokens and
  lands near 2000. Treat a cap as a circuit breaker, not an accounting guarantee.
- **Priority on a simultaneous trip is `turns`, then `total_tokens`, then `output_tokens`.** The
  script sets all three to 1 and gets `limit_turns`.
- **Every cap must be a positive `int`.** Zero, a negative, a float, a string, and `True` all raise
  `TypeError`, before any model call is made, so a bad cap costs nothing.
- **Unknown keys are ignored silently.** `limits={"turn": 1}` is a typo, not an error, and the run
  is uncapped. Only the three documented fields are read.
- **Read the per-invocation counters, not the lifetime ones.** The caps compare against
  `result.metrics.latest_agent_invocation.usage`. `metrics.accumulated_usage` on the same object is
  the agent's total across every call it has served, so on a reused agent it is a larger number than
  the one being enforced.
- **A turn is a trip through the loop, not a model call.** One turn is one model call plus any tools
  it requested, however many of those run in parallel.
- **A token cap is a proxy for spend, not a measure of it.** The same token count costs very
  different amounts on different models, so a budget tuned for one model is wrong for the next.

## Variations

- **Derive the cap per request** from the caller's tier or remaining quota, since it is a per-call
  argument rather than agent configuration.
- **Resume on a larger budget** when `stop_reason` is a `limit_*` value. Tools requested by the
  previous turn always run to completion before a cap fires, so the conversation is never left with
  a dangling tool call and the same agent can be called again.
- **Pass `limits` to `stream_async`** as well. The same keyword exists on all three invoke paths.

## See also

- [`09-limits-b/02-cancellation`](../02-cancellation/) for bounding wall-clock time.

Verified against strands-agents 1.54.0 on 2026-09-09
