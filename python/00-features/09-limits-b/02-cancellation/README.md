Part II - Control the loop

# Cancellation

Stop an invocation from outside it.

`Limits` counts turns and tokens, never seconds, so a deadline or a Stop button is cancellation
rather than a limit. Two mechanisms do it, both report `stop_reason` of `cancelled`, and neither
takes effect immediately.

## Teaches

| Symbol | Where it comes from |
|--------|---------------------|
| `cancel_signal=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async`, taking a `threading.Event` |
| `Agent.cancel()` | method, thread-safe, cancels whichever invocation is in flight |
| `stop_reason == "cancelled"` | on the returned `AgentResult` |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

The script uses a deliberately slow tool so the timing is visible.

## Which one to use

| | Use when |
|---|---|
| `cancel_signal=` | You can create the `threading.Event` before the run starts, and hand it to a timer, a request lifecycle, or a disconnect handler |
| `agent.cancel()` | You hold the agent rather than a signal, such as in a web request handler or behind a Stop button |

## Note the following

- **Cancellation is checked at safe points, not preempted.** The loop looks for it while the model
  response streams, before tools execute, during an MCP tool call, and after tools execute before
  the next model call. Which one you hit depends on where the run happened to be, which is why the
  two runs in the script return after different delays.
- **Tools already executing always finish.** If the signal lands while tools are running, every one
  of them completes first. In the script's output five `returned` lines print after the signal. A
  run holding a slow tool takes at least that long to stop, so a hard deadline needs tool timeouts
  of its own.
- **A cancelled run is not a broken one.** The conversation stays valid, so the same agent can be
  invoked again. The script cancels a run and then asks the agent an unrelated question, which
  answers normally.
- **A cancelled result may carry text.** Unlike a tripped cap, cancellation can land just after an
  assistant message, so `str(result)` is often non-empty. That text is still not an answer to the
  task.
- **`agent.cancel()` targets the invocation in flight**, so it does nothing useful if no run is in
  progress, and it is not a permanent setting. A `cancel_signal` is the opposite: it exists before
  the run and stays set once fired, so reuse it only if that is what you want.

## Variations

- **Combine with `limits`** so a run is bounded on turns and tokens as well as time. Cancellation
  covers the dimension `Limits` has none for.
- **Reset the event** with `Event.clear()` if you intend to reuse it across invocations.
- **Cancel from a request handler** rather than a timer, which is the realistic case: a client
  disconnect or a user pressing Stop.

## See also

- [`09-limits-b/01-invocation-limits`](../01-invocation-limits/) for bounding turns and tokens.

Verified against strands-agents 1.54.0 on 2026-09-09
