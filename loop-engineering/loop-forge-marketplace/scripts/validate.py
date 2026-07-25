#!/usr/bin/env python3
"""Repo verifier. Runs in CI on every push.

The plugin that generates verifiers ought to have one. If this repo can ship a
broken marketplace.json, or a forge.py that no longer renders, or a forge.py whose
refusals have quietly stopped working, it has no business telling anyone else
about gates.

Same design rule as everything it generates: success is silent, failure is
verbose and specific enough to act on.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent.parent
FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if not ok:
        FAILS.append(f"{name}: {detail}")


# --- catalog and manifests are well-formed ---------------------------------- #
try:
    mkt = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    check("marketplace.name", "name" in mkt, "missing")
    check("marketplace.plugins", bool(mkt.get("plugins")), "no plugins listed")
    for p in mkt.get("plugins", []):
        check("plugin entry", "name" in p and "source" in p,
              f"{p} needs both name and source")
        check("plugin source exists", (REPO_ROOT / p.get("source", "")).is_dir(),
              f"{p.get('source')} not found")
except Exception as e:
    check("marketplace.json", False, f"will not parse: {e}")

for man in ROOT.glob("plugins/*/.claude-plugin/plugin.json"):
    try:
        m = json.loads(man.read_text())
        check(f"{man.parent.parent.name} manifest",
              "name" in m and "description" in m, "needs name and description")
    except Exception as e:
        check(str(man), False, f"will not parse: {e}")

# --- every skill has usable frontmatter ------------------------------------- #
for skill in ROOT.glob("plugins/*/skills/*/SKILL.md"):
    text = skill.read_text()
    check(f"{skill.parent.name} frontmatter", text.startswith("---"),
          "no YAML frontmatter")
    head = text.split("---")[1] if text.count("---") >= 2 else ""
    check(f"{skill.parent.name} description", "description:" in head,
          "no description field, so the skill will never trigger")

# --- forge still renders ----------------------------------------------------- #
forge = ROOT / "plugins/loop-forge/skills/loop-forge/scripts/forge.py"
examples = sorted((ROOT / "plugins/loop-forge/skills/loop-forge/examples").glob("*.yaml"))
check("examples present", bool(examples), "no example specs to smoke-test against")

for spec in examples:
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run([sys.executable, str(forge), "--spec", str(spec), "--out", td],
                           capture_output=True, text=True)
        check(f"forge {spec.name}", p.returncode == 0, p.stderr.strip()[:300])
        check(f"forge {spec.name} wrote LOOP.md", (Path(td) / "LOOP.md").exists(), "missing")
        check(f"forge {spec.name} wrote a verifier",
              (Path(td) / "harness/verify.py").exists(), "missing")

# --- and forge still refuses ------------------------------------------------- #
# The refusals are the feature, so they get a test. A generator that silently
# stops declining bad specs is worse than no generator: it launders them.
bad = {"project": {"name": "x", "description": "y"}, "size": "standard",
       "goal": {"name": "g", "unit": "u"},
       "verify": {"pattern": "none", "gates": []}, "deny": [],
       "autonomy": {"default": "L3"}, "trigger": {"type": "manual"}}
with tempfile.TemporaryDirectory() as td:
    sp = Path(td) / "bad.yaml"
    sp.write_text(json.dumps(bad))      # JSON is valid YAML
    p = subprocess.run([sys.executable, str(forge), "--spec", str(sp), "--out", td],
                       capture_output=True, text=True)
    check("forge refuses a spec with no verifier and no denylist",
          p.returncode == 1, "it generated anyway -- the guard rails are off")

if FAILS:
    print("FAILED:\n" + "\n".join(f"  - {f}" for f in FAILS), file=sys.stderr)
    sys.exit(1)
print("all checks passed")
