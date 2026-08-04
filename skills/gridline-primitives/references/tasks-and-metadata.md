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
create_task(project, id="triage-inbound", evaluation="Correct queue, and a reply within one turn.")
```

Tasks are their own thing rather than a key in the project document, so editing one never collides
with a routing change and never blocks a configuration deploy.

**A create refuses an existing id, and there is no delete.** Session rows carry the task id, so an
upsert would silently repoint months of history at a task nobody meant. `archive_task` takes one out
of use and keeps its history; `update_task` edits it in place.

## The honest gap

**Tasks are declarable but not yet a reporting dimension.** `cost_report` cannot group by task
today. If you need grouping now, put the same value in session metadata as well — it costs one field
and means the data exists when reporting catches up.

## Writing an evaluation worth reading

The point is that somebody — or something — can later judge whether a session succeeded. So write
the criterion, not the intention:

- Poor: *"Handle support email well."*
- Good: *"Routed to the correct queue, and either resolved or escalated within two turns."*

The second can be checked against a transcript. The first cannot.
