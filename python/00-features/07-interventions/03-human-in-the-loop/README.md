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
ACC-1 has a balance of 8,400.00 USD, which is sufficient for the transfer. Let me now proceed with transferring 500 USD to ACC-2.
Tool #2: transfer_funds
Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"} (y/n):   [tool] transfer_funds('ACC-1', 500.0, 'ACC-2') ran
ACC-1 had a balance of 8,400.00 USD, and 500.00 USD has been successfully transferred to ACC-2, leaving ACC-1 with 7,900.00 USD.
--- Result ---
stop_reason : end_turn
```

Rejecting it:

```
Tool #2: transfer_funds
Approve "transfer_funds"?
  Input: {"account": "ACC-1", "amount": 500, "destination": "ACC-2"} (y/n): The transfer of 500 USD from ACC-1 to ACC-2 could not be completed as it failed the confirmation step. Please verify your authorization and try again, or contact support if the issue persists.
--- Result ---
stop_reason : end_turn
```

In both runs `check_balance` executes without a prompt, because it is on the allow-list. Only
`transfer_funds` stops to ask.

## Note the following

- **Approval is opt-out, not opt-in.** By default every tool requires approval, and `allowed_tools`
  is the allow-list of tools that run freely. This is the safe default: a tool added later is gated
  until someone deliberately allows it. The reverse design would leave new tools ungated.
- **The prompt shows the arguments**, not just the tool name. Approving `transfer_funds` in the
  abstract is meaningless; approving it for 500 USD to ACC-2 is a real decision.
- **Rejection is not an error.** The loop continues and the model is told the call failed
  confirmation, so it reports back rather than crashing. `stop_reason` is still `end_turn`.
- **`ask="stdio"` is for the terminal.** Omit `ask` entirely and the agent pauses via the interrupt
  mechanism instead, which is what a web UI or a queue-backed approval workflow uses. That path
  needs a session manager to resume across the pause.
- **This is `Confirm` packaged up.** The handler is built on the same `Confirm` action available in
  [`01-intervention-basics`](../01-intervention-basics/), which is valid only on `before_tool_call`.

## Variations

- **Approve by policy** with `evaluate=`, a callback receiving the tool use and returning a bool,
  when some calls should auto-approve based on their arguments (for example, transfers under 100).
- **Provide a custom `ask` callback** instead of `"stdio"` to route the prompt to Slack, a web UI,
  or a ticket.
- **Enable trust** with `enable_trust=True` and `evaluate_trust=`, so a repeated approval for the
  same shape of call is remembered rather than asked every time.
- **Classify sensitivity with a model** using `classifier=`, rather than maintaining the
  `allowed_tools` list by hand.

## See also

- [`07-interventions/01-intervention-basics`](../01-intervention-basics/) for writing your own handler.
- [`01-agent/01-first-agent`](../../01-agent/01-first-agent/) for the tool definitions this builds on.

Verified against strands-agents 1.53.0 on 2026-08-26
