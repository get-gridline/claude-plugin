# Telemetry and cost

Every attempt is recorded: which agent, which model, which tenant, tokens in and out, cache reads
and writes, cost, latency, and its `request_id`.

## Reports

```
cost_report(project, group_by="tenant",  period="last_7_days")
cost_report(project, group_by="agent")
cost_report(project, group_by="model")
cost_report(project, group_by="session")
reliability_report(project)
```

## Three things reported separately, and why

**Waste is reported alongside the total, not netted off.** Spend on attempts that produced no usable
answer — a hop that failed and fell back, a turn that errored after billing — is a real number you
are paying, and a report that quietly subtracted it would hide the thing most worth fixing.

**`unpriced_attempts` is a visible gap.** When a model's price is unknown, those attempts are
counted and flagged rather than silently valued at zero. A total that looked complete and was not
would be worse than a total that says how much it cannot account for.

**Cache economics are their own line.** A cache write costs more than a plain input token; a cache
read costs much less. Aggregate token counts hide whether caching is working — so reads, writes and
plain input are separate. A rising write count with a flat read count means something is
invalidating your prefix on every turn.

## Failover and one request_id

A failover writes **two attempt rows under one `request_id`**. So:

- "What did this request cost" is the **sum** of its attempts, not the last one.
- The cost of failing over is attributable, which is the point.

## Dead-weight tools

Tools declared in a harness and never called still cost input tokens on every turn. Reports surface
them, because a tool nobody calls is a bill nobody notices.

## Grouping by task

Tasks can be declared but are **not yet a reporting dimension**. Use session metadata for anything
you need to group by today. See `tasks-and-metadata.md`.
