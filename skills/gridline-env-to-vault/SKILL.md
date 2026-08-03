---
name: gridline-env-to-vault
description: Turn the provider API keys an application already has into Gridline credentials and connections. Use when setting Gridline up for the first time, when adding a provider, when rotating a key, or when asked to wire a .env, .envrc, docker-compose file, secrets manager or shell environment into Gridline.
---

# From the keys you already have to Gridline credentials

Cite `gridline-primitives` and `references/credentials.md`.

## The rule this whole workflow is built around

**A secret must never appear in a file you write, a command line you show, or this conversation.**
It travels from the environment to the vault inside a single command and is never rendered.

A hook enforces this and will refuse a tool call containing something key-shaped. If you find
yourself wanting to print a value — to check it, to show a mismatch — describe the situation
instead. "The value in `.env` differs from the one in CI" needs no values.

Gridline stores credentials as references and **cannot hand one back**, so no step here needs a
secret written out.

## Flow

**1. Connectivity, then who and where.** `list_projects`, then `GET /auth/whoami`. Confirm an
`admin` capability — credential writes need it, and finding out later means a plan the user approved
that then half-fails. If more than one project exists and the credential is not bound, **ask which**.
Never infer it.

**2. Find the credentials.** Delegate to the `gridline-secret-scout` subagent. It returns variable
**names** and where each was found, never values. Do not do this sweep inline — it reads many files
and only the conclusion matters.

**3. Map names to components.** Ask the live catalogue: `browse_providers` and
`GET /catalogue/components`. Map by what the catalogue says exists, not from a table written here —
a hardcoded mapping is wrong the first time a component is added.

Ambiguity gets a question, never a guess. `OPENAI_API_KEY`, `OPENAI_KEY` and `OPENAI_TOKEN` all
present means somebody has to say which the application actually reads; guessing wrong points a
live agent at the wrong account. Variables Gridline has no component for are **listed and skipped**,
with a note that this is not a mistake — plenty of an app's secrets are nothing to do with Gridline.

**4. Print the plan and ask once.** For every variable: the component, the `vault://…` reference it
will get, whether it is a create or a rotate, and the connection that will name it. One confirmation
for the whole plan, not one per write — a per-item prompt trains people to click through.

Do not show any part of a value, not even the last four characters. The variable name and its source
identify it well enough.

**5. Write.** One `PUT` per reference, reading from the environment in the same command:

```bash
curl -X PUT "$GRIDLINE_URL/projects/$PROJECT/credentials/anthropic-prod" \
  -H "Authorization: Bearer $GRIDLINE_ADMIN_KEY" \
  -H 'content-type: application/json' \
  -d "{\"secret\":\"$ANTHROPIC_API_KEY\"}"
```

Report the returned fingerprint. That is the confirmation, and it is safe to show.

**6. Create or update the connections**, each naming its reference.

**7. Validate**, then **verify for real.** `check(project)` catches configuration mistakes but not a
key that is wrong — a well-formed dead key validates perfectly. So run one real turn through an
agent that uses the connection and read the reply. There is no credential-verify endpoint, so this
is the only honest proof, and it is worth saying so rather than implying `check` proved more than it
did.

## Situations to handle rather than be surprised by

- **Re-runs are safe.** Writing an identical value is refused with `unchanged_secret`. Report that as
  "already correct", not as a failure.
- **Rotation keeps the old value `retiring` for an overlap window**, so in-flight work does not
  break. **Say this before you start**, along with the fact that rolling back means writing the old
  value again — there is no undo. Afterwards is too late to be useful.
- **A variable set in CI but not locally** (or the reverse) is worth flagging: whichever environment
  is missing it will fail at call time, not now.

## Refusals to explain rather than retry

| Code | What it means |
|---|---|
| `sealing_unavailable` | The deployment cannot encrypt at rest, so it refuses to store rather than storing plaintext. Not something to work around |
| `unowned_project` | The project belongs to no organisation, so no owner resolves. Assign it first |
| `not_storable` | This component's address *is* its identity; there is no secret to store |
| `no_plane` | Nothing would ever fetch this credential. Check the component |
