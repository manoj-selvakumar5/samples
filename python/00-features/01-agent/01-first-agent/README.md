Part I - Build the agent

# Build your first agent and read what it returns

## Overview

Calling a model is one request and one response. Getting a model to act on something outside itself
is not. It has to ask for information it does not have, wait for an answer, and then decide what to
say. Writing that exchange by hand means writing the part that decides whether the model is done,
the part that matches a tool request to the right Python function, and the part that feeds the
result back in the shape the model expects, on every iteration.

That exchange is the agent loop, and Strands runs it for you. You supply a model, a system prompt,
and a list of Python functions the model is allowed to call. Everything between the first request
and the final answer is handled for you.

In this tutorial the agent gets one tool, `word_count`, and one question: how many words are in a
given sentence. Counting is exactly the kind of task a model is unreliable at, so answering well
means calling the tool, reading what it returned, and only then replying. A single `agent(prompt)`
call covers all of it.

What comes back is an `AgentResult`, not a string. Reading that object is the second half of the
tutorial: whether the loop ended on its own, what the final message held, and what the run cost.

---

## What you will learn

- how to construct an `Agent` with a system prompt and a single tool
- how the agent loop turns one call into as many model round trips as the task needs
- why an invocation returns an `AgentResult` rather than a string, and what else that object carries
- how to confirm from the result that the model really called your tool

---

## How the agent loop works

`Agent` and `tool` both come from the top-level package: `from strands import Agent, tool`. Invoking
the agent starts a loop that repeats until the model stops asking for anything:

```text
agent(prompt)
      │
      ▼
Call the model with the conversation so far,
the system prompt, and the schema of every tool
      │
      ├── the model answers in text ──► return AgentResult
      │                                 with stop_reason "end_turn"
      ▼
The model requests one or more tools instead
      │
      ▼
Run those tools and append their results
to the conversation
      │
      └──────────────────► call the model again
```

The important detail is that **the exit condition belongs to the model, not to your code**. You do
not decide how many model calls one invocation takes; the model does, by choosing each turn between
answering and asking for a tool.

So a single line of your code can hide several round trips. In this tutorial the shortest successful
run is already two:

```text
agent(prompt)
     │
     │   model call 1    the model requests word_count
     │   tool run        word_count returns the count
     │   model call 2    the model turns that count into an answer
     ▼
AgentResult
```

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

The script runs one scenario.

### 1. Count the words in a sentence with a tool

The tool is an ordinary Python function with a decorator on it:

```python
@tool
def word_count(text: str) -> int:
    """Count the words in a block of text.

    Args:
        text: The text to count words in.

    Returns:
        The number of whitespace-separated words.
    """
    print(f"  [tool] word_count called with {len(text)} characters")
    return len(text.split())
```

The agent is constructed with that function in its `tools` list, and with a system prompt that
steers the model toward using it:

```python
agent = Agent(
    system_prompt=(
        "You are a concise assistant. When asked to count words, use the "
        "word_count tool rather than counting yourself."
    ),
    tools=[word_count],
)
```

Then the agent is invoked like a function:

```python
prompt = "How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?"
result = agent(prompt)
```

The system prompt asks for the tool, but nothing here forces the call. Whether `word_count` runs is
the model's decision, which is why the script goes on to check the result rather than assume it.

### Expected output

Output varies because model wording and token usage are not deterministic. An abbreviated run:

```text
Prompt: How many words are in this sentence: 'the quick brown fox jumps over the lazy dog'?

  [tool] word_count called with <n> characters


--- AgentResult ---
stop_reason : end_turn
text        : <the model's answer>

role        : assistant
blocks      : 1
tokens      : <n> in, <n> out
tool calls  : word_count x1
```

A real run shows more than this. The agent's default callback handler streams the model's text to
standard output as it is generated and announces each tool call on its own line, so the answer
appears once while it is being produced and again on the `text` line, which reads it back off the
finished result. Every line above comes from `main.py` itself.

**In this example** `blocks` is 1 because the final message carries a single text block. A model
that returns reasoning content alongside its answer would report more. The blank line after `text`
comes from the text block's own trailing newline.

---

## Understanding the agent and its result

### What `Agent` needs to run

Nothing, strictly. Every constructor argument has a default, and `Agent()` with no arguments is a
working agent with no tools and no instructions.

The three used here are the ones that shape behavior:

| Argument        | What it does                                                           |
|:----------------|:-----------------------------------------------------------------------|
| `model`         | Which model to call                                                    |
| `system_prompt` | Standing instructions sent with every model call                       |
| `tools`         | The list the model is allowed to choose from. Extend it to add tools   |

Because `main.py` configures no model, the agent uses the SDK default, a `BedrockModel`. That means
the run calls Amazon Bedrock in whichever region your AWS configuration resolves to, and that region
needs access to the default model.

Two more arguments are worth knowing about early even though this tutorial leaves them unset.
`Agent(name=..., description=...)` label the agent, and those labels become defaults later: turning
an agent into a tool for another agent with `as_tool()` uses them as the tool's name and
description, and adding an agent to a graph uses the name as the node id.

### Why the return value is not a string

`Agent.__call__` returns an `AgentResult`. Printing one renders the final text, which is why
`print(agent(prompt))` behaves as though a string came back, but the object carries the rest of the
run too:

```python
result.stop_reason   # how the loop ended
result.message       # the raw final message, a dict with a role and content blocks
result.metrics       # token usage and per-tool call counts
```

`main.py` reads all three. `result.message['role']` is `assistant`, and
`len(result.message['content'])` is how many content blocks that message holds.

### What `stop_reason` tells you

A returned `AgentResult` does not mean a finished task. `stop_reason` is how the loop ended, and
`end_turn`, the value in the expected output above, is the one that means the model finished on its
own.

It is one of twelve values, and the other eleven mean the run stopped for a reason you probably care
about: a budget ran out (`limit_turns`, `limit_total_tokens`, `limit_output_tokens`), a caller
cancelled it (`cancelled`), content was blocked (`content_filtered`). Most of those arrive as an
ordinary return rather than an exception, so code that reads the text without checking the field
will treat a run that stopped early as a run that succeeded.

```python
if result.stop_reason == "end_turn":
    ...
```

For the budget cases in particular, see
[09-limits/01-stop-a-runaway-agent](../../09-limits/01-stop-a-runaway-agent/).

### Confirming the tool ran

`metrics.tool_metrics` is a dictionary keyed by tool name, and each entry counts the calls:

```python
for name, metrics in result.metrics.tool_metrics.items():
    print(f"tool calls  : {name} x{metrics.call_count}")
```

This is the check that matters in this tutorial. Nine words is easy enough that the model might have
counted them itself and happened to be right. Without `tool_metrics` a correct answer and a lucky
guess look identical.

Token usage sits next to it:

```python
usage = result.metrics.accumulated_usage
usage["inputTokens"]
usage["outputTokens"]
```

`accumulated_usage` totals every model call the agent has served, so reusing one agent across
several invocations keeps adding to it rather than resetting.

### Reading the conversation the agent built

`agent.messages` holds every turn the loop produced, including the model's tool request and the
result that was fed back. It is the fastest way to see what the model actually saw, and it persists
on the agent, so a second invocation continues the same conversation.

### Invoking without blocking

`agent(prompt)` blocks until the loop finishes. To handle events as they happen instead, iterate the
async stream:

```python
async for event in agent.stream_async(prompt):
    ...
```

The loop is the same one. Only the delivery of intermediate events changes.

---

## Writing a docstring the model can use

The `@tool` decorator does not just register the function. It builds the tool definition the model
reads, and it builds it out of things you have already written:

```text
the docstring, minus its Args block   ──►  the tool's description
the Args: block                       ──►  each argument's description
the type hints                        ──►  the input schema
```

So the docstring is not documentation for your teammates that the model happens to ignore. It is the
only description the model has when deciding whether this tool is the right one for the request in
front of it. A vague docstring produces a tool that gets called at the wrong times, and the symptom
looks like a model problem rather than a writing problem.

Two things follow in practice. Describe when to use the tool, not only what it does, because the
model is choosing rather than reading reference material. And describe each argument in the `Args:`
block, because an undescribed argument leaves the model guessing what to put there.

---

## Prose answers versus structured output

Everything above returns prose. The model writes a sentence, and your code gets that sentence as
text. That is the right shape when a person reads the answer.

It is the wrong shape when your code does. Parsing a number back out of "There are nine words in
that sentence" is a habit that fails the first time the model phrases it differently. When the
caller needs a typed value, ask for one instead of parsing prose: see
[01-agent/03-structured-output](../03-structured-output/).

---

## Additional resources

- [Quickstart](https://strandsagents.com/docs/user-guide/quickstart/)
- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/)
- [Python Tools](https://strandsagents.com/docs/user-guide/concepts/tools/python-tools/)
- [Amazon Bedrock model provider](https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/)
- [Metrics](https://strandsagents.com/docs/user-guide/observability-evaluation/metrics/)
