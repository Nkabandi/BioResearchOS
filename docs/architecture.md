# Architecture

## Core idea

BioResearchOS is a thin orchestration layer over domain **skills** (from ClawBio). Each skill is:

1. A `SKILL.md` — YAML frontmatter (openclaw schema) + a markdown methodology that an AI agent can follow directly.
2. An optional Python implementation accepting `--input`, `--output`, `--demo`.
3. Registered in the CLI's `SKILLS` dict with an `allowed_extra_flags` whitelist (security).

## Flagship pipeline: pharmgx

```
genetic file
  → parse (tsv/vcf/txt)        | clawbio.common.parsers
  → normalize genotypes        | genotypes_to_simple / genotypes_to_positions
  → evaluate gene–drug rules    | CPIC/PharmGKB-aligned tables in SKILL.md
  → report                      | report.md + report.html
  → structured findings         | result.json
  → reproducibility             | commands.sh (exact run replay)
```

## Reproducibility

Every run writes `reproducibility/commands.sh` containing the exact command
used, so any report can be regenerated bit-for-bit. Treat reports as
derivatives, never edited by hand.

## AI-assisted workflow

The agent portion uses a research agent pool: literature (PubMed/OpenAlex/
arXiv), company intelligence (Exa/Firecrawl/Apify), data (DuckDB). See the
parent repo's roadmap for packaging these into standalone projects.

## Safety

- Local-first: no patient data leaves the machine.
- Every report carries the research-only disclaimer.
- Per-skill flag whitelists in the CLI; random extra flags rejected.