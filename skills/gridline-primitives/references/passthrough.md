# Passthrough — tier one

Keep the client you already have. Change its base URL and name an agent instead of a model.

## Anthropic

```python
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["GRIDLINE_ROUTE_KEY"],          # your Gridline key, not Anthropic's
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
    api_key=os.environ["GRIDLINE_ROUTE_KEY"],
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

## Passing an assignment and metadata

Use headers, since the provider's own request body has no field for them:

```
X-Gridline-Tenant: acme
X-Gridline-Subject: user-42
X-Gridline-Metadata: {"workflow":"billing"}
```
