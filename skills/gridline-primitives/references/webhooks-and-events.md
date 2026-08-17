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

## The secret is generated elsewhere, and shown once there

`create_webhook` registers the endpoint and returns **no signing secret** — no Gridline tool returns
credential material, because a tool's answer is a conversation and a conversation is a transcript.
Generate the secret in the Gridline web dashboard or with `gridline apply` under an admin
credential; it is shown once there and never read back afterwards, in any state. The endpoint
subscribes and queues from the moment it is registered, so nothing is lost while it cannot sign yet.
Verify with:

```python
from gridline import webhooks
event = webhooks.unwrap(headers, body, secret=os.environ["GRIDLINE_WEBHOOK_SECRET"])
```

Two slots, as with tunnels: generate into the free one — the same two places, never from a tool —
move your receivers, then retire the old. Retiring the one your receiver still verifies with fails
every subsequent delivery's signature check.

## What an event body never contains

**No message text, no tool arguments, no tool results.** Not by default and not by opt-in. An
endpoint holds no capability, so it is given nothing that needs one.

To get the content, fetch it with a credential that is allowed to: `gridline.control().approvals(…)`
for a pending approval, or `GET /sessions/{id}/messages` for a transcript. Both are the same read
and both need a **`content`** credential — not the route key your application holds, and not a
`config` one, which reads configuration rather than conversations. The event tells you *that*
something happened and gives you the id to look it up with.

## The catalogue

Every type you can receive, and what each one means. A name is not a definition — read the line
before you subscribe.

| Type | What has happened | On by default |
|---|---|---|
| `approval.required` | A turn paused: a tool needs a person to allow or decline it. Ids and names, never arguments. | yes |
| `approval.resolved` | That pause was answered — which calls were allowed and which declined. | yes |
| `approval.stale` | A pause nobody has answered for longer than the endpoint's `stale_after`. Nothing expires; it is still waiting. Re-announced on a cadence rather than once. | no |
| `session.started` | The first turn of a conversation. | no |
| `session.idle` | A conversation has been quiet for its idle threshold. See below — this is the one most often misread. | yes |
| `turn.failed` | A request whose **final** attempt returned a non-2xx to your application. A fallback that rescued the turn is not one of these. | yes |
| `agent.degraded` | An agent has started losing something across a run of turns — a route, its tools, or a session. Carries how many turns it covers. | yes |
| `agent.recovered` | An agent you were told was degraded has been clean since. | yes |
| `credential.rejected` | A provider answered 401 or 403. Once per provider per day, not per turn. | yes |
| `budget.threshold_reached` | Spend crossed a fraction of a ceiling you configured. The one you can act on before anything breaks. | yes |
| `budget.exhausted` | The ceiling is reached and traffic is being refused. | yes |
| `config.published` | A project's stored configuration changed. A project under active editing produces one per save. | no |
| `subagent.started` | A colleague was created by a coordinating agent. | no |
| `subagent.messaged` | A follow-up was sent to a colleague that already exists. | no |
| `subagent.asked` | A colleague paused for a person — the one in this group that needs a human. | yes |
| `subagent.finished` | A colleague answered. Carries its stop reason, turns and token counts. | yes |
| `subagent.failed` | A colleague stopped without answering: refused, cancelled, or died mid-work. Nothing else tells you this. | yes |
| `webhook.ping` | A test event you asked for. Cannot be subscribed to — see *Proving a new receiver* in the webhooks skill. | n/a |

The five `subagent.*` types are per colleague, never per turn and never per token: a twenty-five
member fan-out is fifty events. `started` and `messaged` are off by default because a coordinator
produces one `started` per colleague immediately followed by the `finished` most receivers actually
want.

### `session.idle` means quiet, and quiet takes a while

**It is not an activity signal and it does not fire the moment your agent stops.** It fires once the
conversation has had no turn for its idle threshold — **30 minutes** by default, and settable per
endpoint, because what "the agent has stopped" means is a fact about your workflow rather than ours.
It is then noticed periodically, so the wait is that threshold plus a short lag on top.

The threshold rides on the event as `idle_after_seconds`, so a receiver never has to assume it.

This is the closest thing to "the agent finished", and there is deliberately no completed-session
event of any spelling: a conversation has no terminal state and can always be continued, so an event
claiming completion would assert something that never happens. The table above is the whole
catalogue — anything not in it is refused when you try to subscribe to it.

A delegated colleague never produces one — its lifecycle is the `subagent.*` types, so a fan-out
does not appear as twenty-five new conversations.

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
