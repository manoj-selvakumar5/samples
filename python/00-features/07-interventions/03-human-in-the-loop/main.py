"""Pause the agent for human approval before a sensitive tool runs.

HumanInTheLoop is a vended intervention handler. By default it stops the run at
the tool call and hands the decision back to you, so the approval can come from
a terminal, a web UI, or a review queue. You resume by calling the agent again.

Run:
    python main.py

Approve the transfer on stdin with 'y'; anything else rejects it.
"""

import json
import textwrap

from strands import Agent, tool
from strands.vended_interventions import HumanInTheLoop


@tool
def check_balance(account: str) -> str:
    """Check the balance of an account.

    Args:
        account: The account identifier.

    Returns:
        The current balance as text.
    """
    print(f"  [tool] check_balance({account!r}) ran")
    return f"{account} balance is 8,400.00 USD"


@tool
def transfer_funds(account: str, amount: float, destination: str) -> str:
    """Transfer funds out of an account.

    Args:
        account: The source account identifier.
        amount: The amount to transfer.
        destination: The destination account identifier.

    Returns:
        Confirmation that the transfer completed.
    """
    print(f"  [tool] transfer_funds({account!r}, {amount}, {destination!r}) ran")
    return f"transferred {amount} from {account} to {destination}"


def print_history(messages: list[dict]) -> None:
    """Print the conversation the way the model saw it."""
    pad = " " * 19
    for index, message in enumerate(messages):
        print(f"[{index}] {message['role']}")
        for block in message["content"]:
            label, value = "text", block.get("text", "")
            if "toolUse" in block:
                use = block["toolUse"]
                label, value = "toolUse", f"{use['name']} {json.dumps(use['input'])}"
            elif "toolResult" in block:
                result = block["toolResult"]
                # Status on its own line, the returned text indented beneath it.
                text = "".join(c.get("text", "") for c in result["content"])
                label, value = "toolResult", f"{result['status']}\n{text}"
            for n, line in enumerate(value.split("\n")):
                head = f"      {label:<11}: " if n == 0 else pad
                print(textwrap.fill(line, 96, initial_indent=head, subsequent_indent=pad))


def main() -> None:
    # By default EVERY tool requires approval. `allowed_tools` is the
    # allow-list of tools that run without asking, so approval is opt-out
    # rather than opt-in and a newly added tool is gated by default.
    #
    # No `ask` argument, so the handler never prompts. It pauses the run
    # instead and leaves collecting the answer to the code below.
    hitl = HumanInTheLoop(allowed_tools=["check_balance"])

    agent = Agent(
        system_prompt=(
            "You are a banking assistant. Use the tools available. "
            "Answer in one or two plain sentences, with no markdown formatting."
        ),
        tools=[check_balance, transfer_funds],
        interventions=[hitl],
    )

    prompt = "Check the balance of account ACC-1 and then transfer 500 to account ACC-2."
    print(f"Prompt: {prompt}\n")

    result = agent(prompt)

    # A run can pause more than once, and each pause reports every interrupt
    # still waiting, so this is a loop over a list rather than a single check.
    while result.stop_reason == "interrupt":
        print(f"\n  [paused] stop_reason={result.stop_reason}, awaiting {len(result.interrupts)}")
        responses = []
        for interrupt in result.interrupts:
            # `reason` is the approval prompt HumanInTheLoop built, arguments
            # included. `id` is what the answer is addressed to. Collect the
            # answer however you like: stdin here, a reviewer's click elsewhere.
            print(f"  [interrupt] {interrupt.reason}")
            answer = input("  approve? (y/n) ")
            responses.append(
                {"interruptResponse": {"interruptId": interrupt.id, "response": answer}}
            )
        # Resuming is another call to the same agent, with the responses
        # standing in for a prompt.
        result = agent(responses)

    print("\n\n--- Result ---")
    print(f"stop_reason : {result.stop_reason}")
    print(f"text        : {result}")

    # The approval decision reaches the model as the tool result: the transfer
    # either ran, or the call comes back cancelled at the confirmation step.
    print("\n--- agent.messages ---")
    print_history(agent.messages)


if __name__ == "__main__":
    main()
