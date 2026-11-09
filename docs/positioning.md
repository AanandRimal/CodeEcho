# Positioning: what DevTrust adds, and what it does not

Status: **draft v2, 2026-11-08.** Based on [related_work.md](related_work.md), which covers about 50 papers and tools from more than 20 groups. Section IDs (A1, B12, C6, …) refer to that file.

This is a conservative reading. "Not found" means not found in what we read. It does not mean "does not exist". The search was broad but not a systematic review.

---

## (a) What prior work already covers

### Duplicate and clone detection

- **Mature detectors exist and are evaluated, several of them Python-capable:**
  - NiCad (Roy and Cordy).
  - SourcererCC (UCI; A7).
  - MSCCD (Osaka; A11).
  - PMD/CPD and CloneWorks (both evaluated on Python in A1).
  - Siamese (UCL; A9) and Oreo (UCI; A8), both Java only.
- **Synthetic mutation and injection** is the standard way to measure recall (Roy and Cordy 2009; A6).
- **Benchmarks:**
  - Python semantic-clone sets exist: SemanticCloneBench, GPTCloneBench (A2), and Kamino (A15, LLM-generated).
  - BigCloneBench's semantic labels are largely wrong: 86% and 93% mislabelled in two samples (Krinke and Ragkhitwetsagul, A12).
  - Fine-tuned pair classifiers overfit to the functionalities they were trained on (Sonnekalb et al., A13).
- **AI-era findings:**
  - Classical tools are precise but miss Type-4 clones. Deep-learning tools have higher recall and lower precision (Alam et al., A1).
  - LLMs can judge clone pairs, but are expensive. Their authors recommend classical tools as a pre-filter (Zhu et al., A14).
  - Embeddings rank one-edit near-clones as high as the original, so they work as "candidate-recall components" (ExecRetrieval, A15).

### Duplicate detection at development, commit, or review time

- **Before-snapshot querying with new diff code** has been done on Java code review (Uchoa et al., Siamese; C1).
- **A Python-capable PR bot** that flags newly added clones exists: CLIONE (C2), which uses NiCad or SourcererCC and is now self-host only.
- **Real-time and incremental detection:**
  - Index-based lookup in under 1 s per file (Hummel et al., A10).
  - SourcererCC-I in the IDE (A7).
  - AntiCopyPaster on paste (Java, intra-file; C4).
  - Just-in-time and notification systems (C3).
- **Embedding-based duplicate detection on changed files** exists as an open-source tool: jscpd `--semantic` (C5). It uses CodeRankEmbed, supports Python, and has no published evaluation.
- **Embedding retrieval of new Python PR functions against the base snapshot** has been done as a *study metric*: "More Code, Less Reuse" (MSR 2026; C6).

### Natural-language code search

- **Python NL→code benchmarks:** CodeSearchNet, CoSQA, CodeXGLUE, CoIR, CodeRAG-Bench (B1–B7, B13).
- **BM25 vs. dense, zero-shot**, measured in several settings (B7, B12, B13). Summary in B20:
  - BM25 ≈ dense on docstring-like queries over small corpora.
  - Dense ≫ BM25 on verbose queries over in-repo functions.
- **Hybrid RRF + cross-encoder:**
  - Evaluated at repository level (B19), where RRF scored below dense alone.
  - Small off-the-shelf cross-encoders hurt or are mixed (B13).
  - Fine-tuned or 7B LLM rerankers help (B11, B12, B18).
- **In-repo reuse retrieval from NL descriptions:**
  - Done inside LLM generation pipelines: A³-CodGen (B15), AllianceCoder (B16).
  - Their retrieval evaluation is small (47 cases in A³-CodGen) or indirect (Pass@k only).

### Motivation (AI assistants reimplement existing code)

- **Supporting evidence:**
  - RepoReuse (C8): duplicated logic in 50.8% of task chains by turn 5. Synthetic tasks, work-in-progress preprint.
  - REPOEXEC (C9): LLMs "often reimplement dependencies".
  - "More Code, Less Reuse" (C6): higher embedding redundancy in agent PRs. One repository, unvalidated metric.
- **Counter-evidence:** token-level duplication is *lower* in AI code (Mao et al., C7).
- **Verdict:** the motivation is plausible but not established. That itself is something DevTrust can measure.

**Implication:** every component of DevTrust exists already, and so does the overall idea of embedding-based duplicate flagging on PRs, as a tool (C5) and as a study metric (C6). **We must not claim a new technique or a new idea.**

## (b) What DevTrust plausibly adds

Ranked by how defensible each one is.

1. **A validated evaluation of diff-time duplicate detection for Python** (main contribution).
   - Labelled positives per clone type (T1–T4) and labelled hard negatives (similar-looking but functionally different).
   - Precision, recall, F1, and false-positive rate, with thresholds chosen on dev and reported on test.
   - Head-to-head against baselines that exist but have never been compared on the same data:
     - embedding-only max-cosine (C6's metric)
     - jscpd `--semantic` (C5)
     - NiCad or PMD/CPD (A1, C2)
     - RepoReuse's callee-overlap rule (C8)
     - DevTrust's retrieval + normalised-structure verifier
   - The specific, measurable question:

     > How much does structural verification reduce embedding false positives at fixed recall?

   - ExecRetrieval (A15) and jscpd's own README (C5) predict that embedding-only detection will flag related-but-different code. That gives a clear hypothesis to test.
2. **RQ1 in an under-tested setting.**
   - Short NL reuse descriptions, over one repository's functions.
   - BM25 with identifier splitting vs. zero-shot small embedders vs. RRF/weighted fusion vs. cross-encoder.
   - Prior work covers neighbouring settings: docstring queries (B13), issue queries (B12), repository level (B19), or a single proprietary embedder on 47 cases (B15).
   - This is a replication in a new setting, and its value is the measured answer.
   - Prior evidence makes "BM25 is nearly as good" and "reranking does not help" both plausible outcomes. Either is publishable as a careful negative result.
3. **Optional, if time allows: re-test C6's claim across several repositories with the validated detector.**
   - C6's result rests on one repository and an unvalidated cosine metric.
   - Re-measuring agent vs. human redundancy on more AIDev Python repos would be a direct, useful replication.
   - This is scope creep for a first slice. Decide after the main contribution works.

**Suggested framing for the README and emails:**

> An empirical evaluation of retrieval-based methods for (1) finding existing functions from a description and (2) flagging reimplemented functions in Python diffs. Retrieval-plus-structural verification is compared against embedding-only, token-based and call-overlap baselines on labelled data.

Avoid "novel", "first", and "state-of-the-art".

## (c) What is uncertain

- **Missed work.** Industrial tools (SonarQube, Copilot or Cursor features, code-review bots) were not surveyed, and some items are abstract- or snippet-only (C2, C3, C11). New preprints appear monthly (C8 and A15 are from Sep 2026).
- **Whether "duplicate" has a defensible ground truth.** Uchoa (C1) and C6 both found that moved or renamed code looks like duplication. Related-but-different code (C5) is a grey zone. We need written labelling guidelines and a second annotator with Cohen's κ.
- **Synthetic positives.** Mutation clones, GPTCloneBench, and Kamino are all artificial. Results on real reimplementations may differ. Mitigation: add a small set of *real* duplicates mined from repo history, e.g. functions later deduplicated by a refactoring commit, if feasible.
- **Dense vs. BM25 on short descriptions in-repo.** The evidence points both ways (B20). It depends on query style, so the hand-written query guidelines matter.
- **Reranker choice.** No published evidence supports a small zero-shot cross-encoder for code (B13). The rerank arm is exploratory.
- **Licences:**
  - GPTCloneBench: CC BY-NC-ND in the README vs. MIT on the repo.
  - Pyclone: no licence.
  - CSN and CoSQA: "MIT for non-commercial research" per CoIR.
  - Use for evaluation, don't redistribute the data, and confirm before committing anything.
- **Baseline installability:** NiCad needs FreeTXL; jscpd `--semantic` is "experimental"; SourcererCC's Python path is unverified. Test each before relying on it.

## (d) Recommended datasets, baselines, and metrics

### RQ1: reuse retrieval

| Role | Choice | Why |
|---|---|---|
| Primary | **Hand-labelled in-repo benchmark** (3–5 Python repos, short description queries, second annotator on a subset) | the actual setting; nothing public matches |
| External, comparable | **CoIR CosQA split, NDCG@10, zero-shot** | real Python queries; published BM25 / E5 / BGE / UniXcoder numbers |
| External, in-repo | **CodeRAG-Bench RepoEval** and/or **SWE-bench-Lite function localisation** (as in B11–B12) | in-repo function pools with published BM25 and dense numbers |
| Secondary only | CSN docstring queries, **docstrings stripped** | widely reported; inflated by vocabulary overlap (B1, B10) |
| Do not use | CoIR-CSN (reversed direction), WebQueryTest (classification), BigCloneBench | wrong task |

- **Baselines:**
  - BM25 with identifier splitting.
  - Two small zero-shot embedders: one general (BGE-base or E5-base, to match CoIR) and one code-specific (CodeRankEmbed or CodeSage-small, both evaluated zero-shot in B11–B13).
  - RRF and weighted fusion.
  - Cross-encoder rerank, labelled exploratory.
  - Not raw CodeBERT or GraphCodeBERT (fine-tuned only).
- **Metrics:** MRR, NDCG@10, Recall@K / Hit@K, P@K, bootstrap 95% CIs, and paired tests.
- **Pool:** always state the pool explicitly. GraphCodeBERT's Python MRR is 0.879 with 1,000 candidates and 0.692 on the full pool (B5).

### RQ2: duplication review

| Role | Choice | Note |
|---|---|---|
| T1–T3 positives | **Our `ast`-based re-implementation of Roy & Cordy-style mutation operators**, applied to real functions in the target repos, injected as synthetic diffs | the original framework has no Python support (A6) |
| T3/T4 positives | **GPTCloneBench Python pairs**; optionally Kamino (A15) | GPTCloneBench's "false semantic" pairs are T1/T2, so they are positives for us |
| Hard negatives | **Our own**: related-but-different functions (e.g. client vs. endpoint, sibling validators), and one-edit functional variants in the style of ExecRetrieval | the main source of embedding false positives |
| Real-world check (if feasible) | duplicates later removed by refactoring commits in repo history | reduces the synthetic-data limitation |
| Baselines | embedding-only max-cosine (C6); jscpd `--semantic` (C5); NiCad 6.2 and/or PMD/CPD (A1, C2); callee-overlap rule (C8) | verify each runs; report honestly if not |
| Protocol | before-snapshot index, query with the diff's new functions (C1, C6); filter moves and renames, and measure that filter | prior work shows refactorings are a false-positive source |

- **Metrics:** precision, recall, F1, and false-positive rate, **per clone type**. Also retrieval-only vs. retrieval + structural.
- **Thresholds:** chosen on dev; the test set is used once.
- **Do not use:** BigCloneBench WT3/T4 for semantic evaluation (A12). BCB is Java anyway.

---

## Changes I propose to CLAUDE.md (pending your decision)

1. **Related work section:** extend beyond Roy's group to include the key items from Parts B and C:
   - "More Code, Less Reuse"
   - CLIONE
   - jscpd `--semantic`
   - Uchoa et al.
   - RepoReuse
   - ExecRetrieval
   - CodeRAG-Bench
   - SweRank
   - A³-CodGen
   - Krinke and Ragkhitwetsagul
2. **Benchmark 1:** CoIR-CosQA plus an in-repo external set instead of CSN docstring queries. CSN only as secondary.
3. **Phase 5:** add hard negatives in the style of ExecRetrieval and C5's warning, and the four external baselines above. Drop BigCloneBench.
4. **RQ2 wording:** sharpen it to "Does structural verification reduce false positives of embedding-based duplicate detection in Python diffs, relative to embedding-only, token-based and call-overlap baselines?"
