# Credentials

You store a provider key once. Gridline returns a `vault://…` reference. Configuration names the
reference; the secret never appears in it.

```
PUT /projects/{project}/credentials              # body: {"ref", "plane", "secret"}
→ {"ref": "vault://anthropic/api-key", "version": 1, "state": "current",
   "fingerprint": "…", "source": "…"}
```

The reference is in the **body**, not in the path, and it comes with the thing it belongs to
rather than being invented: a model provider's reference is the one the catalogue declares for that
vendor — `vault://anthropic/api-key`, `vault://openai/api-key` — and a component's is whatever you
gave its connection. `plane` says which of your planes may open it.

**A model provider is not a connection.** `create_connection` registers a *component* account — a
memory store, a sandbox, a skills workspace, one of your own MCP servers — and its `kind` is an id
from `browse_providers`, which is where naming a vendor as a kind is refused:

```
create_connection(project, connection_id="mem0-prod", kind="mem0",
                  credential_ref="vault://acme-mem0/api-key")
```

For a whole vendor account in one call, `PUT /projects/{project}/providers/{vendor}` writes every
secret that vendor needs and is the path to prefer; the per-reference `PUT` above is what it
composes.

## The read surface is a fingerprint, and that is all of it

**No endpoint returns credential material, in any state, to any principal — including for support.**
There is no "show me the key" call, no admin override, no recovery path. If you lose a provider key
you rotate it at the provider.

The consequence for any workflow: **nothing needs a secret written into a file or a conversation.**
If a step seems to require it, the step is wrong.

The fingerprint lets you answer "is this the key I think it is" by comparing, without anybody
seeing it.

## Writing one without it landing anywhere

Read from the environment inside the same command that sends it:

```bash
curl -X PUT "$GRIDLINE_CONTROL_URL/projects/$PROJECT/credentials" \
  -H "Authorization: Bearer $GRIDLINE_ADMIN_KEY" \
  -H 'content-type: application/json' \
  -d "{\"ref\":\"vault://anthropic/api-key\",\"plane\":\"proxy\",\"secret\":\"$ANTHROPIC_API_KEY\"}"
```

The value is never a literal in the command, so it is not in the transcript and not in your shell
history beyond the variable name.

## Rotation

Writing a new value keeps the previous one in a `retiring` state for an overlap window, so
in-flight work does not fail mid-rotation. Two consequences worth knowing:

- **Rolling back is writing the old value again.** There is no "undo".
- **Writing the identical value is refused** with `unchanged_secret`. That is "already correct",
  not an error — re-running a setup is safe.

## Refusals and what each means

| Code | Meaning |
|---|---|
| `sealing_unavailable` | The deployment cannot encrypt at rest right now, so it refuses to store rather than storing in the clear |
| `unowned_project` | The project belongs to no organisation, so no owner can be resolved |
| `not_storable` | This component takes its address as its identity and has no secret to store |
| `no_plane` | Nothing would ever fetch this credential — check the component |
