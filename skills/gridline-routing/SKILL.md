---
name: gridline-routing
description: Author a Gridline fallback chain that will actually validate, and understand what a fallback gives up. Use when designing routing, adding a fallback model, choosing hop order, or when a chain is refused as incompatible.
---

# Authoring a fallback chain

Cite `gridline-primitives` and `references/capabilities-and-parity.md`.

## The rule that decides everything

`CONTRACT` and `STATE` capabilities must be **identical on every hop**. `ADDITIVE` ones may vary and
their loss is recorded.

So before proposing a chain, ask what the agent needs:

- **Tools, streaming or structured output?** Every hop must have it.
- **Extended thinking?** Then **no cross-vendor fallback** — thinking blocks and reasoning items are
  different state formats. Within one vendor you can have both.
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

## Validation happens at compile, not at save

A half-finished chain saves fine. It is refused when a snapshot is compiled for the data plane — so
an invalid chain does not break production, it simply never reaches it. `check(project)` is how to
ask before then.

The refusal names the hop, the capability and its class. If it does not, that is worth reporting.
