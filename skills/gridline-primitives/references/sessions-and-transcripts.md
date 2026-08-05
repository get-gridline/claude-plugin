# Sessions and transcripts

A **session** is a conversation. Recording is on.

## Stored twice, on purpose

Every turn is kept in two forms:

- **canonical** — one shape across providers, which is what you read and diff.
- **native** — the provider's original bytes, untouched.

The original is kept because a normalised conversation cannot always be resumed. Anthropic rejects a
modified thinking block, so a tidied transcript is a transcript you can read and not continue. Both
forms exist so you can do both.

## Reading

```
GET /sessions?project=…                    # list
GET /sessions/{id}                         # metadata, cost, attempts
GET /sessions/{id}/messages                # canonical
GET /sessions/{id}/messages?provider=true  # native, exactly as sent
GET /sessions/{id}/messages?resuming=true  # shaped to continue from
```

## Continuing one

Pass the session id with your next turn and Gridline supplies the history. Your application sends
one message, not the whole conversation.

## Compaction

When a conversation approaches the context limit, Gridline may compact it. When that happens:

- `X-Context-Compacted` is set on the response.
- **The transcript keeps the full, un-elided history.** Only what went upstream was shortened.
- `system` and `tools` are never touched — they are the cached prefix.

So a compacted conversation is still fully readable afterwards, and the next turn re-elides from the
complete history rather than from an already-lossy copy.

## session_degraded

Something about the session was not as configured — a surface unavailable, history unreadable. The
turn still happened; treat it as a signal to investigate rather than a failure.

## Archive and restore

Archiving takes a session out of the working set and keeps it. Restoring brings it back. Neither
deletes anything.

## Deletion

Deleting a conversation's encryption key makes exactly that conversation unrecoverable — a real
erasure story rather than a "marked as deleted" flag.
