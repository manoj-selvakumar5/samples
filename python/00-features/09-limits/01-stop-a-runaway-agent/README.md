Part II - Control the loop

# Stop a runaway agent

Bound what one invocation may spend, so a run that will not end still returns.

Some tasks have no natural ending. The model keeps working because every tool result looks like
progress, and nothing in the loop ever tells it to give up. A budget is what ends those runs.

A cap belongs to one call rather than to the agent, so `limits` is passed at invocation time.
Nothing raises when a cap trips: the loop stops between iterations and names the cap in
`stop_reason`, leaving a conversation you can call again on a larger budget.

## Teaches

| Symbol | Where it comes from |
|--------|---------------------|
| `Limits` | `strands.types.Limits`, a `TypedDict`, so a plain dict works and this script passes one |
| `limits=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async` |
| `result.stop_reason` | names the cap that fired: `limit_turns`, `limit_total_tokens`, or `limit_output_tokens` |
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
| `total_tokens` | Input plus output tokens, as `usage["totalTokens"]` | `limit_total_tokens` |
| `output_tokens` | Model-generated tokens only | `limit_output_tokens` |

## What `stop_reason` tells you

**Reaching a limit is an outcome, not an exception.** Inspect `stop_reason` to decide what your
application does next.

| `stop_reason` | Meaning | What to do |
|---------------|---------|------------|
| `end_turn` | The model chose to finish | Use the text |
| `limit_turns` | The invocation's turn budget stopped the loop | Land or resume on a larger budget |
| `limit_total_tokens` | The invocation's token budget stopped the loop | Land or resume on a larger budget |
| `limit_output_tokens` | The cumulative generated-token budget stopped the loop | Land or resume on a larger budget |
| `cancelled` | The caller stopped it | Do not retry automatically |

There is no time dimension, which is the first thing most readers come here looking for. A
wall-clock bound is cancellation, not a limit, and it reports `cancelled` rather than a `limit_*`
value. See [`02-stop-it-from-outside`](../02-stop-it-from-outside/).

## Note the following

- **There is no cap unless you pass one.** An agent invoked without `limits` runs until the model
  decides it is finished. When the tools never signal an ending, nothing in the loop supplies one.
- **The runaway here is a pagination bug, not a bad prompt.** The tool reports a total computed from
  the offset, so the end of the article always stays ahead of the reader. Every response looks like
  ordinary progress. This matters because the usual advice, write a better prompt, does not help:
  there is no wording that makes an article with no last page have a last page.
- **A tripped limit is not an exception.** The invocation returns an `AgentResult` normally and the
  cap shows up in `stop_reason`, so code that assumes a returned result means a completed task will
  silently accept a truncated one.
- **After a cap trips, the result has no text.** `AgentResult.message` is the last message in the
  conversation, and on a trip that is the message holding the tool result, not an assistant reply,
  so `str(result)` is the empty string.
- **Reaching a limit leaves the conversation reinvokable.** Tools requested by the last turn have
  already completed, so the history never ends on an unanswered tool call and the same agent can be
  called again. The script's free tier uses this to spend one final turn summarizing what it found,
  which is what turns an empty result into a partial answer.
- **A one-turn landing call is not guaranteed to produce text.** A turn is a model call plus any
  tools it requests, and the cap is only checked before the *next* turn. If the model spends that
  turn on another tool call instead of answering, the run ends on a tool result again. Give the
  landing call its own tool-free agent if you need the partial answer to be certain.
- **The cap belongs to the call, not the agent.** Counters are not cumulative across reuses, so a
  second `agent(...)` starts from zero. That is what makes a tripped run resumable.
- **Caps are soft.** They are checked at the top of each loop iteration, never mid-call, so the
  iteration that crosses the line still finishes and the run lands past its cap. Treat a cap as a
  circuit breaker, not an accounting guarantee.
- **Read the per-invocation counters, not the lifetime ones.** The caps compare against
  `result.metrics.latest_agent_invocation.usage`, and `total_tokens` specifically against its
  `totalTokens` field. `metrics.accumulated_usage` on the same object is the agent's total across
  every call it has served, so on a reused agent it is not the number being enforced.
- **A turn is a trip through the loop, not a model call.** One turn is one model call plus any tools
  it requested, however many of those run in parallel. The script's tools are often called three at
  a time inside a single turn.
- **Priority on a simultaneous trip is `turns`, then `total_tokens`, then `output_tokens`.** When a
  budget sets more than one cap, `stop_reason` names whichever bound bit first in that order.
- **A malformed cap does raise, before any model call.** Zero, a negative, a float, a string, and
  `True` all raise `TypeError` during validation, so a bad cap costs nothing. Only a *tripped* cap
  is the quiet path.
- **Unknown keys are ignored silently.** `limits={"turn": 5}` is a typo, not an error, and the run
  is uncapped. Only the three documented fields are read.
- **Size the cap to what you will spend, not to what the task needs.** You rarely know a task's
  length in advance. Pick the number from the caller's allowance, let it trip, and raise it if the
  work was worth continuing.
- **A token cap is a proxy for spend, not a measure of it.** The same token count costs very
  different amounts on different models, so a budget tuned for one model is wrong for the next.
- **Branch on `stop_reason`, do not test it for equality with `end_turn`.** A `limit_*` value means
  resume or land on a larger budget. `cancelled` means the caller stopped it, so do not retry
  automatically. `guardrail_intervened` and `content_filtered` are terminal and should surface a
  refusal.

## Variations

- **Resume instead of landing** by calling the agent again with a larger budget and a short nudge.
  Tools requested by the previous turn always run to completion before a cap fires, so the
  conversation is never left with a dangling tool call and the history carries the context.
- **Derive the cap from the request** rather than the tier, using the caller's remaining quota.
  `limits` is a per-call argument rather than agent configuration, so nothing stops you.
- **Charge the landing call to the caller too**, or absorb it, but decide deliberately: it is a real
  invocation with its own cost.
- **Combine caps** when one boundary is not enough, for example
  `limits={"turns": 10, "total_tokens": 50_000, "output_tokens": 5_000}`. The script's tiers each set
  a single cap so that one example teaches one bound.
- **Pass `limits` to `stream_async`** as well. The same keyword exists on all three invoke paths.

## See also

- [`09-limits/02-stop-it-from-outside`](../02-stop-it-from-outside/) for bounding wall-clock time.
- [`07-interventions/01-intervention-basics`](../../07-interventions/01-intervention-basics/) for gating *what*
  the agent does rather than *how much*.

Verified against strands-agents 1.54.0 on 2026-09-11
