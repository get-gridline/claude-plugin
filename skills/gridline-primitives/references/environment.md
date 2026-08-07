# Environment variables

## The SDK reads none

Every setting is an argument to the constructor. A library that silently picks up a key from the
environment behaves differently in two deployments for reasons nobody can see, so it does not.

What you *choose* to keep in your own environment and pass in is your business:
`GRIDLINE_API_KEY`, `GRIDLINE_ROUTE_KEY`, a base URL.

## The tunnel client

The one component you run. **Two variables, and everything else has a working default.**

| Variable | Required | Notes |
|---|---|---|
| `GRIDLINE_CREDENTIAL` | yes | One value, shown once when the tunnel's credential is issued. It carries which tunnel this is, which key slot, and all three secrets |
| `GRIDLINE_SERVERS` | yes | Your servers, as JSON. The only place your addresses exist. Or `GRIDLINE_SERVERS_FILE`, a path to the same JSON |
| `GRIDLINE_TUNNEL_URL` | no | Only for a broker that is not the hosted one, which the client defaults to |
| `GRIDLINE_TUNNEL_NAME` | no | Checked against the credential rather than believed. Set it and a credential from another environment is refused at startup by name, instead of becoming a 401 |
| `ADMIN_ADDR` | no | `/healthz` and `/readyz`. Loopback by default — **set it to `:8097` for a Kubernetes probe**, which dials the Pod IP |
| `HTTPS_PROXY` / `NO_PROXY` | no | Honoured. Set `NO_PROXY` for in-cluster upstreams or they are dialled through the corporate proxy |
| `SSL_CERT_DIR` | no | For an extra CA. There is no way to disable verification |

Exactly one of `GRIDLINE_SERVERS` and `GRIDLINE_SERVERS_FILE`. Both set is refused rather than
ranked: precedence between two maps is something you discover during an outage, and what it
produces is an agent reaching the wrong server with nothing logged anywhere.

### Naming a server

A dictionary of name to address. **Names are compared exactly** — no case folding, no character
substitution — so `acme-wiki` and `jira.eu` need nothing spelt differently anywhere else.

```
GRIDLINE_SERVERS={"acme-wiki":"http://wiki.internal:8000/mcp","jira":"https://jira.internal/mcp"}
```

A server that wants a bearer takes the long form. The bearer is sent to your server and to
nothing else:

```
GRIDLINE_SERVERS={"acme-wiki":{"url":"http://wiki.internal:8000/mcp","token":"…"}}
```

`token_file` instead of `token` reads it from a path, which is how a mounted Secret stays its
own Secret — rotating one server's bearer then touches no other server's. Naming both is
refused.

One line, so this works unchanged in a `.env`, a systemd `EnvironmentFile`, a Compose file and
a `docker run -e`. In Kubernetes and systemd prefer the file: it needs no quoting rules at all.

The client refuses at startup, by name, anything it could not act on later — a name written as
a URL, an address with no scheme, a misspelt field, a `token_file` it cannot read. The
alternative is failing during somebody's turn, which is the most expensive moment to find out.

### Flags, not variables

`-call-timeout` and `-handshake-timeout` are command-line flags with no environment fallback. In
Kubernetes they go in `args:`, not a ConfigMap.

The call timeout must stay under the broker's staleness window. The shipped default already
accounts for this — raising it without raising the other means a long call has its own connection
reaped mid-flight, and you see session churn with no failing tool call to explain it.
