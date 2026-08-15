---
name: gridline-keys
description: Choose the right Gridline credential for a job, manage people and per-project grants, rotate keys, and onboard a teammate. Use for questions about API keys, permissions, capabilities, roles, invitations, seats or 403 errors.
---

# Keys, people and grants

Cite `gridline-primitives`.

## Six capabilities, and never the same key for two jobs

| Capability | Who holds it | Can |
|---|---|---|
| `route` | your application | Spend tokens, read the routing table |
| `config` | this plugin, a pull-request check | **Read** agents, harnesses and connections, and plan a change against them |
| `telemetry` | a dashboard, a cost job | Read costs and reliability |
| `content` | whoever debugs a conversation | Read transcripts — your customers' data |
| `deploy` | your CI | Apply a whole project document. The `.gridline` file's capability |
| `admin` | a person, deliberately | Everything above, plus credentials, webhooks, tunnels, project creation, and editing one agent or harness on its own |

**Reading configuration is `config`; changing it is not.** That trips people up, because `config`
sounds like the key that configures things. It is the key that *reads* configuration and asks what a
change would do — which is exactly what a pull-request check needs and no more.

Wider implies narrower: `admin` implies `deploy`, and `deploy` implies `config`. So a deployment
pipeline gets `deploy` and can replace agents, harnesses and routing from a file on every merge
without also being able to write a provider credential or mint a bearer. **The credential sitting in
every customer's CI should not be the widest one this API issues.**

`deploy` does not buy a connection change. Moving a connection is `admin`, deliberately — a
connection is also written a level up by an organisation-wide addition, so it is not a local file's
to own.

The reason they are separate at all: a `route` key that leaks can spend tokens — bad, bounded, and
visible in telemetry. If that same key could edit routing, whoever held it could repoint a model and
read every prompt. `content` is its own capability for the mirror-image reason: somebody debugging why
an agent routed the way it did needs `config` and `telemetry`, and handing them every conversation the
agent has ever had alongside is a disclosure nobody chose.

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

1. `invite_member(email=…, role="member", organisation=…)` — the role is lower case, and it is
   `member`, `admin` or `owner`. Omit `organisation` when you are in exactly one.
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
