#!/usr/bin/env python3
"""Refuse a plugin whose parts do not load, since almost none of it fails loudly.

**Everything in a Claude Code plugin degrades to silence.** A skill whose frontmatter will not
parse never triggers. A `description` over the cap is truncated, so a skill fires on half its
triggers. An MCP server pointing nowhere yields no tools and no error the user connects to the
plugin. A command referencing a skill that was renamed does nothing. None of these break a
session -- they quietly subtract capability, and the user's experience is "Gridline's plugin
doesn't seem to do much".

So this reads the files together and asserts the things that are otherwise discovered by a
customer, the same idea as validating a Helm chart's rendered templates before it ships.

Deliberately parsing rather than importing a YAML library: the frontmatter is a handful of scalar
keys, and the control plane's dependencies have no business being installed to check a plugin.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# **The plugin root is an argument, because it is `plugin/` here and the repository root in the
# published mirror.** Checking only the layout in this repository would leave the one customers
# actually install unverified -- and the two differ in exactly the way that matters, since every
# path below is relative to this. `publish-plugin.yml` runs it against the assembled tree.
#
# **A module-level default, reassigned by `check_plugin_tree` per call.** The real entry point
# (`main`) sets it once from `sys.argv`; `--selftest` sets it once per throwaway tree instead, so
# the checks below -- written against this name, not a parameter, to keep this diff small -- see
# whichever tree is actually being checked.
PLUGIN = ROOT / "plugin"
# **No marketplace manifest in this repository, deliberately.** It is generated into the public
# mirror at publish time, because it must say `source: "./"` there -- and a copy here saying
# anything would be a second version of one fact, wrong in one of the two places.

# Claude Code caps `description` + `when_to_use` together. Skills are matched on that text, so
# the cost of exceeding it is a skill that fires on some of its triggers and not others.
DESCRIPTION_CAP = 1024

problems: list[str] = []


def fail(message: str, file: Path | None = None) -> None:
    # Relative to the repository when the file is inside it, absolute otherwise -- the assembled
    # mirror lives outside the tree, and `relative_to` raises rather than coping.
    where = ""
    if file:
        try:
            where = f"file={file.relative_to(ROOT)}::"
        except ValueError:
            where = ""
    print(f"::error {where}{message}" if where else f"::error::{message}")
    problems.append(message)


def frontmatter(path: Path) -> dict[str, str]:
    """The `key: value` scalars from a `---` fenced block at the top of a markdown file."""
    text = path.read_text()
    if not text.startswith("---\n"):
        fail("no YAML frontmatter, so this is not a skill Claude Code will ever load", path)
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        fail("the frontmatter block is not closed with `---`", path)
        return {}
    found: dict[str, str] = {}
    key = None
    for line in text[4:end].splitlines():
        matched = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if matched:
            key = matched.group(1)
            found[key] = matched.group(2).strip().strip('"').strip("'")
        elif key and line.startswith((" ", "\t")):
            # A folded scalar continued on the next line.
            found[key] = (found[key] + " " + line.strip()).strip()
    return found


def check_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail("missing, and the plugin cannot load without it", path)
    except json.JSONDecodeError as bad:
        fail(f"is not valid JSON: {bad}", path)
    return {}


# --- the manifest that decides whether the guard ever runs ---------------------------
#
# **The guard hook decides what to do once it is invoked; `hooks.json` decides whether it is
# invoked at all, and the two are separate hand-written files naming the same tools.** Neither
# can be read against the other by eye: a matcher naming a tool nothing is ever called by looks
# exactly like a matcher that is merely narrow, so every rule the guard states can be correct,
# well-tested and unreachable at the same time. The only symptom is a confirmation that does not
# appear, which is indistinguishable from a call nobody thought was dangerous. So the agreement
# is asserted here rather than left to two people remembering the same spelling.

# A tool name as Claude Code writes one. Used to find names written into prose, where the same
# mistake is just as silent -- a permission entry naming a tool nothing is called by never
# applies, so a read-only tool listed in `allow` goes on asking on every single use.
TOOL_REFERENCE = re.compile(r"mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_]+")

# Claude Code builds an MCP tool's name from the plugin and server it came from, replacing
# anything outside this set with `_`.
UNSAFE_IN_NAME = re.compile(r"[^A-Za-z0-9_-]")


def load_guard(path: Path):
    """Import the guard hook from whichever tree is being checked.

    By path rather than by module name, because this runs against two different roots and the
    guard is not on the import path in either.
    """
    spec = importlib.util.spec_from_file_location("plugin_guard_under_check", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def namespaces(manifest: dict, mcp: dict) -> list[str]:
    """How Claude Code names the tools of an MCP server this plugin bundles.

    Both halves are read from the manifests rather than typed here, so renaming either one moves
    the expectation with it instead of leaving a stale literal behind: a plugin `p` bundling a
    server `s` has its tools called `mcp__plugin_<p>_<s>__<tool>`, which reads doubled whenever
    `p` and `s` are the same word.
    """
    name = UNSAFE_IN_NAME.sub("_", manifest.get("name") or "")
    return [
        f"mcp__plugin_{name}_{UNSAFE_IN_NAME.sub('_', server)}__"
        for server in sorted(mcp.get("mcpServers") or {})
    ]


def check_guard_is_reachable(manifest: dict, mcp: dict, hooks: dict) -> None:
    """Assert the matcher selects every tool the guard hook claims to gate."""
    guard_path = PLUGIN / "hooks/guard.py"
    try:
        guard = load_guard(guard_path)
    except Exception as bad:  # noqa: BLE001 -- any import failure means the same thing here
        guard = None
        fail(f"will not import ({bad}), so nothing can check which tools the hook it backs is "
             f"actually invoked for", guard_path)
    if guard is None:
        return

    # An absent or empty matcher runs the hook on every tool, so there is nothing it can miss.
    # A matcher that will not compile selects nothing at all, which is its own silent failure.
    selectors: list[str] = []
    for entry in (hooks.get("hooks") or {}).get("PreToolUse") or []:
        matcher = entry.get("matcher")
        if matcher in (None, "", "*"):
            selectors.append("")
            continue
        try:
            re.compile(matcher)
        except re.error as bad:
            fail(f"the PreToolUse matcher {matcher!r} is not a usable pattern ({bad}), so it "
                 f"selects nothing and the hook never runs", PLUGIN / "hooks/hooks.json")
            continue
        selectors.append(matcher)

    def fires_on(tool: str) -> bool:
        # Unanchored, matching how a matcher containing pattern characters is evaluated.
        return any(one == "" or re.search(one, tool) for one in selectors)

    prefixes = namespaces(manifest, mcp)

    # **Both directions, because either file alone can be the one that moved.** The guard has to
    # recognise the name its own plugin's tools arrive under, or it runs and then has no opinion
    # on every one of them.
    accepted = getattr(guard, "GRIDLINE_TOOL", None)
    for prefix in prefixes:
        if accepted is not None and not accepted.match(f"{prefix}some_tool"):
            fail(f"does not recognise {prefix}<tool> as one of its own plugin's tools. Every "
                 f"rule below that names a tool would be skipped, and the hook would return "
                 f"no opinion instead of the confirmation it exists to force", guard_path)

    # One entry per tool name rather than per rule, so a single missing alternative in the
    # matcher reads as the one mistake it is instead of as a page of separate ones.
    unreached: dict[str, str] = {}
    for prefix in prefixes:
        for tool in sorted(getattr(guard, "ALWAYS_ASK", {})):
            if not fires_on(f"{prefix}{tool}"):
                unreached[f"{prefix}{tool}"] = (
                    f"`{tool}` is one of the tools the guard forces a confirmation on"
                )

    # And every call the guard's own cases say it answers. This pins the ordinary tools as well
    # as the MCP ones, and any second spelling the guard deliberately accepts: the matcher may
    # not be narrower than the guard, or the difference is a rule that never fires.
    for expected, label, payload in getattr(guard, "CASES", []):
        tool = (payload or {}).get("tool_name") or ""
        if expected and not fires_on(tool):
            unreached.setdefault(tool, f"the guard answers {expected!r} to {label}")

    for tool in sorted(unreached):
        fail(f"the PreToolUse matcher never selects {tool!r}, but {unreached[tool]}. A rule the "
             f"guard states and the matcher does not reach is inert and silent: the hook is not "
             f"invoked, nothing errors, and the confirmation simply never appears",
             PLUGIN / "hooks/hooks.json")

    # The same mistake made in prose. Grouped per file, since one wrong spelling is normally
    # copied down a whole block.
    for source in sorted(PLUGIN.rglob("*.md")):
        if not prefixes or "hooks" in source.relative_to(PLUGIN).parts:
            continue
        wrong = sorted({
            found for found in TOOL_REFERENCE.findall(source.read_text())
            if not any(found.startswith(prefix) for prefix in prefixes)
        })
        if wrong:
            fail(f"names {len(wrong)} tool(s) in a spelling this plugin's tools never arrive "
                 f"under, starting with {wrong[0]!r}. They are called {prefixes[0]}<tool>, so a "
                 f"permission entry written any other way never applies -- and one in an "
                 f"`allow` list that never applies leaves that tool asking on every use, "
                 f"forever", source)


def check_plugin_tree(plugin: Path) -> list[str]:
    """Runs every check against `plugin`, returning whatever `fail()` collected.

    Sets the module-level `PLUGIN`/`problems` rather than threading a return value through
    every helper -- `check_json` and `frontmatter` both call `fail()` directly, and this
    keeps this function's own body identical to what `main()` ran inline before `--selftest`
    needed to call it more than once.
    """
    global PLUGIN, problems
    PLUGIN = plugin
    problems = []

    manifest = check_json(PLUGIN / ".claude-plugin/plugin.json")

    for required in ("name", "version", "description"):
        if not manifest.get(required):
            fail(f"plugin.json has no `{required}`", PLUGIN / ".claude-plugin/plugin.json")

    # The bundled MCP server. A hardcoded host would be wrong the first time it moves, so the
    # URL must stay interpolatable -- and it must still carry a default, or a fresh install
    # connects to nothing.
    mcp = check_json(PLUGIN / ".mcp.json")
    for name, server in (mcp.get("mcpServers") or {}).items():
        url = server.get("url") or ""
        if server.get("type") == "http" and "${" not in url:
            fail(f"the {name!r} MCP server hardcodes {url!r}. Use ${{GRIDLINE_MCP_URL:-…}} so a "
                 f"deployment can be repointed without editing an installed plugin",
                 PLUGIN / ".mcp.json")

    skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    if not skills:
        fail("no skills found under plugin/skills/*/SKILL.md")

    names: set[str] = set()
    for skill in skills:
        meta = frontmatter(skill)
        name = meta.get("name") or ""
        names.add(name)
        if not name:
            fail("no `name` in frontmatter", skill)
        elif name != skill.parent.name:
            fail(f"frontmatter name {name!r} does not match its directory "
                 f"{skill.parent.name!r}; Claude Code keys on the directory", skill)
        described = meta.get("description") or ""
        if not described:
            fail("no `description`, so nothing will ever trigger this skill", skill)
        combined = len(described) + len(meta.get("when_to_use") or "")
        if combined > DESCRIPTION_CAP:
            fail(f"description + when_to_use is {combined} characters, over the {DESCRIPTION_CAP} "
                 f"cap. It is truncated rather than rejected, so the skill fires on some of its "
                 f"triggers and not others", skill)

    # Subagents count as providable names too: a command legitimately names one, and a skill
    # delegates to one. Collected before the command check below, which would otherwise report a
    # perfectly good `gridline-repo-auditor` reference as a missing skill -- as it did once.
    agents = sorted((PLUGIN / "agents").glob("*.md"))
    provided = names | {agent.stem for agent in agents}

    # A command or skill naming something nothing provides is a menu entry that does nothing, or a
    # delegation to an agent that is not there. Neither reports an error at runtime.
    for source in sorted((PLUGIN / "commands").glob("*.md")) + [
        skill for skill in sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    ]:
        for referenced in re.findall(r"gridline-[a-z-]+", source.read_text()):
            if referenced not in provided:
                fail(f"references {referenced!r}, which is neither a skill nor a subagent in this "
                     f"plugin. A command would appear in the `/` menu and do nothing; a skill "
                     f"would delegate to something absent", source)

    for agent in agents:
        meta = frontmatter(agent)
        if not meta.get("description"):
            fail("a subagent with no `description` is never delegated to", agent)
        # Both subagents are read-only by design. A write tool in one is how a "just have a look"
        # fan-out edits a customer's repository.
        #
        # **No `tools:` key is the worst case, not the best one, and has to be checked before
        # the per-name scan rather than falling through it.** `meta.get("tools") or ""`
        # against an absent key produced `""`, and `re.search` against `""` never matches --
        # so a subagent that declared no `tools:` at all passed this check silently. Claude
        # Code reads that the other way: an agent with no `tools:` key gets *every* tool it
        # knows about, Write included, which is exactly the escalation this check exists to
        # refuse. An explicit list is what makes the read-only promise checkable at all.
        if "tools" not in meta:
            fail("has no `tools:` key. Claude Code grants every tool to a subagent that "
                 "declares none, Write included -- both Gridline subagents must list an "
                 "explicit, read-only set", agent)
        else:
            for banned in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                if re.search(rf"\b{banned}\b", meta.get("tools") or ""):
                    fail(f"lists the {banned} tool. Both Gridline subagents are read-only sweeps; a "
                         f"write tool here means a fan-out can edit a customer's code", agent)

    hooks = check_json(PLUGIN / "hooks/hooks.json")
    if not (hooks.get("hooks") or {}).get("PreToolUse"):
        fail("no PreToolUse hook. The secret guard is what makes the credential skill "
             "shippable, and without it that skill must not ship either", PLUGIN / "hooks/hooks.json")
    else:
        check_guard_is_reachable(manifest, mcp, hooks)

    if problems:
        print(f"\n{len(problems)} problem(s). Every one of these degrades to silence in a real "
              f"session, which is why they are checked here.")
        return list(problems)

    print(f"plugin: {len(skills)} skills, "
          f"{len(list((PLUGIN / 'commands').glob('*.md')))} commands, "
          f"{len(list((PLUGIN / 'agents').glob('*.md')))} subagents, manifests and hook all load.")
    return list(problems)


# A stand-in for the guard hook, carrying only the three names the checker reads off it. Written
# out rather than pointed at the real one so a mutation below changes the manifest and nothing
# else, and so this stays a test of the agreement between two files rather than of either file.
GUARD_STUB = '''\
"""A guard hook, reduced to what decides which tools a matcher has to select."""
import re

ALWAYS_ASK = {"delete_thing": "deletes the thing and cannot be undone"}
GRIDLINE_TOOL = re.compile(r"^mcp__(?:plugin_acme-plugin_)?acme__")
CASES = [
    ("ask", "delete_thing",
     {"tool_name": "mcp__plugin_acme-plugin_acme__delete_thing", "tool_input": {}}),
    ("deny", "a credential on a command line",
     {"tool_name": "Bash", "tool_input": {"command": "x"}}),
    ("", "an ordinary read",
     {"tool_name": "mcp__plugin_acme-plugin_acme__list_things", "tool_input": {}}),
]
'''


def _minimal_plugin(root: Path) -> None:
    """A plugin tree with every required part present and valid, so a selftest mutation
    starts from a tree this checker accepts and can attribute a new failure to the one
    thing it broke."""
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin/plugin.json").write_text(json.dumps({
        "name": "acme-plugin", "version": "0.0.1", "description": "a test plugin",
    }))
    (root / ".mcp.json").write_text(json.dumps({
        "mcpServers": {"acme": {"type": "http", "url": "${ACME_MCP_URL:-https://x}"}}
    }))
    (root / "skills/foo").mkdir(parents=True)
    (root / "skills/foo/SKILL.md").write_text(
        "---\nname: foo\ndescription: does foo things\n---\n\nBody.\n"
    )
    (root / "commands").mkdir()
    (root / "agents").mkdir()
    (root / "agents/reader.md").write_text(
        "---\ndescription: reads things\ntools: Read, Grep\n---\n\nBody.\n"
    )
    (root / "hooks").mkdir()
    (root / "hooks/hooks.json").write_text(json.dumps({"hooks": {"PreToolUse": [{
        "matcher": "Bash|mcp__plugin_acme-plugin_acme__.*",
        "hooks": [{"type": "command", "command": "python3 guard.py"}],
    }]}}))
    (root / "hooks/guard.py").write_text(GUARD_STUB)
    (root / "README.md").write_text(
        "# acme\n\nAllow the read-only ones:\n\n"
        '```json\n{"permissions": {"allow": '
        '["mcp__plugin_acme-plugin_acme__list_things"]}}\n```\n'
    )


def selftest() -> int:
    """Feeds `check_plugin_tree` a valid plugin, proves it passes, then breaks one thing at a
    time and proves each break is refused.

    Every case here is a shape that otherwise degrades to silence: a subagent declaring no
    `tools:` at all, a matcher that never selects a tool the guard forces a confirmation on,
    and a documented permission entry naming a tool by a spelling nothing is ever called by.
    None of them error in a real session, so a checker that stopped catching one would look
    exactly like a tree with nothing wrong with it.
    """
    import tempfile

    problems: list[str] = []

    def expect(claim: str, holds: bool) -> None:
        if not holds:
            problems.append(claim)

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _minimal_plugin(root)
        expect(
            "a valid plugin tree with an explicit read-only tools: list passes",
            not check_plugin_tree(root),
        )

        # No `tools:` key at all -- not an empty one, not one naming Read/Grep. That absence
        # reads as `""` to `meta.get("tools") or ""`, and `re.search` against `""` never
        # matches, so it is the case a per-name scan passes over in silence. Claude Code
        # reads the same absence as *every* tool, Write included.
        (root / "agents/reader.md").write_text("---\ndescription: reads things\n---\n\nBody.\n")
        found = check_plugin_tree(root)
        expect(
            "a subagent with no tools: key at all is refused, not treated as matching "
            "no banned tool",
            any("no `tools:` key" in one for one in found),
        )

        # And the ordinary case is untouched: an explicit list naming a banned tool is
        # still refused for the reason it always was.
        (root / "agents/reader.md").write_text(
            "---\ndescription: reads things\ntools: Read, Write\n---\n\nBody.\n"
        )
        found = check_plugin_tree(root)
        expect(
            "an explicit tools: list naming Write is still refused",
            any("lists the Write tool" in one for one in found),
        )
        (root / "agents/reader.md").write_text(
            "---\ndescription: reads things\ntools: Read, Grep\n---\n\nBody.\n"
        )

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _minimal_plugin(root)
        hooks = root / "hooks/hooks.json"
        readme = root / "README.md"
        intact = hooks.read_text()

        # **A matcher that names the bundled server the way an unbundled one would.** The
        # guard is untouched and its own selftest would still pass; what is broken is the
        # only file that decides whether it is ever invoked, and the tool it stops selecting
        # is the one the guard forces a confirmation on.
        hooks.write_text(intact.replace(
            "mcp__plugin_acme-plugin_acme__.*", "mcp__acme__.*"))
        found = check_plugin_tree(root)
        expect(
            "a matcher that never selects a tool the guard forces a confirmation on is "
            "refused",
            any("never selects 'mcp__plugin_acme-plugin_acme__delete_thing'" in one
                for one in found),
        )

        # **The half that already worked has to be held too.** Dropping an ordinary tool
        # from the matcher is the same defect and just as quiet, so the guard's own cases
        # are what pin it rather than the MCP names alone.
        hooks.write_text(intact.replace("Bash|", ""))
        found = check_plugin_tree(root)
        expect(
            "a matcher that stops selecting an ordinary tool the guard answers for is "
            "refused",
            any("never selects 'Bash'" in one for one in found),
        )

        hooks.write_text(intact)
        expect(
            "the tree is accepted again once the matcher is restored",
            not check_plugin_tree(root),
        )

        # The same mistake in prose. A permission entry is matched against the name Claude
        # Code sends, so one written any other way is as inert as the matcher was.
        readme.write_text(readme.read_text().replace(
            "mcp__plugin_acme-plugin_acme__list_things", "mcp__acme__list_things"))
        found = check_plugin_tree(root)
        expect(
            "a documented permission entry naming a spelling the plugin's tools never "
            "arrive under is refused",
            any("mcp__acme__list_things" in one and "never applies" in one for one in found),
        )

    for one in problems:
        print(f"  FAIL: {one}")
    if problems:
        print("\nThis script no longer catches something it exists to catch, so a tree it "
              "passes says nothing.")
        return 1
    print("selftest passed: a valid plugin passes; a subagent with no tools: key and one "
          "naming a banned tool are both refused; and a matcher or a documented permission "
          "entry that never selects the tools the guard gates is refused.")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    plugin = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "plugin"
    return 1 if check_plugin_tree(plugin) else 0


if __name__ == "__main__":
    sys.exit(main())
