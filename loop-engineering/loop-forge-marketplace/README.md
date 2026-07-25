# loop-forge-marketplace

A Claude Code plugin marketplace hosting **loop-forge** — a skill that designs and generates
agentic loops for a project instead of leaving each person to invent their own.

---

## Install

Two commands, in Claude Code:

```
/plugin marketplace add YOUR-ORG/loop-forge-marketplace
/plugin install loop-forge@loop-forge-marketplace
```

Then `/reload-plugins`, or start a new session.

Replace `YOUR-ORG/loop-forge-marketplace` with wherever you push this. Private repositories
work — Claude Code uses the user's existing git credentials, so anyone with read access to
the repo can install without extra setup.

## Use

The skill is model-invoked: describe what you want and it triggers on its own.

> "I want to set up a loop for our nightly pipeline so I stop checking it every morning."

It can also be called directly as `/loop-forge:loop-forge`. (Plugin skills are namespaced by
plugin name, which is why it reads twice — the namespace prevents collisions when you add a
second plugin here later.)

## What it does

1. **Reads your repo first.** Existing tests, CI config, linters, schemas — all of it becomes
   the verifier, and every inferred answer is a question it does not have to ask.
2. **Interviews you.** Six questions maximum, one at a time, and only about the gaps.
3. **Writes a `LOOPSPEC.yaml`** — about forty lines, which you review and argue with. This is
   the step that matters. Nobody reviews thirty generated files.
4. **Generates the loop** at one of three sizes: 4, 9, or 15+ files.
5. **Runs the generated verifier** and shows you it failing, because a verifier that passes
   before any work has been done is not measuring anything.

It refuses to generate when there is no machine-checkable stop condition, when the denylist
is empty, when the "unit of work" is really a project, or when someone sets unattended
autonomy on a first generation. Those refusals are the feature.

## Layout

```
.claude-plugin/marketplace.json     the catalog — what /plugin marketplace add reads
plugins/loop-forge/
  .claude-plugin/plugin.json        this plugin's manifest
  skills/loop-forge/
    SKILL.md                        the skill: workflow, interview, design rules
    reference/verifier-patterns.md  eight ways to build a stop condition, and when to refuse
    reference/interview.md          the question script and inference rules
    reference/loopspec-schema.md    spec fields and a worked example
    templates/                      what gets generated — edit these for house style
    scripts/forge.py                spec in, loop out. Only needs Python and pyyaml.
    examples/                       two filled specs: golden-outputs, and test-suite
evals/evals.json                    three test prompts, including one it should refuse
```

## Before you push this

Three placeholders to fill in:

- `.claude-plugin/marketplace.json` → `owner.name`, `owner.email`
- `plugins/loop-forge/.claude-plugin/plugin.json` → `author.name`
- `evals/evals.json` → replace my guesses with prompts your team would actually type

Then validate and push:

```bash
claude plugin validate .
git add . && git commit -m "loop-forge v1.0.0" && git push
```

## Making it yours

The templates are the point of customisation. Edit `templates/` to change what every
generated loop looks like for your team — your CI runner in `ci.yml.tmpl`, your escalation
channel pre-filled in `gate.yaml.tmpl`, your standard denylist entries, your house wording in
`AGENTS.md.tmpl`.

Bump `version` in both JSON files when you do. Users only receive updates when that field
changes, so a version bump is how you ship a template change to everyone.

## Adding more plugins later

This repo is a marketplace, not a single plugin, so a second one is a new directory under
`plugins/` and a new entry in `marketplace.json`. Nobody has to re-add the marketplace.

## Caveats worth repeating

An unattended loop makes unattended mistakes. The faster one ships code you did not write,
the wider the gap between what exists and what you understand, and that gap does not announce
itself. Everything this tool generates starts at L1 — report only, commits nothing — on
purpose. Promote deliberately, after reading a week of diffs.
