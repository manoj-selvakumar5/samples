Part II - Control the loop

# Stop runaway agent executions with invocation limits

## Overview

Agents can keep working as long as each turn gives the model a reason to continue. Usually the loop
ends naturally when the model has enough information to answer. But some tasks do not have a
reliable stopping point.

In this tutorial, a billing support agent encounters a pagination bug. Every call to `read_article`
returns another chunk and claims that more content remains. From the model's perspective the run is
progressing normally, so it keeps requesting the next chunk.

Invocation limits give that run an external stopping condition.

`limits` is passed when the agent is invoked, not when the `Agent` is constructed. The budget
therefore applies to one call. Reusing the same agent starts the next invocation with fresh
counters.

---

## What you will learn

- how to bound the turns and tokens a single agent invocation may use
- how to detect that a budget stopped the run, using `stop_reason`
- why token limits are soft rather than exact
- how to continue from the valid conversation a limit leaves behind

---

## How the agent loop applies a limit

A simplified agent-loop iteration looks like this:

```text
Start iteration
      │
      ▼
Check invocation limits
      │
      ├── limit reached ──► return AgentResult
      │                     with limit_* stop_reason
      │
      ▼
Call the model
      │
      ▼
Execute any tools requested
      │
      ▼
Update invocation metrics
      │
      └──────────────► next iteration
```

The important detail is **where the check happens**: at the beginning of the next loop iteration.

That makes invocation token limits **soft limits**.

Suppose the total-token limit is 4,000:

```text
Before turn 5:  3,700 tokens
                     │
                     │ under budget
                     ▼
                  turn 5 runs
                     │
                     ▼
                 4,350 tokens
                     │
                     ▼
             next iteration begins
                     │
                     ▼
              limit is detected
                     │
                     ▼
                    stop
```

The final turn is allowed to finish even though it takes the invocation beyond 4,000 tokens.

Treat an invocation limit as a **circuit breaker**, not an exact accounting boundary.

---

## Prerequisites and setup

Before starting, make sure you have:

- Python 3.10 or later
- AWS credentials configured
- access to a supported model in Amazon Bedrock

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the tutorial

```bash
python main.py
```

The script runs two scenarios.

### 1. Stop a loop with no reliable natural ending

The agent is instructed to read a knowledge base article to the end. The tool contains a pagination
bug: every response says that more of the article remains.

The agent therefore has no reliable signal that it should stop.

A total-token limit provides that signal:

```python
RUNAWAY_BUDGET = 4000

result = agent(
    READ_TASK,
    limits={"total_tokens": RUNAWAY_BUDGET},
)
```

When the budget is reached, Strands stops the loop and returns an `AgentResult` with:

```text
stop_reason = "limit_total_tokens"
```

### 2. Give different callers different budgets

The second scenario runs the same support task with different turn budgets:

```python
TIERS = {
    "free": {"turns": 3},
    "pro": {"turns": 10},
}
```

The task and tools do not change. Only the budget assigned to the caller changes.

A smaller budget may stop before the search is complete. A larger budget gives the agent more
opportunities to continue searching.

### Expected output

Output varies because model behavior and token usage are not deterministic. An abbreviated run:

```text
=== A loop with no natural ending ===

    [tool] read_article('KB-207', offset=0)
    [tool] read_article('KB-207', offset=80)
    ...
  stop_reason : limit_total_tokens
  spent       : <turns> turns, <tokens> tokens
  text        : ''

  It overshot the 4000 cap by <n> tokens: caps are checked
  between turns, so the turn that crossed the line still ran.
  The agent stopped because the budget ran out, not because the
  document ended. No wording of the prompt supplies that ending.

=== The same question on two callers' budgets ===

  free tier, limits={'turns': 3}
    [tool] search_kb('duplicate charge', page 1)
    ...
  out of budget, asking for what it has so far
  stopped_by  : limit_turns
  partial     : ...
```

**In this example**, `text` is empty because the limit is detected after a tool-producing turn, so
the last message is a tool result rather than a final assistant answer. The work collected so far
remains in the conversation history, which the follow-up invocation can use.

---

## Understanding invocation limits

### Available limits

Pass `limits` when invoking the agent:

```python
result = agent(
    question,
    limits={
        "turns": 10,
        "total_tokens": 20_000,
        "output_tokens": 2_000,
    },
)
```

All three fields are optional.

| Limit           | What it bounds                                      | Stop reason           |
|:----------------|:----------------------------------------------------|:----------------------|
| `turns`         | Agent-loop iterations                               | `limit_turns`         |
| `total_tokens`  | Cumulative input + output tokens for the invocation | `limit_total_tokens`  |
| `output_tokens` | Cumulative model-generated tokens                   | `limit_output_tokens` |

Omitting a field means that dimension is not limited. Each cap you do set must be a positive
integer.

The same `limits` parameter is available with `__call__`, `invoke_async`, and `stream_async`.

### What counts as a turn?

One turn consists of:

```text
one model call
      +
any tool execution requested by that model call
```

For example, if one model response requests three tools in parallel, those tool calls are still part
of the same turn.

A turn limit therefore bounds how many times the agent can cycle through a model call and any tools
that follow.

### Token limits are cumulative

`total_tokens` applies across the entire invocation, not to a single model call.

For example:

```text
Model call 1       900 tokens
Model call 2     1,200 tokens
Model call 3     1,500 tokens
                 ------------
Invocation total 3,600 tokens
```

Each later model call also sees conversation history from earlier turns, so token consumption can
grow quickly during long-running agent loops.

`output_tokens` works similarly, but counts only tokens generated by the model.

These limits are different from a model provider's per-response token limit. Invocation limits bound
the cumulative work performed by the agent loop.

### What happens when a limit is reached?

Reaching an invocation limit is a normal outcome, not an exception.

The call still returns an `AgentResult`:

```python
result = agent(
    question,
    limits={"turns": 3},
)

print(result.stop_reason)
```

If the turn budget was exhausted:

```text
limit_turns
```

Your application should not assume that receiving an `AgentResult` means the task completed.

Inspect `stop_reason`:

```python
if result.stop_reason == "end_turn":
    # The model completed normally.
    ...
elif result.stop_reason.startswith("limit_"):
    # The invocation exhausted one of its budgets.
    ...
```

Relevant `stop_reason` values include:

| `stop_reason`                                              | Meaning                                 |
|:-----------------------------------------------------------|:----------------------------------------|
| `end_turn`                                                 | The model finished normally             |
| `limit_turns`, `limit_total_tokens`, `limit_output_tokens` | The matching budget was reached         |
| `cancelled`                                                | The invocation was cancelled externally |

### Why the conversation can continue

When an invocation limit fires, Strands does not interrupt a tool halfway through execution.

Tools requested during the current turn finish before the next limit check. As a result, the
conversation history is left in a valid state.

That means the same agent can be invoked again:

```python
result = agent(
    question,
    limits={"turns": 3},
)

if result.stop_reason == "limit_turns":
    continuation = agent(
        "Stop searching. Answer from what you have found so far.",
        limits={
            "turns": 1,
            "output_tokens": 400,
        },
    )
```

The second invocation gets a fresh budget but retains the conversation accumulated by the agent.

This creates two useful recovery strategies:

```text
Budget exhausted
       │
       ├── continue the work with a larger budget
       │
       └── stop gathering information and summarize
           what has already been found
```

The tutorial uses the second approach for any tier whose budget runs out, which in practice is
usually the smaller one.

One subtlety remains: the agent still has access to its tools during that follow-up invocation. If
it chooses to search again instead of answering, the follow-up can also exhaust its budget. If
producing a partial answer is mandatory, use a recovery path that cannot invoke additional tools.

### Inspect invocation usage

The counters the caps compare against are on the result:

```python
invocation = result.metrics.latest_agent_invocation

len(invocation.cycles)            # turns used
invocation.usage["totalTokens"]   # input plus output tokens
invocation.usage["outputTokens"]  # model-generated tokens only
```

These are per-invocation counters, unlike `metrics.accumulated_usage`, which totals every call the
agent has served.

---

## Choosing a budget

There is no universal correct limit.

Choose execution limits based on how much work the caller or application is prepared to spend. The
tier budgets in scenario 2 are that idea in full: both callers submit the same task, and the only
difference is how much iterative work each invocation may perform.

In production, useful limits usually reflect:

- cost budgets
- request service-level objectives
- caller entitlements
- expected task complexity
- protection from unexpected agent or tool behavior

A token limit is useful for controlling model consumption, but tokens are only a proxy for monetary
cost because pricing varies by model.

Turn and token limits can also complement each other:

```python
limits={
    "turns": 10,
    "total_tokens": 50_000,
    "output_tokens": 5_000,
}
```

Neither runaway reasoning cycles nor unexpected token growth can then carry an invocation on
indefinitely.

Monitor how often normal invocations reach their limits. If a budget routinely stops legitimate
work, consider increasing it.

---

## Limits versus cancellation

Invocation limits bound work, not time. They do not provide a wall-clock timeout.

If the requirement is:

> Stop this request after 30 seconds.

that is a cancellation problem rather than an invocation-limit problem.

A cancelled invocation reports:

```text
stop_reason = "cancelled"
```

Use invocation limits for budget boundaries and cancellation for external conditions such as
timeouts, client disconnects, or user-requested stops. See
[02-stop-it-from-outside](../02-stop-it-from-outside/).

---

## Additional resources

- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/), whose
  "Invocation Limits" section documents these semantics.
- [Operating Agents in Production](https://strandsagents.com/docs/user-guide/deploy/operating-agents-in-production/)
