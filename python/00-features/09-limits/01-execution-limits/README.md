Part II - Control the loop

# Execution limits

Cap what a single invocation is allowed to spend.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `Limits` | `strands.types.Limits` |
| `limits=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async` |

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
--- limits=None ---

Tool #1: next_number
    [tool] next_number(1) -> 2

Tool #2: next_number
    [tool] next_number(2) -> 3

Tool #3: next_number
    [tool] next_number(3) -> 4

Tool #4: next_number
    [tool] next_number(4) -> 5

Tool #5: next_number
    [tool] next_number(5) -> 6
The final number is 6.  stop_reason  : end_turn
  tokens       : 4865 in, 276 out

--- limits={'turns': 3} ---

Tool #1: next_number
    [tool] next_number(1) -> 2

Tool #2: next_number
    [tool] next_number(2) -> 3

Tool #3: next_number
    [tool] next_number(3) -> 4
  stop_reason  : limit_turns
  tokens       : 2135 in, 160 out

--- limits={'total_tokens': 2000} ---

Tool #1: next_number
    [tool] next_number(1) -> 2

Tool #2: next_number
    [tool] next_number(2) -> 3

Tool #3: next_number
    [tool] next_number(3) -> 4
  stop_reason  : limit_total_tokens
  tokens       : 2135 in, 160 out

--- limits={'turns': 2, 'total_tokens': 5000} ---

Tool #1: next_number
    [tool] next_number(1) -> 2

Tool #2: next_number
    [tool] next_number(2) -> 3
  stop_reason  : limit_turns
  tokens       : 1357 in, 107 out
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

- **`limits` goes on the invocation, not the constructor.** The budget belongs to one call. Counters
  are not cumulative across reuses of the same agent, so a second `agent(...)` starts from zero.
- **Caps are soft, and can be overshot.** They are checked at the top of each loop iteration, so a
  cap fires on the iteration *after* the one that crossed it. In the output above,
  `total_tokens: 2000` finished at 2135 input plus 160 output, which is 2295. Treat the number as a
  circuit breaker, not an accounting guarantee.
- **A tripped limit is not an exception.** The invocation returns an `AgentResult` normally and the
  cap shows up in `stop_reason`. Code that assumes a returned result means a completed task will
  silently accept a truncated one, so check `stop_reason`.
- **`agent.messages` stays reinvokable.** Tools requested by the previous turn run to completion
  before a cap fires, so the conversation is never left with a dangling tool call. You can raise
  the limit and call the agent again to continue.
- **Priority on a simultaneous trip is `turns`, then `total_tokens`, then `output_tokens`.** The
  last run above sets both `turns` and `total_tokens`, and reports `limit_turns`.
- **Every cap must be a positive `int`.**

## Variations

- **Cap output only** with `{"output_tokens": 500}`, when input size is fixed but you want to stop a
  model that has started rambling.
- **Derive the cap per request** from the caller's tier or remaining quota, since it is a per-call
  argument rather than agent configuration.
- **Retry with a larger budget** when `stop_reason` is a `limit_*` value, because the conversation
  is still in a valid state to reinvoke.
- **Pass `limits` to `stream_async`** as well. The same keyword exists on all three invoke paths.

## See also

- [`09-limits/02-stop-reasons`](../02-stop-reasons/) for the full set of twelve ways a run can end.
- [`07-interventions/01-intervention-basics`](../../07-interventions/01-intervention-basics/) for gating *what*
  the agent does rather than *how much*.

Verified against strands-agents 1.53.0 on 2026-08-26
