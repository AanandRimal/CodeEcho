# Decision log

Every significant decision in DevTrust, in order: **what** was decided, **why**, what was **rejected**, and the **evidence**. Updated as decisions are made. Section IDs like A1, B12, C6 refer to [related_work.md](related_work.md).

**Status (2026-11-09):**

| Phase | Status |
|---|---|
| 0 Literature | ✅ Done |
| 1 Indexer | ✅ Done |
| 2 Retrieval | ✅ Done |
| 3 Retrieval evaluation | 🟡 60 LLM-drafted queries and labels saved (D25, D26); metrics + eval done (D27); error analysis and README pending |
| 4 Duplication review | 🟡 Implemented and unit-tested; thresholds provisional, not yet evaluated (D28) |
| 5–7 | Not started |

---

## Phase 0: Literature study (2026-11-08)

### D1. Read the literature before writing any code
- **Decision:** Phase 0 (reading) comes before any project code.
- **Why:** to find out whether the idea already exists and what to compare against, so the project doesn't claim novelty it doesn't have.
- **How:**
  - Full texts were downloaded and read where accessible. Abstract-only items are marked.
  - Claims that couldn't be verified are flagged ⚑ in related_work.md and must not be cited as fact.
  - Background agents were used for breadth; their key quotes were checked by hand against the paper text.

### D2. Survey the whole field, not one research group
- **Decision:** expand from the 6 initial papers (all from Chanchal Roy's group) to about 50 papers and tools from more than 20 groups.
- **Why:** the project will be shown to many professors (SE, ML/IR, agentic AI). A study centred on one lab looks narrow and targeted.
- **Result:** related_work.md has three parts:
  - A: clone detection (Roy's group A1–A6, others A7–A15)
  - B: code search (B1–B20)
  - C: diff-time duplicates and AI reuse (C1–C13)

### D3. Positioning: not a new technique; the contribution is validation and a usable tool
- **Decision:** never claim "novel", "first", or "state-of-the-art".
- **Why:** every component already exists, and so does embedding-based duplicate flagging on PRs:
  - "More Code, Less Reuse", MSR 2026 (C6): embeds new Python PR functions vs. the base snapshot, but only one repo, and the detector was never validated.
  - jscpd `--semantic` (C5): open-source tool, unevaluated.
  - CLIONE (C2): APSEC 2020 PR bot, Python, token-based.
- **What is open:** nobody has *validated* such a detector against labelled duplicates and near-misses, or measured whether structural verification cuts embedding false positives. Prior evidence predicts it should: ExecRetrieval (A15) shows embeddings rank one-edit buggy variants as high as the original.

---

## Project shape (2026-11-09)

### D4. This is a personal project for MSc applications, not a paper
- **Decision:** priorities are a working tool first, then real measured results, then a clean write-up.
- **Why:** the goal is a finished, honest project to describe in emails to professors. A finished thin slice beats an unfinished big system.

### D5. Thin slice: a small, hand-picked set of models
- **Kept**, with the reason for each:

  | Choice | Why this one |
  |---|---|
  | BM25 + identifier-splitting ablation | the standard lexical baseline in code search (A5, B9). Splitting snake_case/camelCase is common practice (B9) but rarely ablated. |
  | BAAI/bge-small-en-v1.5 (33M parameters) | general-purpose embedder. BGE-family models were among the strongest small zero-shot models on CoIR CosQA (B7). Fast on CPU. |
  | nomic-ai/CodeRankEmbed (137M) | best small open code embedder in SweRank and CoRNStack function-level results (B11, B12). MIT licence. |
  | RRF, k=60 | the standard fusion method (Cormack et al. 2009). Only one prior code-search evaluation, and that one was repository-level (B19). |
  | cross-encoder/ms-marco-MiniLM-L6-v2 | widely used small reranker. Included *because* prior evidence on small off-the-shelf rerankers for code is negative (B13); testing that is informative. |

- **Dropped to future work:**
  - other embedders: E5, GTE, MiniLM, BGE-base, CodeSage, Jina, UniXcoder
  - weighted fusion and a second reranker
  - CodeSearchNet and RepoEval
  - GPTCloneBench
  - PMD/CPD, NiCad, and the call-overlap rule
- **Why:** each extra model adds runtime and code without adding a new insight. Five methods on two benchmarks already shows the comparison.
- **Rule:** no additions without asking the project owner (in CLAUDE.md).

### D6. Search benchmarks: own labelled repos + CoIR CosQA
- **Own labelled queries (primary):** the real setting, one repo's functions searched with short "I need X" descriptions. Nothing public matches it (B20).
- **CoIR CosQA (standard comparison):** real Python web queries, run zero-shot, with published numbers for BM25 and BGE-family models to compare against (B7).
- **Rejected:**
  - CodeSearchNet docstring queries: docstrings share vocabulary with the code (B1). CoIR reports overfitting on CSN (B7). CodeSage shows a docstring/signature "shortcut" (B10).
  - BigCloneBench: Java only, and 86–93% of its semantic labels are wrong in two audits (A12).

### D7. RQ2 (review) baselines: embedding-only and jscpd
- **Embedding-only max-cosine:** the exact metric used by "More Code, Less Reuse" (C6), so we test that method directly.
- **jscpd:** the closest existing open-source tool (C5). One install gives both a token-based mode and an embedding mode.
- **Rejected:**
  - NiCad: needs a TXL install; it's Roy's tool, and we wanted a less group-centred baseline.
  - PMD/CPD: covered by jscpd's token mode.
- **RQ2 wording:** "Does structural verification reduce false positives of embedding-based duplicate detection in Python diffs?"

### D8. RQ3 = measure real AI-agent PRs (AIDev), not run our own agents
- **Decision:** study existing PRs written by Claude Code, Codex, Copilot, Cursor, Devin, and Jules in AIDev (hao-li/AIDev, CC-BY-4.0), and compare them with human PRs in the same repos.
- **Why:**
  - It tests the origin story ("AI assistants rewrite existing utilities") on real data.
  - It covers six agents.
  - It needs no API budget.
  - It extends "More Code, Less Reuse" (C6): several repos instead of one, results per agent, and a validated detector instead of raw cosine.
- **Rejected:** a controlled experiment (agent with vs. without a DevTrust tool). It needs API budget for each agent and roughly doubles the work.
- **MCP server:** kept as a final stretch add-on, as an integration demo only, not as evidence.

### D9. Comparisons are field-wide, not against one group
- **Decision:** measured comparisons use work from many groups:
  - CoIR (Huawei)
  - BAAI / Nomic / sentence-transformers models
  - jscpd (independent)
  - C6 (Science Tokyo / NAIST / UBC)
  - AIDev (Queen's)
- **Why:** project-owner request. Roy's group appears only in citations for standard definitions (clone types) and the mutation method.

---

## Phase 1: Indexer (2026-11-09)

### D10. Python 3.12 through uv, in a project-local .venv
- **Why:** CLAUDE.md requires Python 3.11+, but the machine has 3.10. uv is in the planned tech stack. The system Python is untouched.

### D11. Indexer design
- **Parsing:** the stdlib `ast` module, no extra dependencies. Encoding declarations are honoured via `tokenize.open`.
- **Skipped:** test files and directories, vendored code, virtual environments, build output, hidden directories. They aren't reusable application code, and tests would pollute search results.
- **Parse failures:** reported, not hidden. Example: crewAI's 5 failures are Jinja template files.
- **What each function stores:** source with and without the docstring, so the docstring can be excluded from indexing (D13).
- **Finding:** qualified names aren't unique. The stdlib has 105 repeats, from property getter/setter pairs and conditional definitions. A function's unique key is file + start line, and the labels use both.
- **Sanity check:** Python 3.12 stdlib, 15,953 functions from 684 files in 5.2 s.

---

## Phase 2: Retrieval (2026-11-09)

### D12. Identifier splitting keeps the whole token plus its parts
- `parseHTTPResponse` yields `parsehttpresponse`, `parse`, `http`, `response`, so exact-name matches still work. Turning splitting off is the ablation.

### D13. Docstrings excluded from indexed text by default
- **Why:** queries often resemble docstrings, so indexing them would leak the answer (CSN, B1). Models also learn shortcuts from docstring/signature overlap (CodeSage, B10). It's a config flag.

### D14. Pin every model to an exact Hugging Face revision
- **Why:**
  - Reproducibility.
  - CodeRankEmbed runs code downloaded from its repo (`trust_remote_code`); pinning means that code can't change under us.
- **Also:** the embedding cache key includes the revision.

### D15. Pin sentence-transformers 5.7 / transformers 4.57
- **Why:** CodeRankEmbed's custom code (last updated June 2025) fails on transformers 5.x, which removed `get_extended_attention_mask`. sentence-transformers 6.x requires transformers 5.x.
- **Also:** CPU-only PyTorch, about 200 MB instead of several GB with CUDA.

### D16. Query prefixes taken from the model cards, verified from the raw READMEs
- BGE: "Represent this sentence for searching relevant passages: " (optional; helps short queries).
- CodeRankEmbed: "Represent this query for searching relevant code: " (required).

### D17. Functions truncated to 512 tokens
- **Why:** CPU cost. CodeRankEmbed supports 8192 tokens. This is a stated limitation.

### D18. Speed is a real constraint
- **Measured:** CodeRankEmbed took 479 s for 2,146 functions on CPU; BGE-small took 7 s. About 70× slower.
- **Consequence:** the RQ3 detector model will be chosen by the measured accuracy/speed trade-off in RQ2.
- **Also measured:** the reranker costs about 3 s per query (top 50) vs. 2–190 ms for the others.
- **Early anecdote, 4 queries, not a result:** CodeRankEmbed found the right function where BM25 and BGE didn't; the reranker didn't improve the top answer.

---

## Phase 3: Retrieval evaluation setup (2026-11-09)

### D19. Benchmark repos chosen from AIDev, so one set of repos runs through RQ1–RQ3
- **Selection rule:** Python, not a fork, at least 500 stars, at least 30 merged agent PRs, at least 3 distinct agents. 43 repos qualify. Then: permissive licence, mostly pure Python, 1k–10k functions.
- **Chosen**, pinned in data/repos.json:

  | Repo | Functions | Merged agent PRs | Licence |
  |---|---|---|---|
  | 567-labs/instructor | 1,158 | 91 | MIT |
  | PrefectHQ/fastmcp | 2,932 | 183 | Apache-2.0 |
  | crewAIInc/crewAI | 6,494 | 49 | MIT |

  Function counts are after D23. Before excluding examples/ and docs/ they were 1,470 / 3,292 / 6,518.

- **Why crewAI:** it's the repo C6 studied, so RQ3 can compare directly.
- **Rejected:** litellm (43,290 functions, too big). huggingface_hub is the backup.
- **Known limitation:** all three are LLM/agent frameworks, so generalising to other domains isn't shown.

### D20. The project owner writes the queries; tooling helps (superseded by D25)
- **Why:** queries should be real developer phrasing, and the README should be able to say truthfully "I wrote and labelled the queries".
- **Rejected:** having the AI draft the queries. That would bias them toward the code's own wording, and it couldn't honestly be described as self-written.

### D21. Pooled, blind judging (standard TREC practice)
- **Pool:** the union of the top 10 from all six evaluated configurations: BM25, BM25 without splitting, BGE-small, CodeRankEmbed, RRF, RRF+rerank.
- **Blind:** candidates are shown in a shuffled order, so the judge can't favour a method.
- **Missing answers:** can be added by name. Anything outside the pool counts as not relevant, the standard pooling limitation.
- **Unanswerable queries** are kept separately. They test whether tools return confident wrong answers.
- **Guarding against copied wording:** the helper warns when a query reuses words from the answer's name, and we'll report query/answer overlap.
- **Agreement:** a second annotator labels about 20 queries; we report Cohen's κ.
- **Guidelines:** data/ANNOTATION.md.

### D22. AIDev contains only agent PRs
- **Found:** the `pull_request` table holds 361,296 PRs, all from agents. The current dataset version is larger than the paper's figures.
- **Consequence:** human PRs for RQ3 must come from the GitHub API, same repos and time window. The method will be documented. Still to do.

### D23. Exclude `examples/` and `docs/` directories from the index
- **Found:** in the labelling smoke test, many pooled candidates were demo scripts, e.g. `examples/tenacity-benchmarks/run.py`.
- **Why exclude:** demo and documentation code isn't reusable library code. Nobody should "reuse" an example script instead of writing a helper, and flagging a new function as a duplicate of a demo isn't useful either. It also adds labelling noise.
- **Applies to:** both search and review.
- **Effect:** instructor 1,470 → 1,158 functions, fastmcp 3,292 → 2,932, crewAI 6,518 → 6,494.
- **Rejected:** also excluding `scripts/`. Those can contain real utilities.
- **Stated as a limitation:** a reimplementation placed in an examples folder isn't detected.

### D24. Keep pool depth 10, accepting the labelling cost
- **Found:** the six configurations mostly disagree, so pools hold 26–41 candidates per query (smoke test on instructor). At about 60 queries that's roughly 2,000 judgments.
- **Why keep depth 10:** the headline metrics (NDCG@10, Recall@10) need every system's full top 10 judged. With depth 5, anything at ranks 6–10 would count as non-relevant by default, which biases the results.
- **Rejected:** depth 5. That halves the effort but makes the @10 metrics unreliable. We'd fall back to reporting @5 only if labelling time becomes a hard constraint.
- **Side finding:** that much disagreement between methods is itself worth reporting in RQ1 (overlap of top-10 lists).

---

### D25. Queries and relevance labels drafted by an LLM, disclosed as such, checked against a human subset (2026-11-09)
- **Decision:** the RQ1 queries and relevance judgments are written by Claude (model `claude-opus-5-5`), one agent per repo. Every record says `"annotator": "claude-opus-5-5"`. The README and write-up must state that the labels are LLM-drafted.
- **Why:** the project owner did not know these three codebases. An LLM judge can read the full source of every pooled candidate, and labelling about 2,000 candidates by hand (D24) was the main blocker for Phase 3. LLM relevance judgments are an accepted, actively studied IR practice when they are disclosed and checked against humans.
- **Safeguards:**
  - Queries are frozen to a file before any pool is generated (`eval/llm_label.py pool`), so they can't be tuned to what the methods return. The intended target of each query is also recorded before pooling (`data/llm_labelling/<repo>/targets.json`).
  - Pools stay blind (same hash shuffle as D21), and the judge sees each candidate's full source.
  - Relevant functions outside the pool are counted per query (`added_outside_pool`).
  - Queries, targets and judgments are kept in `data/llm_labelling/` for audit.
  - The owner independently labels about 20 of the same queries with `eval/label.py` (without seeing the LLM labels), and we report Cohen's κ between human and LLM labels. This replaces the second annotator.
- **Rejected:**
  - The owner labels everything: too slow, and error-prone on unfamiliar code.
  - Recording LLM labels under the owner's name: a misrepresentation, never acceptable.
- **Result (2026-11-09):** 60 queries (20 per repo: 15 easy, 36 hard, 9 unanswerable by design; 51 answerable after judging), 8 relevant functions found outside the pool. Pools are regenerable and git-ignored (`.cache/llm_labelling/`); queries, targets and judgments are committed in `data/llm_labelling/`.
- **Known limitation (to report):**
  - The "hard" queries are only moderately hard: many reuse docstring words (fastmcp judge's own note).
  - Borderline calls are judge-dependent (private duplicates of a public helper, thin wrappers, partial matches); these are where human disagreement is expected.
  - An LLM judge may agree more with semantic (dense) rankers than a human would. The κ check is how we measure this.
  - Queries written by an LLM that has read the code may borrow its vocabulary. The query/answer-name word overlap is reported per method.

### D26. Keep it a personal project: evaluate DevTrust itself, no external benchmark, no human κ check (2026-11-09)
- **Decision (owner's call):** RQ1 is reported as "how well does DevTrust find functions", one results table over DevTrust's own search settings (BM25, BM25 without identifier splitting, bge-small, CodeRankEmbed, RRF, RRF + rerank) on the 60 queries. Dropped: the CoIR CosQA comparison and the human Cohen's κ check on the labels.
- **Why:** the owner wants a finished personal project to show professors, not a research paper. CLAUDE.md says "not a paper".
- **Consequences to state in the README:**
  - Labels are AI-drafted (D25) and were NOT independently validated by a human. This is a limitation, not hidden.
  - Results are on 3 repos and 60 queries, with no comparison to published numbers.
  - The "Who made what" disclosure (Open items) still applies, minus the κ sentence.
- **Kept:** bootstrap confidence intervals on the metrics (cheap, and they stop small differences being over-read).
- **Supersedes** the κ safeguard in D25 and the CosQA row of the thin-slice table; D25's other safeguards stand.

### D27. First retrieval results (2026-11-09; numbers live only in `results/retrieval.json`)
- **What was run:** all six search settings on the 51 answerable queries (9 unanswerable ones are not scored), `python -m eval.retrieval_eval`. Records seed, config, revisions, per-query results, latency, model sizes.
- **Findings** (the file has the numbers and CIs):
  - CodeRankEmbed (the code embedder) scored highest on every metric. bge-small was second. BM25 was far behind both, with identifier splitting clearly better than without.
  - **Surprise 1:** fusing BM25 into CodeRankEmbed with RRF scored *below* CodeRankEmbed alone. BM25 is much weaker here, so it drags the fused list down. Hypothesis only, not tested.
  - **Surprise 2:** the cross-encoder reranker made results *worse* than the list it reranks, and is about 20x slower per query. The model (ms-marco MiniLM) is trained on web passages, not code. Hypothesis only, not tested.
  - BM25 did poorly even on queries tagged "easy" (queries drafted to use vocabulary close to the code). Not yet checked whether this is real or an artefact; the BM25 unit tests pass.
  - One query was missed by every setting (instructor-015, template placeholders): the target functions weren't retrieved by any method.
- **Caveats to state in README:**
  - Labels are AI-drafted, not independently checked (D25, D26).
  - The labelling pool is the union of these same six settings' top 10, so a relevant function that none of them ranked in the top 10 may be unlabelled; that is how 8 outside-pool labels were found, and more may exist. Recall is therefore a slightly optimistic estimate.
  - 51 queries over 3 repos; CIs are wide, so small differences (e.g. bge-small vs RRF) are not conclusive.
  - `git_commit` in the results file says "none" because no commit existed when this ran. Re-run after the first commit, and don't commit stale numbers.
- **Re-run with a real commit hash (a26c21d, clean tree) on 2026-11-09:** the numbers are unchanged from the first run; `results/retrieval.json` is that run.
- **Not tuned:** nothing was tuned on these queries; all settings were fixed beforehand, so there is no dev/test split to leak.

## Phase 4: Duplication review (2026-11-09)

### D28. Phase 4 design: retrieve with the code embedder, verify with AST structure, thresholds provisional
- **What it does:** `devtrust/duplication/` finds the functions a git change adds or modifies, searches the repo state BEFORE the change for similar functions, scores each candidate structurally, and prints a side-by-side report. Entry point: `review(repo, base, head)`.
- **Design choices:**
  - **Retrieval:** CodeRankEmbed, the best RQ1 setting (D27). The query is the new function's full source, with the model's query prefix. Not validated for code-to-code search; Phase 5 measures it.
  - **Own previous version excluded** (same file and qualified name) for modified functions.
  - **Moved/renamed filter:** an added function whose body is identical to one removed in the same change is reported separately and not flagged. Exact-body match only, so a move combined with edits still gets flagged as new. Phase 5 must measure how well this filter works (CLAUDE.md).
  - **Structural score:** `difflib` similarity of the AST node-type sequence with names and constant values ignored (constants keep their type). This makes Type-1/2 copies score 1.0 by construction; it cannot see a changed constant value or a changed called-function name.
  - **Categories:** best structural score >= 0.9 -> `likely_duplicate`; >= 0.6 -> `similar_but_different`; else `insufficient_evidence`. Confidence: high if >= 0.95, medium for the rest of `likely_duplicate`, low otherwise. Functions with fewer than 10 AST nodes are skipped and counted.
- **Provisional, NOT validated:** the 0.9 / 0.6 / 0.95 thresholds and the 10-node minimum are placeholders I chose before any data. CLAUDE.md requires thresholds to be chosen on a dev split in Phase 5 and the README must say so until then.
- **Known risks to check in Phase 5/6:** many short getters or boilerplate methods look structurally identical (false positives); the node-type sequence ignores semantics, so two functions that differ only in a called function or constant will score 1.0; dense retrieval may rank a true duplicate below the top 5.
- **Evidence so far:** unit tests on a throwaway git repo (renamed copy flagged, unrelated function not, moved function filtered, modified function does not match itself) and one smoke test on instructor with a planted renamed copy (flagged, structural 1.0). The smoke test is an easy case, not a result.
- **Not built yet:** CLI (Phase 7), evaluation (Phase 5), commit-range convenience beyond two revisions.

## Phase 5: Duplication evaluation (2026-11-09)

### D29. Phase 5 design, written down before any result was seen
- **Question (RQ2):** does structural verification reduce false positives of embedding-only duplicate detection, compared with embedding-only max-cosine and jscpd?
- **Setup:** the index is instructor at its pinned commit plus the "existing" half of 47 hand-written pairs. Each case is one "new function"; the detector either flags it as duplicating something in the index or not.
  - **Positives:** type1 / type2 / type3 = synthetic mutations (`eval/mutate.py`, Roy & Cordy-style operators reimplemented with `ast`; the original framework has no Python support) of 60 real instructor functions (seeded sample, 25-300 AST nodes). type3 = type2 renaming plus one statement inserted or deleted. type4 = 25 hand-written same-behaviour reimplementations.
  - **Negatives:** `unrelated` = 60 real fastmcp functions queried against the instructor index; `sibling` (8), `client_endpoint` (6), `one_edit` (8) = hand-written similar-looking but behaviourally different functions.
- **Hand-written data (`data/duplication/handwritten.json`) is AI-written** (Claude, disclosed like D25). It is behaviour-checked by execution: all 25 type4 pairs return identical values or exception types on every listed input, and all 22 negative pairs differ on at least one. I re-ran that check myself after the agent reported it. Agent's own doubts: client/endpoint pairs ce-01/03/05/06 are looser (different argument shapes); ce-06 is really serialiser/deserialiser; the regex-based type4 pairs could differ on exotic Unicode/newline inputs not tested; sib-01 and sib-04 may be easy negatives.
- **Known weakness of the negatives:** `unrelated` functions are from another repo and not checked for accidental duplicates of instructor code; any `unrelated` case flagged at a high score will be inspected by hand and reported. `one_edit` negatives are a one-token behaviour change, which is exactly where a structural score will look like a duplicate; that is a real limit of the approach, not a bug in the test.
- **Split:** dev / test by hash of the group (all mutations of one original stay together). Thresholds are chosen on dev only (maximise F1; ties go to the higher threshold). The test split is only read by `--final`, which is run once on the final configuration.
- **Methods compared:** `embedding_only` = flag if top-1 CodeRankEmbed cosine >= t. `retrieval_plus_structural` = flag if the best structural score among the top 5 candidates >= t (the tool's actual rule). `jscpd` token mode and `--semantic` mode, each with jscpd's own defaults and with a lowered minimum size (20 tokens / 3 lines) so short functions are not skipped. jscpd is unmodified otherwise; with `--semantic` it reports exact and semantic clones, and we count both. jscpd 5.4.3 was installed locally, and its own copy of CodeRankEmbed (same revision 3c4b608) was downloaded for `--semantic`.
- **Metrics:** precision, recall, F1 per clone type (that type's positives against all negatives), FPR overall and per negative kind, bootstrap CIs on recall and FPR.
- **Observations before the run (jscpd on a 3-file toy example):** jscpd silently skips files below its minimum token count; jscpd token mode needs matching tokens so it cannot see renamed identifiers by design; jscpd `--semantic` scored a renamed copy at 0.558, below its own default same-language threshold of 0.6375.
- **Limitations to state:** synthetic positives are easier than real duplicates; types 1-3 come from the same real functions three times (correlated); thresholds apply to a 60-function sample of one repo; results here say nothing about real agent PRs (that is Phase 6).

## Open items
- README must contain a "Who made what" disclosure (AI-drafted queries/labels/code vs. author's own work, plus human-LLM κ). Draft wording was agreed in chat on 2026-11-09; write it when the README is created (Phase 7). Human labels go in their own file under annotator "Aanand Rimal".
- Git identity for commits (blocks the first commit).
- ⚑ items in related_work.md to check against the originals, especially Alam 2025's CodeBERT configuration, GPTCloneBench's licence, and the CLIONE paper.
- (Dropped in D26) human–LLM Cohen's κ.
- Choose the RQ3 detector model after RQ2 (D18).

---

## Likely interview questions → where the answer is
| Question | Entry |
|---|---|
| "Isn't this already done?" | D3 |
| "Why these models and not X?" | D5 |
| "Why not CodeSearchNet / BigCloneBench?" | D6 |
| "How did you avoid bias in your benchmark?" | D19, D21, D25 |
| "Who labelled the data? Can LLM labels be trusted?" | D25 (human–LLM κ) |
| "Why these repos?" | D19 |
| "How do you know AI agents duplicate code?" | D8; the RQ3 results will answer it |
| "What would you do with more time?" | D5 (dropped list), D8 (MCP / controlled experiment) |
| "What are the limitations?" | D13, D17, D19, D21, D22, D23 |
| "Why not index example code?" | D23 |
| "How big was the labelling effort?" | D24 |
