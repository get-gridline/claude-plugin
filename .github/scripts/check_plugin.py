#!/usr/bin/env python3
"""Refuse a plugin whose parts do not load, since almost none of it fails loudly.

**Everything in a Claude Code plugin degrades to silence.** A skill whose frontmatter will not
parse never triggers. A `description` over the cap is truncated, so a skill fires on half its
triggers. An MCP server pointing nowhere yields no tools and no error the user connects to the
plugin. A command referencing a skill that was renamed does nothing. None of these break a
session -- they quietly subtract capability, and the user's experience is "Gridline's plugin
doesn't seem to do much".

So this is the equivalent of the chart checks in `make chart`: read the files together and assert
the things that are otherwise discovered by a customer.

Deliberately parsing rather than importing a YAML library: the frontmatter is a handful of scalar
keys, and the control plane's dependencies have no business being installed to check a plugin.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# **The plugin root is an argument, because it is `plugin/` here and the repository root in the
# published mirror.** Checking only the layout in this repository would leave the one customers
# actually install unverified -- and the two differ in exactly the way that matters, since every
# path below is relative to this. `publish-plugin.yml` runs it against the assembled tree.
PLUGIN = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "plugin"
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


def main() -> int:
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
        for banned in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            if re.search(rf"\b{banned}\b", meta.get("tools") or ""):
                fail(f"lists the {banned} tool. Both Gridline subagents are read-only sweeps; a "
                     f"write tool here means a fan-out can edit a customer's code", agent)

    hooks = check_json(PLUGIN / "hooks/hooks.json")
    if not (hooks.get("hooks") or {}).get("PreToolUse"):
        fail("no PreToolUse hook. The secret guard is what makes the credential skill "
             "shippable, and without it that skill must not ship either", PLUGIN / "hooks/hooks.json")

    if problems:
        print(f"\n{len(problems)} problem(s). Every one of these degrades to silence in a real "
              f"session, which is why they are checked here.")
        return 1

    print(f"plugin: {len(skills)} skills, "
          f"{len(list((PLUGIN / 'commands').glob('*.md')))} commands, "
          f"{len(list((PLUGIN / 'agents').glob('*.md')))} subagents, manifests and hook all load.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
