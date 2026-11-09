"""RQ2: does structural verification reduce false positives of embedding-only duplicate detection?

Usage:
  .venv/bin/python -m eval.duplication_eval            # build cases, score, choose thresholds, print DEV metrics only
  .venv/bin/python -m eval.duplication_eval --final    # also report TEST metrics and write results/duplication.json

Setup (docs/DECISIONS.md D29): the index is the instructor repo at its pinned commit plus the "existing"
half of every hand-written pair. A case is one "new function"; the question is whether it is flagged as
duplicating something in the index.
  positives: type1/type2/type3 = synthetic mutations (eval/mutate.py) of 60 real instructor functions;
             type4 = hand-written same-behaviour reimplementations (data/duplication/handwritten.json)
  negatives: unrelated = 60 real functions from fastmcp; sibling / client_endpoint / one_edit =
             hand-written similar-looking but behaviourally different functions
Dev/test split is by group, stratified per case kind (all mutations of one original stay together). Thresholds are chosen on dev
only; the test split is read once, by --final.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

from devtrust.duplication.review import review_function
from devtrust.duplication.structural import structure
from devtrust.indexer import FunctionUnit, index_repo
from devtrust.retrieval.dense import REVISION, DenseRetriever
from eval.metrics import bootstrap_ci
from eval.mutate import type1, type2, type3
from eval.repos import checkout, load_repos

SEED, N_ORIG, N_UNRELATED, TOP_K = 0, 60, 60, 5
REPO, OTHER = "567-labs/instructor", "PrefectHQ/fastmcp"
WORK = Path(".cache/dup_eval")
JSCPD = Path(".cache/tools/node_modules/.bin/jscpd")
POSITIVE = ("type1", "type2", "type3", "type4")
NEGATIVE = ("unrelated", "sibling", "client_endpoint", "one_edit")
OUT = Path("results/duplication.json")


def assign_splits(cases: list[dict]) -> None:
    """Stratified dev/test split by group: within each case family, groups are ordered by a seeded hash
    and alternate dev, test, dev, ... (all mutations of one original stay together; every kind is halved)."""
    family = lambda c: "orig" if c["kind"] in ("type1", "type2", "type3") else c["kind"]
    groups = {c["group"]: family(c) for c in cases}
    split = {}
    for fam in sorted(set(groups.values())):
        members = sorted((g for g, f in groups.items() if f == fam),
                         key=lambda g: hashlib.sha256(f"{SEED}|{g}".encode()).hexdigest())
        split.update({g: ("dev" if i % 2 == 0 else "test") for i, g in enumerate(members)})
    for c in cases:
        c["split"] = split[c["group"]]


def _sample(units: list[FunctionUnit], n: int, rng: random.Random) -> list[FunctionUnit]:
    ok = [u for u in units if 25 <= len(structure(u)) <= 300 and u.end_line - u.start_line >= 5]
    return rng.sample(sorted(ok, key=lambda u: (u.file_path, u.start_line)), n)


def build_cases() -> tuple[list[dict], list[FunctionUnit]]:
    """Returns (cases, index units). Writes the base index files and one query file per case to WORK."""
    shutil.rmtree(WORK, ignore_errors=True)
    base, queries = WORK / "base", WORK / "queries"
    src_root = checkout(REPO)
    units = index_repo(src_root).functions
    for fp in sorted({u.file_path for u in units}):                 # exactly the indexed files, for every method
        (base / fp).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / fp, base / fp)
    pairs = json.loads(Path("data/duplication/handwritten.json").read_text())
    for p in pairs:                                                  # the "existing" half of each hand-written pair
        (base / "hw_extras" / f"hw_{p['id']}.py").parent.mkdir(parents=True, exist_ok=True)
        (base / "hw_extras" / f"hw_{p['id']}.py").write_text(p["source_a"] + "\n")
    index = index_repo(base).functions
    by_key = {(u.file_path, u.start_line): u for u in index}

    cases = []
    for u in _sample(units, N_ORIG, random.Random(SEED)):
        gid = f"orig:{u.file_path}:{u.start_line}"
        for kind, f in (("type1", lambda s, r: type1(s)), ("type2", type2), ("type3", type3)):
            rng = random.Random(f"{SEED}|{gid}|{kind}")
            cases.append({"id": f"{kind}|{u.file_path}:{u.start_line}", "kind": kind, "group": gid,
                          "source": f(u.source, rng), "truth": [f"{u.file_path}:{u.start_line}"]})
    other = index_repo(checkout(OTHER)).functions
    for u in _sample(other, N_UNRELATED, random.Random(SEED + 1)):
        cases.append({"id": f"unrelated|{u.file_path}:{u.start_line}", "kind": "unrelated",
                      "group": f"unrel:{u.file_path}:{u.start_line}", "source": u.source, "truth": []})
    for p in pairs:
        kind = "type4" if p["kind"] == "type4" else p["kind"].removeprefix("negative_")
        a = next(x for x in index if x.file_path == f"hw_extras/hw_{p['id']}.py")
        cases.append({"id": f"{kind}|{p['id']}", "kind": kind, "group": f"hw:{p['id']}", "source": p["source_b"],
                      "truth": [f"{a.file_path}:{a.start_line}"] if kind == "type4" else []})
    for c in cases:
        c["file"] = str(Path("queries") / (hashlib.sha1(c["id"].encode()).hexdigest()[:12] + ".py"))
        (WORK / c["file"]).parent.mkdir(parents=True, exist_ok=True)
        (WORK / c["file"]).write_text(c["source"] + "\n")
    assign_splits(cases)
    return cases, index


def score_cases(cases: list[dict], index: list[FunctionUnit]) -> None:
    """Adds retrieval and structural scores (our detector, and the embedding-only baseline's score)."""
    retriever = DenseRetriever(index, model_name="nomic-ai/CodeRankEmbed")
    qunits = {u.file_path: u for u in index_repo(WORK / "queries").functions[::-1]}   # first (outer) function wins
    for c in cases:
        unit = qunits[Path(c["file"]).name]
        matches = review_function(unit, retriever, TOP_K)
        best = max(matches, key=lambda m: m.structural_score)
        c["top1_cosine"] = matches[0].retrieval_score
        c["best_structural"] = best.structural_score
        c["best_match"] = f"{best.unit.file_path}:{best.unit.start_line}"
        keys = [f"{m.unit.file_path}:{m.unit.start_line}" for m in matches]
        c["truth_rank"] = next((i for i, k in enumerate(keys, 1) if k in c["truth"]), None)


def choose_threshold(cases: list[dict], key: str) -> float:
    """Threshold on `key` (flag if score >= t) maximising F1 on these cases; ties go to the higher t."""
    best_t, best_f1 = 1.0, -1.0
    for t in sorted({c[key] for c in cases}):
        f1 = prf(cases, lambda c, t=t: c[key] >= t)["f1"]
        if f1 >= best_f1:
            best_t, best_f1 = t, f1
    return best_t


def prf(cases: list[dict], flag, kind: str | None = None) -> dict:
    """Precision/recall/F1 over positives (all types, or just `kind`) vs ALL negatives; plus FPR."""
    pos = [c for c in cases if c["kind"] in POSITIVE and (kind is None or c["kind"] == kind)]
    neg = [c for c in cases if c["kind"] in NEGATIVE]
    tp, fp = sum(flag(c) for c in pos), sum(flag(c) for c in neg)
    p, r = (tp / (tp + fp) if tp + fp else 0.0), (tp / len(pos) if pos else 0.0)
    return {"n_pos": len(pos), "n_neg": len(neg), "tp": tp, "fp": fp, "precision": p, "recall": r,
            "f1": 2 * p * r / (p + r) if p + r else 0.0, "fpr": fp / len(neg) if neg else 0.0}


def report(cases: list[dict], methods: dict) -> dict:
    """Per method: overall and per-type metrics, and FPR per negative kind, with bootstrap CIs on recall/FPR."""
    out = {}
    for name, flag in methods.items():
        row = {"overall": prf(cases, flag)}
        for k in POSITIVE:
            row[k] = prf(cases, flag, k)
            vec = [float(flag(c)) for c in cases if c["kind"] == k]
            if vec:
                row[k]["recall_ci"] = bootstrap_ci(vec, SEED)[1:]
        row["fpr_by_negative_kind"] = {}
        for k in NEGATIVE:
            vec = [float(flag(c)) for c in cases if c["kind"] == k]
            if vec:
                m, lo, hi = bootstrap_ci(vec, SEED)
                row["fpr_by_negative_kind"][k] = {"n": len(vec), "fpr": m, "ci": [lo, hi]}
        out[name] = row
    return out


def run_jscpd(mode: str, small: bool) -> set[str]:
    """Run jscpd once over base + all query files; returns the query files it links to a base file.

    Any clone kind counts (with --semantic jscpd reports both exact and semantic clones, as shipped).
    Defaults are jscpd's own (min 50 tokens, 5 lines, calibrated semantic thresholds); `small` lowers the
    minimum size to 20 tokens / 3 lines so short functions are not skipped. Nothing else is tuned.
    """
    out_dir = WORK / f"jscpd_{mode}{'_small' if small else ''}"
    cmd = [str(JSCPD), str(WORK / "base"), str(WORK / "queries"), "--format", "python", "--reporters", "json",
           "--output", str(out_dir), "--silent"]
    cmd += ["--semantic"] if mode == "semantic" else []
    cmd += ["--min-tokens", "20", "--min-lines", "3"] if small else []
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3 * 3600)
    data = json.loads((out_dir / "jscpd-report.json").read_text())
    qnames = {p.name for p in (WORK / "queries").glob("*.py")}     # jscpd reports bare file names relative to each root
    linked: set[str] = set()
    for d in data.get("duplicates", []):
        a, b = Path(d["firstFile"]["name"]).name, Path(d["secondFile"]["name"]).name
        for q, other in ((a, b), (b, a)):
            if q in qnames and other not in qnames:
                linked.add(q)
    return linked


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", action="store_true", help="report the TEST split and write results/")
    ap.add_argument("--jscpd", action="store_true", help="also run the jscpd baselines (slow in semantic mode)")
    args = ap.parse_args()

    cases, index = build_cases()
    score_cases(cases, index)
    dev = [c for c in cases if c["split"] == "dev"]
    t_emb, t_struct = choose_threshold(dev, "top1_cosine"), choose_threshold(dev, "best_structural")
    methods = {"embedding_only": lambda c: c["top1_cosine"] >= t_emb,
               "retrieval_plus_structural": lambda c: c["best_structural"] >= t_struct}
    if args.jscpd:
        for mode in ("token", "semantic"):
            for small in (False, True):
                name = f"jscpd_{mode}{'_small' if small else ''}"
                flags = run_jscpd(mode, small)
                for c in cases:
                    c[name] = Path(c["file"]).name in flags
                methods[name] = lambda c, n=name: c[n]
    print(f"cases: {len(cases)} (dev {len(dev)}, test {len(cases) - len(dev)}); "
          f"thresholds chosen on dev: embedding_only {t_emb:.4f}, structural {t_struct:.4f}")
    dev_report = report(dev, methods)
    (WORK.parent / "dup_eval_dev_cases.json").write_text(json.dumps(dev, indent=1))   # dev only, for inspection
    for name, r in dev_report.items():
        o = r["overall"]
        print(f"DEV {name:26s} P {o['precision']:.2f} R {o['recall']:.2f} F1 {o['f1']:.2f} FPR {o['fpr']:.2f}")
    if not args.final:
        return
    test = [c for c in cases if c["split"] == "test"]
    test_report = report(test, methods)
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "meta": {"date": dt.date.today().isoformat(), "git_commit": git("rev-parse", "HEAD"),
                 "git_dirty": bool(git("status", "--porcelain", "--", ".", ":!results")), "seed": SEED,
                 "index_repo": {"name": REPO, "commit": load_repos()[REPO]["commit"]},
                 "unrelated_from": {"name": OTHER, "commit": load_repos()[OTHER]["commit"]},
                 "n_originals": N_ORIG, "n_unrelated": N_UNRELATED, "top_k": TOP_K,
                 "retriever": {"model": "nomic-ai/CodeRankEmbed", "revision": REVISION["nomic-ai/CodeRankEmbed"]},
                 "handwritten": "data/duplication/handwritten.json (AI-written, behaviour-verified; D29)",
                 "thresholds_chosen_on_dev": {"embedding_only_top1_cosine": t_emb, "structural": t_struct},
                 "jscpd": args.jscpd, "n_dev": len(dev), "n_test": len(test)},
        "dev": dev_report, "test": test_report, "cases": cases}, indent=1) + "\n")
    for name, r in test_report.items():
        o = r["overall"]
        print(f"TEST {name:26s} P {o['precision']:.2f} R {o['recall']:.2f} F1 {o['f1']:.2f} FPR {o['fpr']:.2f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
