---
name: gridline-trace
description: Follow one Gridline request end to end from its request_id — which model answered, what it cost, whether it failed over, and what the conversation contained. Use to debug a specific request, an unexpected answer, or a cost that looks wrong.
---

# Tracing one request

Cite `gridline-primitives` and `references/telemetry-and-cost.md`.

## Getting the id

`X-Request-Id` on every response, and `reply.request_id` from the SDK. It is also accepted
**inbound** — if the caller sent their own, that is the id, which is what lets their logs and
Gridline's share one.

If the user has no id, do not guess. Ask, and tell them where it is.

## What to read

1. **The attempt records** — every attempt under this id, with model, tokens, cache reads and writes,
   cost, latency, and outcome.
2. **The stored transcript** — `GET /sessions/{id}/messages`, and `?provider=true` for the exact bytes
   the provider saw. When an answer is surprising, the difference between those two views is often
   the answer.

## The thing to get right

**A failover writes two attempt records under one `request_id`.** So:

- Report **every** attempt, in order, each with its own cost and why it failed.
- "The request cost $X" is the **sum**. Quoting only the successful attempt understates it, and that
  is exactly the case somebody is investigating.

## Read the headers before theorising

| Header | What it tells you |
|---|---|
| `X-Gridline-Model` | Which model actually answered — not necessarily the first hop |
| `X-Gridline-Degraded` | A fallback answered, so output may differ |
| `X-Lost-Capabilities` | What that hop could not do |
| `X-Tools-Degraded` | **Fewer tools reached the model than the harness declares** |
| `X-Context-Compacted` | History was shortened for this turn |

## The two explanations people miss

**`tools_degraded`.** If it is set, the model may never have been given the tool you expected it to
call. A turn where no tools arrived looks exactly like a model deciding not to use them — it just
answers and stops. Check this before concluding the model "ignored" a tool.

**Compaction.** If `X-Context-Compacted` is set, the model saw less history than the transcript
contains. The transcript is kept **un-elided**, so a turn that looks like it should have had context
may not have had it. `system` and `tools` are never touched.

## Finish with the sequence

A short ordered account — what was attempted, what happened, what it cost, what the model saw — then
the specific answer. Not a dump of records.
