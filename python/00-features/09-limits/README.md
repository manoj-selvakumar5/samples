Part II - Control the loop

# Limits

**How far execution may continue.**

Bound a single invocation by turns and token usage, or cancel it externally. When a limit is
reached, the loop stops with an explicit reason.

Limits is one of four independent control surfaces. The others govern where execution happens
(sandbox), what actions may proceed (interventions), and what content may pass (guardrails). This
one governs extent.

## Leaves

| Leaf | Answers |
|------|---------|
| [`01-stop-a-runaway-agent`](./01-stop-a-runaway-agent/) | My agent might not stop, or might cost more than I budgeted |

## What belongs here

The scope test is the ring this surface draws: **per invocation**. If it does not bound how far one
invocation goes, it is not in this area.

## What does not belong here

Recorded so the boundary holds, since several of these were once planned as leaves.

| Not here | Why | Where instead |
|----------|-----|---------------|
| Bedrock Guardrails | A peer control surface governing what content may pass, not how far a run goes | Its own area |
| Retry strategy | Bounds a single model call, not the invocation around it | `models/` or `agent/`, undecided |
| Concurrent invocation | Governs how many runs happen at once, not how far one goes | `01-agent/` |
| The `StopReason` survey | `stop_reason` reports how a run ended; it governs nothing. Only four of its twelve values come from limits | Each area teaches the endings it produces; the "check the field" lesson lives in [`01-agent/01-first-agent`](../01-agent/01-first-agent/) |
| `MaxTokensReachedException` | The provider's output ceiling is model configuration | A model-config leaf |

Verified against strands-agents 1.54.0 on 2026-09-09
