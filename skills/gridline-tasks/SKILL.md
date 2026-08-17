---
name: gridline-tasks
description: Declare a Gridline task with an evaluation, and label sessions with your own metadata dimensions for reporting. Use when asked to track what agents are for, to group sessions by workflow or experiment, or to set up evaluation.
---

# Tasks and metadata

Cite `references/tasks-and-metadata.md`.

## Which one to use

**Session metadata** — your own free-form dimensions, per session. `GET /sessions` filters on one
(`metadata.<key>=<value>`) and `cost_report` groups on one (`by="metadata.<key>"`), so a dimension
you invent is reportable rather than only searchable.

**A task** — a declared unit of work with an `evaluation` describing what a good outcome looks like.
Use it to record what an agent is *for*.

## The gap to be honest about

**Tasks are not a `cost_report` dimension.** It cannot group by task — that is outside the eight
fixed dimensions it offers.

Metadata is different, and this is worth getting right: `cost_report` **can** group by one of your
own metadata keys, written `by="metadata.<key>"`. So the working answer for a task's spend is to put
the same value in session metadata as well and group on that:

```
cost_report(project, by="metadata.task")
```

Say plainly that this reports on the *label you set*, not on the task object — a session that named
the task and not the metadata key is not in it.

## Declaring one

```
create_task(project, task="triage-inbound", evaluation="…")
```

**A create refuses an existing id, and there is no delete.** Session rows carry the task id, so an
upsert would silently repoint months of history at a task nobody meant. `update_task` edits in place;
`archive_task` takes one out of use and keeps its history.

## A task can carry a traffic split

A task is also where a model comparison lives. `create_split` divides that task's traffic across
named **arms**, each an agent-served model with a share:

```
describe_split(project, task="triage-inbound")
create_split(project, task="triage-inbound",
             arms=["incumbent=openai:gpt-5@90", "challenger=anthropic:claude-sonnet-4-5@10"])
```

An arm is `label=provider:model@weight`. **Weights are relative, not percentages** — they need not
add to a hundred, because requiring that turns adding a fourth model into an edit of all four numbers
and the arithmetic slip is silent. `effort` takes one word for every arm, or a list saying something
different per arm in the same order, which is what makes "the same model at two reasoning efforts"
askable.

Four things to say before anybody runs one:

- **It replaces the whole split.** The arms you leave out are the arms you remove, so call
  `describe_split` first when one is already running — a partial write cannot say whether an absent
  arm was removed or merely not mentioned.
- **Assignment is sticky per conversation.** A conversation stays in the arm it started in, so a
  comparison is never corrupted by a session changing model halfway through.
- **Renaming an arm ends the experiment and starts another.** The label is part of what assignment is
  computed from. Its reports will say the same thing, so do not rename one to tidy it up.
- **On a task with no split, every request runs on the configured model of whichever agent serves
  it** — which is what everything does by default. That is not an error state.

To stop a comparison, use `end_split(project, task)`. An empty arm list is refused rather than read as
"paused", precisely so an experiment cannot sit in a shape that still reads as running.

**The arm label records which branch of the experiment a conversation is in, never which model
answered.** Each arm keeps its serving agent's own fallbacks beneath it, so a failover inside an arm
serves a model belonging to no arm — and the label does not move when it does. Read cost and latency
per arm beside the models that actually answered, never as though they were the same fact;
`gridline-cost` is where that report is.

Gridline stamps the label into reserved metadata under `metadata.gridline.arm`, which a caller
structurally cannot set. That is what makes it trustworthy as a grouping, and why you never write it
by hand.

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
