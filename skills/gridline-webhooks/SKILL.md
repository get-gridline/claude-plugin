---
name: gridline-webhooks
description: Register a Gridline webhook endpoint, verify signatures, handle approvals and budget events, and rotate the signing secret. Use when asked to receive Gridline events, set up notifications, or debug deliveries that are failing or not arriving.
---

# Webhooks

Cite `references/webhooks-and-events.md`.

## Registering is one act; generating the signing secret is another

**No Gridline tool returns credential material**, so `create_webhook` registers the endpoint and
issues no signing secret at all. A tool's answer is a conversation, and a conversation is a
transcript, a scrollback and sometimes a screenshot — and a signing secret does not read the user's
data, it forges events into their own systems.

So say this before registering, because the endpoint delivers nothing until the second act happens:
the secret is generated in the **Gridline web dashboard**, or by `gridline apply` under an admin
credential, and is shown once in either. Nothing is lost meanwhile — the endpoint subscribes and
queues from the moment it exists, and what accumulated goes out once it can sign.

`create_webhook` still always asks before running: it arranges for a permanent copy of the project's
operational events to be sent to an address, which is a data-egress decision.

```
create_webhook(project, url="https://yours.example/gridline")
subscribe_webhook(project, endpoint=…, events=["approval.required", "budget.exhausted"])
```

`list_webhooks` shows each endpoint's slots as fingerprints, and says **NOT YET SIGNING** for one
that has no secret yet — which is the first thing to check when a registered endpoint delivers
nothing.

Requirements, **re-checked at every delivery** and not only at registration: `https`, port 443, a
publicly resolvable address. **Redirects are never followed — a 3xx disables the endpoint**, because a
redirect is how a verified destination silently becomes an unverified one. If deliveries stopped, check
this first: a reverse proxy that started redirecting will do it.

## Verifying

```python
from gridline import webhooks
event = webhooks.unwrap(headers, body, secret=os.environ["GRIDLINE_WEBHOOK_SECRET"])
```

Verify before parsing. An unverified body is somebody else's input.

## What the body never contains

**No message text, no tool arguments, no tool results.** Not by default, not by opt-in. An endpoint
holds no capability, so it is given nothing needing one.

To get content, fetch it with a credential allowed to have it — `gridline.control().approvals(…)` for
a pending approval, or `GET /sessions/{id}/messages` for a transcript. Both are the same read and
both need a **`content`** credential, not the route key your application holds and not a `config` one.
The event carries the id to look it up with.
This surprises people, so state it when they ask why a field is missing.

## An event is a state change, not a per-turn record

A surface down for an hour is **two** events — one down, one recovered, each with counts — not four
thousand. Write receivers expecting edges, not a stream.

## Delivery is at-least-once

**The notification is retried; the thing it describes is not.** A duplicate `approval.required` is safe
because approving is idempotent, not because delivery is exactly-once. It is not. Make the receiver
idempotent on the event id.

## Rotation

Two slots. Generate into the free one — dashboard or `gridline apply`, the same two places, never
from here — move receivers, then `retire_webhook_secret` on the old one. **Retiring the slot your
receiver still verifies with fails every subsequent signature check**, so retire last, not first.
Retiring is offered as a tool because a slot number is not a secret.

## Testing locally

Requirements are re-checked per delivery, so a `localhost` URL will not work. Use a tunnel to expose a
local receiver, or a request-capture service, and say which. Then `replay_webhooks` to send real past
events at it — remembering the receiver sees them **again**, so anything non-idempotent happens twice.
