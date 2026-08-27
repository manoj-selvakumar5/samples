# Strands features

One runnable script per Strands Agents feature. Every example is a complete program you run with
`python main.py`, not a snippet with the setup elided.

Each leaf folder holds exactly three files: `main.py`, `README.md`, and a pinned
`requirements.txt`. Areas are named after the SDK module they teach.

> This track is being built area by area. The areas below are the ones available today.

## Part I - Build the agent

What the agent is, and what it can do.

| Area | Leaves |
|------|--------|
| [`01-agent/`](./01-agent/) | [`01-first-agent`](./01-agent/01-first-agent/), [`03-structured-output`](./01-agent/03-structured-output/) |

## Part II - Control the loop

The agent runs correctly without these. You add them because you do not trust it.

| Area | Leaves |
|------|--------|
| [`07-interventions/`](./07-interventions/) | [`01-intervention-basics`](./07-interventions/01-intervention-basics/), [`03-human-in-the-loop`](./07-interventions/03-human-in-the-loop/) |
| [`09-limits/`](./09-limits/) | [`01-execution-limits`](./09-limits/01-execution-limits/), [`02-stop-reasons`](./09-limits/02-stop-reasons/) |

### I want to restrict...

| ...what? | Use | Where |
|----------|-----|-------|
| **whether** a step runs at all | `InterventionHandler` returning `Deny`, `Confirm`, `Transform`, or `Guide` | [`07-interventions/`](./07-interventions/) |
| **how much** it does | `Limits` for turns, output tokens, total tokens | [`09-limits/01-execution-limits`](./09-limits/01-execution-limits/) |
| **how** a run ended | `stop_reason` on the result | [`09-limits/02-stop-reasons`](./09-limits/02-stop-reasons/) |

## Getting started

```bash
cd 01-agent/01-first-agent
pip install -r requirements.txt
python main.py
```

You need Python 3.10 or later, AWS credentials, and model access enabled in Amazon Bedrock. No leaf
outside a provider-specific area configures a model, so every example runs on the SDK default.

## Conventions

- **Numbers are positions, not a sequence.** Gaps are expected at both levels and are not missing
  content. Area numbers are slots in the full planned order, so `01-agent/` is followed today by
  `07-interventions/` because areas 02 through 06 are not built yet. Leaf numbers work the same way
  within an area. The tables above are the authority on reading order.
- **Numbers are assigned once and not reused.** A new area takes its reserved slot rather than
  pushing its neighbours along, so a published path never changes meaning.
- **Each leaf teaches one concept** and keeps `main.py` under 150 lines.
- **Each leaf README lists the symbols it teaches**, and carries the SDK version it was verified
  against.
- **Output shown in a leaf README is real**, captured from an actual run.
- **Requirements track the latest SDK**, not a frozen version. Each leaf declares a floor it is
  known to need and an upper bound at the next major version, so `pip install -r requirements.txt`
  gives you current Strands Agents rather than a stale pin. The `Verified against` line at the
  bottom of each leaf README records the version the pasted output came from, so you can tell
  whether your run is expected to match it exactly.
