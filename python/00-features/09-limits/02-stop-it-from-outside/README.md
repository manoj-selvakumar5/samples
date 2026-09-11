Part II - Control the loop

# Stop it from outside

Cancel a run that is already going, and make the stop arrive when you meant it to.

`Limits` counts turns and tokens, never seconds, so a deadline, a client disconnect, or a Stop
button is cancellation rather than a limit. Two mechanisms do it and both report a `stop_reason` of
`cancelled`.

Neither is immediate. The loop stops at the next cancellation-safe point, and a tool already
executing runs to completion first. That last part is usually what makes a Stop button feel broken,
and it is fixable: a tool can be handed the same signal the loop is watching and give up on its own.

## Teaches

| Symbol | Where it comes from |
|--------|---------------------|
| `cancel_signal=` | keyword on `Agent.__call__`, `invoke_async`, and `stream_async`, taking a `threading.Event` |
| `Agent.cancel()` | method, thread-safe, cancels whichever invocation is in flight |
| `stop_reason == "cancelled"` | on the returned `AgentResult` |
| `ToolContext.cancel_signal` | `strands.ToolContext`, reached with `@tool(context=True)`, so a slow tool can give up |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

The script uses a deliberately slow tool so the timing is visible, and cancels two of the runs at
exactly the same point so their delays can be compared.

## Which one to use

| | Use when |
|---|---|
| `cancel_signal=` | You can create the `threading.Event` before the run starts, and hand it to a timer, a request lifecycle, or a disconnect handler |
| `agent.cancel()` | You hold the agent rather than a signal, such as in a web request handler or behind a Stop button |

## Note the following

- **Cancellation is checked at safe points, not preempted.** The loop looks for it while the model
  response streams, before tools execute, during an MCP tool call, and after tools execute before
  the next model call. Which one you hit depends on where the run happened to be, so the delay
  varies from run to run unless you control where the signal lands, as the script does.
- **A tool that ignores the signal sets your floor.** If cancellation arrives while tools are
  running, every one of them completes first, so the run cannot stop sooner than the slowest tool in
  flight. This is the single biggest reason a Stop button feels unresponsive.
- **A tool can cooperate instead.** `@tool(context=True)` places a `ToolContext` in the named
  parameter, and its `cancel_signal` is the same event the agent watches. Poll it between steps and
  return early, or forward it to an API that accepts one. The script runs the same cancellation
  against both kinds of tool and prints the two delays next to each other.
- **Cooperating changes the tool, not the loop.** Both runs stop at the same safe point and both
  report `cancelled`. The only thing that moves is how long the tool made the loop wait.
- **A cancelled run is not a broken one.** The conversation stays valid, so the same agent can be
  invoked again. The script cancels a run and then asks the agent an unrelated question, which
  answers normally.
- **A cancelled result may carry text.** Unlike a tripped cap, cancellation can land just after an
  assistant message, so `str(result)` is often non-empty. That text is still not an answer to the
  task.
- **`agent.cancel()` targets the invocation in flight**, so it does nothing useful if no run is in
  progress, and it is not a permanent setting. The agent clears its own signal when an invocation
  completes, which is what keeps it reusable.
- **A caller-owned `cancel_signal` stays set once fired.** The agent does not clear an event you
  passed in, so reuse it across invocations only after `Event.clear()`. The script clears it before
  each timed run.

## Variations

- **Cancel from a request handler** rather than a timer, which is the realistic case: a client
  disconnect, a closed websocket, or a user pressing Stop.
- **Forward the signal to your own client** if it accepts one, instead of polling. Any API that
  takes a cancellation token can be handed `tool_context.cancel_signal` directly.
- **Combine with `limits`** so a run is bounded on turns and tokens as well as time. Cancellation
  covers the dimension `Limits` has none for.
- **Poll on a coarser interval** than this script's, which steps every 0.1 seconds to make the
  difference visible. Match the interval to how quickly you actually need to give up.

## See also

- [`09-limits/01-stop-a-runaway-agent`](../01-stop-a-runaway-agent/) for bounding turns and tokens.

Verified against strands-agents 1.54.0 on 2026-09-11
