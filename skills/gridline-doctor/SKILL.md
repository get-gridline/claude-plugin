---
name: gridline-doctor
description: Diagnose a Gridline setup and report what is broken, half-configured or wired to nothing. Use when something is not working and the cause is unclear, after setting Gridline up, or when asked to check or audit a Gridline configuration. Read-only.
---

# Diagnosing a Gridline setup

Read-only. Change nothing, and finish with a ranked list of fixes — most broken first. If the user
wants something fixed, that is a separate step they ask for.

Cite `gridline-primitives` for any term that needs defining rather than re-explaining it.

## Order, because early failures explain later ones

**1. Connectivity.** `list_projects`. No tools at all, or a 401 → stop here. Tell them to run
`/mcp` to sign in. Everything below would be guesswork.

**2. Who am I.** `GET /auth/whoami`. Report the principal, its capabilities, and whether it is bound
to a project. A missing `config` capability explains every write failure below, so establish it now
rather than reporting fifteen permission errors.

**3. Every project, or the one named.** For each:

- `check(project)` — the validation summary.
- `describe_project(project)` — the inventory.

**4. Then look for these specifically.** Each is a real, common state that produces no error until
something tries to use it:

| Check | Why it matters |
|---|---|
| Agents with no models | Cannot serve a request at all |
| Agents whose chain mixes a `CONTRACT` or `STATE` capability | Refused when applied, so the change never takes effect |
| Harnesses with no surfaces | The agent has no tools; a turn looks fine and does nothing |
| MCP server entries declaring no tools | Same, and easy to miss because the connection exists |
| Connections with no `credential_ref` where one is needed | Resolves to nothing at call time |
| Credentials referenced but not present | The reference is a dangling pointer |
| Credentials present but referenced by nothing | Probably dead; worth confirming before it is carried forward |
| Components in the catalogue wired to nothing | Not a fault — report as informational |
| Tunnels registered but not `usable` | No credential issued, or both slots retired |
| Tunnels usable but with no client report | Nothing is running, or it has not swept yet |
| Webhook endpoints disabled | A 3xx disables them; deliveries are being dropped now |
| Budget ceilings already exceeded | Requests are being refused and it looks like an outage |

**5. Recent traffic.** `reliability_report` and a short `cost_report`. Zero traffic on a setup that
should have some is itself a finding. High `unpriced_attempts`, a rising cache-write count with flat
reads, or a nonzero `tools_degraded` rate all belong in the output.

## Reporting

```
## Blocking — nothing will work until these are fixed
## Broken — this specific thing does not work
## Suspicious — probably wrong, worth a look
## Informational — fine, but you should know
```

Each line: what, where, and the one action that fixes it. If everything passes, say so plainly and
give the traffic summary — "healthy, and here is what it has been doing" is a useful answer.

Never invent a problem to have something to report.
