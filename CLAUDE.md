# DevTrust: a reuse checker for developers and AI coding agents

## What this project is
A tool, with a measured evaluation, that:
1. finds existing functions in a repository from a natural-language description (reuse search);
2. reviews a code change (git diff) and flags newly added functions that duplicate or closely resemble code already in the repo (duplication review);
3. measures how often real AI coding agents (Claude Code, Codex, Copilot, Cursor, Devin, Jules) add code that duplicates what already exists, compared with human developers.

Origin: as a full-stack engineer on SaaS products, I kept seeing developers, and increasingly AI coding assistants, reimplement utilities that already existed in the repo, because text search can't find them under different names. I built DevTrust to solve that problem for myself and measured how well it works.

Purpose: a finished, honest personal project I can show to professors (software engineering, ML/IR, agentic AI) in MSc applications. It is not a paper. Priority order: working tool, then real measured results, then a clean write-up.

## Research questions
- RQ1 (search): How do BM25, dense embedders (general vs. code-specific), hybrid fusion, and cross-encoder reranking compare for finding existing functions in a repo from a short description?
- RQ2 (review): Does structural verification reduce false positives of embedding-based duplicate detection in Python diffs, compared with embedding-only and jscpd baselines?
- RQ3 (AI agents in the wild): In real Python repositories, do pull requests written by AI coding agents (Claude Code, OpenAI Codex, Copilot, Cursor, Devin, Jules) add functions that duplicate existing code more often than human pull requests? How does this differ by agent? Measured with the detector validated in RQ2, on the AIDev dataset.

## Related work
The Phase 0 literature study is in `docs/related_work.md` (about 50 papers and tools from more than 20 groups) and `docs/positioning.md`. Items marked ⚑ there are unverified; do not cite them as fact.

Key points that constrain this project:
- None of DevTrust's components is new. Embedding-based duplicate flagging on PRs also already exists: "More Code, Less Reuse" (MSR 2026), jscpd `--semantic`, and CLIONE.
- DevTrust's contribution is a validated, reproducible comparison plus a usable tool. Never claim "novel", "first", or "state-of-the-art".
- BigCloneBench is Java-only and its semantic labels are unreliable, so don't use it. The Roy & Cordy mutation framework has no Python support, so we reimplement the operators with `ast` and cite the method.

## Honesty rules (non-negotiable)
- Never invent, estimate, or hardcode result numbers. All numbers come from scripts in `eval/` and are written to `results/*.json`. README tables are generated from those files.
- Every results file records: git commit hash, config, random seed, dataset name/version, model names and revisions, and the date.
- Never tune on the test set. Use a dev split for thresholds and hyperparameters; touch the test split once per final run.
- Every model, benchmark, or baseline named in the README must actually have been run. If one could not run, say so.
- README and docs must label each feature as implemented, partial, or planned. Don't describe planned work as done.
- Embedding similarity alone is not proof of duplication. Report a candidate with evidence and confidence, never as a confirmed duplicate.

## Scope
- In scope:
  - Python repositories, function-level indexing.
  - BM25, dense retrieval, hybrid fusion, reranking.
  - Evaluation.
  - Duplication review of git diffs.
  - CLI.
  - The RQ3 study of AI-agent pull requests (AIDev); an MCP server as a stretch goal.
- Out of scope:
  - Web frontend, JS/TS support, defect prediction, change impact analysis, databases beyond local files.
  - List these under "future work" in the README.

## Tech stack
- Python 3.11+. The project uses `.venv`, created with `uv venv --python 3.12`; the system Python is 3.10.
- Pinned `requirements.txt`, pytest, `ast` (stdlib).
- `rank_bm25`, `sentence-transformers`, `numpy`, plain numpy cosine search.
- subprocess git; `typer` for the CLI; the `mcp` SDK for Phase 6.
- Must run on CPU; GPU optional. Keep dependencies minimal.

## Thin slice: a small, hand-picked set (all CPU-feasible)
This is a personal project. Keep it small and finished, not big and unfinished. Don't add models, benchmarks, or baselines beyond this list without asking me. Extras go under "future work".

| Part | Choice |
|---|---|
| Lexical | BM25, with identifier splitting on/off as the only ablation |
| General embedder | BAAI/bge-small-en-v1.5 |
| Code embedder | nomic-ai/CodeRankEmbed |
| Fusion | RRF (BM25 + best embedder) |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Search benchmarks | own hand-labelled repos (primary); CoIR CosQA (standard comparison) |
| Review baselines | embedding-only max-cosine; jscpd (token mode and `--semantic` mode) |
| AI-agent study (RQ3) | AIDev dataset (hao-li/AIDev on Hugging Face, CC-BY-4.0), Python repos only, agent PRs vs. human PRs in the same repos |
| MCP tool for agents | stretch goal, only after RQ3 is finished |

## Repository layout
```
devtrust/
  indexer/       # parse repo -> list of FunctionUnit
  retrieval/     # bm25.py, dense.py, hybrid.py, rerank.py
  duplication/   # diff parsing, candidate search, structural comparison, report
  mcp_server.py  # Phase 6
  cli.py
eval/
  retrieval_eval.py    # RQ1: own labelled repos + external benchmarks
  duplication_eval.py  # RQ2
  agent_eval.py        # RQ3
  metrics.py
data/            # labelled queries and annotation notes (versioned JSON)
results/         # JSON outputs, committed
tests/
README.md
```

## Build in phases. Finish and test each before starting the next.

### Phase 1: Indexer
- Walk a repo and parse `.py` files with `ast`. Extract each function and method as a `FunctionUnit`: name, qualified name, signature, docstring, body source (with and without docstring), file path, start and end line, decorators, and imports used.
- Skip tests, vendored dirs, and unparsable files. Count and report parse failures.
- Unit tests on small fixture repos.

### Phase 2: Retrieval
- Query = natural-language description. Document text = name + signature + body; the docstring is included or excluded by a config flag.
- Implement:
  - BM25, with snake_case and camelCase identifier splitting as an ablation.
  - Dense retrieval, with a configurable model.
  - RRF hybrid fusion.
  - Cross-encoder reranking of the top N.
- Every retriever exposes `search(query, k) -> list[(FunctionUnit, score)]`.
- Cache embeddings on disk, keyed by content hash and model.
- Record indexing time, query latency, and model size for the systems metrics.

### Phase 3: Retrieval evaluation (RQ1)
- Primary benchmark: 3 Python repos, with 50–80 hand-written short-description queries in total and labelled correct functions. Store labels in `data/` as versioned JSON with annotator notes. If possible, have a second annotator label a subset and report Cohen's κ.
- Standard benchmark: the CoIR CosQA split, zero-shot NDCG@10, comparable with CoIR's published numbers. Always state the candidate pool.
- Metrics: MRR, NDCG@10, Recall@1/5/10, P@K, bootstrap 95% CIs, paired tests between methods, plus latency, index time, and model size.
- Deliverables: an ablation table and an error analysis (queries where every method fails, with examples).

### Phase 4: Duplication review (RQ2)
- Input: a git diff or commit range. Extract added or modified functions.
- For each, query the index of the repo state BEFORE the change, excluding the function's own previous version. Filter moved and renamed functions, and measure how well that filter works.
- Run structural comparison on the top candidates: normalised AST/token similarity, with identifiers and literals renamed.
- Report per finding:
  - the new function, and the matching existing function(s) with file and line
  - retrieval score and structural score
  - confidence level and category (`likely_duplicate`, `similar_but_different`, `insufficient_evidence`)
  - the evidence shown side by side
- Never claim certainty. Never auto-modify code.

### Phase 5: Duplication evaluation
- Positives:
  - Synthetic Type 1–3 variants from a small `ast`-based reimplementation of Roy & Cordy-style mutation operators.
  - A small hand-written Type-4 set (same behaviour, different code).
  - These are synthetic; state that as a limitation.
- Negatives: hand-made similar-looking but functionally different functions (client vs. endpoint, sibling validators, one-edit functional variants), plus unrelated functions.
- Baselines:
  - embedding-only max-cosine (as in "More Code, Less Reuse")
  - jscpd, token mode and `--semantic` mode
  - Verify each one runs, and report honestly if it doesn't.
- Metrics: precision, recall, F1, and false-positive rate, **per clone type**. Also report retrieval-only vs. retrieval + structural. Choose thresholds on dev and report on test.

### Phase 6: AI-agent duplication study (RQ3)
- Data: AIDev-pop subset, restricted to Python repositories with enough agent PRs. Pick about 5–10 repos and record the selection rule.
  - Human PRs from the same repos and time window form the comparison set.
  - ⚑ Verify how AIDev provides human PRs. If it doesn't, fetch them from the GitHub API and document the method.
- For each PR:
  - Check out the base commit and index it.
  - Run DevTrust review on the PR's added functions.
  - Filter moves and renames.
- Report per agent and for humans:
  - share of PRs with a `likely_duplicate` finding
  - duplicates per added function
  - with bootstrap CIs and a significance test
- Also report a manual audit of a random sample of findings, with the precision observed on real data.
- Extends "More Code, Less Reuse" (MSR 2026), which covered one repo with an unvalidated embedding metric: several repos, per agent, validated detector. Cite it and don't overclaim. A null result is still a result.
- Stretch, only after this is done: an MCP server exposing `search_existing_functions` and `review_diff`.

### Phase 7: CLI, packaging, write-up
- `devtrust index <repo>`, `devtrust search "<query>"`, `devtrust review --diff <range>`.
- `make reproduce` (or one documented command) regenerates every README table from scratch.
- README sections:
  - motivation (origin story)
  - demo GIF
  - method
  - results (real numbers only)
  - limitations
  - related work
  - future work
  - how to reproduce
- Also a one-page write-up in `docs/`.

## Decision log (mandatory)
- Every significant decision goes into `docs/DECISIONS.md` as it's made: what, why, what was rejected, and the evidence. Covered: choices of models, data, repos, thresholds, metrics, scope, and dependency pins, plus surprising findings.
- Update the status table at the top when a phase changes state.
- Keep the "Likely interview questions" table current.
- Don't rely on chat history. Future sessions start from this file and DECISIONS.md.

## Engineering rules
- Small commits, one phase at a time. Run `pytest` before every commit.
- Type hints and docstrings on public functions.
- Fixed random seeds. Deterministic outputs where possible.
- When something is ambiguous (dataset details, metric definitions), stop and ask me instead of guessing.
- At the end of each phase, summarise what is implemented, what is not, and what I should verify manually.
