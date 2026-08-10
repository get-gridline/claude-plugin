# HTTP API

Base URL is your Gridline deployment. Auth is `Authorization: Bearer <key>`.

The capability column is what the key or grant must carry. `route`, `config` and `admin` are
different keys on purpose — see the keys skill.

## Projects and configuration

| Method | Path | Capability |
|---|---|---|
| GET | `/projects` | config |
| GET | `/projects/{project}` | config |
| PUT | `/projects/{project}` | config |
| POST | `/projects` | admin — key path only; a person uses the organisation route |
| POST | `/organisations/{org}/projects` | admin — creates **and** assigns in one call |
| GET | `/projects/{project}/validate` | config |
| GET | `/projects/{project}/agents/{id}` | config |
| PUT | `/projects/{project}/agents/{id}` | config |
| GET | `/projects/{project}/harnesses/{id}` | config |
| PUT | `/projects/{project}/harnesses/{id}` | config |
| GET | `/projects/{project}/connections/{id}` | config |
| PUT | `/projects/{project}/connections/{id}` | config |
| GET | `/projects/{project}/snapshot` | route **or** config — the compiled plan your agents route by; read it to see why a turn went where it did |

Each `GET` above answers in the shape the `PUT` beside it takes, so read-modify-write round-trips: read
one, change a field, send it back. Their `ETag` is the *project's* revision — one document per project,
so an edit to any part of it moves them all.

**Every read-modify-write should send `If-Match` with the revision you read.** Without it two
concurrent edits silently lose one. A mismatch is `409`; re-read, re-apply, retry.

A revision is a content hash, not a counter — so writing identical content twice is a non-event.

**A sub-resource `PUT` replaces wholesale, so send the whole document.** A partial list cannot say
whether an absent entry was removed or simply not mentioned. On a harness this has a guard: a write
that would leave one reaching for nothing, where the stored one reached for something, is refused
`409 would_empty_harness` unless the request carries `?allow_empty=true` — a query parameter rather
than a body field, so that `GET` then `PUT` stays a no-op. Removing one surface of several says
nothing, and filling in a harness you have just created is untouched.

## Credentials

| Method | Path | Capability |
|---|---|---|
| PUT | `/projects/{project}/credentials/{name}` | admin |
| GET | `/projects/{project}/credentials` | admin — names and fingerprints only |
| DELETE | `/projects/{project}/credentials/{name}` | admin |

No endpoint returns credential material. Ever.

## Sessions

| Method | Path | Capability |
|---|---|---|
| GET | `/sessions?project=…` | content |
| GET | `/sessions/{id}` | content |
| GET | `/sessions/{id}/messages` | content |
| GET | `/sessions/{id}/messages?provider=true` | content |
| GET | `/sessions/{id}/messages?resuming=true` | content |

`project` is a filter for an unbound credential. **A bound key overrides it** rather than being
validated against it, so the safe answer is what you get when you say nothing.

## Telemetry

| Method | Path | Capability |
|---|---|---|
| GET | `/telemetry/cost` | telemetry |
| GET | `/telemetry/reliability` | telemetry |

## Tunnels

| Method | Path | Capability |
|---|---|---|
| GET | `/tunnels` | tunnel — the broker's own |
| PUT | `/organisations/{org}/tunnels/{tunnel}` | admin |
| POST | `/organisations/{org}/tunnels/{tunnel}/keys` | admin — returns **both** secrets, once |
| DELETE | `/organisations/{org}/tunnels/{tunnel}/keys/{slot}` | admin |

## Webhooks

| Method | Path | Capability |
|---|---|---|
| POST | `/projects/{project}/webhooks` | admin — returns the signing secret, once |
| GET | `/projects/{project}/webhooks` | admin |
| DELETE | `/projects/{project}/webhooks/{endpoint}` | admin |
| POST | `/projects/{project}/webhooks/{endpoint}/replay` | admin |

## Identity and catalogue

| Method | Path | Capability |
|---|---|---|
| GET | `/auth/whoami` | any — the fastest connectivity check |
| GET | `/catalogue/components` | any |
| GET | `/catalogue/models` | any |
| GET | `/catalogue/surfaces` | any |

## Health

`/health` returns state — auth, telemetry, config version — rather than just liveness. `/readyz`
gates on configuration **and** credentials.
