# AGENTS.md — twskillz

Standing rules for this repository. Claude Code reads this file automatically at the start of
every session, so keep it short and keep every line earned.

**What this repo is:** a Claude Code plugin marketplace holding Tim's skills. Each skill ships
as a plugin; the root catalog lists them. People install with two commands and get everything.

---

## Structural rules

These are mechanical requirements, not preferences. Getting one wrong produces a plugin that
silently fails to load rather than an error message, which is why they are written down.

**One catalog, at the root.** `.claude-plugin/marketplace.json` must be at the repository
root. Nowhere else is read.

**Only `plugin.json` goes inside `.claude-plugin/`.** This is the most common mistake in the
whole system. `skills/`, `agents/`, `hooks/`, `commands/`, `.mcp.json` and everything else
live at the *plugin* root — the directory containing `.claude-plugin/`, never `~/.claude/`.

**Skills are directories.** `skills/<name>/SKILL.md`. The folder name becomes the invocation
name, namespaced by plugin: `skills/loop-forge/` inside plugin `loop-forge` is
`/loop-forge:loop-forge`.

**Every SKILL.md needs `description` in its frontmatter.** That description is the entire
triggering mechanism — Claude decides whether to consult a skill by reading it. No
description means the skill exists and never fires. Write it to include both what the skill
does and the situations that should invoke it.

**Plugins are copied to a cache on install.** A plugin therefore cannot reference files
outside its own directory — no `../shared-utils`. Anything a skill's scripts need must sit
inside that skill or that plugin. When adding a plugin, check its scripts resolve paths
relative to themselves.

**Relative `source` paths only work for git-added marketplaces.** Adding via a direct URL to
`marketplace.json` will not resolve them. Since this repo is installed from GitHub, relative
paths are correct here.

**Bump `version` when you change anything.** Users only receive updates when that field
changes. Omit it and the commit SHA is used instead, which makes every commit a new version.
Bump both the plugin manifest and its catalog entry together.

Reference: https://code.claude.com/docs/en/plugins and
https://code.claude.com/docs/en/plugin-marketplaces

---

## Adding a plugin

1. Create `plugins/<name>/` (or a themed subfolder, as `loop-engineering/` does) with
   `.claude-plugin/plugin.json` and a `skills/<skill-name>/SKILL.md`.
2. Add an entry to the root `.claude-plugin/marketplace.json` with `name` and `source`.
3. Test before committing: `claude --plugin-dir ./path/to/plugin`, then `/reload-plugins`
   after edits rather than restarting.
4. Run `claude plugin validate .` from the repo root.
5. Bump versions, commit, push.

Nobody has to re-add the marketplace when a plugin is added — that is the reason this repo is
a marketplace rather than a single plugin.

## Working style

- Read this file first. It is the only context that carries between sessions.
- Do not restructure working plugins to fix an unrelated problem. Smallest change first.
- Prefer a check that fails over a rule written in prose. A validation script is a constraint;
  a line in a markdown file is a request.
- Data are plural. "The data are", not "the data is".
