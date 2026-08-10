# Response headers

Set on every response Gridline returns. These are how you tell what actually happened.

| Header | Meaning |
|---|---|
| `X-Request-Id` | Joins this response to its attempt records and its transcript. Also accepted **inbound** — send your own and it is used, so your logs and Gridline's share an id |
| `X-Gridline-Agent` | Which agent served it |
| `X-Gridline-Model` | Which model actually answered — not necessarily the first hop |
| `X-Gridline-Degraded` | A fallback answered, so output may differ from the preferred model |
| `X-Lost-Capabilities` | Capabilities unavailable on the hop that answered (e.g. prompt caching) |
| `X-Tools-Degraded` | **The turn went upstream with fewer tools than the harness declares** |
| `X-Context-Compacted` | History was shortened for this turn. The transcript keeps it in full |
| `X-Session-Id` | The conversation this turn belongs to |

## Why X-Tools-Degraded deserves an alert

Without it, a turn that reached the provider with **no tools at all** is indistinguishable from a
model that considered its tools and chose not to use one. Both look like a plain answer ending
normally. It is set for *any* loss, not only total loss, and the reply carries `tools_dropped` with
the names.

If you wire one Gridline signal to an alert, this is the one.

## X-Gridline-Degraded vs X-Lost-Capabilities

`Degraded` is about *which model*. `Lost-Capabilities` is about *what that model could not do*. A
failover to an equally capable model is degraded with nothing lost; a preferred model without cache
support is not degraded but has lost something. They answer different questions.
