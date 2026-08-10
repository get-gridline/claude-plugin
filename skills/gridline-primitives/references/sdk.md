# The Python SDK

```
pip install gridline
```

Needed for tier two. Tier one — pointing your existing client at Gridline — needs nothing installed.

## Shape

```python
from gridline import Gridline

grid = Gridline(api_key=os.environ["GRIDLINE_API_KEY"], base_url=…)

reply = grid.run(
    agent="support-triage",
    messages=[{"role": "user", "content": "My invoice is wrong"}],
    assignment={"tenant": "acme", "subject": "user-42"},
    metadata={"workflow": "billing"},
)

reply.text                # the answer
reply.model               # which model actually served it
reply.degraded            # a fallback answered
reply.tools_degraded      # fewer tools reached the model than the harness declares
reply.tools_dropped       # which ones
reply.lost_capabilities   # e.g. prompt caching unavailable
reply.request_id          # joins to telemetry and the transcript
reply.session_id          # continue with this
reply.cost                # this turn, across every attempt
```

## Continuing a conversation

Pass `session=reply.session_id`. Send **one** message; Gridline supplies the history. Do not resend
the conversation — that is what the session is for.

## Approvals

```python
reply = grid.run(agent="ops", messages=[…])
if reply.paused:
    for call in grid.approvals(reply.session_id):
        print(call.tool, call.arguments)     # fetched with your credential, not pushed to a webhook
    grid.approve(reply.session_id, call_id=…)
```

Approving is per call, never per tool — "yes to this deletion" rather than "yes to deletions".

## The SDK reads no environment variables

Every setting is an argument. This is deliberate: a library that silently picks up
`ANTHROPIC_API_KEY` from the environment is a library that behaves differently in two deployments
for reasons nobody can see. Pass what you mean.

## Versioning

Semver, published to PyPI. Pin a minor in production. `reply` gains fields rather than changing
them, so reading an unknown field defensively is worth doing.
