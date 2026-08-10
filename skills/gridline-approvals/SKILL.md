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

## `default` is what reaches a tool nobody named

Beside `tools` in the same `permissions` block. It applies to tools your own MCP servers offer,
including ones you never declared on the harness — which is what makes it the only way to scope an
agent to part of a server. `default: deny` plus the tools you name `allow` is an allowlist; `default:
ask` stops every tool you have not named for a person. Say nothing and it is `allow`.

**It is never about a memory, sandbox or skills tool.** Those arrive by attaching the surface rather
than by being named, so there is no name for the default to be a rule about, and locking down a server
does not switch off the sandbox attached beside it. Naming one of them explicitly still applies a
policy to it — `{"tools": {"write_memory": "ask"}}` does what it says.

## The shape

```python
reply = grid.run(agent="ops", messages=[…])
if reply.paused:
    for call in grid.approvals(reply.session_id):
        print(call.tool, call.arguments)
    grid.approve(reply.session_id, call_id=call.id)      # or .deny(...)
```

## A colleague can pause too, and the answer names it

An agent with a roster delegates, and a colleague of it can hold a guarded tool. When one stops, its
request arrives on the **coordinator's** reply — that is the response somebody is holding — carrying
the colleague's own session id.

```python
answer = chat.send("audit the ledger")
if answer.awaiting_approval:
    for request in answer.approvals:
        print(request.name, request.session)   # `session` may be a colleague's
    answer = chat.resume({r.id: True for r in answer.approvals})
```

`resume` sends the session back with the decision, so the answer reaches the colleague rather than the
coordinator, which never made that call. The SDK carries it for you.

The colleague then carries on where it stopped, and **the turn holds itself open for it** rather than
ending with it still working — so its answer normally arrives on the reply to the resume. A colleague
doing long work can outlast that wait; when it does, the coordinator is told what is still outstanding
and answers with what it has, and the colleague's answer is delivered into the conversation whenever it
lands. So handle a reply that says work is outstanding, but do not write a polling loop around the
resume: the wait is the platform's job.

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
