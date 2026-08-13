---
name: gridline-webhooks
description: Register a Gridline webhook endpoint, verify signatures, handle approvals and budget events, and rotate the signing secret. Use when asked to receive Gridline events, set up notifications, or debug deliveries that are failing or not arriving.
---

# Webhooks

Cite `references/webhooks-and-events.md`.

## Before registering, say what the secret does

`create_webhook` **prints a signing secret once**, into this conversation and therefore into the
transcript. Offer to have the user run it themselves first. If it does run here, say plainly what is
now in the transcript and that rotating is the fix. The tool always asks before running.

## Registering

```
create_webhook(project, url="https://yours.example/gridline")
subscribe_webhook(project, endpoint=…, events=["approval.required", "budget.exhausted"])
```

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
a pending approval, which needs a `config` credential rather than the route key your application
holds, or `GET /sessions/{id}/messages` for a transcript. The event carries the id to look it up with.
This surprises people, so state it when they ask why a field is missing.

## An event is a state change, not a per-turn record

A surface down for an hour is **two** events — one down, one recovered, each with counts — not four
thousand. Write receivers expecting edges, not a stream.

## Delivery is at-least-once

**The notification is retried; the thing it describes is not.** A duplicate `approval.required` is safe
because approving is idempotent, not because delivery is exactly-once. It is not. Make the receiver
idempotent on the event id.

## Rotation

Two slots. Issue into the free one, move receivers, retire the old. **Retiring the slot your receiver
still verifies with fails every subsequent signature check** — so retire last, not first.

## Testing locally

Requirements are re-checked per delivery, so a `localhost` URL will not work. Use a tunnel to expose a
local receiver, or a request-capture service, and say which. Then `replay_webhooks` to send real past
events at it — remembering the receiver sees them **again**, so anything non-idempotent happens twice.
