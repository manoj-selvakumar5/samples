Part II - Control the loop

# Human in the loop

Pause the agent for human approval before a sensitive tool runs.

`HumanInTheLoop` is a vended intervention handler. By default it does not prompt anyone. It stops
the run at the tool call and hands the decision back to you, so the approval can come from a
terminal, a web UI, or a review queue. You resume by calling the agent again.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `HumanInTheLoop` | `strands.vended_interventions.HumanInTheLoop` |
| `allowed_tools` | keyword on `HumanInTheLoop` |
| `stop_reason == "interrupt"` | on the result of `agent(...)` |
| `result.interrupts` | list of `strands.interrupt.Interrupt` |
| `interruptResponse` | content block you resume the agent with |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock
- An interactive terminal. That is this script's choice, not the SDK's: the pause is handed to your
  code, and this script happens to answer it from stdin.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Approve with `y`, reject with `n`.

## Resuming

The pause and the resume are the whole API:

```python
result = agent(prompt)

while result.stop_reason == "interrupt":
    responses = []
    for interrupt in result.interrupts:
        answer = input(f"{interrupt.reason} (y/n) ")
        responses.append(
            {"interruptResponse": {"interruptId": interrupt.id, "response": answer}}
        )
    result = agent(responses)
```

Each `Interrupt` carries an `id` to address the answer to, a `name` (here the handler's own,
`strands:human-in-the-loop`), and a `reason` holding the approval prompt with the tool arguments in
it. Resuming is another call to the same agent with a list of `interruptResponse` blocks standing in
for a prompt.

## Note the following

- **The default is a pause, not a prompt.** Construct `HumanInTheLoop()` with no `ask` and the run
  returns at the tool call. This is what a web UI, a queue, or a Slack approval uses, because none of
  them can answer a blocking `input()`. `ask="stdio"` is the opt-out for interactive CLI use.
- **Loop, do not branch.** A run can pause more than once, and each pause reports *every* interrupt
  still unanswered, so build the response list from all of `result.interrupts` and keep going until
  `stop_reason` is no longer `interrupt`.
- **Resuming in the same process needs nothing extra.** A session manager is only required to
  survive a pause that outlives the process, which is the realistic case once a human is involved.
- **Approval is opt-out, not opt-in.** By default every tool requires approval, and `allowed_tools`
  is the allow-list of tools that run freely. This is the safe default: a tool added later is gated
  until someone deliberately allows it. The reverse design would leave new tools ungated.
- **`allowed_tools` takes wildcards.** `["*"]` allows everything, and a `!` prefix carves tools
  back out, so `["*", "!transfer_funds"]` gates only the transfer. Useful once the tool list grows
  past the point where naming every safe tool is practical, at the cost of the safe default above.
- **The prompt shows the arguments**, not just the tool name. Approving `transfer_funds` in the
  abstract is meaningless; approving it for 500 USD to ACC-2 is a real decision.
- **Rejection is not an error.** The loop continues and the model is told the call failed
  confirmation, so it reports back rather than crashing. `stop_reason` is still `end_turn`.
- **You cannot reword what the model is told.** On a rejection the tool result is
  `CONFIRMATION_FAILED:` followed by the approval prompt, which `HumanInTheLoop` builds internally
  from the tool name and arguments. Because that text reads as a question, the model tends to hedge
  about a failed confirmation step rather than say a person declined. A hand-written `Confirm` in
  [`01-intervention-basics`](../01-intervention-basics/) lets you phrase it; this handler does not.
- **One per agent.** `name` is a fixed class attribute on `HumanInTheLoop`, and handler names must
  be unique, so a second instance cannot be registered. Layering two approval policies means
  subclassing to rename.
- **This is `Confirm` packaged up.** The handler is built on the same `Confirm` action available in
  [`01-intervention-basics`](../01-intervention-basics/), which is valid only on `before_tool_call`.

## Variations

- **Prompt inline instead** with `ask="stdio"`, which reads the answer from the terminal inside the
  agent loop. The run never pauses, so there is no resume loop to write, and `stop_reason` is never
  `interrupt`. Convenient for a CLI, and unusable anywhere the approver is not at that terminal.
- **Provide a custom `ask` callback**, sync or async, to route the prompt to Slack, a web UI, or a
  ticket while still blocking inline. Returning `None` is treated as a denial.
- **Decide by argument** with `classifier=`, which receives the `BeforeToolCallEvent` and can read
  `tool_use["input"]`, so a transfer under 100 can skip the prompt while a larger one still asks.
  Pass `True` for the built-in LLM risk classifier, or your own callable.
- **Accept a different answer** with `evaluate=`, which receives the human's *response* and returns
  a bool. The default takes `True`, `"y"`, and `"yes"`; override it to accept `"approve"` or a
  button payload from a web UI. It never sees the tool call, so it cannot decide by argument.
- **Enable trust** with `enable_trust=True` and `evaluate_trust=`, so answering `t` approves the
  call and records the **tool name** in `agent.state` for the rest of the session. Every later call
  to that tool then runs unasked, whatever its arguments, and with a `classifier` it also turns off
  argument-level classification for that name. Broader than it first sounds.

## See also

- [`07-interventions/01-intervention-basics`](../01-intervention-basics/) for writing your own
  handler. That leaf gates a tool inline and never pauses the run; this one pauses and hands the
  decision out.
- [`01-agent/01-first-agent`](../../01-agent/01-first-agent/) for the tool definitions this builds on.

Verified against strands-agents 1.54.0 on 2026-09-04
