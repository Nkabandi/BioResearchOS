# EvidenceTable + Citation Checker

**The client-ready deliverable.** Produces a verified evidence table where every DOI is cross-checked against Crossref — a hallucinated or mistyped citation cannot survive a BioResearchOS report.

## What it does

| Output | Purpose |
|--------|---------|
| `evidence_table.md` | Paper / Status / Reference / Sample / Method / Finding / Limitations — the report table you hand a client |
| `citation_check.csv` | Per-DOI verdict from Crossref |
| `rejections.md` | Human-readable list of citations that failed verification |
| `result.json` | Machine-readable summary (total / verified / rejects) |

## Usage

```bash
python evidence/evidence_table.py \
  --input evidence/sample_input/papers.csv \
  --output output/evidence/
```

Input CSV columns — only `doi` is required:

```
doi,title,year,sample,method,finding,limitations,group
```

Where `title`/`year` are supplied, they are compared against Crossref and any mismatch is flagged `MISMATCH_*`. A DOI with no Crossref record is flagged `NOT_FOUND`. `finding` and `limitations` carry from your literature review into the client table.

## Verdicts

- `VERIFIED` — Crossref record matches supplied title+year
- `MISMATCH_TITLE` / `MISMATCH_YEAR` — real paper, but your citation metadata is wrong
- `NOT_FOUND` — DOI unregistered: either invented or a real citation with a broken DOI

## Safety

Crossref is a public bibliographic registry (no key, no patient data). All replication is
local; reports must carry the ClawBio disclaimer when used for research/education.