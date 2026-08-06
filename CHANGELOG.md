# Changelog

All notable changes to BioResearchOS. Semantic versioning: major.minor.patch.

## [0.5.0] - 2026-08-07

### Added
- **Report Generator** (`reports/`) — wraps EvidenceTable into a consulting report
  - Cover → Executive Summary → Research Question → Methods → Evidence Table → Key Findings → Research Gaps → Limitations → References
  - `report.md` + self-contained `report.html` (File→Print→Save as PDF)
- **Project Template** (`projects/TEMPLATE/`) — standardized folder layout per engagement
- **Intake Form** (`projects/TEMPLATE/intake_form.md`) — question, purpose, deliverables, citation style, budget
- **Portfolio** (`portfolio/`) — working demo report on real verified evidence (sales material)

## [0.4.0] - 2026-08-07

### Added
- **EvidenceTable** (`evidence/`) — verified evidence tables + citation checker
  - Every DOI checked against Crossref; hallucinated/mistyped citations flagged
  - `evidence_table.md` (client handout), `citation_check.csv`, `rejections.md`, `result.json`
  - Demo: 8/8 real DOIs verified (2 deliberate fakes rejected)

## [0.3.0] - 2026-08-06

### Added
- **BioData** (`bio-data/`) — dataset analysis skill
  - CSV / TSV / XLSX input
  - Missing-value report + descriptive statistics tables
  - Distribution histograms, correlation heatmap, PCA
  - report.md / report.html / result.json / notebook.ipynb
  - Deterministic demo (seed=42) + sample input/output

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