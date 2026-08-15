# Response headers

How you tell what actually happened. The first group is on every response; the rest are set only
when they have something to say, so an absent header means the ordinary case.

| Header | Always | Meaning |
|---|---|---|
| `X-Request-Id` | yes | Joins this response to its attempt records and its transcript. Also accepted **inbound** — send your own and it is used, so your logs and Gridline's share an id |
| `X-Session-Id` | yes | The conversation this turn belongs to |
| `X-Route-Model` | yes | Which model actually answered — not necessarily the first hop |
| `X-Route-Provider` | yes | And whose |
| `X-Route-Position` | yes | Which hop of the chain that was. Anything but the first means a fallback took the turn |
| `X-Config-Version` | yes | Which configuration served it, so "we changed something at 14:00" is checkable |
| `X-Route-Degraded` | no | A fallback answered, so output may differ from the preferred model |
| `X-Route-Lost` | no | Capabilities unavailable on the hop that answered, comma-separated (e.g. prompt caching) |
| `X-Tools-Degraded` | no | **The turn went upstream with fewer tools than the harness declares** |
| `X-Session-Degraded` | no | The conversation could not be read or written as configured |
| `X-Context-Compacted` | no | History was shortened for this turn. The transcript keeps it in full |
| `X-Files-Degraded` | no | An attachment did not reach the model that answered |
| `X-Files-In-Sandbox` | no | How many attachments reached the agent through its sandbox instead of inline |
| `X-Approval-Required` | no | Call ids this turn is waiting on a person for. Ids only — a header is no place for your tool arguments |
| `X-Loop-Exhausted` | no | The turn hit its tool-iteration limit and answered with what it had |
| `X-Refusal-Reason` | no | Why a request was refused, when it was |

## Inbound, on a tier-one request

`X-Request-Id` (above), plus `X-Workflow` and `X-Run-Id` as reporting labels, and `X-Tenant` — which
a key bound to a tenant overrides, so attribution does not depend on callers being honest. See
`references/passthrough.md`.

## Why X-Tools-Degraded deserves an alert

Without it, a turn that reached the provider with **no tools at all** is indistinguishable from a
model that considered its tools and chose not to use one. Both look like a plain answer ending
normally. It is set for *any* loss, not only total loss.

**It does not name what was lost, and neither does the reply.** The signal is that the turn was
short of tools; which ones is a question for the attempt records under this `X-Request-Id`. If you
wire one Gridline signal to an alert, this is the one.

## X-Route-Degraded vs X-Route-Lost

`Degraded` is about *which model*. `Lost` is about *what that model could not do*. A failover to an
equally capable model is degraded with nothing lost; a preferred model without cache support is not
degraded but has lost something. They answer different questions, and a receiver that reads only one
of them is answering the other by accident.

## `X-Gridline-*` is a different direction

Headers spelled `X-Gridline-Agent-Id` and `X-Gridline-Model` exist, and they are **not** on the
reply to your call — they are what Gridline sends *to your own MCP server* so it knows which agent
is asking. Do not look for them on a response; the response names are in the table above.
