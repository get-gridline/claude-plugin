---
name: gridline-agents
description: Create and validate a Gridline agent and its harness — the models it uses and the tools, memory, skills and sandbox it can reach. Use when adding or changing an agent, wiring up tools or memory, or asking what belongs in a harness.
---

# Authoring an agent and its harness

Cite `gridline-primitives` and `references/harness-and-surfaces.md`.

## Order, and it matters

```
create_connection(id="e2b-prod", component="e2b", credential_ref="vault://…")
create_harness(id="support-tools")
attach_sandbox(harness="support-tools", connection="e2b-prod")
add_mcp_server(harness="support-tools", connection="wiki", tools=["search"])
create_agent(id="support-triage", system="…", models=["claude-sonnet-4-5"], harness="support-tools")
```

A connection first, because a harness names one. A harness before an agent, because the agent names
it. Creating in the wrong order fails on a name that does not exist yet.

## Share a harness rather than duplicating it

Two agents on one harness present the **same tool list**, so they share one cached prefix. Two
near-identical harnesses are two prefixes, each paid for separately, forever.

So when you are about to create a second harness that differs slightly, stop and ask what the
difference is:

- **Whose data / which store** → that is an assignment, passed per session. Not a new harness.
- **A narrower tool list for one turn** → that is a per-request override. Not a new harness.
- **A genuinely different set of surfaces** → fine, a second harness is right.

The first two are the common cases and both are cheaper than a duplicate.

## Finding components

`browse_providers` returns prose about what each is for and when to choose it — written for exactly
the question "which memory provider should I use". Use it rather than guessing from a name. It is
live; prefer it over anything written down.

## Tool lists

Naming a connection is usually the whole action: an E2B connection's tools appear automatically and
should never be typed by hand. **The exception is your own MCP server**, which declares its own —
Gridline cannot know what your wiki exposes.

For a tunnelled server, `show_tunnel` reports what the client actually found. Read the tool list from
there rather than transcribing it: a hand-typed list is wrong the moment the server gains a tool, and
nothing compares the two.

## Validate, and read the explanation

`check(project)` for validity. `explain_agent(project, agent)` for what it will actually do — the
resolved chain, each hop's capabilities, and what a fallback would lose.

## Concurrent edits

Every read-modify-write should send `If-Match` with the revision you read. Without it, two people
adding different agents at the same time silently lose one. A `409` means re-read, re-apply, retry —
never blindly retry, because the write that would be lost is somebody's deliberate change.

## Watch for dead weight

Tools declared and never called still cost input tokens on every single turn. If a harness has
accumulated surfaces nobody uses, that is a recurring bill with a one-line fix.
