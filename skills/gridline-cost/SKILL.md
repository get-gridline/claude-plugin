---
name: gridline-cost
description: Explain Gridline spend — why a period cost what it did, and where the money went by tenant, agent, model or session. Use for questions about cost, spend, billing, budgets being hit, attribution, or why a bill changed.
---

# Explaining Gridline spend

Cite `gridline-primitives` and `references/telemetry-and-cost.md` for the model.

## Start with the shape, not the total

```
cost_report(project, by="tenant", days=30)
cost_report(project, by="agent",  days=7)
cost_report(project, by="model",  days=7)
```

`by` is one of **`tenant`, `agent`, `workflow`, `model`, `session`, `project`, `parent`, `stage`** —
or `metadata.<key>` for one of your own session dimensions. `days` is a whole number of days back
from now, 1 to 365 — there is no named period, so translate "last week" into `days=7` yourself.

The question is almost always "why is this different from what I expected", so lead with the
dimension that answers it — a total on its own explains nothing.

If the period is vague, say what you used. "Last week" is ambiguous and a report labelled with its
actual range is worth the extra line.

## What a team cost is two shapes of this report

```
cost_report(project, by="parent")                  # what each delegating agent's colleagues cost
cost_report(project, by="agent", parent="lead")    # the per-member breakdown inside one team
cost_report(project, by="stage")                   # cost per round of delegation
```

`by="parent"` puts the traffic nothing delegated on its own row, so a team's cost is visible against
the rest rather than mixed into it. `by="stage"` is what makes a fan-out that cost more than the turn
it was serving a row rather than part of a total.

`parent` is the only narrowing this tool takes, and that is deliberate: it is the one that turns a
grouping into the tree.

## What a traffic split cost, which is two reports and not one

A task running a split labels every conversation with the arm it is in, under the reserved key
`metadata.gridline.arm`. So the comparison is a grouping:

```
cost_report(project, by="metadata.gridline.arm", days=14)
```

That answers *what each branch of the experiment cost*. It does **not** answer what each model cost,
and treating it as though it did is the single mistake this report invites.

**The arm label records which branch a conversation is in, never which model answered.** Each arm
keeps its serving agent's own fallbacks beneath it — so a failover inside an arm serves a model
belonging to no arm, and its spend still lands on that arm's row. Collapse the two and one provider's
bad afternoon reads as its arm being slow, which is a conclusion about the wrong thing entirely.

So drill in rather than inferring:

```
cost_report(project, by="model", days=14)
```

and read it beside the per-arm figures. If an arm's row is dominated by a model that is not that
arm's model, the finding is the failover, not the experiment. Say so explicitly — the user is
comparing models and will otherwise attribute a fallback's cost to the challenger.

Two more things worth saying when reporting one:

- **Weights are relative, not percentages**, so an arm's share of traffic is its weight over the sum
  of them. Do not report a weight as a percentage unless they happen to add to a hundred.
- **A renamed arm is a different arm.** Its history does not carry over, so a report spanning a
  rename shows two partial arms rather than one whole one. Check the window against when the split
  was last written before comparing.

`describe_split(project, task)` is where the arms and their shares come from; `gridline-tasks` covers
authoring one and `gridline-routing` covers why a split is not a fallback chain.

## Three things to report and never quietly fold in

**Waste, alongside the total.** Spend on attempts that produced no usable answer. Do not subtract it
— it is money being spent, and usually the most actionable number in the report.

**`unpriced_attempts`, as a visible gap.** Attempts whose model has no known price. Say how many and
that the total excludes them. A total that looked complete and was not is worse than one that admits
what it cannot account for.

**Cache reads, writes and plain input, separately.** A write costs more than plain input; a read
costs much less. Rising writes with flat reads means something invalidates the prefix every turn —
usually a tool list or system prompt that varies per request, or two near-identical harnesses where
one would do. That is a fixable bill.

## Failover cost

A failover writes two attempt records under one `request_id`. So a request's cost is the **sum** of
its attempts. If the fallback rate is material, report what failover cost over the period on its own
line — it is real spend that no provider dashboard will attribute for you.

## Dead-weight tools

Tools declared in a harness and never called still cost input tokens every turn. If reports surface
them, name them: it is a recurring cost with no benefit and a one-line fix.

## Then answer the question

Finish with the specific answer in one or two sentences, and at most three ranked actions. A table
the user has to interpret is not an answer.

Do not recommend a cheaper model without saying what it gives up — check `explain_agent` or
`browse_models` first. A recommendation that breaks tool support to save money is not a saving.

