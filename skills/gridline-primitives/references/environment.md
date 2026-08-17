# Environment variables

## The SDK

Four variables, and an explicit argument beats each of them. Nothing else is read — in particular
the SDK never picks up `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, because a library that silently took
another vendor's key would behave differently in two deployments for reasons nobody can see.

| Variable | Read by | Notes |
|---|---|---|
| `GRIDLINE_BASE_URL` | `gridline.connect()` | Where turns go. Optional — the hosted address is the default, so pointing a test run at a local stack is this variable and no code change |
| `GRIDLINE_API_KEY` | `gridline.connect()` | The `route` key. `connect()` refuses at the call rather than handing back a client that can only 401 later; a stack running with auth off wants `key=""` said out loud |
| `GRIDLINE_CONTROL_URL` | `gridline.control()` | Where configuration goes. Optional in the same way |
| `GRIDLINE_CONFIG_KEY` | `gridline.control()` | The `config` key |

**Two planes, two addresses, two keys, and they are deliberately not interchangeable.** The control
plane is not on the request path, so an application holds only the route key and never needs the
other — which is what stops a leaked route key from rewriting which model serves an agent. Never set
one to the value of the other.

## Writing a credential

One more variable, and it is deliberately not one of the four above: it carries an **`admin`** key.

| Variable | Read by | Notes |
|---|---|---|
| `GRIDLINE_ADMIN_KEY` | the `curl` you run to write a credential | An `admin` key. A `config` key is refused here, and so is a route key |

**`admin` is a wider capability than either key above, not a stronger version of one.** Writing a
credential is the most consequential thing this API does and it is not a configuration edit, which
is why a `config` key cannot do it — and `admin` already implies `config`, so a key that can write
a credential can read back what it did.

That makes it the one key to hold in the fewest places: set it only where a credential is actually
written, and never in an application that just sends turns, which needs the route key and nothing
else.

Its value follows the same rule as any other secret here — never show any part of it, not even the
last four characters. The variable name says which key you mean.

## Verifying a webhook

Your receiver needs the endpoint's signing secret to check a delivery before parsing it. Unlike every
other name on this page, **this variable is yours and only its value is ours**:

| Variable | Read by | Notes |
|---|---|---|
| `GRIDLINE_WEBHOOK_SECRET` | your own receiver, which passes it to `gridline.webhooks.unwrap(...)` | The signing secret of one webhook endpoint. The SDK never reads this variable itself — it takes the secret as an argument, so the name is entirely your choice and this is the one our examples use |

**The value is issued, not chosen, and never by a tool in a conversation.** `create_webhook`
registers the endpoint and issues nothing at all; the secret is generated where a person is looking
— the Gridline web dashboard, or `gridline apply` under an admin credential — and shown once there,
so store it the moment you see it. No endpoint reads it back afterwards in any state, so having
lost it the fix is to generate another the same way rather than a lookup. It begins `whsec_`, because we emit
Standard Webhooks and any off-the-shelf verifier for that format works against our deliveries.

**One secret belongs to one endpoint.** Two endpoints are two secrets and two variables; naming both
in one is the mistake that makes half your deliveries fail verification. During a rotation an
endpoint briefly has two live secrets and both sign every delivery, so a receiver reading a single
variable moves across by having the variable set to the new value before the old slot is retired.

## The tunnel client

The one component you run. **Two variables, and everything else has a working default.**

| Variable | Required | Notes |
|---|---|---|
| `GRIDLINE_CREDENTIAL` | yes | One value, shown once when the tunnel's credential is issued. It carries which tunnel this is, which key slot, and all three secrets |
| `GRIDLINE_SERVERS` | yes | Your servers, as JSON. The only place your addresses exist. Or `GRIDLINE_SERVERS_FILE`, a path to the same JSON |
| `GRIDLINE_TUNNEL_URL` | no | Only for a broker that is not the hosted one, which the client defaults to |
| `GRIDLINE_TUNNEL_ID` | no | Checked against the credential rather than believed. Set it and a credential from another environment is refused at startup by name, instead of becoming a 401. The id, because the credential carries no name — so a rename never invalidates it |
| `GRIDLINE_PROJECT_ID` | no | The same, for the project whose calls this client answers. Worth more than the one above wherever several clusters share a tunnel: a credential from the wrong cluster does not 401, that cluster simply serves the other one's calls. Leave it unset for a credential serving every project |
| `GRIDLINE_CONCURRENCY` | no | How many calls this client serves at once. The shipped default is the one to leave alone unless your own servers are the bottleneck |
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
