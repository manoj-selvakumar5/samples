# Cancel a running agent invocation from outside the loop

## Overview

Some reasons to stop an agent have nothing to do with how much work it has done. A request deadline
expires, a client closes its connection, a user presses Stop. The run may be behaving perfectly and
still need to end now.

In this tutorial, a billing support assistant reads a support ticket thread one message at a time
through a deliberately slow tool, so the moment a stop arrives and the moment the run actually
returns are far enough apart to watch. The script stops it three ways: with an event the caller
owns, fired while a fetch is in flight; with `agent.cancel()` from a timer thread; and then once
more at exactly the same point, against a tool that watches the signal instead of ignoring it.

Both mechanisms are external and scoped to one invocation. `cancel_signal` is a keyword on the
invocation, not constructor configuration, and `Agent.cancel()` is a method on the agent that
targets whichever invocation is in flight. They feed the same signal, and either produces an
`AgentResult` with a `stop_reason` of `cancelled`.

Neither is instant. The signal is read between units of work, so where a run stops depends on what
it was doing when the stop arrived.

---

## What you will learn

- how to cancel an invocation with a caller-owned `threading.Event` passed as `cancel_signal`
- how to cancel the invocation in flight with `Agent.cancel()` from another thread
- why a cancelled run does not stop immediately, and where it does stop
- how to let a slow tool give up early through `ToolContext.cancel_signal`

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

The script runs three scenarios.

### 1. A client disconnect

A `threading.Event` the caller creates before the run starts, then hands to the invocation:

```python
DISCONNECT = threading.Event()

result = support_agent(fetch_tool)(TASK, cancel_signal=DISCONNECT)
```

Anything can own that event: a request lifecycle, a websocket disconnect handler, a timer. Because
it exists before the invocation does, it is the mechanism that can express a deadline.

The script fires it from inside the fetch of message `DISCONNECT_DURING = 3`. That is both the
realistic case, since a client goes away mid-request rather than on a schedule, and the way the two
timed runs are pinned to the same cancellation point so their delays can be compared.

`fetch_message` sleeps for `FETCH_SECONDS = 1.5` and never looks at the signal, so this run cannot
return before that sleep finishes.

### 2. A Stop button

No signal is passed here. The agent itself is the handle, and `cancel()` is safe to call from any
thread:

```python
def fire() -> None:
    print("    [signal] cancel() called")
    agent.cancel()

timer = threading.Timer(5.0, fire)
```

Where this one lands is deliberately left to chance, so no delay is reported for it. It may arrive
mid-stream or mid-fetch; scenario 3 is the one that times the difference on purpose.

Afterwards the same agent is asked something unrelated:

```python
followup = agent("Never mind the thread. In one sentence, what is a chargeback?")
```

Cancelling did not invalidate the conversation, so that follow-up answers normally.

### 3. A tool that cooperates

The same disconnect, at the same fetch, against a tool that participates. `context=True` places a
`ToolContext` in the named parameter:

```python
@tool(context=True)
def fetch_message_promptly(number: int, tool_context: ToolContext) -> str:
```

Its `cancel_signal` is the same event the agent is watching, so the fetch can check between steps
and give up:

```python
for _ in range(int(FETCH_SECONDS / STEP_SECONDS)):
    if tool_context.cancel_signal.is_set():
        print(f"    [tool] fetch_message_promptly({number}) abandoned")
        return "Abandoned: the run was cancelled."
    time.sleep(STEP_SECONDS)
```

The total work is the same 1.5 seconds, split into `STEP_SECONDS = 0.1` slices. The script then
prints both delays next to each other.

<details>
<summary><b>Expected output</b></summary>

Output varies because model behavior and thread timing are not deterministic. An abbreviated run:

```text
=== A client disconnect ===

    [tool] fetch_message(1) started
    [tool] fetch_message(1) returned
    ...
    [tool] fetch_message(3) started
    [signal] client disconnected
    [tool] fetch_message(3) returned
  stop_reason : cancelled
  returned    : <n>s after the signal

=== A Stop button ===

    [tool] fetch_message(1) started
    ...
    [signal] cancel() called
  stop_reason : cancelled

  called again -> end_turn: <one-sentence answer>

=== A tool that cooperates ===

    [tool] fetch_message_promptly(1) started
    ...
    [tool] fetch_message_promptly(3) started
    [signal] client disconnected
    [tool] fetch_message_promptly(3) abandoned
  stop_reason : cancelled
  returned    : <n>s after the signal

  a tool that ignores the signal : <n>s after it
  a tool that polls the signal   : <n>s after it
  Same mechanism, same cancellation point. The loop behaved identically
  in both runs; the difference is entirely in whether the tool looked.
```

The two `returned` lines are the point of the exercise. In the first scenario the signal lands
inside a fetch that ignores it, so the run cannot end until that fetch returns. In the third the
fetch notices on its next step and abandons the work, and the same cancellation therefore comes back
much sooner.

**In this example**, the disconnect only fires if the model actually requests message 3. If it
answers from the first two, the signal never fires, the script prints `<stop_reason>, but the run
ended before the signal` instead of a delay, and the comparison lines are skipped.

</details>

---

## How cancellation reaches the agent loop

Both mechanisms set one signal, and the loop reads it at four fixed points:

```text
agent.cancel() ──┐
                 ├──► the invocation's cancellation signal
cancel_signal ───┘             │
                               │ read at four checkpoints, between units
                               │ of work rather than inside one
                               ▼
                      Start iteration
                            │
                            ▼
                      Call the model ──────► checkpoint 1, between stream chunks
                            │                       │
                            ▼                       │
                      Before tools start ──► checkpoint 2
                            │                       │
                            ▼                       │
                      Tools execute ───────► checkpoint 3, an MCP call in flight
                            │                       │
                            ▼                       │
                      Tools returned ──────► checkpoint 4, before the next model call
                            │                       │
                            │                       ▼
                            │              return AgentResult
                            │              with stop_reason "cancelled"
                            ▼
                      next iteration
```

The important detail is **where the signal is read**: between units of work, never inside one. The
loop is not preempted. It finishes whatever unit it is in, and then looks.

For an ordinary Python tool, that unit is the whole tool call. Once a tool has started, cancellation
is **cooperative**: only the tool itself can react mid-execution. A tool that never looks runs to
completion, and the loop resumes cancellation handling after it returns.

So the slowest tool in flight sets the floor on how quickly a run can stop, unless the tool
participates:

```text
signal fires
     │
     ├── tool that ignores it:  [ ---- 1.5s of work ---- ] returns ──► run stops
     │
     └── tool that polls it:    [ step ] gives up ──► run stops
```

Both paths stop at the same checkpoint and both report `cancelled`. The only thing that moves is how
long the tool made the loop wait, which is usually the whole reason a Stop button feels broken.

---

## Understanding cancellation

<details>
<summary><b>The two ways to cancel</b></summary>

`cancel_signal` takes a `threading.Event` the caller owns, and is available with `__call__`,
`invoke_async`, and `stream_async`.

`Agent.cancel()` takes nothing. It is thread-safe and idempotent, so calling it repeatedly or from
several threads is fine, and it aims at whichever invocation is currently running.

The agent watches both, so either one cancels independently of the other. There is no separate
"cancellable" mode to enable on the `Agent`.

</details>

<details>
<summary><b>Where the loop checks</b></summary>

| Checkpoint                                  | What happens there                                               |
|:--------------------------------------------|:-----------------------------------------------------------------|
| Between chunks of the model response stream | Partial output is discarded                                      |
| Before the turn's tools start               | Pending tool calls are skipped, each given an error result       |
| While an MCP tool call is in flight         | The MCP request is cancelled, without closing the shared session |
| After tools return                          | The loop stops instead of calling the model again                |

Which checkpoint a given run hits depends on where it happened to be, so the delay varies from run
to run unless you control where the signal lands, as the script does.

MCP is the one case where work already started can be cut short, and only locally: remote
cancellation is best effort, so the agent stops even if the server never acknowledges it.

The signal is also forwarded to the model provider so it can abort a request in flight rather than
letting the response run on. Support is provider-dependent. Amazon Bedrock closes a streaming
response at the next chunk boundary, but cannot abort a request that has not returned headers yet,
nor a non-streaming call. A provider that ignores the signal still stops at the between-chunks
checkpoint.

</details>

<details>
<summary><b>Letting a tool give up early</b></summary>

`@tool(context=True)` places a `ToolContext` in the named parameter, and
`tool_context.cancel_signal` is the same event the agent is watching. There are two ways to use it:

- poll `tool_context.cancel_signal.is_set()` between steps and return early, as scenario 3 does
- hand the event to any API that accepts a cancellation token, such as `MCPClient.call_tool_async`

Forwarding is the better option when it is available, because there is no polling interval to
choose.

An agent used as a tool through `as_tool()` receives the parent's signal automatically, so
cancelling the parent also cancels the delegated agent.

Cooperating changes the tool, not the loop. The checkpoints are the same, the `stop_reason` is the
same, and the only difference is how long the loop waited on the tool.

</details>

<details>
<summary><b>What a cancelled result carries</b></summary>

Cancellation is a normal outcome, not an exception. The call still returns an `AgentResult`:

```python
result = agent(TASK, cancel_signal=DISCONNECT)

if result.stop_reason == "cancelled":
    ...
```

Unlike a tripped budget cap, a cancelled result is usually not empty, and what it holds depends on
the checkpoint:

| Cancelled at         | `str(result)` is                                                        |
|:---------------------|:------------------------------------------------------------------------|
| the model stream     | the fixed text `Cancelled by user`                                      |
| after tools returned | that turn's assistant message, including any text beside its tool calls |

Neither is an answer to the task, so branch on `stop_reason` rather than on whether text came back.

Usage metrics can be inaccurate when the stop lands mid-stream, because the stream closes before the
model sends its final metadata event.

</details>

<details>
<summary><b>Why the agent stays reusable</b></summary>

A cancelled run is not a broken one. A tool is never interrupted halfway, and skipped tool calls
still receive error results, so the conversation history is left in a valid state. The same agent
can be invoked again, which is what scenario 2 does with its follow-up question.

The agent clears its own signal when an invocation completes, which is what keeps it reusable.

Because that is the only thing that clears it, aim matters. `cancel()` sets the signal whether or
not a run is in progress, so calling it on an idle agent leaves the signal set, and the next
invocation is then cancelled at its first checkpoint. Aim it at a run you know is in flight.

An event you own is treated differently: the agent never sets or clears it, so it stays set once
fired. Call `Event.clear()` before handing it to another invocation, as the script does before each
timed run.

Two smaller edges of the contract:

- The agent observes a caller-owned event by polling, with up to roughly 50 ms of latency that
  compounds per `as_tool()` nesting level. An event set and cleared inside one poll window is
  missed, so only clear it between invocations.
- An event that is already set when the invocation starts cancels it at the first checkpoint, which
  sits inside model streaming. The user turn is still recorded, and one model request may be issued
  and then aborted.

</details>

---

## Choosing a cancellation trigger

<details>
<summary><b>Which trigger fits, and how fast the run can actually give up</b></summary>

| Mechanism        | Use when                                                                               |
|:-----------------|:---------------------------------------------------------------------------------------|
| `cancel_signal=` | The event can exist before the run: a timer, a request lifecycle, a disconnect handler |
| `Agent.cancel()` | You hold the agent rather than a signal: a web request handler, a Stop button          |

A timer is the easiest trigger to demonstrate and the least likely one in production. The realistic
source is a request handler: a client disconnect, a closed websocket, a user pressing Stop. A
caller-owned event has one further advantage, which is that the same event can drive several agents.

Whichever fires it, the useful question is how quickly you need the run to actually give up, because
that is a property of your tools rather than of the loop. Any tool on the cancellation path that can
block for seconds should either poll the signal or forward it. The polling interval you pick is the
worst case you are accepting, and this script's `STEP_SECONDS = 0.1` is tuned to make the difference
visible rather than to be a recommendation.

</details>

---

## Cancellation versus limits

<details>
<summary><b>Why a budget cannot express a deadline, and how to use both at once</b></summary>

A budget is declared before the run and the loop enforces it alone. Cancellation always needs
something outside the run to decide when, so what it guarantees is who gets to stop the invocation,
not how much the invocation may spend.

It is also less precise in time than a budget is in work. A cap is compared at turn boundaries,
while a cancellation arrives at whatever checkpoint the run reaches next, delayed by whatever was in
flight.

The two compose, and both are invocation keywords, so one call can carry both:

```python
result = agent(
    TASK,
    limits={"turns": 10, "total_tokens": 50_000},
    cancel_signal=DISCONNECT,
)
```

For the budget side of this pair, see [01-stop-a-runaway-agent](../01-stop-a-runaway-agent/).

</details>

---

## Additional resources

- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/#cancellation),
  whose "Cancellation" section documents these checkpoints.
- [Custom Tools](https://strandsagents.com/docs/user-guide/concepts/tools/custom-tools/#toolcontext)
  for `ToolContext` and the `context=True` parameter.
