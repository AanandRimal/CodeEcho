# DevTrust

By Aanand Rimal, built with AI assistance (Claude Code). The project is directed and owned by the author; see [Who made what](#who-made-what) for exactly which parts the AI drafted.

A reuse checker for developers and AI coding agents. It finds functions that already exist in a Python repository from a plain-language description, flags newly added functions that closely resemble existing code, and measures how often AI coding agents' pull requests do that compared with human ones.

This is a personal project with a measured evaluation, not a paper. Every number below is generated from `results/*.json` by scripts in `eval/`. Nothing here is estimated or typed by hand. Where something was not run, this README says so.

## Why this exists

As a full-stack engineer on SaaS products, I kept seeing developers, and increasingly AI coding assistants, reimplement utilities that already existed in the repository, because text search cannot find them when they are named differently. I built DevTrust to solve that for myself, then measured how well it works.

## What is implemented

| Part | Status |
|---|---|
| Indexer: Python repo to function-level units, with a parse-failure report | Implemented, tested |
| Search: BM25, dense retrieval (bge-small, CodeRankEmbed), RRF fusion, cross-encoder rerank | Implemented, evaluated (RQ1) |
| Duplication review of a git diff (retrieval, then structural check, with side-by-side evidence) | Implemented, evaluated on synthetic and hand-written cases (RQ2) |
| CLI: `index`, `search`, `review` | Implemented, tested |
| Study of AI-agent vs human PRs on three real repos (RQ3) | Pipeline implemented; see the RQ3 section for whether results exist |
| Demo GIF | Planned, not recorded |
| MCP server (`search_existing_functions`, `review_diff`) | Planned (stretch goal), not started |
| CoIR CosQA comparison, human-vs-AI label agreement check | Dropped, not run (see `docs/DECISIONS.md` D26) |

## Use it

```bash
uv venv --python 3.12 && uv pip install -r requirements.txt   # CPU only; Python 3.11+

.venv/bin/python -m devtrust.cli index path/to/repo           # parse report, warm embedding cache
.venv/bin/python -m devtrust.cli search "build a stable cache key from a request" --repo path/to/repo
.venv/bin/python -m devtrust.cli review --diff main..my-branch --repo path/to/repo
```

`review` reports candidates, each with the new function, the existing function it resembles (file and lines), a retrieval score, a structural score, a category (`likely_duplicate`, `similar_but_different`, `insufficient_evidence`) and the two functions side by side. Embedding similarity is not proof of duplication, so findings are candidates for a human to check. The tool never changes code.

## Method

- **Indexer.** `ast` parses every non-test, non-vendored `.py` file into one unit per function or method (name, signature, docstring, body, lines, decorators, imports used). Files that fail to parse are counted and reported.
- **Search.** The query is a short description. The indexed text is name, signature and body; the docstring is left out by default so labels cannot leak through it. Compared settings: BM25 (with and without splitting snake_case and camelCase), `BAAI/bge-small-en-v1.5`, `nomic-ai/CodeRankEmbed`, reciprocal rank fusion (k=60) of BM25 and CodeRankEmbed, and a `cross-encoder/ms-marco-MiniLM-L6-v2` reranker over the top 50. Models are pinned to exact revisions.
- **Review.** For each function a diff adds, the repository state before the change is searched with CodeRankEmbed (top 5, the function's own previous version excluded). Each candidate gets a structural score: similarity of the two functions' AST node sequences, ignoring identifier names and literal values. Functions that were only moved or renamed (identical body to one removed in the same change) are filtered out.
- **RQ1 benchmark.** 60 queries (20 per repo) on instructor, fastmcp and crewAI at pinned commits, 51 of them answerable and 9 deliberately unanswerable. Candidate functions were pooled from all search settings and judged blind (shuffled, method hidden). Relevance labels are AI-drafted; see "Who made what".
- **RQ2 benchmark.** Positives: Type-1/2/3 variants made by an `ast` reimplementation of Roy & Cordy-style mutation operators applied to 60 real functions, plus 25 hand-written Type-4 pairs (same behaviour, different code). Negatives: 60 unrelated functions from another repo, plus 22 hand-written look-alike pairs with different behaviour (siblings, client vs endpoint, one-edit variants). The hand-written pairs were checked by executing both sides. Thresholds were chosen on a dev split, and the test split was read once.
- **RQ3 study.** Merged agent PRs from the AIDev dataset (`hao-li/AIDev`, CC-BY-4.0) for the same three repos, against a seeded random sample of merged human PRs from the GitHub API in the same time window. Only functions a PR adds are counted. Full design: `docs/DECISIONS.md` D32.

## Results

### RQ1: how well does search find the right function?

<!-- BEGIN:retrieval -->
| Search setting | MRR [95% CI] | NDCG@10 [95% CI] | Recall@1 | Recall@5 | Recall@10 [95% CI] | ms/query (CPU) |
|---|---|---|---|---|---|---|
| BM25 | 0.28 [0.18, 0.38] | 0.29 [0.20, 0.40] | 0.13 | 0.38 | 0.41 [0.28, 0.54] | 9 |
| BM25, no identifier splitting | 0.20 [0.11, 0.30] | 0.22 [0.12, 0.32] | 0.14 | 0.26 | 0.29 [0.17, 0.42] | 8 |
| bge-small-en-v1.5 | 0.60 [0.49, 0.72] | 0.59 [0.49, 0.69] | 0.35 | 0.61 | 0.71 [0.60, 0.81] | 23 |
| CodeRankEmbed | 0.72 [0.62, 0.81] | 0.74 [0.66, 0.82] | 0.42 | 0.79 | 0.91 [0.84, 0.96] | 130 |
| RRF (BM25 + CodeRankEmbed) | 0.53 [0.40, 0.65] | 0.51 [0.40, 0.63] | 0.32 | 0.53 | 0.63 [0.50, 0.74] | 159 |
| RRF + cross-encoder rerank (top 50) | 0.39 [0.28, 0.51] | 0.40 [0.30, 0.51] | 0.17 | 0.42 | 0.55 [0.42, 0.67] | 2842 |

| Search setting | MRR, easy queries | MRR, hard queries |
|---|---|---|
| BM25 | 0.29 | 0.27 |
| BM25, no identifier splitting | 0.25 | 0.18 |
| bge-small-en-v1.5 | 0.97 | 0.45 |
| CodeRankEmbed | 0.96 | 0.62 |
| RRF (BM25 + CodeRankEmbed) | 0.71 | 0.45 |
| RRF + cross-encoder rerank (top 50) | 0.69 | 0.27 |

51 answerable queries over 3 repos (9 unanswerable queries not scored). Labels are AI-drafted. 1 query was missed by every setting at rank 10.

_Generated from `results/` on 2026-11-09, commit `860e70a`._
<!-- END:retrieval -->

On this benchmark the code-specific embedder was best on every metric, the general embedder second, and BM25 well behind. Two results were unexpected: fusing BM25 into CodeRankEmbed scored below CodeRankEmbed alone, and the cross-encoder reranker (trained on web passages, not code) made rankings worse and slower. Both explanations are untested guesses. Confidence intervals are wide with 51 queries, so small gaps should not be over-read.

### RQ2: does a structural check reduce false positives?

<!-- BEGIN:duplication -->
| Method | Precision | Recall | F1 | False-positive rate |
|---|---|---|---|---|
| Embedding-only (max cosine) | 0.87 | 0.89 | 0.88 | 0.34 |
| Retrieval + structural (F1 threshold) | 0.86 | 0.92 | 0.89 | 0.37 |
| Retrieval + structural (tool default 0.9) | 0.94 | 0.81 | 0.87 | 0.12 |
| jscpd, token mode | 1.00 | 0.10 | 0.18 | 0.00 |
| jscpd, token mode, min 20 tokens | 0.83 | 0.28 | 0.42 | 0.15 |
| jscpd --semantic | 0.91 | 0.28 | 0.43 | 0.07 |
| jscpd --semantic, min 20 tokens | 0.84 | 0.36 | 0.51 | 0.17 |

| Method (recall) | type1 | type2 | type3 | type4 |
|---|---|---|---|---|
| Embedding-only (max cosine) | 1.00 [1.00, 1.00] | 0.90 [0.77, 1.00] | 0.87 [0.73, 0.97] | 0.67 [0.42, 0.92] |
| Retrieval + structural (F1 threshold) | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.97 [0.90, 1.00] | 0.42 [0.17, 0.67] |
| Retrieval + structural (tool default 0.9) | 1.00 [1.00, 1.00] | 0.93 [0.83, 1.00] | 0.83 [0.70, 0.97] | 0.00 [0.00, 0.00] |
| jscpd, token mode | 0.30 [0.13, 0.47] | 0.03 [0.00, 0.10] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| jscpd, token mode, min 20 tokens | 0.90 [0.80, 1.00] | 0.07 [0.00, 0.17] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| jscpd --semantic | 0.83 [0.70, 0.97] | 0.07 [0.00, 0.17] | 0.07 [0.00, 0.17] | 0.00 [0.00, 0.00] |
| jscpd --semantic, min 20 tokens | 1.00 [1.00, 1.00] | 0.13 [0.03, 0.27] | 0.03 [0.00, 0.10] | 0.17 [0.00, 0.42] |

| Method (false-positive rate) | unrelated (n=30) | sibling (n=4) | client_endpoint (n=3) | one_edit (n=4) |
|---|---|---|---|---|
| Embedding-only (max cosine) | 0.17 | 1.00 | 0.33 | 1.00 |
| Retrieval + structural (F1 threshold) | 0.20 | 0.75 | 0.67 | 1.00 |
| Retrieval + structural (tool default 0.9) | 0.00 | 0.50 | 0.00 | 0.75 |
| jscpd, token mode | 0.00 | 0.00 | 0.00 | 0.00 |
| jscpd, token mode, min 20 tokens | 0.00 | 0.50 | 0.00 | 1.00 |
| jscpd --semantic | 0.00 | 0.50 | 0.00 | 0.25 |
| jscpd --semantic, min 20 tokens | 0.00 | 0.50 | 0.33 | 1.00 |

Test split only (143 cases). Thresholds chosen on the dev split (144 cases): embedding cosine 0.390, structural 0.539. Precision is over each row's positives against all negatives.

_Generated from `results/` on 2026-11-09, commit `cdd2c5e`._
<!-- END:duplication -->

- At the thresholds that maximise F1 on the dev split, adding the structural check did not reduce the overall false-positive rate compared with embedding-only; the difference is within noise.
- At the tool's untuned default (structural score at least 0.9) the false-positive rate is much lower, but Type-4 recall is zero and Type-3 recall drops. This is a threshold trade-off. Embedding-only was not given an equally strict setting, so the two are not compared on equal footing.
- Every method flags functions that differ by a single behaviour-changing token, and most look-alike siblings. This is the main limit on this test.
- jscpd was precise but missed most renamed and modified copies (it matches tokens), and `--semantic` recovered only a small share of Type-4 at its calibrated threshold.
- The search step rarely lost the original: the true source was in the top 5 for nearly every positive, so errors come mostly from the scoring step.

### RQ3: do AI-agent pull requests duplicate existing code more often than human ones?

<!-- BEGIN:agents -->
**Primary analysis** (the design fixed before the run, `docs/DECISIONS.md` D32): every flagged function counts.

| Group | PRs | PRs with new functions | New functions reviewed | Flagged | Share of PRs with a flagged function [95% CI] | Flagged per new function [95% CI] |
|---|---|---|---|---|---|---|
| Human | 440 | 108 | 1127 | 127 | 0.35 [0.26, 0.44] | 0.113 [0.081, 0.150] |
| Claude_Code | 203 | 60 | 482 | 89 | 0.23 [0.13, 0.35] | 0.185 [0.078, 0.326] |
| Devin | 52 | 19 | 57 | 0 | 0.00 [0.00, 0.00] | 0.000 [0.000, 0.000] |
| OpenAI_Codex | 48 | 10 | 37 | 4 | 0.30 [0.00, 0.60] | 0.108 [0.000, 0.171] |
| All analysed agents pooled | 303 | 89 | 576 | 93 | 0.19 [0.11, 0.27] | 0.161 [0.072, 0.277] |

| Agent vs human | Diff in share | p | p (Holm) | Diff in rate | p | p (Holm) |
|---|---|---|---|---|---|---|
| Claude_Code | -0.119 | 0.283 | 0.567 | +0.0720 | 0.123 | 0.246 |
| Devin | -0.352 | <0.001 | <0.001 | -0.1127 | 0.006 | 0.019 |
| OpenAI_Codex | -0.052 | 1.000 | 1.000 | -0.0046 | 0.941 | 0.941 |
| All analysed agents pooled | -0.161 | 0.017 | n/a | +0.0488 | 0.270 | n/a |

**Sensitivity analysis** (added after reading the audit sample, D33): findings whose matched function no longer exists at the PR's head are not counted, because the PR moved or renamed that function (a move combined with edits slips past the exact-body move filter).

| Group | PRs | PRs with new functions | New functions reviewed | Flagged | Share of PRs with a flagged function [95% CI] | Flagged per new function [95% CI] |
|---|---|---|---|---|---|---|
| Human | 440 | 108 | 1127 | 84 | 0.27 [0.19, 0.35] | 0.075 [0.052, 0.102] |
| Claude_Code | 203 | 60 | 482 | 35 | 0.17 [0.08, 0.27] | 0.073 [0.033, 0.119] |
| Devin | 52 | 19 | 57 | 0 | 0.00 [0.00, 0.00] | 0.000 [0.000, 0.000] |
| OpenAI_Codex | 48 | 10 | 37 | 4 | 0.30 [0.00, 0.60] | 0.108 [0.000, 0.171] |
| All analysed agents pooled | 303 | 89 | 576 | 39 | 0.15 [0.08, 0.22] | 0.068 [0.034, 0.105] |

| Agent vs human | Diff in share | p | p (Holm) | Diff in rate | p | p (Holm) |
|---|---|---|---|---|---|---|
| Claude_Code | -0.102 | 0.453 | 0.906 | -0.0019 | 0.929 | 0.929 |
| Devin | -0.269 | 0.007 | 0.022 | -0.0745 | 0.010 | 0.031 |
| OpenAI_Codex | +0.031 | 1.000 | 1.000 | +0.0336 | 0.459 | 0.917 |
| All analysed agents pooled | -0.122 | 0.063 | n/a | -0.0068 | 0.747 | n/a |

Groups with too few PRs with new functions to analyse (under 10): Copilot, Cursor. Permutation tests shuffle agent/human labels within each repo; "Holm" adjusts across the agents tested; the pooled row is not part of that family. "Flagged" means a structural score of at least 0.9 against a retrieved function, counted for functions the PR adds (at least 10 AST nodes).

**Manual audit** (40 random flagged findings out of 223, judged by an AI, not blind, no human check): 16 real duplicates, 15 where the PR itself removed or moved the matched function, 9 similar in shape but not duplicates. Precision 0.40 [0.25, 0.55] overall, and 0.64 among the 25 findings whose matched function still exists at the PR head.

_Generated from `results/` on 2026-11-10, commit `739ca17`._
<!-- END:agents -->

## Limitations

- **Labels and test data are AI-written.** The RQ1 queries and relevance labels, and the hand-written RQ2 pairs, were produced by Claude. There was no independent human check of the labels (the planned agreement check was dropped). The RQ1 candidate pool came from the same search settings that were evaluated, so recall may be slightly optimistic.
- **Small samples.** 51 answerable queries over 3 repos; very small groups of hand-written negatives (4, 3 and 4 in the test split). Confidence intervals are wide.
- **Synthetic positives are easier than real duplicates.** Types 1 to 3 come from the same 30 test originals, so those rows are correlated. Thresholds were set on synthetic data.
- **The structural score cannot see semantics.** Differing in one constant, operator or called function barely changes it, and a reimplementation written differently scores low.
- **Move/rename filter** matches exact bodies only.
- **RQ3.** Humans may use AI assistants without labelling it, and AIDev's agent labels have their own error. Agent and human PRs differ in size and kind. Only three repositories are covered, so most agents have few PRs and Google Jules and Copilot are essentially absent. Findings are candidates; precision on real code comes only from the audit in the RQ3 section.
- Python only, function level only, CPU only.

## Related work

None of DevTrust's components is new. Embedding-based flagging of duplicate code in pull requests already exists: "More Code, Less Reuse" (Huang et al., MSR 2026) ranks each PR by the maximum cosine similarity between new functions and base functions, using CodeSage embeddings. It reports the analysis for one repository and, as far as I could tell, does not validate the detector against labelled data. `jscpd` has an experimental `--semantic` mode that embeds functions with CodeRankEmbed, and CLIONE targets clone changes in pull-request workflows. Reciprocal rank fusion is from Cormack et al. (SIGIR 2009), the mutation-operator idea from Roy & Cordy (2009), and CodeRankEmbed from the CoRNStack work (Suresh et al., ICLR 2025). DevTrust's contribution is a reproducible comparison with the baselines run on the same cases, a usable tool, and a per-agent study across three repositories. The literature notes, including items I could not verify, are in `docs/related_work.md` and `docs/positioning.md`.

## Who made what

- **Written by the author (Aanand Rimal):** the project idea, research questions, scope and the decisions recorded in `docs/DECISIONS.md`.
- **Drafted by an AI model (Claude, via Claude Code):** almost all of the code in `devtrust/` and `eval/`, the 60 benchmark queries and their relevance labels (every label records `claude-opus-5-5` as annotator), the hand-written RQ2 pairs, the audit judgments in RQ3, and the first drafts of `docs/` and this README.
- Two Claude models worked on this project at different times: Opus 5.5 (the benchmark labels, the first phases) and Sonnet 5.5 (later phases). Commit messages carry a Claude co-author line, but because it names the model active when each commit was made, it does not always match the model that wrote earlier-drafted work.

## Future work

Not done, and not claimed: JavaScript/TypeScript support; the MCP server; an independent human label check for RQ1; a CoIR CosQA run for comparison with published numbers; precision-recall curves and equal-operating-point comparisons for RQ2; more repositories and per-agent power for RQ3; a controlled experiment where agents are given the repo with and without DevTrust.

## How to reproduce

```bash
uv venv --python 3.12 && uv pip install -r requirements.txt
npm install --prefix .cache/tools jscpd@5.4.3
.cache/tools/node_modules/.bin/jscpd --semantic-download      # 548 MB model for jscpd --semantic
echo "GITHUB_TOKEN=<read-only token for public repos>" > .env  # for the RQ3 human PRs; .env is git-ignored
make reproduce                                                 # tests, then every result file, then the README tables
```

`make reproduce` takes many hours on CPU (about 20 minutes for RQ1 and RQ2 once models are cached, the rest for RQ3). Individual steps: `python -m eval.retrieval_eval`, `python -m eval.duplication_eval --jscpd --final`, `python -m eval.agent_data`, `python -m eval.agent_eval run`, `python -m eval.agent_eval analyze`, `python -m eval.report`. Every results file records the git commit, configuration, seed, dataset and model revisions, and the date. Every decision, with its reasoning and what was rejected, is in `docs/DECISIONS.md`.
