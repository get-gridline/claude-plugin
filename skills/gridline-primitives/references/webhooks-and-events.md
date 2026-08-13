# Webhooks and events

Gridline calls your endpoint when something changes.

## Registering

```
create_webhook(project, url="https://yours.example/gridline")
subscribe_webhook(project, endpoint=…, events=["approval.required", "budget.exhausted"])
```

Requirements, re-checked at **every** delivery rather than only at registration: `https`, port 443,
and a publicly resolvable address. **Redirects are never followed** — a 3xx disables the endpoint,
because a redirect is how a verified destination becomes an unverified one.

## The secret is printed once

`create_webhook` returns a signing secret you will not see again. Verify with:

```python
from gridline import webhooks
event = webhooks.unwrap(headers, body, secret=os.environ["GRIDLINE_WEBHOOK_SECRET"])
```

Two slots, as with tunnels: rotate into the free one, move your receivers, retire the old. Retiring
the one your receiver still verifies with fails every subsequent delivery's signature check.

## What an event body never contains

**No message text, no tool arguments, no tool results.** Not by default and not by opt-in. An
endpoint holds no capability, so it is given nothing that needs one.

To get the content, fetch it with a credential that is allowed to: `gridline.control().approvals(…)`
for a pending approval — a `config` credential, not the route key your application holds — or
`GET /sessions/{id}/messages` for a transcript. The event tells you *that* something happened and
gives you the id to look it up with.

## An event marks a state change, not a property of a turn

A surface being down for an hour is **two** events — one when it went down, one when it recovered,
each carrying counts — not four thousand events, one per affected turn. Build your receiver
expecting edges rather than a stream.

## Delivery is at-least-once

**The notification is retried; the thing it describes is not.** A duplicate `approval.required` is
safe because approving is idempotent — not because delivery is exactly-once. It is not. Make your
receiver idempotent on the event id.

## replay

`replay_webhooks` re-delivers past events. Your receiver sees them again, so anything not
idempotent happens twice. Always confirmed before it runs.
