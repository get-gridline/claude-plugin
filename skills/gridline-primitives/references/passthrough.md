# Passthrough — tier one

Keep the client you already have. Change its base URL and name an agent instead of a model.

## Anthropic

```python
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["GRIDLINE_API_KEY"],            # your Gridline key, not Anthropic's
    base_url=os.environ.get("LLM_BASE_URL", "https://api.anthropic.com"),
)

response = client.messages.create(
    model="support-triage",                            # an AGENT id, not a model
    messages=[{"role": "user", "content": "…"}],
    max_tokens=1024,
)
```

## OpenAI

```python
client = OpenAI(
    api_key=os.environ["GRIDLINE_API_KEY"],
    base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
)
response = client.chat.completions.create(model="support-triage", messages=[…])
```

## Keep the base URL in a variable

Then reverting is a redeploy with one variable changed, not a rollback. Do this even if you are
confident — it is the difference between an incident lasting a minute and lasting as long as a
release takes.

## What you get for that alone

Routing and failover, cost attribution by tenant/agent/model/session, transcripts, spend ceilings,
and the degradation headers. No new dependency, no change to how you parse a response.

## What tier one cannot do

- **Approvals.** A raw client has no way to render a pause, so an `ask` policy breaks it. Agents
  reached this way should have no `ask` tools.
- **One reply shape across vendors.** A cross-vendor fallback returns *that vendor's* shape, so your
  parser sees something new exactly when a provider is down. Either keep the chain within one
  vendor, or move to the SDK.
- **Streaming with proxy-run tools.** A turn where Gridline runs the tool loop cannot stream.

## Labelling a tier-one request

The provider's own request body has no field for any of this, so it goes in headers:

```
X-Workflow: billing
X-Run-Id: nightly-close-2026-08-13
X-Request-Id: your-own-trace-id
```

`X-Workflow` is the reporting dimension — `cost_report(by="workflow")` groups on it. `X-Run-Id` ties
every turn of one batch together. `X-Request-Id` is yours if you send one, so your logs and
Gridline's share an id; Gridline mints one otherwise.

**The tenant is not a header you set.** A key bound to a tenant decides which customer a request acts
as, and it wins over anything the caller asks for — an unauthenticated tenant claim would make
per-customer cost and per-customer transcripts only as trustworthy as the callers. Issue a key per
customer and the attribution follows.

**There is no tier-one way to send session metadata or a subject.** Those are session-level and tier
one has no session object to hang them on. If a report needs to slice by something `X-Workflow`
cannot express, that is a reason to move to the SDK.
