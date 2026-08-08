---
name: gridline-budgets
description: Set and reason about Gridline spend ceilings — per project, agent or tenant — and what a caller sees when one is hit. Use when asked to cap spend, limit costs, stop runaway usage, or when requests are being refused for budget reasons.
---

# Spend ceilings

Cite `gridline-primitives`.

## The shape

A ceiling has an `amount`, a `scope` and a `period`. Scope is what it applies to — the project, one
agent, one tenant. **`month` means a rolling 30 days**, not a calendar month; say so, because people
assume calendar and then find the reset date is not the 1st.

## Where it lives

There is **no MCP tool for ceilings**. A ceiling is a field on the project document, so it is a
read-modify-write:

1. `GET /projects/{project}` and keep the revision.
2. Edit the budget field.
3. `PUT` with `If-Match` set to the revision you read.

Send `If-Match` even though nothing forces you to. Without it, a concurrent edit silently loses one
of the two changes.

## What a caller sees when a ceiling is hit

The request is **refused**, and the refusal names which scope was hit and what the limit is. This is
important to convey: it is not an error in the caller's code and not an outage, but from the
application's point of view it looks like one unless somebody knew the ceiling existed.

So when setting one, say what will happen at the boundary and ask whether the application handles a
refusal gracefully. A ceiling that silently breaks production at month-end is worse than no ceiling.

## The two events

`budget.warning` and `budget.exceeded`. Subscribe to both — the warning is the one that lets somebody
act before requests start failing. See the webhooks skill.

## Sizing one

Look before guessing: `cost_report(project, by="tenant", days=30)` over a representative period. A
ceiling set from intuition is either so high it never fires or so low it fires on a normal Tuesday.

Mention **waste** when sizing. If a material share of spend is failed attempts, the ceiling should
account for it — it is real money and it counts toward the limit.
