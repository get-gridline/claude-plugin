---
name: gridline-routing
description: Author a Gridline fallback chain that will actually validate, and understand what a fallback gives up. Use when designing routing, adding a fallback model, choosing hop order, or when a chain is refused as incompatible.
---

# Authoring a fallback chain

Cite `gridline-primitives` and `references/capabilities-and-parity.md`.

## The rule that decides everything

`CONTRACT` capabilities must be **identical on every hop**. `STATE` is refused across vendors unless
the fallback explicitly accepts losing it. `ADDITIVE` ones may vary and their loss is recorded.

So before proposing a chain, ask what the agent needs:

- **Tools, streaming or structured output?** Every hop must have it. No opt-in, no exceptions — a
  hop without one breaks the caller's code rather than giving a worse answer.
- **Extended thinking?** Within one vendor you get thinking and a fallback with nothing given up.
  Across vendors, pick one: keep the chain inside a vendor, `disable: ["thinking_blocks"]` so
  nothing is ever produced, or `allow_state_loss: true` on the fallback so it takes the turn
  without the reasoning. The third is the right answer when an outage with a worse answer beats an
  outage with no answer — say plainly that the conversation cannot be natively resumed afterwards.
- **Prompt caching?** May vary. Losing it costs money, not correctness.

## Then check rather than assume

```
browse_models(capabilities=["tools", "structured_output"])
explain_agent(project, agent)
```

`explain_agent` prints the resolved chain, what each hop supports, and what falling back to it would
lose. Read it before shipping — cheaper than a validation error, and much cheaper than discovering it
during an outage.

## Hop order

First hop is preferred; the rest are tried in order on a retryable failure. A refusal that is the
caller's fault — a malformed request, a bad tool schema — is **returned rather than failed over**,
because the next model would refuse it identically.

Gridline reports how *far* each fallback is from the preferred hop (same model elsewhere, same
family, different family, different vendor) but **does not enforce an ordering**. Putting a cheaper
distant model ahead of a nearer one is a legitimate cost decision, and Gridline reports it rather
than second-guessing you.

## What to tell the user about the cost

A failover writes **two attempt records under one `request_id`**, so a failed hop's spend is
attributable. Worth saying: a chain that falls back often is a chain quietly costing more than its
first hop suggests, and `cost_report` will show it.

## Validation happens when it is applied, not when you save

A half-finished chain saves fine. It is refused when the configuration is applied to serve requests
— so an invalid chain does not break production, it simply never takes effect. `check(project)` is how to
ask before then.

The refusal names the hop, the capability and its class. If it does not, that is worth reporting.
