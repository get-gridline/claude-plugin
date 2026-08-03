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
| PUT | `/projects/{project}/agents/{id}` | config |
| PUT | `/projects/{project}/harnesses/{id}` | config |
| PUT | `/projects/{project}/connections/{id}` | config |
| GET | `/projects/{project}/snapshot` | route — what the data plane reads; ETagged |

**Every read-modify-write should send `If-Match` with the revision you read.** Without it two
concurrent edits silently lose one. A mismatch is `409`; re-read, re-apply, retry.

A revision is a content hash, not a counter — so writing identical content twice is a non-event.

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
