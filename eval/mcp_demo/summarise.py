"""Summarise results/mcp_demo: reuse = the agent's file imports from the repo (no reimplementation).
Usage: .venv/bin/python -m eval.mcp_demo.summarise.  n=16 runs; a demo, not a statistical result (D34)."""
import datetime as dt, json, re, subprocess
from collections import defaultdict
from pathlib import Path

D = Path("results/mcp_demo")
rows = [l.split("\t") for l in (D / "runs.tsv").read_text().splitlines()[1:] if l != "DONE"]
out, models = defaultdict(lambda: defaultdict(list)), set()
for task, cond, rep, *_ in rows:
    src = (D / "raw" / f"{task}-{cond}-{rep}.py").read_text()
    out[cond][task].append(bool(re.search(r"^from (eval|devtrust)\S* import", src, re.M)))
    models |= set(json.loads((D / "raw" / f"{task}-{cond}-{rep}.json").read_text()).get("modelUsage", {}))
summary = {"meta": {"date": dt.date.today().isoformat(), "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
           capture_output=True, text=True).stdout.strip(), "models_used_by_agent": sorted(models),
           "tasks": 4, "reps": 2, "note": "demo only; tasks written by Claude, who knew the helpers exist; "
           "agent also had Grep/Read in both conditions; reuse judged by an import check on the saved file"},
           "reused_runs": {c: {t: f"{sum(v)}/{len(v)}" for t, v in ts.items()} for c, ts in out.items()},
           "reused_total": {c: f"{sum(sum(v) for v in ts.values())}/{sum(len(v) for v in ts.values())}" for c, ts in out.items()}}
(D / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary, indent=1))
