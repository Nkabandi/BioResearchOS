# BioPaper AI

**Automatically searches the scientific literature, compares relevant studies, extracts methods, and produces a structured literature review — in minutes.**

Built for biotechnology students and researchers who need a defensible starting point for a review, not a ChatGPT summary blob. Every claim traces to a real search result with a stable identifier (PubMed ID, OpenAlex Work ID).

## Input

```text
Topic
```

## Output

```text
literature_review.md
```

Sections: Overview · Key papers table (Paper / Year / Method / Finding) · Methods landscape · Consensus · Disagreements · Open questions · References · Automated-review disclaimer.

## Pipeline

```
Topic
 ↓
Search PubMed ──────────────► E-utilities (esummary)
Search OpenAlex ────────────► search works, citation-sorted
Search arXiv (optional) ────► query API
 ↓
Deduplicate (title match across sources)
 ↓
Rank relevance / recency
 ↓
Summarize each paper (abstract-level)
 ↓
Extract methods → consensus → disagreements → open questions
 ↓
Generate references (numbered) + caveat
 ↓
literature_review.md
```

## Example

`sample_output/literature_review.md` is a **real, generated review** on *"machine learning for drug repurposing in rare diseases"* — 10 papers merged from PubMed + OpenAlex, deduplicated, ranked, summarized.

## Note on this version

- Source integration is **search + metadata only**: the pipeline reads titles, abstracts, and identifiers, not full texts. Full-text method extraction is on the roadmap.
- arXiv API was timing out during generation; the demo review documents this instead of silently dropping a source.
- Every review ends with an explicit caution that it is an **automated first pass** and must be verified against primary sources before citation.

## Roadmap (semantic versions)

- v0.2: paper ranking by recency + citation floor
- v0.3: full-text method extraction (PubMed Central / bioArxiv Open Access)
- v0.4: evidence tables
- v0.5: automatic citations (BibTeX/CSL)
- v1.0: complete literature review generator with configurable depth