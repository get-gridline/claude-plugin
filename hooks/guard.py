#!/usr/bin/env python3
"""Two rules that must hold every time, so neither is left to prose.

A skill that says "never echo a secret" is a request. A team that forgets to paste the
recommended permissions block has no confirmation on `delete_tunnel`. Both of those are
one bad afternoon, and both are cheap to make impossible instead:

1. **A credential must not travel in a tool call.** Refused outright. This is what makes the
   credential skill shippable at all -- it reads secrets out of your environment and sends them
   to the vault, and the one thing it must never do is put one in a file, a command line or this
   transcript.

2. **Anything that destroys, revokes or prints a secret is always confirmed.** Forced to `ask`
   here rather than only recommended in settings, because "always" is the whole request and a
   settings file somebody has to paste is not always.

Reads a `PreToolUse` payload on stdin and answers on stdout. Standard library only: this runs on
a customer's machine and a plugin hook that needs `pip install` is a plugin hook that fails on
first use.

**Failing open is deliberate.** A crash here prints nothing and returns 0, so a malformed payload
or an unfamiliar tool shape leaves Claude Code's own permission prompt in charge. A guard that
blocked every tool call the moment it hit an input it did not recognise would be uninstalled
within the hour, and then it guards nothing at all.
"""

from __future__ import annotations

import json
import re
import sys

# --- what a leaked credential looks like -------------------------------------------
#
# Prefixes first, because they are unambiguous: these are literally how the issuers shape their
# keys, so a match is a secret rather than a string that resembles one.
SECRET_SHAPES: list[tuple[str, re.Pattern[str]]] = [
    ("an Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("an OpenAI API key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("a webhook signing secret", re.compile(r"whsec_[A-Za-z0-9_\-]{16,}")),
    ("a Gridline API key", re.compile(r"gl_[A-Za-z0-9]{24,}")),
    ("a Google API key", re.compile(r"AIza[A-Za-z0-9_\-]{30,}")),
    ("an AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("a GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("a private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY")),
]

# A tunnel's delivery key is 32 bytes of base64url and carries no prefix at all, so there is
# nothing to match on but its shape -- which is also the shape of plenty of innocent things
# (a git SHA is not this long, but a content hash or a minified blob can be).
#
# **So this only fires next to a name that says what it is.** Matching the shape alone would
# refuse legitimate work often enough that somebody disables the hook, and a disabled hook is
# strictly worse than a narrow one.
BARE_KEY = re.compile(
    r"(?i)(?:key|secret|token|ikm|credential|password|passwd)\W{0,4}"
    r"([A-Za-z0-9_\-]{43}=?|[A-Za-z0-9+/]{43}=)"
)

# --- what must always be confirmed --------------------------------------------------
#
# Every one of these either destroys something, revokes access, or prints a live secret into the
# conversation. The reason each is here is worth keeping, because "why does this prompt" is the
# first question and an unexplained prompt gets clicked through.
ALWAYS_ASK: dict[str, str] = {
    "delete_tunnel": (
        "deletes the tunnel and revokes BOTH credential slots. It cannot be undone, and "
        "re-registering the name issues new secrets -- so every client using it stops working "
        "until it is reconfigured"
    ),
    "delete_webhook": "deletes the endpoint and its signing secrets. Undelivered events are lost",
    "retire_tunnel_key": (
        "retires a credential slot. Retiring the last one leaves the tunnel registered and "
        "carrying nothing, and the broker refuses calls until a new credential is issued"
    ),
    "retire_webhook_secret": (
        "retires a signing secret. Retiring the one your receiver verifies with means every "
        "delivery starts failing its signature check"
    ),
    "revoke_invitation": "withdraws an invitation. The address has to be invited again",
    "rename_project": (
        "renames the project. Anything naming the old one -- your own configuration, deploy "
        "scripts, dashboards -- stops resolving"
    ),
    "replay_webhooks": (
        "re-delivers past events to your endpoint. Your receiver sees them again, so anything "
        "not idempotent happens twice"
    ),
    "create_webhook": (
        "prints a live signing secret into this conversation, which is then in the transcript "
        "and anywhere it is stored. Consider running it yourself instead"
    ),
    "rotate_webhook_secret": (
        "prints a live signing secret into this conversation, which is then in the transcript "
        "and anywhere it is stored. Consider running it yourself instead"
    ),
    "archive_task": "archives the task. Its history stays, but it stops accepting new sessions",
}

# Destructive shell shapes, for the same reason: the model can reach an irreversible outcome with
# `curl -X DELETE` whether or not the MCP tool is confirmed. Not an attempt at a complete list of
# dangerous commands -- Claude Code already prompts for Bash -- only at closing the specific gap
# where gating the tool would otherwise look like gating the action.
#
# **One `(?i)` and it must be at the very start.** Python 3.11+ raises on an inline global flag
# anywhere else, and because this compiles at import time the whole module died -- so the guard
# failed open on *everything*, including every secret shape above, while printing nothing. That
# is indistinguishable from "this call is fine", which is why `--selftest` exists below.
DESTRUCTIVE_SHELL = re.compile(
    r"(?i)"
    r"curl[^\n|;]*(?:-X\s*DELETE|--request\s+DELETE)"
    r"|(?:-X\s*DELETE|--request\s+DELETE)[^\n|;]*curl"
)


def decide(payload: dict) -> tuple[str, str]:
    """The whole ruleset, as a pure function of the payload.

    Separated from the printing so `--selftest` exercises the same code path a real call takes.
    A test that re-implemented the decision would agree with itself and prove nothing.

    Returns `("", "")` for "no opinion", which leaves Claude Code's normal permission flow in
    charge -- the common case, and the one that must stay quiet.
    """
    tool = payload.get("tool_name") or ""
    supplied = payload.get("tool_input") or {}
    # Whole input as text, so a secret is caught wherever it sits -- a bash command, a file body,
    # an MCP argument, something nested. Searching named fields would mean maintaining a list of
    # field names, and the one that gets forgotten is the one that leaks.
    text = json.dumps(supplied)

    for what, shape in SECRET_SHAPES:
        if shape.search(text):
            return "deny", (
                f"This call contains what looks like {what}, and a credential must not travel in "
                f"a tool call -- it would land in the transcript, and possibly in a file or your "
                f"shell history.\n\n"
                f"Read it from the environment inside the command instead, so the value is never "
                f"a literal here:\n\n"
                f"    curl … -d \"{{\\\"secret\\\":\\\"$ANTHROPIC_API_KEY\\\"}}\"\n\n"
                f"Gridline stores credentials as references and never returns the material, so no "
                f"Gridline workflow needs a secret written out."
            )

    if BARE_KEY.search(text):
        return "deny", (
            "This call contains a 32-byte base64 value next to a name like key, secret or token "
            "-- the shape of a Gridline delivery key or a tunnel bundle key. Pass it through the "
            "environment rather than writing it into a command or a file.\n\n"
            "If it is not a credential, the name beside it is what triggered this: rename the "
            "field, or set the value from an environment variable."
        )

    if tool.startswith("mcp__gridline__"):
        bare = tool[len("mcp__gridline__"):]
        if bare in ALWAYS_ASK:
            return "ask", (
                f"`{bare}` {ALWAYS_ASK[bare]}.\n\n"
                f"The Gridline plugin forces a confirmation on every destructive or "
                f"secret-printing tool, whatever your permission settings say."
            )

    if tool == "Bash" and DESTRUCTIVE_SHELL.search(str(supplied.get("command") or "")):
        return "ask", (
            "This is an HTTP DELETE against an API. Deleting a Gridline object is not "
            "recoverable -- a tunnel takes both its credential slots with it, and a webhook "
            "takes its signing secrets. Confirm what is being removed before it runs."
        )

    return "", ""


def main() -> None:
    decision, reason = decide(json.load(sys.stdin))
    if decision:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }))
    sys.exit(0)


CASES: list[tuple[str, str, dict]] = [
    # (expected decision, label, payload)
    ("deny", "an Anthropic key in a file",
     {"tool_name": "Write", "tool_input": {"content": "K=sk-ant-api03-AbCdEf1234567890xyz"}}),
    ("deny", "an OpenAI key on a command line",
     {"tool_name": "Bash", "tool_input": {"command": "curl -d sk-proj-abcdefghij1234567890ABCDEF x"}}),
    ("deny", "a webhook signing secret",
     {"tool_name": "Bash", "tool_input": {"command": "export S=whsec_abcdef1234567890abcdef"}}),
    ("deny", "a Gridline API key",
     {"tool_name": "Edit", "tool_input": {"new_string": "gl_live00000000000000000000000abc"}}),
    ("deny", "an AWS access key id",
     {"tool_name": "Write", "tool_input": {"content": "AKIAIOSFODNN7EXAMPLE"}}),
    ("deny", "a private key block",
     {"tool_name": "Write", "tool_input": {"content": "-----BEGIN PRIVATE KEY-----"}}),
    ("deny", "a bare 32-byte key beside a telling name",
     {"tool_name": "Write",
      "tool_input": {"content": "GRIDLINE_BUNDLE_KEY=aGVsbG93b3JsZGhlbGxvd29ybGRoZWxsb3dvcmxkaGU"}}),

    ("ask", "delete_tunnel",
     {"tool_name": "mcp__gridline__delete_tunnel", "tool_input": {"name": "acme"}}),
    ("ask", "delete_webhook",
     {"tool_name": "mcp__gridline__delete_webhook", "tool_input": {"endpoint": "e"}}),
    ("ask", "retire_tunnel_key",
     {"tool_name": "mcp__gridline__retire_tunnel_key", "tool_input": {"name": "a", "slot": "1"}}),
    ("ask", "retire_webhook_secret",
     {"tool_name": "mcp__gridline__retire_webhook_secret", "tool_input": {}}),
    ("ask", "revoke_invitation",
     {"tool_name": "mcp__gridline__revoke_invitation", "tool_input": {}}),
    ("ask", "rename_project",
     {"tool_name": "mcp__gridline__rename_project", "tool_input": {"name": "a"}}),
    ("ask", "replay_webhooks",
     {"tool_name": "mcp__gridline__replay_webhooks", "tool_input": {}}),
    ("ask", "archive_task",
     {"tool_name": "mcp__gridline__archive_task", "tool_input": {}}),
    ("ask", "create_webhook prints a secret",
     {"tool_name": "mcp__gridline__create_webhook", "tool_input": {"url": "https://x"}}),
    ("ask", "rotate_webhook_secret prints a secret",
     {"tool_name": "mcp__gridline__rotate_webhook_secret", "tool_input": {}}),
    ("ask", "an HTTP DELETE by hand",
     {"tool_name": "Bash", "tool_input": {"command": "curl -X DELETE https://api/x"}}),
    ("ask", "an HTTP DELETE with the flag first",
     {"tool_name": "Bash", "tool_input": {"command": "curl --request DELETE https://api/x"}}),

    # Silence matters as much as refusal: a guard that fires on ordinary work gets uninstalled,
    # and then it protects nothing at all.
    ("", "an ordinary write tool",
     {"tool_name": "mcp__gridline__create_agent", "tool_input": {"id": "chat"}}),
    ("", "a read tool",
     {"tool_name": "mcp__gridline__list_projects", "tool_input": {}}),
    ("", "a secret referenced through the environment",
     {"tool_name": "Bash",
      "tool_input": {"command": 'curl -d "{\\"secret\\":\\"$ANTHROPIC_API_KEY\\"}" https://api'}}),
    ("", "a git SHA",
     {"tool_name": "Bash", "tool_input": {"command": "git show da4c88a1b2c3"}}),
    ("", "a long digest with no credential-ish name near it",
     {"tool_name": "Write",
      "tool_input": {"content": "digest = aGVsbG93b3JsZGhlbGxvd29ybGRoZWxsb3dvcmxkaGU"}}),
    ("", "a GET, not a DELETE",
     {"tool_name": "Bash", "tool_input": {"command": "curl https://api/x"}}),
]


def selftest() -> int:
    """Assert every rule, because this file failing open is invisible.

    A `PreToolUse` hook that crashes prints nothing and returns 0, which Claude Code reads as
    "no opinion" -- so a syntax error in a regex silently disables every protection here. That
    happened once, before this existed: an inline `(?i)` in the middle of a pattern raised at
    import and the guard passed all seven secret shapes straight through.

    Run with `python3 guard.py --selftest`. No pytest, no dependencies: this has to be runnable
    on a customer's machine and in CI without either.
    """
    failures = 0
    for expected, label, payload in CASES:
        decided, reason = decide(payload)
        if decided != expected:
            failures += 1
            want = expected or "silence"
            got = decided or "silence"
            print(f"FAIL  {label}: expected {want}, got {got}")
        elif decided and not reason.strip():
            failures += 1
            print(f"FAIL  {label}: decided {decided} with no reason to show the user")

    print(f"\n{len(CASES) - failures}/{len(CASES)} guard cases pass")
    if failures:
        print("\nA failure here means the guard is not protecting what it claims to. It fails")
        print("open by design, so nothing else will tell you.")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Fail open, quietly enough not to break a session. See the module docstring: a guard
        # that blocks on surprise gets uninstalled. `--selftest` is what stops this hiding a bug.
        sys.exit(0)
