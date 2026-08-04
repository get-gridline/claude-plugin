# Credentials

You store a provider key once. Gridline returns a `vault://…` reference. Configuration names the
reference; the secret never appears in it.

```
PUT /projects/{project}/credentials/{name}     # body carries the secret, once
→ {"reference": "vault://anthropic-prod", "fingerprint": "sha256:1f3a…"}
```

Then `create_connection(id="anthropic-prod", component="anthropic",
credential_ref="vault://anthropic-prod")`.

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
curl -X PUT "$GRIDLINE_URL/projects/$PROJECT/credentials/anthropic-prod" \
  -H "Authorization: Bearer $GRIDLINE_ADMIN_KEY" \
  -H 'content-type: application/json' \
  -d "{\"secret\":\"$ANTHROPIC_API_KEY\"}"
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
