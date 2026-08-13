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
browse_models(capability="tools")            # one capability per call, never a list
browse_models(capability="structured_output")
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

## A split is not a route, and this is the thing people get wrong

A **fallback chain** is ordered and conditional: the first hop is preferred, and the next one is
reached only because something failed. A **traffic split** is neither. Its arms are concurrent, each
takes a share of traffic all of the time, and **nothing triggers it** — no failure, no threshold, no
condition. That is why it is called a split rather than a route.

They compose rather than compete, and the shape is the point:

- A split is bound to a **task**, never to an agent — an agent is a shared persona reused across many
  tasks, so splitting there would pull every task it touches into the comparison.
- **Each arm compiles with its serving agent's own fallbacks beneath it.** Entering an experiment
  never costs a task its failover.

So the two questions have two different answers, and a chain answers neither of the split's:

| | Fallback chain | Traffic split |
|---|---|---|
| Bound to | an agent | a task |
| When it acts | on a retryable failure | always, concurrently |
| Chosen by | order | weight |
| Question it answers | what happens when this breaks | which of these is better |

If somebody describes "send 10% to the new model", that is a split and not a chain — a chain with the
new model second sends it 0% until an outage, which is the least representative traffic there is.

See `gridline-tasks` for authoring one and `gridline-cost` for reading its result.

## What to tell the user about the cost

A failover writes **two attempt records under one `request_id`**, so a failed hop's spend is
attributable. Worth saying: a chain that falls back often is a chain quietly costing more than its
first hop suggests, and `cost_report` will show it.

## Validation happens when it is applied, not when you save

A half-finished chain saves fine. It is refused when the configuration is applied to serve requests
— so an invalid chain does not break production, it simply never takes effect. `check(project)` is how to
ask before then.

The refusal names the hop, the capability and its class. If it does not, that is worth reporting.
