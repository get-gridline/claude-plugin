# The Python SDK

```
pip install gridline
```

Needed for tier two. Tier one — pointing your existing client at Gridline — needs nothing installed.

## Shape

```python
import gridline

grid = gridline.connect()                       # GRIDLINE_BASE_URL / GRIDLINE_API_KEY
chat = grid.session(agent="support-triage", subject="user-42",
                    metadata={"workflow": "billing"})

reply = await chat.send("My invoice is wrong")
```

Three steps, and each is a different thing: `connect` is the client, `session` is one conversation,
`send` is one turn. There is no one-shot call that skips the middle — a conversation is the unit
Gridline stores, bills and traces.

**Asynchronous unless you say otherwise.** A turn is almost entirely spent waiting on a model, so
`connect()` returns the awaiting client. `gridline.connect(sync=True)` returns the blocking one and
every other name is identical, so switching between them is adding or deleting `await`.

## What comes back

```python
reply.text                # the answer
reply.model               # which model actually served it
reply.provider            # and whose
reply.session             # the conversation id — joins to the transcript
reply.usage               # tokens, cache included
reply.tool_calls          # what ran, and whether the harness or your own code ran it
reply.stop_reason
reply.degraded            # anything about this turn was less than configured
reply.route_degraded      # a fallback answered
reply.tools_degraded      # fewer tools reached the model than the harness declares
reply.files_degraded      # an attachment did not reach the model that answered
reply.context_compacted   # the conversation was shortened before it went upstream
reply.lost_capabilities   # e.g. prompt caching unavailable on the hop that answered
reply.awaiting_approval   # the turn paused for a person rather than finishing
reply.raw                 # exactly what the provider sent
```

**`degraded` is deliberately not everything.** It covers route, session, tools and files — the ways
a turn came out *less than configured*. `context_compacted` and a pause are the harness working as
configured, so folding them in would make the flag true on most correct turns and teach everyone to
ignore it. Read them beside it, not through it.

**The request id is on the response, not on the reply object.** `X-Request-Id` is what joins a turn to
telemetry and to a trace — see `references/headers.md`. A `GridlineError` carries `.request_id`, so a
turn that failed is traceable too.

## Continuing a conversation

Keep the `chat` object and send again — Gridline supplies the history, so send **one** message rather
than resending the conversation. A second process that never started it resumes by id:

```python
chat = grid.session(agent="support-triage", resume=reply.session)
```

## Approvals

A guarded tool pauses the turn. The decision goes back on the conversation:

```python
answer = await chat.send("close the ledger")
if answer.awaiting_approval:
    answer = await chat.resume({request.id: True for request in answer.approvals})
```

`resume` takes a mapping of call id to a boolean, so a denial is `False` rather than a second method.
Approving is per call, never per tool — "yes to this deletion" rather than "yes to deletions".

The arguments a call is about are fetched with a credential that carries `config`, which is the
control plane rather than this client:

```python
for pending in gridline.control().approvals(session_id):
    print(pending["name"], pending["arguments"])
```

## Configuration is the other plane, and the other key

```python
cp = gridline.control()                          # GRIDLINE_CONTROL_URL / GRIDLINE_CONFIG_KEY
cp.project("acme").apply(reconciler, support_harness)
```

`apply` sends the **whole project in one PUT** — never one write per agent, harness or connection.
Those have an order that has to be right, and making a caller know it is making them do the work this
replaces. It is idempotent, so re-running the same configuration is a no-op. `cp.plan(name, document)`
answers what applying it *would* change and writes nothing, which is what a pull-request check runs.

See `references/environment.md` for why configuration is a different address and a different key from
the request path.

## The environment it reads

Four variables, two planes, and nothing is guessed from another vendor's:

| Variable | Plane |
|---|---|
| `GRIDLINE_BASE_URL` | Where turns go. Optional — the hosted address is the default |
| `GRIDLINE_API_KEY` | The route key `connect()` uses |
| `GRIDLINE_CONTROL_URL` | Where configuration goes. Optional in the same way |
| `GRIDLINE_CONFIG_KEY` | The config key `control()` uses |

An explicit argument beats the variable every time. **The two keys are deliberately separate**: an
application holds the route key and never needs the other, so a leaked route key cannot rewrite which
model serves an agent. Never set one to the value of the other.

Nothing else is read. In particular the SDK never picks up `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` —
a library that silently did would behave differently in two deployments for reasons nobody can see.

## Versioning

Semver, published to PyPI. Pin a minor in production. `reply` gains fields rather than changing them,
so reading an unknown field defensively is worth doing.
