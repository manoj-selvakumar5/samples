Part I - Build the agent

# First agent

Construct an agent, give it one tool, invoke it, and read what comes back.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `Agent` | `strands.Agent` |
| `tool` | `strands.tool` |
| `AgentResult` | returned by `Agent.__call__` |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

No model is configured in `main.py`, so the agent uses the SDK default. Set `AWS_REGION` if your
default region does not have model access.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Output

```
Prompt: How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?


Tool #1: word_count
  [tool] word_count called with 43 characters
The sentence **"the quick brown fox jumps over the lazy dog"** contains **9 words**.
--- AgentResult ---
stop_reason : end_turn
text        : The sentence **"the quick brown fox jumps over the lazy dog"** contains **9 words**.

role        : assistant
blocks      : 1
tokens      : 1348 in, 88 out
tool calls  : word_count x1
```

## Note the following

- **`Agent` returns an `AgentResult`, not a string.** Printing it renders the final text, which is
  why `print(agent(prompt))` looks like it returns a string. The object also carries
  `stop_reason`, the raw `message`, and `metrics`.
- **`stop_reason` is how the loop ended**, and `end_turn` means the model finished on its own. It
  is one of twelve values, and the other eleven are how you detect a run that ended for a reason
  you care about. See [`09-limits/02-stop-reasons`](../../09-limits/02-stop-reasons/).
- **The `@tool` docstring is the tool description the model sees.** Argument descriptions come from
  the `Args:` block, so a vague docstring produces a tool the model calls at the wrong times.
- **`metrics.tool_metrics` proves the tool ran.** Without it you cannot tell whether the model
  called `word_count` or simply counted the words itself and got lucky.

## Variations

- **Stream the response** instead of blocking, with `async for event in agent.stream_async(prompt)`.
- **Inspect the conversation** through `agent.messages`, which holds every turn including the tool
  call and its result.
- **Add more tools** by extending the `tools=[...]` list. Tool selection is the model's decision,
  driven entirely by the docstrings.
- **Name the agent** with `Agent(name=..., description=...)`, which matters once an agent becomes a
  tool for another agent or a node in a graph.

## See also

- [`01-agent/03-structured-output`](../03-structured-output/) to get a typed object back instead of prose.
- [`09-limits/01-execution-limits`](../../09-limits/01-execution-limits/) to cap what a single invocation may spend.

Verified against strands-agents 1.53.0 on 2026-08-26
