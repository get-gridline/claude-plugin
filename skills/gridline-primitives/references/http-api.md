# HTTP API

Base URL is your Gridline deployment. Auth is `Authorization: Bearer <key>`.

The capability column is what the key or grant must carry. `route`, `config`, `telemetry`, `content`,
`deploy` and `admin` are different keys on purpose — see the keys skill. Wider ones imply narrower:
`admin` implies `deploy`, and `deploy` implies `config`, so a pipeline that applies a project document
does not also need the key that can mint a bearer.

## Projects and configuration

| Method | Path | Capability |
|---|---|---|
| GET | `/projects` | config |
| GET | `/projects/{project}` | config |
| PUT | `/projects/{project}` | **deploy** — the whole-project write |
| POST | `/projects` | admin — key path only; a person uses the organisation route |
| POST | `/organisations/{org}/projects` | admin — creates **and** assigns in one call |
| GET | `/projects/{project}/validate` | config |
| POST | `/projects/{project}/plan` | config — what a document *would* change, writing nothing |
| GET | `/projects/{project}/agents/{id}` | config |
| PUT | `/projects/{project}/agents/{id}` | **admin** |
| GET | `/projects/{project}/harnesses/{id}` | config |
| PUT | `/projects/{project}/harnesses/{id}` | **admin** |
| GET | `/projects/{project}/connections/{id}` | config |
| PUT | `/projects/{project}/connections/{id}` | **admin** |
| GET | `/projects/{project}/snapshot` | route **or** config — the compiled plan your agents route by; read it to see why a turn went where it did |

**Reading is `config`; writing is not.** Every `PUT` here needs more than the key that read it, and
they do not all need the same thing — the whole-project write is `deploy`, and moving a single agent,
harness or connection is `admin`. Issue the narrowest key that does the job and expect a `403` rather
than a partial write if it is too narrow.

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
| PUT | `/projects/{project}/credentials` | admin — the credential is named in the **body**, not the path |
| GET | `/projects/{project}/credentials` | config — what is stored, never what it is |
| DELETE | `/projects/{project}/credentials?ref=…&plane=…` | admin |

**There is no per-credential path segment.** Which credential a write is about is `ref` and `plane`
in the JSON body; the delete names the same two as query parameters, and omitting them is a refusal
rather than a wildcard.

The listing answers per reference: its version, its state, a fingerprint, where it came from, and
when each of those last moved. **No endpoint hands back credential material to a reader.** A
credential leaves Gridline only sealed to the plane that fetched it, which cannot be opened with the
key that asked.

## Sessions

| Method | Path | Capability |
|---|---|---|
| GET | `/sessions?project=…` | content |
| GET | `/sessions/{id}` | content |
| GET | `/sessions/{id}/messages` | content |
| GET | `/sessions/{id}/messages?provider=…` | content — **the provider id** that will receive it, not a flag |
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
| GET | `/tunnels` | route — and only a broker's key, which names its own plane |
| PUT | `/organisations/{org}/tunnels/{tunnel}` | admin |
| POST | `/organisations/{org}/tunnels/{tunnel}/keys` | admin — returns **one credential**, exactly once. The parts are deliberately not returned beside the whole |
| DELETE | `/organisations/{org}/tunnels/{tunnel}/keys/{slot}` | admin |

## Webhooks

| Method | Path | Capability |
|---|---|---|
| POST | `/projects/{project}/webhooks` | admin — returns the signing secret, once |
| GET | `/projects/{project}/webhooks` | config |
| DELETE | `/projects/{project}/webhooks/{endpoint}` | admin |
| POST | `/projects/{project}/webhooks/{endpoint}/replay` | admin |

## Identity and catalogue

| Method | Path | Capability |
|---|---|---|
| GET | `/auth/whoami` | any — the fastest connectivity check |
| GET | `/catalogue/components` | any |
| GET | `/catalogue/offerings` | any — what a provider offers. `?vendor=` and `?capability=` narrow it |
| GET | `/catalogue/surfaces` | any |

## Health

`/health` returns state rather than just liveness — whether auth, the database, telemetry and the
catalogue are each answering, and how large the catalogue is. Read it before believing that a
half-configured deployment is merely slow.

`/readyz` is the proxy's, not the control plane's, and it gates on **credentials as well as
configuration**: a proxy holding a routing plan it has no key to execute is not ready, and a probe
that only asked about configuration would put it into service anyway.
