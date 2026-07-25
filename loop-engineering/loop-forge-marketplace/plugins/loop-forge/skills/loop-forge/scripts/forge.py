#!/usr/bin/env python3
"""forge.py — generate a loop scaffold from LOOPSPEC.yaml.

    python scripts/forge.py --spec LOOPSPEC.yaml --out ../my-project
    python scripts/forge.py --spec LOOPSPEC.yaml --out . --dry-run

Generation is a pure function of the spec, so regenerating after an edit is cheap.
That is the reason the spec exists as a separate step: one forty-line file gets
reviewed by a human, and thirty generated files do not.

The renderer is deliberately home-made rather than jinja2. Two reasons: no
dependency to install on a teammate's machine, and unresolved `{{ ... }}` is left
untouched rather than blanked, which matters because GitHub Actions expressions
like ${{ github.ref }} live inside the workflow template and jinja2 would silently
eat them.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("forge needs pyyaml:  pip install pyyaml")

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"

# ---------------------------------------------------------------------------- #
# a very small template renderer: {{ path }}, {% if path %}, {% for x in path %}
# ---------------------------------------------------------------------------- #

TAG = re.compile(r"\{%\s*(if|for|endif|endfor)\b([^%]*)%\}")
VAR = re.compile(r"\{\{\s*([A-Za-z_][\w.]*)\s*\}\}")


def resolve(path: str, ctx: dict):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def substitute(text: str, ctx: dict) -> str:
    def one(m):
        val = resolve(m.group(1), ctx)
        # Unknown names are left exactly as written. This is what keeps
        # ${{ github.ref }} intact inside the CI template.
        return m.group(0) if val is None else str(val)
    return VAR.sub(one, text)


def render(text: str, ctx: dict) -> str:
    out: list[str] = []
    pos = 0
    while True:
        m = TAG.search(text, pos)
        if not m:
            out.append(substitute(text[pos:], ctx))
            return "".join(out)

        out.append(substitute(text[pos:m.start()], ctx))
        kind, arg = m.group(1), m.group(2).strip()
        if kind in ("endif", "endfor"):
            raise ValueError(f"unbalanced {{% {kind} %}}")

        depth, p, inner, after = 1, m.end(), None, None
        while depth:
            m2 = TAG.search(text, p)
            if not m2:
                raise ValueError(f"unclosed {{% {kind} %}}")
            depth += 1 if m2.group(1) in ("if", "for") else -1
            p = m2.end()
            if depth == 0:
                inner, after = text[m.end():m2.start()], p

        if kind == "if":
            if resolve(arg, ctx):
                out.append(render(inner, ctx))
        else:
            var, _, seq_path = arg.partition(" in ")
            for item in (resolve(seq_path.strip(), ctx) or []):
                out.append(render(inner, {**ctx, var.strip(): item}))
        pos = after


# ---------------------------------------------------------------------------- #
# validation — these refusals are the point, not obstacles to work around
# ---------------------------------------------------------------------------- #

def validate(spec: dict) -> list[str]:
    errs = []
    v = spec.get("verify", {})
    gates = v.get("gates") or []

    if not gates:
        errs.append(
            "verify.gates is empty. Without a check that fails, there is no stop\n"
            "  condition, and without a stop condition there is no loop -- just an agent\n"
            "  that runs until it feels finished. See reference/verifier-patterns.md.")

    if gates and not any(g.get("blocking", True) for g in gates):
        errs.append("no blocking gate. Advisory-only means nothing can ever fail the loop.")

    if not v.get("command"):
        errs.append("verify.command is required: the one command that returns non-zero\n"
                    "  when the work is not finished.")

    deny = spec.get("deny") or []
    if not deny:
        errs.append(
            "deny is empty. Whatever the verifier reads to decide -- tests, contracts,\n"
            "  reference outputs, the verifier itself, gate.yaml -- must be listed. An\n"
            "  agent that can edit its own criteria has no criteria, and every green\n"
            "  result it produces is meaningless.")

    if spec.get("autonomy", {}).get("default") == "L3":
        errs.append(
            "autonomy.default is L3 on a first generation. Nobody should start\n"
            "  unattended. Set L1, run for a week, read the diffs, then promote.")

    unit = spec.get("goal", {}).get("unit", "")
    if len(unit) > 200:
        errs.append("goal.unit is over 200 characters -- that is usually a project\n"
                    "  wearing a unit's clothing. Find the smallest useful increment.")

    for key in ("project.name", "goal.name", "verify.pattern"):
        if resolve(key, spec) is None:
            errs.append(f"{key} is required.")
    return errs


# ---------------------------------------------------------------------------- #
# context enrichment — templates stay dumb, all logic happens here
# ---------------------------------------------------------------------------- #

def build_context(spec: dict) -> dict:
    ctx = {
        "project": spec.get("project", {}),
        "goal": spec.get("goal", {}),
        "verify": dict(spec.get("verify", {})),
        "deny": spec.get("deny", []),
        "autonomy": dict(spec.get("autonomy", {})),
        "trigger": dict(spec.get("trigger", {})),
        "stop": {"max_attempts": 6, "no_progress": 3, **(spec.get("stop") or {})},
        "notes": dict(spec.get("notes") or {}),
    }

    v = ctx["verify"]
    gates = v.get("gates") or []
    for g in gates:
        g.setdefault("blocking", True)
        g["cmd_repr"] = repr(g.get("cmd", ""))
    v["gates"] = gates
    v["blocking_ids"] = ", ".join(g["id"] for g in gates if g["blocking"])
    v["first_gate"] = gates[0]["id"] if gates else "L0"

    adv = v.get("advisory") or []
    v["advisory"] = adv
    v["has_advisory"] = bool(adv)
    v["advisory_ids"] = ", ".join(a["id"] for a in adv)

    a = ctx["autonomy"]
    a.setdefault("default", "L1")
    pg = a.get("per_goal") or {}
    a["has_per_goal"] = bool(pg)
    a["per_goal_list"] = [{"key": k, "value": val} for k, val in pg.items()]

    t = ctx["trigger"]
    kind = t.get("type", "manual")
    for k in ("schedule", "push", "manual", "file-arrival"):
        t[f"is_{k.split('-')[0]}"] = (kind == k)
    t.setdefault("cron", "0 8 * * 1-5")

    n = ctx["notes"]
    stub = n.get("stubbed") or []
    n["stubbed"] = stub
    n["has_stubbed"] = bool(stub)
    n["no_stubbed"] = not stub
    return ctx


# ---------------------------------------------------------------------------- #
# what each size generates
# ---------------------------------------------------------------------------- #

MINIMAL = [
    ("LOOP.md.tmpl", "LOOP.md"),
    ("STATE.md.tmpl", "STATE.md"),
    ("verify.py.tmpl", "harness/verify.py"),
    ("run_loop.sh.tmpl", "harness/run_loop.sh"),
]

STANDARD = MINIMAL + [
    ("AGENTS.md.tmpl", "AGENTS.md"),
    ("gate.yaml.tmpl", "gate.yaml"),
    ("check_deny.py.static", "harness/check_deny.py"),
    ("loop-run-log.md.tmpl", "loop-run-log.md"),
    ("implementer.md.tmpl", ".claude/agents/implementer.md"),
]

FULL = STANDARD + [
    ("loop-budget.md.tmpl", "loop-budget.md"),
    ("verifier.md.tmpl", ".claude/agents/verifier.md"),
    ("pre_commit.sh.static", "harness/hooks/pre_commit.sh"),
    ("post_edit.sh.static", "harness/hooks/post_edit.sh"),
    ("ci.yml.tmpl", ".github/workflows/loop.yml"),
]

SIZES = {"minimal": MINIMAL, "standard": STANDARD, "full": FULL}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a loop from LOOPSPEC.yaml")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text())

    errs = validate(spec)
    if errs:
        print("Refusing to generate:\n", file=sys.stderr)
        for e in errs:
            print(f"  - {e}\n", file=sys.stderr)
        print("These are design problems, not configuration problems. Fix the spec.",
              file=sys.stderr)
        return 1

    size = spec.get("size", "standard")
    if size not in SIZES:
        return print(f"unknown size {size!r}; use minimal|standard|full", file=sys.stderr) or 1

    ctx = build_context(spec)
    out = Path(args.out)
    written, skipped = [], []

    for tmpl_name, dest_rel in SIZES[size]:
        src = TEMPLATES / tmpl_name
        if not src.exists():
            print(f"  ! missing template {tmpl_name}", file=sys.stderr)
            continue
        dest = out / dest_rel

        if tmpl_name.endswith(".static"):
            text = src.read_text()
        else:
            text = render(src.read_text(), ctx)

        if args.dry_run:
            print(f"  would write {dest_rel} ({len(text)} bytes)")
            continue
        if dest.exists() and not args.force:
            skipped.append(dest_rel)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
        if dest.suffix in (".sh", ".py"):
            dest.chmod(0o755)
        written.append(dest_rel)

    if args.dry_run:
        return 0

    # The spec travels with the loop. Someone reading LOOP.md in six months needs to
    # know what it was generated from and what can be regenerated.
    spec_dest = out / "LOOPSPEC.yaml"
    if not spec_dest.exists() or args.force:
        shutil.copy2(args.spec, spec_dest)
        written.append("LOOPSPEC.yaml")

    print(f"\nGenerated {len(written)} files in {out} (size: {size})")
    for w in written:
        print(f"  + {w}")
    if skipped:
        print("\nSkipped (already present; use --force to overwrite):")
        for s in skipped:
            print(f"  = {s}")

    print(f"\nNext, and do this before anything else:\n\n"
          f"    cd {out} && {ctx['verify']['command']}\n\n"
          f"It should FAIL. A verifier that passes before any work has been done is not\n"
          f"measuring the thing you care about. Then start at "
          f"{ctx['autonomy']['default']}:\n\n"
          f"    bash harness/run_loop.sh --goal {ctx['goal']['name']} "
          f"--level {ctx['autonomy']['default']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
