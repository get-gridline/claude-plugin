---
name: gridline-tasks
description: Declare a Gridline task with an evaluation, and label sessions with your own metadata dimensions for reporting. Use when asked to track what agents are for, to group sessions by workflow or experiment, or to set up evaluation.
---

# Tasks and metadata

Cite `references/tasks-and-metadata.md`.

## Which one to use

**Session metadata** — your own free-form dimensions, per session. `GET /sessions` can filter on one
(`metadata.<key>=<value>`), but `cost_report` cannot group by it — only by its own eight dimensions
(`references/telemetry-and-cost.md`). Use metadata for filtering a listing, not for a `cost_report`
grouping it does not offer.

**A task** — a declared unit of work with an `evaluation` describing what a good outcome looks like.
Use it to record what an agent is *for*.

## The gap to be honest about

**Tasks are not a `cost_report` dimension.** It cannot group by task, and neither can it group by
metadata — both are outside the eight it offers.

If the user wants a task's spend isolated, tell them to put the same value in session **metadata**
too, then filter `GET /sessions` by it and total what comes back by hand. That is a filter on a
listing, not a report grouping — do not imply a task, or metadata, gives them reporting neither does.

## Declaring one

```
create_task(project, task="triage-inbound", evaluation="…")
```

**A create refuses an existing id, and there is no delete.** Session rows carry the task id, so an
upsert would silently repoint months of history at a task nobody meant. `update_task` edits in place;
`archive_task` takes one out of use and keeps its history.

## Writing an evaluation worth reading

The point is that somebody — or something — can later judge whether a session succeeded. Write the
criterion, not the intention:

- Poor: *"Handle support email well."*
- Good: *"Routed to the correct queue, and either resolved or escalated within two turns."*

The second can be checked against a transcript. The first cannot, and an evaluation nobody can apply
is a field nobody reads.

## Metadata limits

Keys and values are strings and are not interpreted. Keep them low-cardinality if you intend to group
by them — a metadata value that is unique per session is an id, not a dimension, and produces a report
with one row per session.
