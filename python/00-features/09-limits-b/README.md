Part II - Control the loop

# Limits (variant B)

**How far execution may continue.**

Bound a single invocation by turns and token usage, or cancel it externally. When a limit is
reached, the loop stops with an explicit reason.

> This is an experimental second cut of [`09-limits/`](../09-limits/), organized by SDK feature
> rather than by the reader's problem. One of the two will be kept.

Limits is one of four independent control surfaces. The others govern where execution happens
(sandbox), what actions may proceed (interventions), and what content may pass (guardrails). This
one governs extent.

## Leaves

| Leaf | Teaches |
|------|---------|
| [`01-invocation-limits`](./01-invocation-limits/) | The `Limits` caps on turns and tokens |
| [`02-cancellation`](./02-cancellation/) | `cancel_signal` and `Agent.cancel()`, the wall-clock bound |

## What belongs here

The scope test is the ring this surface draws: **per invocation**. If it does not bound how far one
invocation goes, it is not in this area.

## What does not belong here

| Not here | Why | Where instead |
|----------|-----|---------------|
| Bedrock Guardrails | A peer control surface governing what content may pass | Its own area |
| Retry strategy | Bounds a single model call, not the invocation around it | `models/` or `agent/`, undecided |
| Concurrent invocation | Governs how many runs happen at once | `01-agent/` |
| The `StopReason` survey | `stop_reason` reports how a run ended; it governs nothing | Each area teaches the endings it produces |
| `MaxTokensReachedException` | The provider's output ceiling is model configuration | A model-config leaf |

Verified against strands-agents 1.54.0 on 2026-09-09
