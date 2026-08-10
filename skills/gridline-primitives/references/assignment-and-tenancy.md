# Assignment and tenancy

An **assignment** is which store and whose data a session uses. It sits *beside* the harness, never
inside it, and is chosen per session.

```
grid.session(agent="support-triage", assignment={"tenant": "acme", "subject": "user-42"})
```

## Why it is not in the harness

The harness is what gets cached. Fold a tenant into it and one agent serving five hundred
customers becomes five hundred harnesses, five hundred cached prefixes, and five hundred times the
prompt cost — making the most common variation in your product the most expensive one.

A store id and a subject are also invisible to the model. They decide where memory reads and writes
go; they are not part of what the model sees, so they have no business in the thing that describes
what the model sees.

## What it gives you

- **Isolation.** Memory reads and writes are scoped to the tenant. One customer's agent cannot
  recall another's conversation.
- **Attribution.** Cost reports group by tenant, so "what does this customer cost us" is a query
  rather than a project.
- **One configuration.** Onboarding a customer is a new assignment value, not new configuration.

## Tenant vs subject

- **`tenant`** — the customer, workspace or organisation. The isolation boundary and the cost
  dimension.
- **`subject`** — the individual within it. Finer-grained memory scoping.

Both are your identifiers; Gridline stores and groups by them without interpreting them.

## Sessions and metadata

An assignment is *structural* — it decides isolation. Session **metadata** is descriptive: your own
dimensions for reporting. Use metadata for "which A/B arm", "which workflow"; use an assignment for
"whose data". See `tasks-and-metadata.md`.
