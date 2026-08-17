---
name: gridline-keys
description: Choose the right Gridline credential for a job, manage people and per-project grants, rotate keys, and onboard a teammate. Use for questions about API keys, permissions, capabilities, roles, invitations, seats or 403 errors.
---

# Keys, people and grants

Cite `gridline-primitives`.

## One key per project, and it does everything in that project

Create a key on a project, give it a label, and that is the whole decision. There are no scopes to
pick and no second secret to put in a codebase: the key sends traffic, reads and edits agents,
harnesses, connections and routing, reads its own transcripts and telemetry, and manages that
project's vaults, tunnels and webhooks. Set it as `GRIDLINE_API_KEY` and the SDK uses it for
everything — sending traffic and changing configuration alike.

**Two things it deliberately cannot do**, and they are about the *account* rather than the project:

| Not the key's | Where it happens instead |
|---|---|
| Billing — subscriptions, checkout, payment details | The dashboard, as an owner or admin |
| Teams — members, invitations, seats | The dashboard, or MCP as somebody signed in |
| Permissions — per-project grants, ownership | The dashboard, as an owner or admin |

Those are acts a person performs where somebody is looking, not things an application does in code,
so an API key is refused at them however wide it is. A 403 there is not a key that needs widening —
there is no wider key.

**What it costs, stated plainly.** One key that does everything has a wider blast radius than a
traffic-only key: whoever holds it can both spend and repoint. That is the trade made for a
credential a developer can actually use, so treat a project key as production-grade — one per
project, held server-side, rotated rather than shared, and never in a browser or a repository.

**The narrow capabilities still exist** — `route`, `config`, `telemetry`, `content`, `deploy`,
`admin` — and a key issued before this change keeps exactly the ones it was given, so nothing already
deployed changed. A grant to a *person* is still a capability set, which is what makes "developer,
but not on the payroll project" expressible. What went away is being asked to choose between them
when creating a key.

A key is also never wider than whoever created it: a colleague who cannot read transcripts issues a
key that cannot either.

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

1. `invite_member(email=…, role="member", organisation=…)` — the role is lower case, and it is
   `member`, `admin` or `owner`. Omit `organisation` when you are in exactly one. **Signed in as
   yourself**: inviting is a team act, so it is refused to a project key.
2. They accept and sign in.
3. Grant per-project access with the capabilities they need — also as yourself, for the same reason.

**An invitation carries no token.** The email notifies; it is not the way in. It is redeemed by
*address*, so an invitation forwarded to somebody else does not let them in. A refused sign-in writes
nothing.

Joining an organisation is invitation-only. `list_invitations` shows what is outstanding;
`revoke_invitation` withdraws one and always asks first.

## Rotation

Issue the new key, deploy it, then retire the old — in that order. Retiring first is an outage.

A key is shown **once**. There is no endpoint that returns key material, so a lost key is rotated
rather than recovered.
