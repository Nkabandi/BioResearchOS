# Changelog

All notable changes to BioResearchOS. Semantic versioning: major.minor.patch.

## [0.2.0] - 2026-08-06

### Added
- **BioPaper AI** (`bio-paper-ai/`) — literature review generator
  - PubMed integration (E-utilities esummary)
  - OpenAlex integration (search works, citation-sorted)
  - arXiv integration (best effort; timeout documented)
  - Deduplication + ranking + abstract-level summarization
  - Real demo review: *ML for drug repurposing in rare diseases* (10 papers)
  - workflow.md contract documenting the exact pipeline

### Changed
- Repo indexed as a platform (roadmap in README)

## [0.1.0] - 2026-08-06

### Added
- Pharmacogenomics Reporter (`pharmgx/`)
  - CPIC/PharmGKB-aligned gene–drug rules
  - `report.md` + `report.html` + `result.json` output
  - Reproducibility bundle (exact command replay)
- MIT LICENSE
- Architecture doc (`docs/architecture.md`)
- Demo dataset + generated output under `pharmgx/sample_*`