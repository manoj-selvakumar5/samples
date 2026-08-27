"""Pause the agent for human approval before a sensitive tool runs.

HumanInTheLoop is a vended intervention handler. You do not write the pause,
the prompt, or the resume plumbing.

Run:
    python main.py

The script asks for approval on stdin. Approve with 'y', reject with 'n'.
"""

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


def main() -> None:
    # By default EVERY tool requires approval. `allowed_tools` is the
    # allow-list of tools that run without asking, so approval is opt-out
    # rather than opt-in and a newly added tool is gated by default.
    #
    # ask="stdio" prompts on the terminal. Omit `ask` entirely and the agent
    # pauses via interrupt instead, which is what a web UI would use.
    hitl = HumanInTheLoop(
        allowed_tools=["check_balance"],
        ask="stdio",
    )

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

    print("\n--- Result ---")
    print(f"stop_reason : {result.stop_reason}")
    print(f"text        : {result}")


if __name__ == "__main__":
    main()
