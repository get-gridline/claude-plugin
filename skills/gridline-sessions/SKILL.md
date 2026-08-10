---
name: gridline-sessions
description: List, read, resume and archive Gridline conversations. Use to inspect what an agent actually said, to continue a conversation, to audit a transcript, or when asked about session history or replay.
---

# Sessions and transcripts

Cite `references/sessions-and-transcripts.md`.

## Reading

```
GET /sessions?project=…                    # list
GET /sessions/{id}                         # metadata, cost, attempts
GET /sessions/{id}/messages                # canonical — one shape across providers
GET /sessions/{id}/messages?provider=true  # native — the exact bytes sent
GET /sessions/{id}/messages?resuming=true  # shaped to continue from
```

`project` is a filter for an unbound credential. **A bound key overrides it**, so the safe answer is
what you get when you say nothing — do not treat the parameter as an access control.

## Which view to use

- **canonical** for reading and diffing across providers.
- **native** when the question is "what exactly did the provider see". Debugging an odd answer usually
  ends here.
- **resuming** when continuing.

Both forms are stored because a normalised conversation cannot always be resumed — Anthropic rejects a
modified thinking block, so a tidied transcript is one you can read and not continue.

## Continuing

Pass the session id with the next turn. Your application sends **one** message and Gridline supplies
the history. If you find code resending the whole conversation, that is the thing to fix — it is
paying for tokens the session already has.

## Saying something to a turn that is already running

`queue` puts a message in the conversation's inbox. It is **not a turn**: no tokens, no model call,
and it returns before anything has read it.

```python
chat.queue("actually -- only January")     # from a web handler, a keystroke, anywhere
```

It is delivered at the conversation's next tool-loop boundary, which is the only place a conversation
can take a new message — a model mid-generation cannot be interrupted, on any provider. If the
conversation is idle it waits and arrives at the start of the next turn, ahead of whatever is sent
then, because that is when it was said.

Only the session id is needed, so any process holding it can queue: no connection, no affinity.

**It is refused rather than dropped** when too much is outstanding or one message is too large, and the
refusal names the number to change. And a message queued into a conversation nobody continues
**expires** rather than arriving much later into one whose context has moved on.

`chat.inbox()` says what is waiting, what was delivered and what expired. It is the first thing to
call when something was queued and nothing happened.

## Compaction

If a turn was compacted, the model saw less than the transcript holds. **The transcript keeps the full
history** and turn N+1 re-elides from the complete version rather than from an already-lossy copy. So
a compacted conversation is still fully auditable.

## session_degraded

Something was not as configured — a surface unavailable, history unreadable. The turn happened.
Treat it as a signal to investigate, not a failure, and look at what the harness expected to reach.

## Archive and restore

Archiving takes a session out of the working set and keeps it; restoring brings it back. Neither
deletes anything, so archive freely.

## Deletion

Deleting a conversation's encryption key makes exactly that one conversation unrecoverable — a
genuine erasure story rather than a "deleted" flag. Worth mentioning if somebody asks about
data-subject requests.
