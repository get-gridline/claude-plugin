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

## Traffic splits

A task is also where a model comparison lives. A **traffic split** divides one task's traffic across
named **arms** — `label=provider:model@weight` — so two models are compared on the same real work.
It is bound to the task rather than to an agent, because an agent is a shared persona reused across
many tasks and splitting there would pull every one of them into the experiment.

Weights are relative rather than percentages. Assignment is sticky per conversation. Each arm keeps
its serving agent's own fallbacks beneath it, so entering an experiment never costs the task its
failover — **and therefore a failover inside an arm serves a model belonging to no arm.**

**The arm label records which branch of the experiment a conversation is in, never which model
answered.** Anything reporting cost or latency per arm reads the model off the attempt rather than
off the label; collapse the two and one provider's bad afternoon reads as its arm being slow. The
label is stamped into reserved metadata under `metadata.gridline.arm`, which a caller structurally
cannot set, and renaming an arm ends that experiment and starts another.

## The gap, and what does work

**Tasks are not a `cost_report` dimension.** It groups by tenant, agent, model, session, workflow,
project, parent or stage — never by task.

Metadata is, which is the working answer: put the same value in session metadata too
(`grid.session(agent=..., task="triage-inbound", metadata={"task": "triage-inbound"})`) and group on
it with `cost_report(by="metadata.task")`. That reports on the label you set rather than on the task
object, so a session that named the task and not the metadata key is absent from it — say so rather
than presenting the two as the same number.

## Writing an evaluation worth reading

The point is that somebody — or something — can later judge whether a session succeeded. So write
the criterion, not the intention:

- Poor: *"Handle support email well."*
- Good: *"Routed to the correct queue, and either resolved or escalated within two turns."*

The second can be checked against a transcript. The first cannot.
