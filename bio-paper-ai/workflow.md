# BioPaper AI — Workflow

## How a review is produced

This project is currently an **agent workflow** (no standalone script yet): an AI agent with search tools executes the pipeline turn-by-turn. The steps below are the exact contract the agent follows.

### 1. Query construction

From the user's topic, build three queries:
- PubMed: `topic keywords`
- OpenAlex: `topic keywords` (search works, sort by citations)
- arXiv: `topic keywords` (best-effort; skip-and-report on timeout)

### 2. Discovery

- PubMed → return up to 8 PMIDs + sources
- OpenAlex → return up to 8 works (title, year, venue, citations, Work ID)
- arXiv → return up to 5 papers

### 3. Merge & deduplicate

Match titles between sources (normalize case/punct). If a paper appears in 2 sources, keep one row and record both IDs.

### 4. Rank

Order by: recency first, then citation count floor. Target 8–12 papers in a review.

### 5. Summarize

One row per paper in the key-papers table: **Paper | Year | Method | Finding** — method and finding are abstract-level, never invented from nothing.

### 6. Synthesize

Write: Methods landscape → Consensus → Disagreements → Open questions. Every bullet must trace to at least one paper in the table.

### 7. Reference

Numbered list of the papers in the table, with PubMed ID / OpenAlex Work ID / DOI for every entry.

### 8. Caveat (mandatory)

Every generated review ends with: *This is an automated example review; verify all papers against primary sources before citation.*

## Guarantees

- **No hallucinated citations** — every reference has a real PMID or Work ID from the search step.
- **No invented findings** — each summary sentence originates from an abstract.
- **Source failures are reported, not hidden** — e.g. an arXiv timeout is explicitly documented in the output (see the demo review).
- **Research-only framing** maintained: reviews are decision-support, not medical or academic-grade output without verification.

## Roadmap to v1.0

| Version | Capability |
|---------|-----------|
| v0.1 | Discovery + dedupe + abstract-level summarization (current) |
| v0.2 | Ranking by recency + citation floor |
| v0.3 | Full-text method extraction (PMC/bioArxiv OA) |
| v0.4 | Evidence tables |
| v0.5 | Auto-citations (BibTeX/CSL) |
| v1.0 | Complete review generator, configurable depth |