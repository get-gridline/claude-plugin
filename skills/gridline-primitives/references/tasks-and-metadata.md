# Tasks and metadata

Two ways to label a session for later analysis.

## Session metadata

Your own dimensions, attached per session, for grouping in reports:

```python
grid.session(agent="triage", metadata={"workflow": "onboarding", "arm": "b"})
```

Free-form keys and values. Use it for anything you want to slice by that Gridline has no opinion
about — which experiment arm, which internal workflow, which release.

## Tasks

A declared unit of work, with an `evaluation` describing what a good outcome looks like:

```
create_task(project, task="triage-inbound", evaluation="Correct queue, and a reply within one turn.")
```

Tasks are their own thing rather than a key in the project document, so editing one never collides
with a routing change and never blocks a configuration deploy.

**A create refuses an existing id, and there is no delete.** Session rows carry the task id, so an
upsert would silently repoint months of history at a task nobody meant. `archive_task` takes one out
of use and keeps its history; `update_task` edits it in place.

## The gap, and the nearest workaround

**Tasks are not a `cost_report` dimension.** It groups by tenant, agent, model, session, workflow,
project, parent or stage — never by task, so a task's own spend cannot be isolated from that tool.

The nearest working substitute: put the same value in session metadata too
(`grid.session(agent=..., task="triage-inbound", metadata={"task": "triage-inbound"})`), then filter
`GET /sessions` by `metadata.task=triage-inbound` and total the sessions returned by hand. That is a
filter on a listing, not a `cost_report` grouping — do not imply to a user that it produces the same
report.

## Writing an evaluation worth reading

The point is that somebody — or something — can later judge whether a session succeeded. So write
the criterion, not the intention:

- Poor: *"Handle support email well."*
- Good: *"Routed to the correct queue, and either resolved or escalated within two turns."*

The second can be checked against a transcript. The first cannot.
