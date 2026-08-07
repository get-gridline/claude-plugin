# Telemetry and cost

Every attempt is recorded: which agent, which model, which tenant, tokens in and out, cache reads
and writes, cost, latency, and its `request_id`.

## Reports

```
cost_report(project, group_by="tenant",  period="last_7_days")
cost_report(project, group_by="agent")
cost_report(project, group_by="model")
cost_report(project, group_by="session")
cost_report(project, group_by="workflow")
cost_report(project, group_by="project")   # name several projects to compare them
reliability_report(project)
```

**Rows come back dearest first, and the answer says whether it was cut short.** There is a `limit`,
so `truncated: true` means there was more below the cheapest row you got — which matters for
`group_by="session"`, where a busy month has one row per conversation and every other dimension is
bounded by how many of the thing exist.

**A window can have two ends.** `since` and `until` take instants and `until` is exclusive, so
"the week before last" is askable and two adjacent windows never both count whatever landed on the
boundary between them. The resolved window comes back on the response, so a figure can be labelled
with the period it came from.

**Naming several projects returns `refused` beside the rows.** A project you cannot read is named
rather than dropped, so a total is never quietly three-quarters of what you asked for.

## Three things reported separately, and why

**Waste is reported alongside the total, not netted off.** Spend on attempts that produced no usable
answer — a hop that failed and fell back, a turn that errored after billing — is a real number you
are paying, and a report that quietly subtracted it would hide the thing most worth fixing.

**`unpriced_attempts` is a visible gap.** When a model's price is unknown, those attempts are
counted and flagged rather than silently valued at zero. A total that looked complete and was not
would be worse than a total that says how much it cannot account for.

**And where *nothing* in a group could be priced, `cost_total` is `null` rather than `0`.** Those
are different facts: zero is "this cost nothing", null is "we cannot say what this cost". A row
reading `$0.00` for a month of real traffic is the reading you would act on wrongly, so it is never
what you get. A partly-priced group totals what it knows and reports the rest in
`unpriced_attempts`.

**Cache economics are their own line.** A cache write costs more than a plain input token; a cache
read costs much less. Aggregate token counts hide whether caching is working — so reads, writes and
plain input are separate. A rising write count with a flat read count means something is
invalidating your prefix on every turn.

## Failover and one request_id

A failover writes **two attempt rows under one `request_id`**. So:

- "What did this request cost" is the **sum** of its attempts, not the last one.
- The cost of failing over is attributable, which is the point.

The reliability report gives you two figures for it, and they mean different things:

- **`fallback_cost`** — spend on attempts that were not the first choice. Most of this bought the
  answer you actually got, so it is what failing over *cost*, not what it wasted.
- **`wasted_cost`** — spend on attempts that produced no usable answer at all.

There is deliberately no single number called "the cost of failover", because it would be wrong
whichever of those two it held.

## Dead-weight tools

Tools declared in a harness and never called still cost input tokens on every turn. Reports surface
them, because a tool nobody calls is a bill nobody notices.

## Grouping by task

Tasks can be declared but are **not yet a reporting dimension**. Use session metadata for anything
you need to group by today. See `tasks-and-metadata.md`.
