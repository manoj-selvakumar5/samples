Part II - Control the loop

# Human in the loop

Pause the agent for human approval before a sensitive tool runs.

`HumanInTheLoop` is a vended intervention handler. You do not write the pause, the prompt, or the
resume plumbing.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `HumanInTheLoop` | `strands.vended_interventions.HumanInTheLoop` |
| `allowed_tools` | keyword on `HumanInTheLoop` |
| `ask` | keyword on `HumanInTheLoop` |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock
- An interactive terminal, since this leaf prompts on stdin

## Run

```bash
pip install -r requirements.txt
python main.py
```

Approve with `y`, reject with `n`.

## Output

Approving the transfer:

```
Prompt: Check the balance of account ACC-1 and then transfer 500 to account ACC-2.

I'll start by checking the balance of ACC-1 first before proceeding with the transfer.
Tool #1: check_balance
  [tool] check_balance('ACC-1') ran
ACC-1 has a balance of 8,400.00 USD, which is sufficient for the transfer. Let me now transfer 500 USD to ACC-2.
Tool #2: transfer_funds
Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"} (y/n): y
  [tool] transfer_funds('ACC-1', 500.0, 'ACC-2') ran
ACC-1 had a balance of 8,400.00 USD, and the transfer of 500.00 USD to ACC-2 has been completed successfully, leaving ACC-1 with an estimated balance of 7,900.00 USD.

--- Result ---
stop_reason : end_turn
text        : ACC-1 had a balance of 8,400.00 USD, and the transfer of 500.00 USD to ACC-2 has been completed successfully, leaving ACC-1 with an estimated balance of 7,900.00 USD.


--- agent.messages ---
[0] user
      text       : Check the balance of account ACC-1 and then transfer 500 to account ACC-2.
[1] assistant
      text       : I'll start by checking the balance of ACC-1 first before proceeding with the
                   transfer.
      toolUse    : check_balance {"account": "ACC-1"}
[2] user
      toolResult : success
                   ACC-1 balance is 8,400.00 USD
[3] assistant
      text       : ACC-1 has a balance of 8,400.00 USD, which is sufficient for the transfer.
                   Let me now transfer 500 USD to ACC-2.
      toolUse    : transfer_funds {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
[4] user
      toolResult : success
                   transferred 500.0 from ACC-1 to ACC-2
[5] assistant
      text       : ACC-1 had a balance of 8,400.00 USD, and the transfer of 500.00 USD to ACC-2
                   has been completed successfully, leaving ACC-1 with an estimated balance of
                   7,900.00 USD.
```

Rejecting it:

```
Prompt: Check the balance of account ACC-1 and then transfer 500 to account ACC-2.

Sure! Let me start by checking the balance of account ACC-1 first.
Tool #1: check_balance
  [tool] check_balance('ACC-1') ran
ACC-1 has a balance of $8,400.00 USD, which is sufficient to cover the transfer. Let me now proceed with transferring $500 to ACC-2!
Tool #2: transfer_funds
Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"} (y/n): n
It looks like the transfer of $500 from ACC-1 to ACC-2 could not be completed due to a confirmation failure. Please try again or contact support if the issue persists.

--- Result ---
stop_reason : end_turn
text        : It looks like the transfer of $500 from ACC-1 to ACC-2 could not be completed due to a confirmation failure. Please try again or contact support if the issue persists.


--- agent.messages ---
[0] user
      text       : Check the balance of account ACC-1 and then transfer 500 to account ACC-2.
[1] assistant
      text       : Sure! Let me start by checking the balance of account ACC-1 first.
      toolUse    : check_balance {"account": "ACC-1"}
[2] user
      toolResult : success
                   ACC-1 balance is 8,400.00 USD
[3] assistant
      text       : ACC-1 has a balance of $8,400.00 USD, which is sufficient to cover the
                   transfer. Let me now proceed with transferring $500 to ACC-2!
      toolUse    : transfer_funds {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
[4] user
      toolResult : error
                   CONFIRMATION_FAILED: Approve "transfer_funds"?
                     Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"}
[5] assistant
      text       : It looks like the transfer of $500 from ACC-1 to ACC-2 could not be completed
                   due to a confirmation failure. Please try again or contact support if the
                   issue persists.
```

In both runs `check_balance` executes without a prompt, because it is on the allow-list. Only
`transfer_funds` stops to ask.

The `agent.messages` section shows how the decision reaches the model. Approving produces a normal
`success` tool result; rejecting produces an `error` carrying `CONFIRMATION_FAILED:` followed by the
approval prompt itself. Note that the prompt is phrased as a question, so the model is told
`CONFIRMATION_FAILED: Approve "transfer_funds"?` and tends to hedge about a "confirmation failure"
rather than state that a person declined. `HumanInTheLoop` builds that text internally, so unlike a
hand-written `Confirm` in [`01-intervention-basics`](../01-intervention-basics/) you cannot reword
it.

## Note the following

- **Approval is opt-out, not opt-in.** By default every tool requires approval, and `allowed_tools`
  is the allow-list of tools that run freely. This is the safe default: a tool added later is gated
  until someone deliberately allows it. The reverse design would leave new tools ungated.
- **`allowed_tools` takes wildcards.** `["*"]` allows everything, and a `!` prefix carves tools
  back out, so `["*", "!transfer_funds"]` gates only the transfer. Useful once the tool list grows
  past the point where naming every safe tool is practical.
- **The prompt shows the arguments**, not just the tool name. Approving `transfer_funds` in the
  abstract is meaningless; approving it for 500 USD to ACC-2 is a real decision.
- **Rejection is not an error.** The loop continues and the model is told the call failed
  confirmation, so it reports back rather than crashing. `stop_reason` is still `end_turn`.
- **`ask="stdio"` is for the terminal.** Omit `ask` entirely and the agent pauses via the interrupt
  mechanism instead, which is what a web UI or a queue-backed approval workflow uses. The run then
  returns with `stop_reason` of `interrupt`, and you resume by calling the agent again with a list
  of `interruptResponse` content. A session manager is only needed to survive a pause that outlives
  the process; resuming in the same process needs nothing extra.
- **One per agent.** `name` is a fixed class attribute on `HumanInTheLoop`, and handler names must
  be unique, so a second instance cannot be registered. Layering two approval policies means
  subclassing to rename.
- **This is `Confirm` packaged up.** The handler is built on the same `Confirm` action available in
  [`01-intervention-basics`](../01-intervention-basics/), which is valid only on `before_tool_call`.

## Variations

- **Decide by argument** with `classifier=`, which receives the `BeforeToolCallEvent` and can read
  `tool_use["input"]`, so a transfer under 100 can skip the prompt while a larger one still asks.
  Pass `True` for the built-in LLM risk classifier, or your own callable.
- **Accept a different answer** with `evaluate=`, which receives the human's *response* and returns
  a bool. The default takes `True`, `"y"`, and `"yes"`; override it to accept `"approve"` or a
  button payload from a web UI. It never sees the tool call, so it cannot decide by argument.
- **Provide a custom `ask` callback** instead of `"stdio"` to route the prompt to Slack, a web UI,
  or a ticket.
- **Enable trust** with `enable_trust=True` and `evaluate_trust=`, so answering `t` approves the
  call and records the **tool name** in `agent.state` for the rest of the session. Every later call
  to that tool then runs unasked, whatever its arguments, and with a `classifier` it also turns off
  argument-level classification for that name. Broader than it first sounds.

## See also

- [`07-interventions/01-intervention-basics`](../01-intervention-basics/) for writing your own handler.
- [`01-agent/01-first-agent`](../../01-agent/01-first-agent/) for the tool definitions this builds on.

Verified against strands-agents 1.54.0 on 2026-09-04
