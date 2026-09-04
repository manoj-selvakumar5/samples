Part II - Control the loop

# Stop reasons

Every way the agent loop can end, and how to tell them apart.

`stop_reason` is a twelve-value union. Almost every Part II feature produces one of these values,
and this is the only place they are shown as a set.

## Teaches

| Symbol | Import path |
|--------|-------------|
| `StopReason` | `strands.types.event_loop.StopReason` |
| `AgentResult.stop_reason` | returned by every invoke path |
| `MaxTokensReachedException` | `strands.types.exceptions.MaxTokensReachedException` |

## Prerequisites

- Python 3.10 or later
- AWS credentials configured, and model access enabled in Amazon Bedrock

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Output

```
  plain question         -> end_turn             OK
  structured output      -> tool_use             OK
  model max_tokens=16    -> raised MaxTokensReachedException
  stop_sequences=['4']   -> stop_sequence        OK
  limits turns=3         -> limit_turns          OK
  limits total_tokens=2000 -> limit_total_tokens   OK
  limits output_tokens=64 -> limit_output_tokens  OK

--- Coverage: 7 of 12 ---
  [not here]     cancelled              agent.cancel()
  [not here]     checkpoint             checkpointing=True
  [not here]     content_filtered       provider-side content filtering
  [demonstrated] end_turn               model finished on its own
  [not here]     guardrail_intervened   Amazon Bedrock Guardrails
  [not here]     interrupt              an intervention raising an interrupt
  [demonstrated] limit_output_tokens    the output_tokens cap in `limits`
  [demonstrated] limit_total_tokens     the total_tokens cap in `limits`
  [demonstrated] limit_turns            the turns cap in `limits`
  [demonstrated] max_tokens             provider output ceiling, raised as an exception
  [demonstrated] stop_sequence          model emitted a configured stop string
  [demonstrated] tool_use               loop ended on a tool call, including structured output
```

The script derives its own coverage report from `typing.get_args(StopReason)`, so if the SDK adds a
thirteenth value the run reports it as uncovered rather than silently ignoring it.

## All twelve values

| Value | Meaning | Where it comes from |
|-------|---------|---------------------|
| `end_turn` | The model finished on its own | normal completion |
| `tool_use` | The loop ended on a tool call, including structured output | [`01-agent/03-structured-output`](../../01-agent/03-structured-output/) |
| `stop_sequence` | The model emitted a configured stop string | model config |
| `max_tokens` | Provider output ceiling hit. **Raised, not returned** | model config |
| `limit_turns` | The `turns` cap tripped | [`01-execution-limits`](../01-execution-limits/) |
| `limit_total_tokens` | The `total_tokens` cap tripped | [`01-execution-limits`](../01-execution-limits/) |
| `limit_output_tokens` | The `output_tokens` cap tripped | [`01-execution-limits`](../01-execution-limits/) |
| `cancelled` | `agent.cancel()` was called | a later `09-limits/` leaf |
| `checkpoint` | The run paused at a checkpoint | a later `10-sessions/` leaf |
| `interrupt` | An intervention raised an interrupt | a later `07-interventions/` leaf |
| `guardrail_intervened` | Amazon Bedrock Guardrails blocked the content | a later `09-limits/` leaf |
| `content_filtered` | The provider filtered the content | provider-side |

Five of these are not demonstrated here, because the areas that produce them are not built yet.
The script says so at runtime rather than quietly covering seven and implying twelve.

## Note the following

- **`max_tokens` is the exception to the pattern, literally.** It does not come back as a
  `stop_reason`. The loop raises `MaxTokensReachedException`, because a truncated message is not
  something you should be able to mistake for an answer by forgetting to check a field. The partial
  message is still appended to the conversation, so you can raise the ceiling and reinvoke.
- **`tool_use` does not mean something went wrong.** A successful structured-output call reports
  `tool_use`, not `end_turn`. Code that treats `end_turn` as the only success value will
  misclassify every structured response.
- **Checking `stop_reason` is not optional.** Apart from `max_tokens`, none of these raise. An
  invocation that hit a cap returns an ordinary `AgentResult`, so ignoring the field means treating
  a truncated run as a finished one.
- **`stop_sequence` fires on the string appearing in output**, so the sequence is consumed and the
  visible answer stops just before it. In the run above, `stop_sequences=["4"]` yields `1 2 3`.

## Variations

- **Branch on the value** rather than testing equality with `end_turn`, for example treating any
  `limit_*` value as retryable with a larger budget and `guardrail_intervened` as terminal.
- **Assert coverage in a test** with `typing.get_args(StopReason)`, so an SDK upgrade that adds a
  value fails loudly instead of falling through a handler.
- **Catch `MaxTokensReachedException` and reinvoke** after raising `max_tokens` on the model, since
  the partial message is preserved in the conversation.

## See also

- [`09-limits/01-execution-limits`](../01-execution-limits/) for the three `limit_*` values.
- [`01-agent/03-structured-output`](../../01-agent/03-structured-output/) for why `tool_use` shows up on success.

Verified against strands-agents 1.54.0 on 2026-09-03
