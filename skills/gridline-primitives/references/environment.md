# Environment variables

## The SDK reads none

Every setting is an argument to the constructor. A library that silently picks up a key from the
environment behaves differently in two deployments for reasons nobody can see, so it does not.

What you *choose* to keep in your own environment and pass in is your business:
`GRIDLINE_API_KEY`, `GRIDLINE_ROUTE_KEY`, a base URL.

## The tunnel client

The one component you run. It reads these:

| Variable | Required | Notes |
|---|---|---|
| `GRIDLINE_TUNNEL_URL` | yes | An **origin, no path** |
| `GRIDLINE_TUNNEL_NAME` | yes | The tunnel's name |
| `GRIDLINE_KEY` | yes | Route credential |
| `GRIDLINE_BUNDLE_KEY` | yes | Delivery secret. **Exactly 32 bytes** or it refuses at startup |
| `GRIDLINE_SERVERS` | yes | `name=url`, one per line. The only place your addresses exist |
| `GRIDLINE_KEY_SLOT` | no | Defaults to `1` |
| `GRIDLINE_TUNNEL_PROJECT` | **if pinned** | Omit on a pinned tunnel and every envelope fails to open, with an error that does not mention pins |
| `GRIDLINE_SERVER_TOKEN_<NAME>` | no | A bearer for one of your servers. Never leaves your network |
| `ADMIN_ADDR` | no | `/healthz` and `/readyz`. Loopback by default — **set it to `:8097` for a Kubernetes probe**, which dials the Pod IP |
| `HTTPS_PROXY` / `NO_PROXY` | no | Honoured. Set `NO_PROXY` for in-cluster upstreams or they are dialled through the corporate proxy |
| `SSL_CERT_DIR` | no | For an extra CA. There is no way to disable verification |

### GRIDLINE_SERVERS format

```
wiki=http://wiki.internal:8000/mcp
jira=https://jira.internal/mcp
```

A bare URL with no `name=` is refused at startup naming the line, rather than parsing as a name of
`http`. Duplicate names are refused too.

### Flags, not variables

`-call-timeout` and `-handshake-timeout` are command-line flags with no environment fallback. In
Kubernetes they go in `args:`, not a ConfigMap.

The call timeout must stay under the broker's staleness window. The shipped default already
accounts for this — raising it without raising the other means a long call has its own connection
reaped mid-flight, and you see session churn with no failing tool call to explain it.
