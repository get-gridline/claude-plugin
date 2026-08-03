---
name: gridline-incident
description: Work out what Gridline did during a provider outage or a spike in failures — what failed over, what it cost, and which knob to turn. Use when a provider is down, error rates are up, latency has jumped, or an incident needs explaining.
---

# When a provider is having a bad day

Cite `gridline-primitives` and `references/telemetry-and-cost.md`.

## First, what actually happened

```
reliability_report(project)
cost_report(project, group_by="model", period="today")
```

The reliability report is the shape of the incident: which models failed, how often, with what errors.
The cost report by model shows where traffic actually went — which is how you tell a working failover
from a failing one.

## Then answer the question people really have

**"Did our users see it?"** A failover that worked means requests succeeded on a later hop. Look for
degraded responses rather than failed ones — `X-Gridline-Degraded` set, answers served by hop two.
That is the system working, and it is worth saying so explicitly during an incident.

**"What is it costing us?"** This is the number nobody else's dashboard will show. A failover writes
**two attempt records under one `request_id`** — the failed hop is billed too. So an outage costs
more per successful request than a normal day, and the fallback model may be priced differently
again. Report the failover spend on its own line.

**"What broke that we did not expect?"** Check `tools_degraded` across the period. A provider having
trouble can complete a turn while dropping tools, and that is not visible as an error — the model
simply answers without calling anything.

## Which knob

| Situation | What to do |
|---|---|
| No fallback configured | Add a hop. Check the capability classes first — a chain that will not compile is not a fallback |
| Fallback exists but is not being used | The failures may not be retryable. A 400 is returned rather than failed over, by design |
| Fallback used but output shape changed | A cross-vendor fallback returns that vendor's shape to a raw client. Keep the chain within one vendor, or move to the SDK |
| Thinking agent has no fallback | Expected: extended thinking is `STATE` and cannot cross vendors. The options are a same-vendor fallback or accepting the exposure |
| Ceiling hit during the incident | Failover spend counts toward it. Requests refused for budget look exactly like the outage continuing |
| Latency up, no errors | Check whether a slower fallback is serving. `X-Gridline-Model` on a sample of responses answers it |

## What not to do

Do not recommend removing a capability to widen the fallback pool mid-incident. Dropping structured
output or tools to get more hops changes what the application receives, and that is a second incident
on top of the first. Note it as a follow-up.

## Afterwards

The useful artefacts are: the failover rate over the window, what it cost, whether any turn went
upstream degraded, and whether the chain behaved as configured. Those four make a post-incident note
that is worth writing down.
