# Telemetry and cost

Every attempt is recorded: which agent, which model, which tenant, tokens in and out, cache reads
and writes, cost, latency, and its `request_id`.

## Reports

```
cost_report(project, by="tenant", days=7)
cost_report(project, by="agent")
cost_report(project, by="model")
cost_report(project, by="session")
cost_report(project, by="workflow")
cost_report(project, by="project")             # name several projects to compare them
cost_report(project, by="parent")              # what each delegating agent's colleagues cost
cost_report(project, by="agent", parent="lead")  # the per-member breakdown inside one team
cost_report(project, by="stage")               # cost per round of delegation
reliability_report(project)
```

**The tool takes four arguments and no others: `project`, `by`, `days`, `parent`.** `by` is one of
the eight dimensions above; `days` is a whole number, 1 to 365, counted back from now. There is no
named period — translate "last week" into `days=7` yourself, and say which window you used.

`parent` is the only narrowing, and deliberately so: it is the one that turns a grouping into the
tree. **Every other filter and the two-ended window belong to `GET /telemetry/cost`, not to this
tool** — `since`, `until`, `limit`, `agent`, `model`, `tenant`, `session`, `workflow`, `stage`. They
are for a caller building a page; passing one here is an error rather than a filter.

**Rows come back dearest first, and the answer says whether it was cut short.** `truncated: true`
means there was more below the cheapest row you got — which matters for `by="session"`, where a busy
month has one row per conversation and every other dimension is bounded by how many of the thing
exist. The resolved window comes back on the response, so a figure can be labelled with the period
it came from.

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

`cache_requested` on an attempt says whether that hop asked its provider to cache, which is what
separates **we asked and missed** from **we never asked** — zero cache reads looks the same either
way and the two call for opposite actions. It is `false` on the providers that cache a repeated
prefix without being asked, so it reports whether a marker was placed rather than whether anything
was cached.

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

`by` is one of the eight dimensions above — never `task`. A task's own spend cannot be isolated from
`cost_report` today. See `tasks-and-metadata.md` for the nearest workaround.
