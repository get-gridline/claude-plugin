---
name: gridline-keys
description: Choose the right Gridline credential for a job, manage people and per-project grants, rotate keys, and onboard a teammate. Use for questions about API keys, permissions, capabilities, roles, invitations, seats or 403 errors.
---

# Keys, people and grants

Cite `gridline-primitives`.

## Three kinds of key, and never the same key

| Capability | Who holds it | Can |
|---|---|---|
| `route` | your application | Spend tokens, read the routing table |
| `config` | this plugin, your CI | Edit agents, harnesses, connections |
| `admin` | a person, deliberately | Credentials, webhooks, tunnels, project creation |

The reason they are separate: a `route` key that leaks can spend tokens — bad, bounded, and visible in
telemetry. If that same key could edit routing, whoever held it could repoint a model and read every
prompt. So **never give an application an `admin` key** even though it would work.

Ask for the narrowest credential that does the job. If a 403 appears, the fix is usually a different
key rather than a wider one.

## A person is not a key

A **person** signs in and is authorised by their organisation role — `OWNER`, `ADMIN`, `MEMBER`, and
nothing else — plus per-project **grants**. A **key** is not a person and is never a seat.

Roles are organisation-wide. Per-project access is a grant, which is what makes "developer, but not on
the payroll project" expressible — as a `PRESETS` capability set on a grant rather than a fourth role.

## Scope comes from the credential

A key bound to a project **overrides** any project named in a request rather than being validated
against it. A person has no bound project, so they must name one.

The practical consequence: the safe answer is whatever you get when the caller says nothing. Never
treat a `project` parameter as an access control — it is a filter.

## Onboarding a teammate

1. `invite_member(organisation, email=…, role="MEMBER")`
2. They accept and sign in.
3. Grant per-project access with the capabilities they need.

**An invitation carries no token.** The email notifies; it is not the way in. It is redeemed by
*address*, so an invitation forwarded to somebody else does not let them in. A refused sign-in writes
nothing.

Joining an organisation is invitation-only. `list_invitations` shows what is outstanding;
`revoke_invitation` withdraws one and always asks first.

## Rotation

Issue the new key, deploy it, then retire the old — in that order. Retiring first is an outage.

A key is shown **once**. There is no endpoint that returns key material, so a lost key is rotated
rather than recovered.
