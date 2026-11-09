# Annotation guidelines for the RQ1 search benchmark

Goal: about 20 queries per repo (instructor, fastmcp, crewAI). Each query is a short description a developer might type when looking for an existing helper before writing one. Each is labelled with the function(s) that satisfy it.

## Writing a query

1. **Describe the need, not the code.** Write what you want done, the way you'd ask a colleague: "retry a failing call with exponential backoff", not "retry_with_backoff".
2. **Don't copy identifiers.** Avoid function, class, or variable names from the target code. Ordinary words that happen to appear in a name are fine ("parse", "schema") if that's how you'd naturally say it. The script measures word overlap between query and answer, and we report it.
3. **Keep it short:** 3–12 words, one need per query.
4. **Prefer reusable helpers:** utilities, converters, validators, formatters, small algorithms. Skip framework plumbing nobody would search for (`__init__`, trivial getters).
5. **Mix of difficulty.** Some queries should be easy (obvious vocabulary), some hard (different vocabulary from the code). Don't only write queries you know the tool will get right.
6. **Write the query before you look up the answer.** This is the main guard against copying the code's wording. A practical order: skim a module to see what kinds of things exist, close it, write 3–5 needs from memory, then label.

## Labelling

The helper shows a **pooled, shuffled** list of candidates from every search method being evaluated. You can't see which method found what. Mark every candidate that would genuinely satisfy the need if you called or reused it.

- **Relevant:** calling or reusing this function solves the need, possibly with trivial adaptation.
- **Not relevant:** related topic but doesn't do the job; private internals you wouldn't reuse; tests.
- If the right function is **not in the list**, add it with `+name` (searches by name). Functions outside the pool count as non-relevant unless added. This is standard pooling, noted as a limitation.
- If **nothing** in the repo satisfies the need, label it as unanswerable. We keep these separately; they test whether tools return confident wrong answers.
- Use the note field for anything ambiguous.

## Second annotator

A second person labels a random subset of about 20 queries independently, without seeing the first labels. We report Cohen's κ on relevant vs. not-relevant decisions over the pooled candidates.
