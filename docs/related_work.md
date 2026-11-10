# Related work (Phase 0 literature study)

Status: **draft, compiled 2026-11-08.** All claims come from the text of the papers as fetched (arXiv versions unless stated otherwise). Where I read only part of a paper, the "Access" line says which parts. Numbers are copied from the paper and cite the table or section they come from. They are the papers' numbers, not ours.

Items marked **⚑ VERIFY** are places where the text was ambiguous, versions disagree, or I depended on a secondary source. Check these against the originals before citing them.

Note on versions: the arXiv preprint can differ from the camera-ready IEEE/ACM version. I did not have access to the publisher versions.

**How the reading was done:** I read A1–A6 and B1–B8 myself, or checked them by hand. A7 onwards, B9 onwards and Part C were extracted by three literature-search agents from the full PDF text. I then checked their key quotes and numbers against the extracted text by hand.

**Coverage by research group (so the study is not centred on one group):**

| Area | Roy group (USask) and co-authors | Other groups |
|---|---|---|
| Clone detection and benchmarks | A1–A6 | A7–A15: UCI/Lopes, UCL/Krinke, Mahidol/Ragkhitwetsagul, TU München, Osaka, DLR, Fudan, UBC, Kennesaw, Montréal |
| Code retrieval | A5 (query reformulation review) | B1–B19: GitHub/Microsoft, Microsoft Research, Huawei, AWS, UIUC/Nomic, Salesforce, CMU, CityU, ANU/CSIRO, TUM/SYSU, NASA-IMPACT |
| Diff-, commit- and development-time duplicates; AI reuse | — | C1–C13: UFC/UECE/Mahidol, Osaka, TU München, NEC/Osaka, UCI, Stevens/JetBrains, Science Tokyo/NAIST/UBC, PKU/Fudan, FPT, others |

---

## Part A: Clone detection and code similarity

_A1–A6 are from Roy's group or have Roy as a co-author. A7–A15 are from other groups._

### A1. Alam et al., "Are Classical Clone Detectors Good Enough For the AI Era?" (ICSME 2025)

- **Citation:** A. I. Alam, P. R. Roy, F. Al-omari, C. K. Roy, B. Roy, K. A. Schneider. ICSME 2025. arXiv:2509.25754.
- **Access:** full text (arXiv PDF), read in full except the reference list.
- **Research questions (verbatim, Sec. I):**
  - RQ1: How do classical clone detection tools perform on AI-generated clones?
  - RQ2: Do tools perform differently in AI versus non-AI clone benchmarks?
  - RQ3: What is the execution time and scalability for each tool?
- **Datasets/benchmarks:**
  - GPTCloneBench (GCB). Only the Moderately Type-3 (MT3) and Type-4 pairs were used, not the cross-language pairs.
  - SemanticCloneBench (SCB): 4,000 pairs in Python, Java, C, and C#.
  - BigCloneBench (BCB): Java only, run within IJaDataset 2.0.
  - Clones were injected into subject systems JHotDraw, Django (Python), PostgreSQL, and Mono, using an injection framework derived from BigCloneEval and the mutation/injection framework (Sec. V-A).
- **Tools (9):** PMD/CPD, Simian, Deckard, Clone Digger, CCCD, CloneWorks, StoneDetector, ASTNN, and CodeBERT (Table I).
  - Tools listed as supporting **Python** in Table I: PMD/CPD, Clone Digger, CloneWorks, and CodeBERT.
  - **NiCad and iClones were deliberately not chosen.** CloneWorks was used instead "due to its superior performance compared to NiCad and iClones in previous evaluations" (Sec. V-B).
- **Metrics:**
  - Recall uses a coverage-based clone match ("c-match") with minimum coverage t = 70% (Eq. 1–2).
  - Precision comes from manually validating 50 randomly selected reported clone pairs per tool (Sec. VI).
  - Also F1, execution time, and scalability (up to 1M LOC).
- **Setup details that matter for us:**
  - ASTNN and CodeBERT were **not** run through the injection framework, because it "could exceed 100 days for a single result". They were run on stand-alone clone pairs instead (Sec. V-A).
  - Table I lists CodeBERT as "Pretrained model" and ASTNN as "fine-tuned on BigCloneBench".
  - **⚑ VERIFY:** the BCB results paragraph says "CodeBERT fine-tuned for the BCB". It is unclear whether the GCB/SCB CodeBERT runs used a fine-tuned or a purely pretrained model.
- **Main findings (as stated):**
  - Abstract: classical tools, "particularly those enhanced by effective normalization techniques, retain considerable effectiveness against AI-generated clones, while some exhibit notable performance variation compared to traditional benchmarks."
  - Python, GCB (Table II / Sec. VI-A): CodeBERT recall 0.87 (MT3) and 0.88 (T4). CloneWorks 0.71 (MT3) and 0.24 (T4). PMD/CPD 0.08 (MT3) and 0.01 (T4). Clone Digger 0.01 (MT3).
  - Python, SCB T4 (Table II): CodeBERT 0.839, CloneWorks 0.111.
  - Precision, Python (Table II): CloneWorks 0.93, CodeBERT 0.53, PMD/CPD 0.47, Clone Digger 0.40.
  - RQ2 (Sec. VII-B): DL/transformer tools have better recall on Type-3/4, but classical tools (CloneWorks, StoneDetector) have much higher precision and better execution time and scalability. Recall differences between GCB and SCB are "not significant".
  - Normalization (Sec. VII-B): CloneWorks' "conservative" normalization consistently beat its "aggressive" setting. The authors conclude that normalization is critical.
  - RQ3 (Sec. VI-D): for Python, PMD/CPD processed a 1M-LOC project "within 4 seconds". Clone Digger's time grew about 52× from 10k to 100k LOC.
  - The authors recommend a hybrid of classical and AI-based methods (abstract).
  - **⚑ VERIFY:** Table II has a single precision column per tool and language. I could not tell from the extracted text which benchmark or system the 50-pair precision sample was drawn from.
- **Stated limitations (Sec. VIII):**
  - Results depend on configuration (the "confounding configuration choice problem"). Configurations followed documentation and defaults, not tuning.
  - Possible bias in the precision sample, mitigated by random sampling and multiple judges.
  - Injected systems must remain compilable.
  - Results may vary on datasets with very different characteristics.
- **Other:** the authors also report semi-structured interviews with 5 experts (Sec. II-C). They say transcripts are "available upon request".
- **Data/code:** replication package at https://github.com/srlabUsask/classical-clone-detector-in-ai-era (stated in Sec. I).
- **Relevance to CodeEcho:**
  - This is the closest work on the *detector* side.
  - It gives a Python-capable baseline set (PMD/CPD, CloneWorks) and an evaluation protocol (injection plus c-match recall, plus sampled precision).
  - It evaluates code-to-code clone detection. It does not evaluate natural-language retrieval or diff-time review.

### A2. Alam et al., "GPTCloneBench: A comprehensive benchmark of semantic clones and cross-language clones using GPT-3 model and SemanticCloneBench" (ICSME 2023)

- **Citation:** A. I. Alam, P. R. Roy, F. Al-omari, C. K. Roy, B. Roy, K. A. Schneider. ICSME 2023. arXiv:2308.13963.
- **Access:** full text (arXiv PDF), read in full except the reference list.
- **Goal (Sec. I):** build a semantic and cross-language clone benchmark large enough for ML training and evaluation. It responds to stated problems with existing benchmarks:
  - BigCloneBench: not designed for semantic clones, imbalanced, Java only.
  - SemanticCloneBench: 1,000 pairs per language, too small for ML.
  - CLCDSA: programming-contest "toy data".
- **Construction (Sec. III):**
  - Input functions come from SemanticCloneBench, which sourced them from Stack Overflow answers. They were sent to GPT-3 (text-davinci-003) with few-shot prompts.
  - Two prompts were kept: "Give me Type-3, Type-4 clone for the following code <code fragment>" and "Give me 10 distinctive implementation for the following code <code fragment>". Each prompt was run 4 times per input.
  - NiCad (blind renaming, minimum 3 lines) filtered the pairs. Pairs with > 75% textual similarity were moved to a "false semantic" (Type-1/Type-2) set.
  - Manual validation by 9 judges: 6 undergraduate students working in pairs, plus 3 postdocs who resolved 357 undecided pairs. This took about 510 hours.
  - Functionality testing: the first two authors checked 1,000 randomly selected pairs, about 192 hours, and "observed 99% of them functioning accurately" (Sec. IV-1).
  - CloneCognition was applied "in reverse" as an extra check (Tables III–IV).
- **Clone-type definitions (Sec. II, III-D):**
  - "Type-3" means Moderately Type-3: 50–75% similarity, including a 5% grey zone above BigCloneBench's 70%.
  - "Type-4" means Weak Type-3/Type-4: 0–50% similarity.
  - Cross-language clones are treated as Type-4.
- **Size (abstract, Sec. III-D):**
  - 79,928 GPT-3 pairs were generated. From these: 37,149 true semantic pairs, 19,288 false-semantic (T1/T2) pairs, and 20,770 cross-language pairs.
  - Languages: Java, C, C#, and Python.
  - **⚑ VERIFY:** the paper does not give a per-language breakdown of the 37,149 pairs. Tables III–IV list per-language "# Clones" for the CloneCognition check only (e.g. Python 1,495 and 4,968), and these should not be read as the Python totals. Count them from the released data instead.
- **Forms:** stand-alone pairs and system-injected pairs. The Python pairs are injected into **Django** (2,031 files, 240k LOC; Table II).
- **Tools evaluated (Sec. V):**
  - SourcererCC: recall Java 0.135, C 0.12, C# 0.10 (Table V).
  - Oreo: Java 0.49.
  - CLCDSA (cross-language): about 0.
  - No single-language Python detector was evaluated in this paper.
- **Metrics:** precision and recall. For stand-alone pairs recall is the main measure, because "all the clones are true positive" (Sec. V).
- **Stated limitations (Sec. VII):**
  - The clones are artificial. The authors describe them as "in between real-world and artificial clones".
  - Manual validation can introduce errors.
  - Results depend on the prompts.
  - Concern about training ML detectors on ML-generated data.
- **Data/code:**
  - The paper links to a shortened URL (https://shorturl.at/jvxOV).
  - The current GitHub README (https://github.com/srlabUsask/GPTCloneBench) points to Zenodo DOI 10.5281/zenodo.10198952 for semantic clones (stand-alone plus injected). Cross-language zips are in the repo.
  - **⚑ VERIFY license:** the README states CC BY-NC-ND (non-commercial). The repo sidebar shows MIT.
- **Relevance to CodeEcho:**
  - This is the only benchmark here with **Python Type-3/Type-4 pairs**, plus a Python injection target (Django). That makes it usable as a code-to-code positive set for RQ2.
  - It has **no natural-language queries**, so it cannot serve RQ1.
  - Its "false semantic" pairs are T1/T2 clones, not non-clones. They are positives for our purpose (a T1/T2 copy is still a duplicate), so they must not be used as negatives.

### A3. Pinku, Mondal, Roy, "On the Use of Deep Learning Models for Semantic Clone Detection" (ICSME 2024)

- **Citation:** S. N. Pinku, D. Mondal, C. K. Roy. ICSME 2024, pp. 512–524 (per DBLP). arXiv:2412.14739.
- **Access:** full text (arXiv HTML and PDF). I read the abstract, Sec. IV (setup), the RQ3 results, Sec. VI–VIII, and Tables I–III, XIV, and XV. I skimmed the RQ1/RQ2 tables.
- **Research questions (Sec. V):**
  - RQ1: How do the cutting-edge single-language clone detection models compare with each other when detecting semantic clones?
  - RQ2: How do the cross-language clone detection models compare with single-language clone detection models?
  - RQ3: How robust are these models when evaluated with semantic clones that are mutated with common mutation operations?
- **Datasets:**
  - BigCloneBench, SemanticCloneBench, and GPTCloneBench, **Java only** for the single-language experiments (Sec. IV-B, VII).
  - A CLCDSA subset with Java and Python, from programming competitions.
  - With GPTCloneBench, the models separate Type-IV pairs from Type-I–III pairs. This is not clone vs. non-clone classification.
- **Models:**
  - Single-language: ASTNN, GMN (flow-augmented AST), CodeBERT.
  - Cross-language: CLCDSA, C4 (built on CodeBERT with contrastive learning).
  - All are **trained or fine-tuned** with an 8:1:1 split.
- **Mutation:**
  - 15 atomic mutation operators from Svajlenko et al.'s MutationInjectionFramework, applied to SCB to create 15 test sets (Sec. IV-C).
  - **⚑ VERIFY:** the Zakeri-Nasrabadi SLR describes Roy and Cordy's operator set as 14 operators. These are probably different versions (2009 paper vs. the later Svajlenko framework).
- **Metrics:** precision, recall, F1.
- **Main findings (abstract, Sec. V–VI):**
  - All single-language models reach F1 of 0.93–0.95 on BCB (Table III). Their performance "varied quite differently (sometimes over 20%)" on SCB.
  - C4 is about 7% better on SCB.
  - Under mutation, C4 varies by less than 1%, while the other models vary by 3–9%.
  - "evaluation is largely dataset-dependent": LLM-based models do well on GPTCB and less well on SCB (Sec. VI).
- **Stated limitations (Sec. VII):**
  - CLCDSA consists of competition problems.
  - GPTCB is not from real-world software.
  - SCB is small, which risks overfitting.
  - Single-language experiments are Java only.
- **Data/code:** https://github.com/subrotonpi/clone_evaluation (Sec. IV-F).
- **Relevance to CodeEcho:**
  - Shows that benchmark choice changes conclusions. That argues for using more than one evaluation set.
  - Its models are supervised pair classifiers. They are not the zero-shot retrieval setting we use.
  - No Python single-language results.

### A4. Zakeri-Nasrabadi, Parsa, Ramezani, Roy, Ekhtiarzadeh, "A systematic literature review on source code similarity measurement and clone detection: techniques, applications, and challenges" (JSS 2023)

- **Citation:** JSS vol. 204, article 111796 (2023), per DBLP. arXiv:2306.16171.
- **Access:** full text (arXiv PDF). I read the abstract, the RQ list, Sec. 4.6–4.7 (datasets, comparison), Sec. 5 (challenges), Sec. 6 (threats), and Sec. 7 (conclusion). I did not read every per-study table.
- **Research questions (Sec. 3):**
  - RQ1: techniques.
  - RQ2: applications.
  - RQ3: tools and supported languages.
  - RQ4: projects and datasets.
  - RQ5: performance.
  - RQ6: challenges and opportunities.
- **Method:** SLR following Kitchenham and Charters. Over 10,000 articles from 4 digital libraries were narrowed to 136 primary studies, plus snowballing.
- **Main findings (Sec. 7):**
  - 8 basic technique families. Over 27% of studies use hybrid methods. Only 41% have a public tool.
  - 80 tools, of which 33 are public, covering 18 languages. More than 77% support Java, C, or C++.
  - 12 clone and similarity datasets. Only 50% of studies used one.
  - Meta-analysis means: precision 86.3, recall 88.4, F1 86.5, accuracy 82.5. The authors call these "only moderately reliable" because the datasets differ.
  - The performance of "emerging applications", e.g. code recommendation, is lower than older applications.
- **Challenges directly relevant to CodeEcho (Sec. 5):**
  - **Challenge 5:** most work targets Java and C/C++. Multi-paradigm languages "such as Python and JavaScript" need support.
  - **Challenge 6:** clone tools "have been designed to be used in the software maintenance phase". The authors write that "real-time measurement and notification of code similarity during software development help programmers avoid repeating code and reuse the available software component". They name development-phase support as an open challenge.
  - Mentions **Pyclone** (Duncan et al., 2021), which "generates type I, II, and III code clones for Python" by the same mutation approach as Roy and Cordy.
- **Stated limitations (Sec. 6):** selection bias, incomplete search, imbalanced distribution of studies, and possible inaccuracy in data extraction.
- **Data:** Zenodo 10.5281/zenodo.7993619.
- **Relevance:**
  - Supports the motivation: Python is under-served, and development-time reuse is named as a gap.
  - This was the situation as of 2023. Later work, such as the code-review clone study in Part C, partly addresses it.

### A5. Rahman and Roy, "A Systematic Review of Automated Query Reformulations in Source Code Search" (TOSEM 2023)

- **Citation:** M. M. Rahman, C. K. Roy. ACM TOSEM 2023, 81 pages. arXiv:2108.09646v2.
- **Access:** full text (arXiv PDF, v2). I read the abstract, the contribution summary (Sec. 1), the RQ list (Sec. 3.1), the RQ1 and RQ3 summaries, the metrics discussion, and the baseline list (Sec. 4.2). I did **not** read all 81 pages.
- **Scope:** reformulating developer queries for code search during maintenance.
  - 58% of the primary studies target local code search: concept, bug, and feature location.
  - 42% target Internet-scale code search.
- **Method:** 70 primary studies selected from 2,970 candidates, analysed with Grounded Theory. Seven RQs.
- **Main findings (Sec. 1, RQ summaries):**
  - 8 methodology families: term weighting and relevance feedback (40%); semantic relations, co-occurrence, and thesaurus (46%); ML and query-difficulty analysis (17%); data mining and API recommendation (44%).
  - 56% of the studies expand queries.
  - 30 metrics in use. Hit@K, Recall, MAP, and MRR are each used by more than 30% of studies.
  - 64% of studies use re-enactment-based evaluation. Human participation is generally low.
  - Limitations found across studies: noisy keywords, vocabulary mismatch, lack of generalizability, subjective bias.
  - Recommended practices: collect queries from professional developers; use both open- and closed-source systems; compare against state-of-the-art techniques through replication; share replication packages.
  - Future directions include neural language modelling such as word embeddings.
- **Baselines used by the reviewed work (Sec. 4.2):** Internet-scale code-search studies often compare against Google/GitHub search, **BM25**, and TF-IDF, plus tools such as RACK and NLP2API.
- **Observation (mine, from searching the text):** the review does not mention pre-trained transformer models (no hits for "BERT" or "transformer"). Its scope is query reformulation, not dense retrieval.
- **Data:** replication package at https://bit.ly/3QpZkSx (Sec. 1).
- **Relevance:**
  - Supports the vocabulary-mismatch motivation, and BM25 as the standard lexical baseline.
  - Its practice recommendations apply to our hand-labelled benchmark: real developer-style queries, a public replication package, and reporting Hit@K and MRR.
  - Query reformulation itself is out of scope for CodeEcho's first slice.

### A6. Roy and Cordy, "A Mutation/Injection-based Automatic Framework for Evaluating Code Clone Detection Tools" (2009)

- **Access:** abstract plus targeted reading of Sec. 4 (operators) from the authors' PDF (https://www.cs.usask.ca/~croy/papers/2009/RC_Mutation09_Framework.pdf).
  - **⚑ VERIFY venue:** the IEEE record lists it as a conference paper. I did not confirm the exact workshop or venue name from the PDF.
- **Contribution (abstract):** an automated method that "leverages mutation-based techniques ... by automatically synthesizing large numbers of known clones based on an editing theory of clone creation". It measures recall and precision for fine-grained clone types without manual intervention.
- **Language support:**
  - Operators are implemented in TXL. The control-replacement operator "currently supports C, Java and C#, although adaptation to other languages is not difficult" (Sec. 4).
  - The public implementation (https://github.com/jeffsvajlenko/MutationInjectionFramework) lists only `java`, `c`, and `cs` as subject-system languages in its README.
  - **Python is not supported out of the box.**
- **Relevance:**
  - The *method* (mutate a real function by its clone type, inject it, measure whether the tool recovers it) is exactly what CLAUDE.md Phase 5 describes.
  - For Python we would need to reimplement the operators, e.g. with `ast`, or use Pyclone. We should cite the method and state that our operators are a re-implementation.

### A7. Sajnani, Saini, Svajlenko, Roy, Lopes, "SourcererCC: Scaling Code Clone Detection to Big Code" (ICSE 2016), and Saini et al., "SourcererCC-I" (tool paper)

- **Group:** led by UCI (Lopes). Roy and Svajlenko are co-authors.
- **IDs:** arXiv:1512.06448 and arXiv:1603.01661.
- **Access:** full text of both.
- **Research question:** a scalable Type-1–3 detector that runs on one workstation.
- **Method:** bag-of-tokens overlap similarity, an inverted index, and sub-block filtering.
- **Data:** IJaDataset (250 MLOC, Java), BigCloneBench, and the Mutation Framework.
- **Baselines:** CCFinderX, Deckard, iClones, NiCad.
- **Metrics:** recall, sampled precision, run time.
- **Findings:** precision 91% (355 TP / 35 FP from manual judging). Scales to 250 MLOC.
- **Languages:**
  - The core paper calls it "programming language agnostic".
  - The tool paper says "we have parsers to support Java, C, C++, C#, and python".
  - The repo tutorial covers Java at file level. **⚑ A ready Python function-level tokenizer is unverified.**
- **Development-time use:** SourcererCC-I is an Eclipse plug-in that reports Java method clones "in real-time during software development".
- **Code:** https://github.com/Mondego/SourcererCC
- **Relevance:** index-based code-to-code candidate retrieval, a development-time precedent, and nominal Python support. CLIONE (C2) uses it as a backend.

### A8. Saini, Farmahinifarahani, Lu, Baldi, Lopes, "Oreo: Detection of Clones in the Twilight Zone" (ESEC/FSE 2018)

- **IDs:** arXiv:1806.05837.
- **Access:** full text.
- **Research question:** detect clones between Type-3 and Type-4.
- **Method:** a size filter, then an "action filter" over shared method calls and field accesses, then a Siamese DNN over 24 software metrics.
- **Data:** BigCloneBench recall; trained on 50k Java GitHub projects. **Java only.**
- **Finding:** "precision of Oreo is 89.5%".
- **Limitation:** porting to another language "requires careful consideration of the heuristics and the software metrics".
- **Code:** the arXiv text says "anonimized". **⚑ Public repo not verified.**
- **Relevance:** the idea of a cheap shared-call pre-filter transfers to Python. The tool itself does not support Python. Compare RepoReuse's callee-overlap rule (C8).

### A9. Ragkhitwetsagul and Krinke, "Siamese: Scalable and Incremental Code Clone Search via Multiple Code Representations" (EMSE 2019)

- **Access:** full accepted manuscript (UCL Discovery).
- **Method:** an Elasticsearch tf-idf index over four normalised token representations (raw, then progressively abstracted identifiers and literals), query reduction, and custom ranking.
- **Research questions:** RQ1 multi-representation and query reduction; RQ2 accuracy; RQ3 ranking; RQ4 scalability; RQ5 incremental update.
- **Data:** OCD, SOCO, BigCloneBench (all Java).
- **Baselines:** 7 clone detectors and 3 code search engines.
- **Metrics:** MAP, MRR, recall.
- **Findings:** "highest mean average precision of 95% and 99% on two clone benchmarks". Results in under 8 s on 365 MLOC. Incremental index updates.
- **Languages:** "The current implementation of Siamese supports Java." A new language needs a method extractor, tokeniser, and normaliser.
- **Code:** https://github.com/UCL-CREST/Siamese
- **Relevance:** the closest *architectural* analogue to CodeEcho's code-to-code retrieval: lexical IR over normalised views, queried with new code. Uchoa et al. (C1) use it on diffs.

### A10. Hummel, Juergens, Heinemann, Conradt, "Index-Based Code Clone Detection: Incremental, Distributed, Scalable" (2010)

- **Group:** TU München and Google.
- **Venue:** **⚑ ICSM 2010, unverified.** The venue is not printed in the PDF.
- **Access:** full text.
- **Method:** a hash index of normalised statement chunks. Type-1/2 clones only.
- **Finding:** "on 42 MLOC of Eclipse code, average time to retrieve all clones for a file was below 1 second".
- **Languages:** Java, ABAP, C.
- **Code:** ConQAT (maintenance status unverified).
- **Relevance:** classic prior art for change-time, per-file clone lookup through an index.

### A11. Zhu, Yoshida, Kamiya, Choi, Takada, "MSCCD: Grammar Pluggable Clone Detection Based on ANTLR Parser Generation" (ICPC 2022)

- **IDs:** arXiv:2204.01028.
- **Access:** full text.
- **Method:** generates a block extractor from any ANTLRv4 grammar, then compares token bags (Type-3).
- **Python:** function-level detection by "providing a keyword list that only contains the keyword 'def'". The paper reports function-level support for 18 of 20 languages.
- **Data:** recall measured only on BigCloneBench (Java).
- **Relevance:** a Python-capable syntactic baseline candidate.

### A12. Krinke and Ragkhitwetsagul, "BigCloneBench Considered Harmful for Machine Learning" (IWSC 2022), and the follow-up "How the Misuse of a Dataset Harmed Semantic Clone Detection" (arXiv:2505.04311)

- **Access:** full text of both.
- **2022 finding:** in a random sample of 100 WT3/T4 pairs, "86% of constructed clone pairs [were] false positives (only 6% were true positives)". The authors "call for a stop" to using BCB for machine learning.
- **2025 finding:** in a sample of 406 WT3/T4 pairs, "93% of them do not have a similar functionality and are therefore mislabelled". Of 179 papers that use BCB, 139 have semantic-clone results that are "threatened in their validity". BCB "remains valid" for Type-1–3.
- **Also cited:** Yu et al. (TOSEM 2022). A model using only identifier names matches learned detectors on BCB.
- **Data:** https://github.com/jkrinke/BigCloneBench-Sample-Validation
- **Relevance:** do not evaluate semantic duplicates on BigCloneBench WT3/T4. Learned similarity can lean on identifiers. This supports identifier-normalised structural checking.

### A13. Sonnekalb, Gruner, Brust, Mäder, "Generalizability of Code Clone Detection on CodeBERT" (ASE 2022 NIER)

- **IDs:** arXiv:2208.12588.
- **Access:** full text (3 pages).
- **Finding:** on held-out BigCloneBench functionalities, CodeBERT's F1 drops by about 27% and about 47%. On unseen functionalities F1 is 48.97.
- **Language:** Java.
- **Relevance:** fine-tuned pair classifiers overfit to the functionalities they were trained on. This argues against relying on a learned classifier in CodeEcho.

### A14. LLM-era clone detection (three studies)

- **Dou et al., "Towards Understanding the Capability of LLMs on Code Clone Detection" (arXiv:2308.01191)**
  - Group: Fudan / NTU / Westlake. Access: full text.
  - Data: BigCloneBench, plus **Python** and C++ pairs drawn from CodeNet.
  - Embedding similarity: the best cosine thresholds were 0.995 for CodeBERT and 0.8 for text-embedding-ada-002. Raw cosine is compressed into a narrow range.
  - The authors note the Python/C++ test data "might overlap with the training data".
  - Caveat: the Type-4 results rely on BigCloneBench labels (see A12).
  - Code: https://github.com/LLM4CodeClone/LLM4CodeClone
- **Khajezade et al., "Investigating the Efficacy of LLMs for Code Clone Detection" (ICPC 2024 ERA, arXiv:2401.13802)**
  - Group: UBC. Access: full text.
  - Zero-shot ChatGPT on Type-4 CodeNet pairs (Java–Java, Java–Ruby). No Python.
  - F1 0.878 vs. 0.914 for GraphCodeBERT (Java–Java). F1 0.877 vs. 0.665 (Java–Ruby).
- **Zhu, Yoshida, Choi, Matsubara, Takada, "An Empirical Study of LLM-Based Code Clone Detection" (arXiv:2511.01176)**
  - Group: Osaka / Nanzan. Access: full text.
  - Data: 7 datasets from CodeNet (Java, C, C++, **Python**) and BigCloneBench.
  - o3-mini reached F1 0.943 on CodeNet but dropped sharply on BCB.
  - Advice: "existing clone detection technologies should be actively used to reduce the number of comparisons through LLM". That is a retrieve-then-verify design.
  - Data: https://zenodo.org/records/15019503
- **Relevance:** LLM judges work on Python but are expensive per pair. At most a verifier on a small top-k, and out of scope for CodeEcho's first slice.

### A15. Python-specific semantic-clone and retrieval work (2026 preprints)

- **Kapoor and Khan, "ExecRetrieval: Measuring the Functional-Correctness Gap in Code-Embedding Retrieval" (arXiv:2609.01865, Sep 2026)**
  - Group: Kennesaw State. Access: full text.
  - 939 **Python** NL queries. Each pool contains the canonical implementation plus up to 4 single-edit, execution-verified buggy near-clones. Compares 23 embedding configurations against BM25.
  - The best system has "exec@10=1.00 but only exec@1=0.331". "rank-1 misses are paired buggy variants 91.5–99.4% of the time". BM25 exec@1 is 0.058.
  - The authors conclude that "Current code embeddings function as candidate-recall components".
  - Data: https://huggingface.co/datasets/AaryanK/ExecRetrieval
  - Relevance: embeddings cannot tell "same logic" from "one edit away". Use them for recall, not as the verdict. This directly supports CodeEcho's structural-verification stage.
- **Marchezan, Delcourt, Syriani, Sahraoui, "Type-IV Code Clone Detection via Layer-Wise Non-Contrastive Representation Learning" (arXiv:2609.17338, under review)**
  - Group: Montréal. Access: full text.
  - Uses **Kamino**: 78,771 LLM-generated, test-validated Python Type-IV pairs from BigCodeBench, cited as ISSTA 2026 (**⚑ venue not checked**).
  - Reports F1 0.920 on the Python part of GPTCloneBench.
  - Code: doi 10.5281/zenodo.21363019
  - Relevance: Kamino is a candidate Python Type-4 test source. Like GPTCloneBench, it is LLM-generated.
- **Pyclone:** see Part C note C13. Still **⚑ unverified** (paper not accessible).

---

## Part B: Code retrieval benchmarks and models

Access for all seven papers: full text (arXiv PDFs). These were read with targeted searches of the text, not cover to cover. Key quotes were checked against the text by hand.

### B1. Husain et al., "CodeSearchNet Challenge: Evaluating the State of Semantic Code Search" (arXiv:1909.09436)

- **Goal:** release a corpus of (function, documentation) pairs in 6 languages, plus a challenge set of "99 natural language queries with about 4k expert relevance annotations".
- **Python corpus:** 503,502 functions with documentation, 1,156,085 in total. Documentation is "truncated to the first full paragraph". The split is 80/10/10.
- **Challenge queries:**
  - Bing queries with high click-through to code, plus StaQC intent rewrites, manually filtered.
  - Candidates for annotation came from "ensembles of all neural models and ElasticSearch" (top 10).
  - Relevance graded 0–3. 2,089 Python annotations. Cohen κ = 0.47.
- **Candidate pools (critical):**
  - *Corpus test set:* "we fix a set of 999 distractor snippets cj for each test pair", with the docstring as the query, scored by MRR.
  - *Challenge:* NDCG computed either "Within" the annotated subset or over "All" of the corpus. The authors warn that "All" can penalise a new tool that returns relevant functions nobody annotated.
- **Baselines:** NBoW, 1D-CNN, biRNN, and self-attention bi-encoders, plus ElasticSearch "with the default parameters". The paper never names BM25. Its neural baselines split camelCase identifiers into subtokens.
- **Findings:**
  - "the non-neural ElasticSearch-based baseline performs competitively". NBoW was the best baseline.
  - Python NDCG (Within): ElasticSearch 0.406, NBoW 0.582.
- **Stated limitations:** documentation "is fundamentally different from queries ... tends to use the same vocabulary". Some docs are outdated. The challenge annotation set is small.
- **Docstring removal:** the paper does **not** say whether docstrings are stripped from the code side.
  - **⚑ VERIFY in the data:** according to a web summary, the README's `code` field includes the docstring while `code_tokens` omits it. Check this in the raw data before Phase 3.
- **Data:** https://github.com/github/CodeSearchNet.
  - The 99 queries and annotations are at `resources/queries.csv` and `resources/annotationStore.csv` (web check).
  - The repo has been archived since Apr 2023 (web check).
  - Annotations point to GitHub URLs, not corpus IDs. **⚑ Mapping them to functions is unverified.**

### B2. Huang et al., "CoSQA: 20,000+ Web Queries for Code Search and Question Answering" (arXiv:2105.13239)

- **Goal:** a code-search training and evaluation set built from real web queries, plus the CoCLR contrastive method.
- **Data:**
  - **Python only.** Bing queries; "Queries without the keyword 'python' are removed."
  - The code side is CodeSearchNet Python functions, *with* documentation.
- **Candidate construction:** a CodeBERT matcher fine-tuned on StaQC retrieves code. Only the top-1 is kept, and pairs below 0.5 cosine similarity are removed.
  - **Observation (mine):** this pre-filter likely biases the positives toward what a dense model finds.
- **Labels:** binary, at least 3 annotators per pair, Krippendorff's α = 0.63.
- **Pool:** split 19,604/500/500 with "a code database with 6,267 different codes".
- **Baselines:** RoBERTa and CodeBERT. No BM25.
- **Metric:** MRR.
- **Findings:**
  - CodeBERT trained on CSN: 51.29 MRR. On CSN+CoSQA: 54.41. With CoCLR: 64.66.
  - Ablation: **"w/o documentation" drops MRR from 64.66 to 58.54**. Documentation in the indexed code matters a lot.
- **Stated limitation:** Python only.
- **Data:** in the CodeXGLUE repo (`Text-Code/NL-code-search-WebQuery`). Code at https://github.com/Jun-jie-Huang/CoCLR.

### B3. Lu et al., "CodeXGLUE" (arXiv:2102.04664)

- **Goal:** 10 tasks over 14 datasets.
- **Python NL→code datasets:**
  - **AdvTest:**
    - Queries are docstrings, as in CodeSearchNet.
    - Function and variable names in the test and dev sets are normalised to `func` / `argi`.
    - "we use the entire testing set for each query" rather than 1,000 candidates. The test set has 19,210 examples.
    - Metric: MRR.
  - **WebQueryTest:**
    - Real web queries containing "python". The top-2 candidates came from a CodeBERT retriever.
    - Labelled by 13 developers; only labels 0 and 1 are kept.
    - Framed as **binary classification** (F1, accuracy), not ranking.
- **Baselines:** RoBERTa, CodeBERT. AdvTest MRR: 18.33 and 27.19 respectively.
- **Relevance:**
  - AdvTest's name normalisation removes identifier signal that real repositories have. My inference: this penalises BM25 by design.
  - WebQueryTest is not a ranking pool.

### B4. Feng et al., "CodeBERT" (arXiv:2002.08155; Findings of EMNLP 2020 per CoSQA's citation)

- **Model:** RoBERTa-base, 125M parameters, pre-trained with MLM+RTD on CodeSearchNet.
- **Search setup:**
  - Pool of 999 distractors.
  - **Fine-tuned** per language with a binary classifier on the concatenated NL+code [CLS]. That is cross-encoder style.
  - Python MRR 0.8685.
- **Zero-shot:** used only for NL–PL probing, not for search.
- **Relevance:** not a zero-shot bi-encoder, so don't use raw CodeBERT embeddings as the dense baseline.
- **Code:** https://github.com/microsoft/CodeBERT.

### B5. Guo et al., "GraphCodeBERT" (ICLR 2021; arXiv:2009.08366)

- **Goal:** pre-training that uses data flow.
- **Search setup:**
  - Low-quality queries are filtered.
  - The pool is expanded from 1,000 candidates to the whole test corpus: Python has 14,918 queries against 43,827 candidates.
  - Bi-encoder (inner product of [CLS]), **fine-tuned**.
- **Results:** Python MRR 0.692 on the full pool, versus 0.879 on the 1,000-candidate setting. **This shows how much pool construction changes the numbers.**
- **Error analysis:** failures on library-API terms (e.g. "tf", "unistr").

### B6. Guo et al., "UniXcoder" (arXiv:2203.03850)

- **Goal:** unified cross-modal pre-training with contrastive learning.
- **NL→code search:** **fine-tuned** for 10 epochs; cosine similarity of mean-pooled states.
- **MRR, Table 1:**

  | Model | CosQA | AdvTest | CSN (GraphCodeBERT version) |
  |---|---|---|---|
  | UniXcoder | 70.1 | 41.3 | 74.4 |
  | GraphCodeBERT | 68.4 | 35.2 | 71.3 |
  | CodeBERT | 65.7 | 27.2 | 69.3 |

- **Zero-shot:** evaluated in this paper only for code→code search.
- **Code:** https://github.com/microsoft/CodeBERT; checkpoint `microsoft/unixcoder-base`.

### B7. Li et al., "CoIR: A Comprehensive Benchmark for Code Information Retrieval Models" (arXiv:2407.02883)

- **Goal:** "a one-stop zero-shot evaluation benchmark" for code retrieval: 10 datasets, 8 sub-tasks.
- **NL→code tasks:** APPS, CosQA, and Synthetic Text2SQL.
  - CosQA keeps its original 19,604/500/500 split, but the corpus is "all code snippets", about 21K.
  - **⚑ VERIFY:** this differs from CoSQA's own 6,267-code pool, and CoIR does not explain why.
- **CodeSearchNet direction:** CoIR runs CSN **reversed** (code→docstring), so CoIR's CSN numbers are not NL→code.
- **Models (all zero-shot):** BM25, Contriever, E5-base, BGE-base, GTE-base, UniXcoder, BGE-M3, E5-Mistral, Ada-002, and Voyage-Code-002.
- **Metric:** NDCG@10.
- **CosQA NDCG@10 (Table 3):**

  | Model | CosQA NDCG@10 |
  |---|---|
  | BGE-base | 32.76 |
  | E5-base | 32.59 |
  | E5-Mistral | 31.27 |
  | GTE-base | 30.24 |
  | Voyage-Code-002 | 29.79 |
  | Ada-002 | 28.88 |
  | UniXcoder | 25.14 |
  | BGE-M3 | 22.73 |
  | Contriever | 14.21 |
  | BM25 | 13.96 |

  Zero-shot UniXcoder scores below general-purpose 110M text embedders on this task.
- **Other findings:** "No single model dominates". "Most models score significantly higher on CodeSearchNet, indicating a strong overfitting tendency."
- **Stated limitations:** English only; text-only retrieval.
- **Licences:** CSN and CoSQA are listed as "MIT License" for non-commercial research.
- **Code:** https://github.com/CoIR-team/coir.

### B8. Which datasets and models fit Python NL→function retrieval

**Datasets**

| Dataset | Real queries? | Python? | Pool | Fit for CodeEcho RQ1 | Main caveat |
|---|---|---|---|---|---|
| CoSQA / CoIR-CosQA | yes (Bing) | yes | 6,267 (CoSQA) or ~21K (CoIR) | **good** | positives pre-filtered by a dense model; "python" in every query; code includes docs |
| CSN Challenge (99 queries) | yes (Bing) | yes | annotated subset or full corpus | **good, small** | κ = 0.47; unannotated relevant hits; URL→function mapping unverified |
| CSN corpus test (docstring query, 1+999) | no | yes | 1,000 | weak (comparability only) | docstring/code vocabulary overlap; must strip docstrings; random easy distractors |
| AdvTest | no | yes | full test set (19,210) | weak | names normalised to `func`/`argi`, unlike real repositories |
| WebQueryTest | yes | yes | n/a (classification) | no | not a ranking task |
| CoIR-CSN | n/a | yes | — | no | reversed direction (code→docstring) |
| GPTCloneBench / SCB | n/a | yes | — | no for RQ1 (no NL queries); yes for RQ2 | code-to-code only |
| BigCloneBench | n/a | **no** (Java) | — | no | Java only |

**Models**

- **CodeBERT and GraphCodeBERT:** search results exist only after fine-tuning. **Not appropriate** as zero-shot dense baselines.
- **UniXcoder:** usable zero-shot with mean pooling (CoIR does this), but it scored below general text embedders on CosQA in CoIR.
- **General 110M text embedders (E5-base, BGE-base, GTE-base):** zero-shot, CPU-feasible, and strong on CoIR-CosQA. These are reasonable dense baselines.
- **Code-specific open embedders** (from model cards, web check; **self-reported scores, ⚑ unverified**):

  | Model | Licence | Size | Notes |
  |---|---|---|---|
  | `jinaai/jina-embeddings-v2-base-code` | Apache-2.0 | 161M | |
  | `nomic-ai/CodeRankEmbed` | MIT | 137M | needs a query prefix |
  | `codesage/codesage-small-v2` | Apache-2.0 | 130M | |
  | `nomic-ai/nomic-embed-code` | Apache-2.0 | 7B | not CPU-practical |

- **Voyage-code and Ada:** API-only. Excluded under the CPU/open-model constraint.
- **Hybrid RRF and cross-encoder reranking:** none of B1–B7 evaluates them. The closest is CodeBERT's fine-tuned pairwise classifier. The only hybrid/rerank code-search evaluation I found is Pantha et al. 2026 (B19), and it is repository-level.

### B9. Surveys of code search

- **Di Grazia and Pradel, "Code Search: A Survey of Techniques for Finding Code" (ACM Comput. Surv.; arXiv:2204.02765)**
  - Access: full text.
  - A taxonomy of queries, query expansion, indexing, and ranking.
  - Names vocabulary mismatch as the core problem of free-form queries.
  - Notes that "early studies are about searching through a single project", while later work searches across many projects.
  - Lists zero-shot code search as an open challenge.
- **Sun et al., "A Survey of Source Code Search: A 3-Dimensional Perspective" (arXiv:2311.07107; **⚑ final venue unverified**)**
  - Access: full text.
  - "it is a common practice to split the camel–case … or snake–case … method names".
  - Calls BM25 "not only effective but also easy to use".
  - Catalogues retrieve-then-rerank designs.
- **Relevance:** citations for identifier splitting and BM25 as standard practice. Neither survey ablates identifier splitting.

### B10. Zhang et al. (AWS), "CodeSage: Code Representation Learning at Scale" (ICLR 2024; arXiv:2402.01935)

- **Access:** full text.
- **Models:** 130M / 356M / 1.3B, trained on The Stack.
- **Evaluation:** zero-shot NL→code on CoSQA, AdvTest, and CSN (MRR). No BM25.
- **Key observation:** "substantial overlap between docstrings and function signatures simplifies the contrastive learning process". The model "tends to learn shortcut by leveraging such overlap". They therefore strip signatures when building training pairs.
- **Code:** https://github.com/amazon-science/CodeSage
- **Relevance:** a CPU-size code embedder (130M). It also warns that docstring-like queries inflate scores through name overlap.

### B11. Suresh et al. (UIUC/Nomic), "CoRNStack" / CodeRankEmbed (ICLR 2025; arXiv:2412.01007)

- **Access:** full text.
- **Model:** CodeRankEmbed, a 137M bi-encoder trained on 21M filtered pairs. Evaluated zero-shot on CSN, AdvTest, and CoIR. Baselines: E5, Arctic, CodeSage, CodeT5+, Jina-code-v2. No BM25.
- **Reranker:** CodeRankLLM, a 7B listwise LLM.
- **Closest-to-CodeEcho setup:** SWE-bench-Lite function localisation. "The GitHub issue serves as the text query, while all functions within the files in the repository are considered as candidates."
- **⚑ caveat:** queries are issue reports, not short descriptions, and the target is the function to edit, not one to reuse.
- **Code:** https://github.com/gangiswag/cornstack

### B12. Gangi Reddy et al. (UIUC/Salesforce), "SweRank" (ICLR 2026; arXiv:2505.07849)

- **Access:** full text.
- **Setup:** retrieve-then-rerank issue localisation. SWE-bench-Lite function Acc@10, all retrievers zero-shot (Table 1):

  | Retriever | Function Acc@10 |
  |---|---|
  | BM25 | 36.86 |
  | Jina-Code-v2 (161M) | 52.19 |
  | CodeSage-large-v2 (1.3B) | 44.53 |
  | CodeRankEmbed (137M) | 58.76 |

  Large fine-tuned LLM rerankers reach much higher scores.
- **Caveat:** same group as B11. Long issue queries.
- **Relevance:** the clearest head-to-head of BM25 vs. dense over in-repo functions. Dense wins clearly *with verbose queries*.

### B13. Wang et al. (CMU/UW/USC), "CodeRAG-Bench" (arXiv:2406.14497; **⚑ venue unverified**)

- **Access:** full text. Python only.
- **Retrievers:** BM25 (pyserini), several dense models used zero-shot, and a BGE-reranker-base cross-encoder.
- **NDCG@10 (Table 3):**

  | Retriever | CSN | RepoEval | SWE-bench-Lite |
  |---|---|---|---|
  | BM25 | 89.1 | 93.2 | 43.0 |
  | CodeSage-small | 90.7 | 94.1 | 47.1 |
  | Jina-v2-code | — | 90.5 | 58.3 |

- **Authors' conclusions:**
  - "dense embedding models frequently surpass" BM25.
  - Reranking over 200–800-token chunks "greatly degrades the results, showing limited utility of current rerankers".
- **Relevance:**
  - On small Python corpora with docstring-like queries, BM25 is within about 1 point of small code embedders.
  - An off-the-shelf small cross-encoder may hurt. Treat CodeEcho's rerank arm as exploratory; a null result is plausible.

### B14. Zhang et al. (CityU/Microsoft), "RepoCoder" (arXiv:2303.12570; **⚑ EMNLP 2023 unverified**)

- **Access:** full text.
- **Setup:** repository-level completion. The query is the unfinished code, so this is code→code retrieval.
- **Findings:**
  - Sparse Jaccard retrieval was "comparable to" UniXcoder dense retrieval.
  - Little gain "when a repository has few instances of code duplication".
- **Code:** https://github.com/microsoft/CodeT/tree/main/RepoCoder

### B15. Liao et al. (ANU/CSIRO), "A³-CodGen" (arXiv:2312.05772v5; **⚑ venue unverified**)

- **Access:** full text.
- **Data:** 29 PyPI repos, sampled down to 383 functions.
- **Retrieval:**
  - A per-repo "function base" of LLM-written function summaries.
  - The NL description is embedded with ada-002 and matched by cosine similarity.
  - This is unioned with matches from LLM-generated "what-if" code.
  - No BM25, no open models, no reranker.
- **Retrieval evaluated directly on only 47 cases:** "FunDes method retrieved 41.5% of global functions, while the FunDes+FunCode method retrieved 60.6%".
- **Limitations:** subjective labelling; Python only.
- **Relevance:** **the closest prior work to CodeEcho RQ1** (in-repo reuse retrieval from NL descriptions). Its retrieval evaluation is small and uses a single proprietary embedder.

### B16. Gu et al. (TUM/SYSU/Huawei), "What to Retrieve for Effective Retrieval-Augmented Code Generation?" (AllianceCoder; arXiv:2503.20589)

- **Access:** full text.
- **Data:** CoderEval and RepoExec (Python).
- **Retrieval:** per-repo API retrieval through LLM-written descriptions. Evaluated by Pass@k only.
- **Finding:** retrieved similar code "can even degrade performance".
- **Relevance:** a wrong retrieved function hurts. This supports abstaining when confidence is low.

### B17. Other embedding models (brief)

- **CodeT5+ (Salesforce, arXiv:2305.07922):** retrieval numbers are fine-tuned, so not comparable to zero-shot use.
- **CodeXEmbed (Salesforce, COLM 2025, arXiv:2411.12644):** 400M / 2B / 7B models. The 400M model is borderline for CPU.

### B18. Gotmare et al., "CasCode: Cascaded Fast and Slow Models for Efficient Semantic Code Search" (arXiv:2110.07811, 2021)

- **Method:** bi-encoder top-K, then a cross-encoder rerank. Both fine-tuned on CSN.
- **Result:** MRR 0.7795 vs. 0.7422.
- **Relevance:** evidence that *fine-tuned* reranking helps. Says nothing about zero-shot reranking.

### B19. Pantha et al., "Scientific Code Search at Scale" (arXiv:2607.05443, July 2026)

- **Access:** full text, read by targeted search of the text.
- **Setup:** repository search over README text. Compares BM25, embeddings, **Hybrid-RRF**, and **Hybrid-Rerank** (Table 10).
- **Finding:** Hybrid-RRF scored *below* embeddings alone (MRR@10 0.487 vs. 0.518). Reranking was best on 5 of 6 metrics, "modestly improving over the embedding-only baseline".
- **Relevance:** the only hybrid-plus-rerank code-search evaluation found. It is repository-level, not function-level.
- **Also seen, abstract only:** Chesnokov and Mingazov (arXiv:2608.19957), a 1C:Enterprise NL→code benchmark. Whether it uses RRF is **⚑ unverified**.

### B20. Retrieval synthesis

| Setting | Evidence | Who wins |
|---|---|---|
| Small Python corpora, docstring-like queries | CodeRAG-Bench (B13); RepoCoder (B14) | BM25 ≈ small dense |
| In-repo functions, long issue queries | SweRank (B12); CodeRAG SWE-bench-Lite (B13) | dense ≫ BM25 |
| Real Python web queries, zero-shot | CoIR-CosQA (B7) | 110M text embedders > UniXcoder ≫ BM25 |
| Hybrid RRF | Pantha (B19), repository-level only | RRF < dense alone there |
| Small off-the-shelf cross-encoder | CodeRAG-Bench (B13) | negative or mixed |
| Fine-tuned or 7B LLM reranker | CasCode (B18); CoRNStack/SweRank (B11–B12) | helps |
| Near-clone discrimination | ExecRetrieval (A15) | embeddings can't separate them at rank 1 |

**Not found:** an evaluation of BM25 with identifier splitting, small zero-shot embedders, RRF or weighted fusion, and a cross-encoder, all compared on **short NL function descriptions over a single repository's functions**.

---

## Part C: Development-, commit- and diff-time duplicate detection; AI reuse

_None of these are from Roy's group._

### C1. Uchoa, Sousa, Uchôa, Ragkhitwetsagul, Paixão, Maia, "An Exploratory Study on the Lifecycle of Code Clones During Code Review" (SBES 2025)

- **Access:** full text, plus the SBQS expanded abstract.
- **Research questions:** does cloning occur in code review; which types; what lifecycle.
- **Method:**
  - For each of 80k Gerrit revisions (CROP dataset, 6 **Java** systems), "take the revision's before snapshot and index it into Siamese", then query it with the newly added code.
  - Moved code had to be filtered out, because it appears as added code.
- **Findings:**
  - 27,656 relevant clones; 96.7% precision on a manual sample.
  - Type-I 46.7%, Type-II 7.9%, Type-III 45.3%.
  - Clones "are often introduced early and frequently persist through the review process".
- **Data:** https://zenodo.org/records/16746835
- **Overlap with CodeEcho:** **the same before-snapshot query protocol**. Differences: Java, a code-to-code token detector, and an empirical study rather than a reviewer tool.

### C2. Nakagawa, Higo, Kusumoto, "CLIONE: Clone Modification Support for Pull Request Based Development" (APSEC 2020)

- **Access:** **paper not accessible.** I used the README at https://github.com/T45K/CLIONE.
- **What it does:** a bot "triggered by Pull Requests" that reports clone sets edited inconsistently or newly added.
- **Languages:** Java, Kotlin, **Python**, C++.
- **Detectors:** NiCad (Java, Python, C++) or SourcererCC.
- **Status:** README: "CLIONE is currently unavailable as a GitHub bot". You have to self-host it.
- **⚑ Evaluation figures** come from an abstract snippet only.
- **Overlap with CodeEcho:** **a Python-capable PR bot that flags newly added clones already exists.** It is token-based and has no retrieval, embeddings, or confidence evidence.

### C3. Development-time and incremental detection (classic)

- **Hummel et al. 2010 (A10):** below 1 s per file through an index.
- **SourcererCC-I (A7):** real-time Eclipse plug-in.
- **Barbour, Yuan, Zou, "A Technique for Just-in-Time Clone Detection in Large Scale Systems" (ICPC 2010):** **⚑ abstract summary only.** Commit-time string matching against representative clones.
- **Yamanaka et al., "Applying Clone Change Notification System into an Industrial Development Process" (ICPC 2013), Clone Notifier:** **⚑ snippets only.** Reported as a 40-day trial at NEC.

### C4. AlOmar et al., AntiCopyPaster 1.0 and 2.0 (arXiv:2302.03416, arXiv:2402.06035)

- **Access:** full text.
- **What it does:** an IntelliJ plug-in for **Java** that fires on paste. It compares the pasted code against "all methods inside the same file" (intra-file only) with token bag-of-words, then a CNN decides whether to recommend Extract Method (F-measure 0.82).
- **Code:** https://github.com/refactorings/anti-copy-paster
- **⚑ "AntiCopyPaster 3.0":** I found no full source.
- **Overlap with CodeEcho:** low. IDE-time, intra-file, Java.

### C5. jscpd `--semantic` (open-source tool, MIT licence; not peer-reviewed)

- **Access:** README only (https://github.com/kucherenko/jscpd).
- **What it does:**
  - Token clone detection, plus an experimental Type-4 mode that embeds functions (including **Python**) with CodeRankEmbed, on CPU.
  - `jscpd --changed .` matches the files `git status` lists against the whole project.
- **The README warns:** "Besides real duplicates it reports related code, such as a client function and the server endpoint it calls".
- **Evaluation:** no published evaluation found.
- **Overlap with CodeEcho:** **very high in mechanics** (embeddings plus token clones on changed files, Python). Missing: evidence and confidence output, and validation.

### C6. Huang, Jaisri, Shimizu, Chen, Nakashima, Rodríguez-Pérez, "More Code, Less Reuse: Investigating Code Quality and Reviewer Sentiment towards AI-generated Pull Requests" (MSR 2026; arXiv:2601.21276)

- **Access:** full text.
- **Method:**
  - **Python** PRs from the AIDev dataset (repos with more than 500 stars).
  - Embed every function in the base snapshot with CodeSage-Large.
  - Remove Move/Rename refactorings with PyRef.
  - **Max Redundancy Score** per PR: the maximum, over new functions, of the maximum cosine similarity to any base function.
- **Finding:** "Average Max Redundancy (AMR) for AI agents is 0.2867, compared to only 0.1532 for humans" (Mann-Whitney p < 0.001). Reviewer sentiment toward agent PRs is less negative.
- **Stated limitations:**
  - The redundancy analysis covers **only crewAI** (617 PRs) "due to computational costs".
  - For the PyRef filter, "we manually verified 10 sample of the results".
  - Python only.
- **Observation (mine):** cosine similarity is used as redundancy with no precision or recall validation of the detector, and there is no structural check.
- **Data/code:** no link found in the paper.
- **Overlap with CodeEcho:** **the closest prior work to RQ2.** It uses nearly the same retrieval step, but as an unvalidated study metric, not a validated reviewer.

### C7. Mao, Zhao, Tang, Wang, Zhang, "A Large-Scale Comprehensive Measurement of AI-Generated Code in Real-World Repositories" (arXiv:2603.27130 v3)

- **Access:** full text.
- **Method:** about 19.8k AI-involved files vs. matched human files. Duplication measured with jscpd token detection (≈ T1/T2).
- **Finding:** "human-written code exhibits substantially higher duplication ratios than AI-generated code … (e.g., duplicated lines: 27.57% vs. 14.29%)", driven by cross-file duplication.
- **Caveats (the authors'):** the control set's construction; tool precision.
- **Relevance:** **counter-evidence** at the token level. If AI reimplements, the effect would be T3/T4, which token tools miss.

### C8. Ma, Wang et al. (PKU/Fudan), "Do Coding Agents Reuse Existing Code or Reinvent the Wheel?" (RepoReuse; arXiv:2609.35357, Sep 2026, "Work In Progress")

- **Access:** full text.
- **Setup:** 5 pure-**Python** libraries, 75 five-turn task chains.
- **Reuse metric:** an AST call edge to the target function.
- **Reimplementation rule:** the target "is re-implemented at turn t if st does not call f but calls at least 80% of the non-builtin functions that f itself calls" (only targets with ≥ 3 such callees).
- **Findings:**
  - Agents "leave duplicated logic in 50.8% of task chains by turn 5—all while pass rates barely move".
  - Repository code read falls from 83.6% (turn 1) to 35.4% (turn 5).
- **Limitations:** synthetic tasks; generalisation open.
- **Relevance:** controlled evidence for the motivation. Its callee-overlap rule is a cheap structural baseline CodeEcho should compare against.

### C9. Le Hai, Nguyen, Bui (FPT AI), "REPOEXEC" (arXiv:2406.11927)

- **Access:** full text.
- **What it is:** a **Python** repo-level generation benchmark with Dependency Invocation Rate, DIR = |Dg ∩ Ds| / |Ds|.
- **Findings:** "Pretrained LLMs excel in correctness but often reimplement dependencies". Models were "occasionally reimplementing dependencies already present in the given context".
- **Limitation:** counts direct callees only.
- **Code:** https://github.com/FSoft-AI4Code/RepoExec

### C10. Orlanski et al., "SlopCodeBench" (arXiv:2603.24755)

- **Access:** full text.
- **What it measures:** agents extending their own Python code across checkpoints. Verbosity in 75.5% of trajectories; agent code "2.3x more verbose" than 473 Python repos.
- **Relevance:** self-redundancy, not reuse of pre-existing repo code.

### C11. GitClear, "AI Copilot Code Quality" (2025 industry report; **not peer-reviewed**)

- **Access:** secondary coverage only; the primary page returned 403.
- **Reported claims:** an 8× increase in duplicated 5+-line blocks during 2024. 2024 was the first year copy/pasted lines exceeded moved lines.
- **Caveats:** no per-line AI attribution; commercial interest. Cite only as motivation, if at all.

### C12. Assessment of Part C

- **Already done, in pieces:**
  - Before-snapshot querying with new diff code (C1, Java).
  - Python PR bot for new clones (C2, token-based, offline).
  - Embedding retrieval of new Python functions vs. base, as a study metric (C6, unvalidated).
  - Embeddings plus token clones on changed files (C5, tool, unevaluated).
  - A structural reimplementation heuristic (C8).
- **Not found:**
  - A *validated* Python diff reviewer that combines retrieval with structural evidence.
  - Precision and recall per clone type against embedding-only, token-detector, and callee-overlap baselines.
  - Measurement of how much structural evidence cuts embedding false positives.
- **Evidence that AI reimplements:** suggestive, not established. C6 covers one repository and an unvalidated metric. C8 and C9 are synthetic or preprints. C7 is counter-evidence at the token level.

### C13. Tool and resource notes

- **NiCad Python support:** verified on https://txl.ca/txl-nicaddownload.html. NiCad 6.2 (Nov 2020) "handles a range of languages, including C, Java, Python, C#, ...". It needs FreeTXL 10.8+ and a gcc-compatible compiler, and runs on Linux, Mac, Cygwin, or MinGW. Free to use with acknowledgement in published work.
- **Pyclone** (Duncan, Walker, DeHaan, Alvord, Cerny, Tisnovsky, 2021; doi 10.1007/978-981-33-6385-4_22):
  - I have not read the paper.
  - The repo (https://github.com/calebdehaan/PycloneTestBankCreator) README lists Types 1–4, requires Python 3.7+, and has **no licence file**.
  - **⚑** The SLR (A4) says Types I–III.

---

