# Agents and hops

An **agent** is an id, a system prompt, and an ordered chain of models. Each entry in the chain is
a **hop**.

```
create_agent(
  id="support-triage",
  system="You triage inbound support email…",
  models=["claude-sonnet-4-5", "gpt-5"],     # ordered: first is preferred
  harness="support-tools",
)
```

Callers name the agent, never a model. That indirection is the product: you repoint a model in
configuration and no application deploys.

## How a hop is chosen

The first hop is tried. If it fails in a way worth retrying — the provider is unavailable, rate
limiting, a timeout, a 5xx — the next hop is tried. A refusal that is *your* fault (a malformed
request, an invalid tool schema) is returned rather than failed over, because the next model would
refuse it identically.

**Every attempt is recorded**, each with its own cost, all joined by one `request_id`. This is why
a fallback's spend is attributable rather than showing up as an unexplained overage.

## What a chain may not mix

See `capabilities-and-parity.md`. The short version: `CONTRACT` and `STATE` capabilities must be
identical on every hop, so extended thinking rules out a cross-vendor fallback.

`explain_agent(project, agent)` prints the resolved chain, what each hop supports, and what a
fallback to it would lose. Read it before shipping a chain — it is cheaper than discovering the
constraint from a validation error.

## Distance

Gridline reports how far a fallback is from the preferred hop — same model elsewhere, same family,
a different family, a different vendor — but does **not** enforce an ordering. You may put a
cheaper distant model ahead of a near one; that is a legitimate cost decision and Gridline reports
it rather than second-guessing it.
