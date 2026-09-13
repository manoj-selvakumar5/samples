Part II - Control the loop

# Pause an agent for human approval before a sensitive tool runs

## Overview

Most tool calls are safe to let an agent make unsupervised. Reading a record, searching a knowledge
base, counting words: if the model gets one of those wrong, little is lost. A few tool calls are not
like that. Moving money, deleting a customer, mailing a client. Those are worth a person looking at
before they happen.

In this tutorial a banking assistant has two tools. `check_balance` is harmless and runs freely.
`transfer_funds` moves money, so it has to be approved first. The prompt asks for both, so the run
gets as far as the transfer and stops there.

`HumanInTheLoop` is a vended intervention handler, imported from `strands.vended_interventions` and
passed to `interventions=` when the `Agent` is constructed rather than per call. It therefore
applies to every invocation of that agent.

The part that surprises people is that **by default it does not prompt anyone**. It stops the run at
the tool call and hands the decision back to your code. The approval can then come from a terminal,
a web UI, or a review queue, and you resume by calling the agent again. This script happens to
answer from stdin, which is its own choice and not something the SDK does for you.

---

## What you will learn

- how to gate one sensitive tool behind human approval while safe tools keep running freely
- how to answer the pause the agent hands back, and resume the run with that answer
- why the default is a pause rather than a prompt, and when to prompt inline instead
- what the model is told when a person rejects a call

---

## How the approval pause works

```text
agent(prompt)
      │
      ▼
Model requests a tool call
      │
      ▼
HumanInTheLoop.before_tool_call
      │
      ├── the tool is allow-listed ──► the tool runs, the loop continues
      │
      ▼
Approval is required, and no answer exists yet
      │
      ▼
The agent loop stops. The tool has not run.
      │
      ▼
AgentResult
  stop_reason = "interrupt"
  interrupts  = [Interrupt(id, name, reason)]
      │
      │   ◄── your code collects the answer, not the SDK
      │       (stdin here; a click, a Slack reply, a queue elsewhere)
      ▼
agent([{"interruptResponse": {"interruptId": ..., "response": ...}}])
      │
      ▼
HumanInTheLoop.before_tool_call runs again, with the answer this time
      │
      ├── approved ──► the tool runs, the loop continues
      │
      └── rejected ──► the tool is cancelled, the model is told, the loop continues
```

The important detail is **who collects the answer**. Strands stops the loop and returns; nothing in
the SDK asks anyone anything. Everything between the pause and the resume call is yours to build,
which is exactly what makes the pattern work when the approver is not attached to the process.

The second detail is that a pause is not one question. A single model turn can request several gated
tools, and they arrive together:

```text
One model turn requesting three tools
      │
      ├── check_balance    allow-listed  ──► ran
      ├── transfer_funds   needs approval ──┐
      └── close_account    needs approval ──┤
                                            ▼
                              one pause, and result.interrupts
                              holds both of them
```

---

## Prerequisites and setup

Before starting, make sure you have:

- Python 3.10 or later
- AWS credentials configured
- access to a supported model in Amazon Bedrock
- an interactive terminal, because this script reads the approval from stdin

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the tutorial

```bash
python main.py
```

The script runs one scenario.

### 1. Gate a funds transfer behind human approval

The handler is constructed with a single allow-listed tool and no `ask` argument, which is what
makes it pause rather than prompt:

```python
hitl = HumanInTheLoop(allowed_tools=["check_balance"])

agent = Agent(
    system_prompt=(
        "You are a banking assistant. Use the tools available. "
        "Answer in one or two plain sentences, with no markdown formatting."
    ),
    tools=[check_balance, transfer_funds],
    interventions=[hitl],
)
```

The prompt asks for one ungated action and one gated one:

```python
prompt = "Check the balance of account ACC-1 and then transfer 500 to account ACC-2."
```

When the run pauses, answer on stdin. `y` or `yes` approves the transfer, case-insensitively and
ignoring surrounding whitespace. Anything else rejects it, `n` included.

### Expected output

Output varies because the model's wording and its choice of how many tools to request per turn are
not deterministic. An abbreviated run, approving the transfer:

```text
Prompt: Check the balance of account ACC-1 and then transfer 500 to account ACC-2.

  [tool] check_balance('ACC-1') ran

  [paused] stop_reason=interrupt, awaiting 1
  [interrupt] Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
  approve? (y/n) y
  [tool] transfer_funds('ACC-1', 500.0, 'ACC-2') ran


--- Result ---
stop_reason : end_turn
text        : <the assistant's one or two sentence answer>


--- agent.messages ---
[0] user
      text       : Check the balance of account ACC-1 and then transfer 500 to account ACC-2.
[1] assistant
      toolUse    : check_balance {"account": "ACC-1"}
[2] user
      toolResult : success
                   ACC-1 balance is 8,400.00 USD
[3] assistant
      toolUse    : transfer_funds {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
[4] user
      toolResult : success
                   transferred 500.0 from ACC-1 to ACC-2
[5] assistant
      text       : <the assistant's one or two sentence answer>
```

Three things in that output are worth reading twice.

`awaiting 1` counts only the gated call. `check_balance` is allow-listed, so it ran without asking
and is already a finished `toolResult` in the history by the time the pause happens. Resuming does
not re-run it.

The final `stop_reason` is `end_turn`, not `interrupt`. `interrupt` was the stop reason of the
paused call; the resumed call ran to completion and reported its own.

**In this example** the argument appears twice in two shapes: `"amount": 500` in the JSON the model
produced, and `500.0` in the tool's own output. The `transfer_funds` parameter is annotated `float`,
so the integer the model sent arrives in the function as a float.

---

## Understanding the approval pause

### Resuming from a pause

The pause and the resume are the whole API:

```python
result = agent(prompt)

while result.stop_reason == "interrupt":
    print(f"\n  [paused] stop_reason={result.stop_reason}, awaiting {len(result.interrupts)}")
    responses = []
    for interrupt in result.interrupts:
        print(f"  [interrupt] {interrupt.reason}")
        answer = input("  approve? (y/n) ")
        responses.append(
            {"interruptResponse": {"interruptId": interrupt.id, "response": answer}}
        )
    result = agent(responses)
```

Resuming is another call to the same agent, with a list of `interruptResponse` content blocks
standing in for a prompt.

Both levels of that nesting are load-bearing, so **loop, do not branch**. The inner `for` exists
because one pause can carry several interrupts, as the second diagram above shows. The outer `while`
exists because a run can pause more than once: answering the first gated call lets the loop carry
on, and the next gated call stops it again. Keep going until `stop_reason` is no longer
`"interrupt"`.

### What an interrupt carries

Each entry in `result.interrupts` is a `strands.interrupt.Interrupt`:

| Field      | What it holds                                                            |
|:-----------|:-------------------------------------------------------------------------|
| `id`       | The identifier the answer must be addressed to, as `interruptId`         |
| `name`     | The handler's own name, which here is always `strands:human-in-the-loop` |
| `reason`   | The approval prompt, built from the tool name and its arguments          |
| `response` | The answer, once one has been supplied                                   |

`reason` is the text a reviewer actually sees, and it carries the arguments rather than just the
tool name:

```text
Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
```

That distinction matters. Approving `transfer_funds` in the abstract is meaningless; approving it
for 500 USD to ACC-2 is a real decision.

### Which tools require approval

By default every tool requires approval, and `allowed_tools` is the allow-list of tools that run
without asking. Approval is therefore opt-out rather than opt-in. That is the safe default: a tool
added to the agent later is gated until someone deliberately allows it, where the reverse design
would leave new tools ungated.

Two wildcard forms are recognized inside the list:

| Entry          | Effect                                                            |
|:---------------|:------------------------------------------------------------------|
| `"*"`          | Every tool runs freely                                            |
| `"!tool_name"` | Carves that tool back out of `"*"`, so it still requires approval |

So `allowed_tools=["*", "!transfer_funds"]` gates only the transfer. That is useful once the tool
list grows past the point where naming every safe tool is practical, at the cost of the safe default
above.

### What the model is told when you reject

Rejection is not an error. The loop continues and `stop_reason` is still `end_turn`, so the agent
reports back rather than crashing.

The tool does not run. In its place the model receives a tool result with status `error` whose text
is `CONFIRMATION_FAILED:` followed by the same approval prompt:

```text
CONFIRMATION_FAILED: Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
```

You cannot reword that text. `HumanInTheLoop` builds it internally from the tool name and arguments.
Because it reads as a question, the model tends to hedge about a failed confirmation step rather
than say that a person declined.

### Narrowing or widening what gets asked

Three more keyword arguments change what gets asked and what counts as a yes.

`classifier=` decides, per call, whether a non-allow-listed tool needs approval at all. It receives
the `BeforeToolCallEvent`, so it can read `tool_use["input"]` and let a transfer under 100 through
while a larger one still asks. Pass your own callable, or `True` for the built-in LLM risk
classifier.

`evaluate=` decides whether a response counts as approval. It receives the human's response and
returns a bool. The default accepts `True`, `"y"`, and `"yes"`, case-insensitively and ignoring
surrounding whitespace. Override it to accept `"approve"`, or a button payload from a web UI. It
never sees the tool call, so it cannot decide by argument.

`enable_trust=True` adds a third possible answer, validated by `evaluate_trust=`, which by default
accepts `"t"` and `"trust"`. That answer approves the call and records the **tool name** in
`agent.state` for the rest of the session. Every later call to that tool then runs unasked, whatever
its arguments, and alongside a `classifier` it also switches off argument-level classification for
that name. Broader than it first sounds. A negated tool such as `"!transfer_funds"` can never be
trusted.

### One handler per agent

`name` is a fixed class attribute on `HumanInTheLoop`, and intervention handler names must be unique
within an agent, so registering a second instance raises:

```text
ValueError: Duplicate intervention handler name: 'strands:human-in-the-loop'
```

Layering two approval policies therefore means subclassing to rename.

### Resuming after the process has gone

Resuming inside the same process needs nothing extra. The pending interrupt lives on the agent, and
the resume call in this script is the very next thing that happens.

A session manager is only required when the pause outlives the process, which is the realistic case
once a human is involved: the approval may arrive minutes later, possibly at a different worker.
Strands serializes pending interrupt state along with the rest of the session, so a restored agent
resumes at the same pause.

---

## Choosing where the approval comes from

The `ask` argument decides this, and it is the one real design choice the handler asks you to make.

| `ask`             | What happens                                           | Fits                        |
|:------------------|:-------------------------------------------------------|:----------------------------|
| omitted (default) | The run stops and returns, and you resume it           | Web UI, review queue, Slack |
| `"stdio"`         | The loop blocks on `input()` inline                    | An interactive CLI          |
| Your own callable | The loop blocks while your callback collects an answer | Slack, web UI, ticketing    |

The default is the only one that works when the approver is not attached to the process. A browser
tab and a queue worker cannot answer a blocking `input()`.

`ask="stdio"` prompts on the terminal from inside the agent loop. The run never pauses, so there is
no resume loop to write and `stop_reason` is never `"interrupt"`. Convenient for a CLI, and unusable
anywhere the approver is not at that terminal.

A custom `ask` callable, sync or async, routes the prompt to Slack, a web UI, or a ticket while
still blocking inline. An async one lets the agent keep serving its event loop while it waits.
Returning `None` is treated as a denial.

This tutorial takes the default and answers from stdin in its own code, which is deliberate: it
exercises the mode a real approval workflow needs, using the simplest possible source of answers.

---

## Human-in-the-loop versus writing your own handler

`HumanInTheLoop` is the human-approval case of the broader interventions feature. Underneath, it is
built on the same `Confirm` action a hand-written handler returns, and `Confirm` is valid only on
`before_tool_call`.

Reach for [`01-intervention-basics`](../01-intervention-basics/) when you want to write the handler
yourself. That leaf is the general case: it gates a tool inline and never pauses the run, and
because you construct the `Confirm` yourself, you get to phrase what the model is told on a
rejection. This leaf pauses instead, hands the decision out of the process, and accepts the wording
that comes with the packaged handler.

Reach for `HumanInTheLoop` when the policy is "ask a person before these tools run" and you would
rather configure that than build it.

---

## Additional resources

- [Human in the Loop](https://strandsagents.com/docs/user-guide/concepts/agents/interventions/human-in-the-loop/)
- [Interventions](https://strandsagents.com/docs/user-guide/concepts/agents/interventions/)
- [Interrupts](https://strandsagents.com/docs/user-guide/concepts/interrupts/), which documents the
  interrupt and resume contract on its own.
- [Session Management](https://strandsagents.com/docs/user-guide/concepts/agents/session-management/)
- [`01-agent/01-first-agent`](../../01-agent/01-first-agent/), where the `@tool` decorator that
  defines these two tools is introduced.
