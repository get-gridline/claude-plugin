# Capabilities and parity

Every capability has a class, and the class decides whether a fallback chain may mix it.

| Class | Examples | Rule |
|---|---|---|
| `ADDITIVE` | prompt caching, vision, reasoning effort | May vary. Loss is recorded as degradation |
| `CONTRACT` | tools, streaming, structured output | Must be identical on every hop |
| `STATE` | thinking blocks, reasoning items | Refused, unless the fallback opts in |

## Why `CONTRACT` is strict

Your code is written against a shape. If hop one supports structured output and hop two does not, a
failover returns something your parser has never seen — at 3am, on the day a provider has an
outage. So a chain that mixes them is refused at configuration time instead.

## Why `STATE` is different, and the constraint everybody meets

Reasoning state is opaque and provider-specific. Gridline models it as **two distinct
capabilities** — `thinking_blocks` (Anthropic) and `reasoning_items` (OpenAI) — because one is
signed and the other encrypted, and neither can be converted into the other. There is no
translation, only omission.

So **a chain using extended thinking with a cross-vendor fallback is refused by default.** Within
one vendor you get both with nothing given up. Across vendors you have three choices, and they are
genuinely different decisions:

1. **Keep the chain within one vendor.** Nothing is ever lost.
2. **Turn thinking off** — `disable: ["thinking_blocks"]` on the model. No reasoning on any hop,
   and a cross-vendor fallback becomes legal because there is no state to lose.
3. **Accept the loss on the fallback** — `allow_state_loss: true` on that hop. The reasoning is
   kept while the primary is healthy; if the fallback is ever taken, it continues on the dialogue
   alone. Off unless you set it, so nobody trades their reasoning away by accident.

Option 3 has a cost that outlives the turn, and it is worth understanding before choosing it: the
conversation then holds two vendors' turns, so it can never be resumed with either vendor's own
state again. Every later turn reports itself degraded for that reason.

## Degraded vs lost

- **`degraded`** — a different model answered, so the output may differ.
- **`lost_capabilities`** — a named capability the hop could not carry over. `prompt_cache` costs
  money and produces identical output. `thinking_blocks` means the model could not see its own
  reasoning, which is why it appears here *and* sets `degraded`.

Kept apart deliberately. Netting them together would make a perfectly good failover look like a
downgrade, and the useful signal — "this answer came from a different model" — would be buried.
The name is what tells the two apart, so read `lost_capabilities` rather than the boolean alone.

## Answering "can I use X and Y on provider Z"

```
browse_models(capabilities=["tools", "thinking_blocks"])
```

Returns only models with all of them. Then `explain_agent` for what a specific chain gives up.

## The one degradation signal worth wiring an alert to

`tools_degraded` / `X-Tools-Degraded`. It means a turn went upstream with fewer tools than the
harness declares. Without it, a model that was never given its tools looks exactly like a model
that chose not to use them — it just answers, and says it is finished.
