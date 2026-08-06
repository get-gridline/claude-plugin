---
name: gridline-approvals
description: Require human approval before an agent runs a specific tool, and handle the pause and resume. Use when asked to gate destructive actions, add a human in the loop, or when a session is paused waiting on approval.
---

# Approvals

Cite `references/sdk.md`.

## The policies

Per tool, in the harness:

- **`allow`** — runs.
- **`ask`** — the turn **pauses** and waits for a human.
- **`deny`** — never runs; the model is told it is unavailable.

A tool the catalogue marks `destructive` is **seeded as `ask`**. You can change it, but the default is
the safe one, and if somebody is loosening it that should be a decision rather than a side effect.

## The shape

```python
reply = grid.run(agent="ops", messages=[…])
if reply.paused:
    for call in grid.approvals(reply.session_id):
        print(call.tool, call.arguments)
    grid.approve(reply.session_id, call_id=call.id)      # or .deny(...)
```

## Approving is per call, never per tool

"Yes to *this* deletion", not "yes to deletions". A per-tool approval is a switch somebody flips once
and forgets, which is the thing approvals exist to prevent.

## Where the arguments come from

`grid.approvals(...)` — **fetched with your credential**. They are deliberately **not** in the webhook
body: an endpoint holds no capability, so it is given nothing needing one. The `approval.required`
event tells you *that* a decision is waiting and gives you the session to look it up with.

So a receiver that wants to show a human what is being approved must make that fetch. Say this when
somebody plans to render an approval UI straight from a webhook payload.

## A raw client cannot render a pause

Tier one passthrough has no way to express "the turn stopped, waiting for a person" — it just gets a
response that looks finished. **So an agent reached by a raw client should have no `ask` tools.** If a
migration is in progress, check for this combination explicitly; it is a silent behaviour change.

## Duplicate events are safe

`approval.required` may be delivered more than once. Approving is idempotent, so a duplicate is
harmless — but that is a property of approving, not of delivery. Key your own bookkeeping on the call
id.
