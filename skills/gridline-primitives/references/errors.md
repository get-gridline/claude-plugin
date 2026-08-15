# Errors

Every error names the thing to change. If one does not, report it.

## Configuration, at write or compile time

| Condition | What to do |
|---|---|
| Incompatible group | A chain mixes a `CONTRACT` or `STATE` capability. The message names the hop, the capability and its class. Remove the hop or drop the capability |
| Unknown component | Not in the catalogue. `browse_providers` for the real id |
| Unknown model | `browse_models`; it may be deprecated |
| Missing credential | The connection names a `vault://…` reference that does not exist |
| Name exists | Creates refuse to overwrite. Rename, or edit the existing one |
| `409 Conflict` | Somebody else edited it since you read it. Re-read, re-apply, retry. **Never retried automatically** — the write that would be lost is a human's change |
| `409 would_empty_harness` | A different 409, and retrying never clears it. The harness you are writing reaches for nothing while the stored one reached for something, and a harness is replaced wholesale — so its memory, skills, sandbox, MCP servers and roster would go with the write. If you are editing, `GET` the harness and send it back with your change; if you mean it, repeat the request with `?allow_empty=true` |

## Credentials

`sealing_unavailable` · `unowned_project` · `not_storable` · `no_plane` · `unchanged_secret`
(which means "already correct"). See `credentials.md`.

## At request time

| Status | Meaning |
|---|---|
| 400 | Your request. The next hop would refuse it identically, so it is **not** failed over |
| 401 | Key unknown or revoked |
| 403 | Authenticated, but this key lacks the capability — six exist and the fix is usually a different one rather than a wider one. Reading configuration is `config` and **writing it is not**: a whole project document is `deploy`, one agent, harness or connection is `admin`. Reading a conversation, including the arguments a paused turn is waiting on, is `content`. See the keys skill |
| 404 on a session id | The session is gone from where it was pinned. **Start a new one** — this is the documented recovery, not an error to retry |
| 429 | Rate limited upstream. Failed over if a hop remains |
| 502 | Upstream answered something unusable |
| 503 | Nothing can serve it. For a tunnel this is immediate rather than a timeout |
| 504 | Gridline gave up waiting upstream |

## Tunnel-specific 503s

The message distinguishes them, and they need different fixes:

- *no registered key* → issue a credential
- *no tunnel client is connected* → nothing is running, or it cannot reach the broker
- *did not take the call in time* → a client is running but saturated

## Budget ceilings

A request refused by a ceiling says which scope was hit and what the limit is. It is a refusal, not
an error in your code. See the budgets skill.
