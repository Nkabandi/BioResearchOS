# BioResearchOS

**A local-first biotechnology AI operating system.** A growing collection of agents that turn natural-language prompts into reproducible scientific outputs — genome interpretation, literature reviews, company intelligence, and data analysis. Genetic data never leaves the machine.

Current flagship: **Pharmacogenomics Reporter** (`pharmgx/`).

---

## What problem does this solve?

Bringing a genetic dataset to a pharmacogenomics question today means wrangling databases (CPIC, PharmGKB, ClinVar), lookup tables, and report generators by hand. BioResearchOS packages that workflow into a single command that produces a clinician-readable `report.md`, a structured `result.json`, and a reproducibility trail — all local-first.

## Who is it for?

- Students and researchers exploring their own **WGS / genotyping** data
- AI developers wanting a **reference implementation** of a domain skill
- Anyone who wants to see how an LLM toolchain produces a **verifiable scientific report** instead of a chat blob

## How it works

```
genetic file ──► pharmgx skill ──► report.md + result.json + reproducibility/
(tsv/vcf/txt)        │
                     └── CPIC/PharmGKB-aligned gene–drug rules
```

The skills are built on [ClawBio](https://github.com/OpenClaw/ClawBio) — each is a self-contained module registered in a CLI that enforces per-skill argument whitelists (no arbitrary flags, no data exfiltration).

## Quickstart

```bash
# one project, end-to-end (pharmacogenomics demo)
python clawbio.py run pharmgx --demo --output out/

# with your own data
python clawbio.py run pharmgx --input your_genotypes.txt --output out/
```

The demo needs no network and no setup. See `pharmgx/sample_output/` for a real generated report.

## What's inside

| Path | What it is |
|------|-----------|
| `pharmgx/` | Pharmacogenomics Reporter — flagship project |
| `pharmgx/sample_input/` | Demo genetic dataset |
| `pharmgx/sample_output/` | Real generated report, JSON, reproducibility trail |
| `bio-paper-ai/` | Literature review agent + sample review |
| `bio-data/` | Dataset analysis: stats, figures, notebook |
| `evidence/` | EvidenceTable — verified citations + client-ready evidence tables |
| `docs/` | Architecture + workflow notes |
| `notebooks/` | Analysis notebooks (bio-data) |
| `data/` | Cleaned demo datasets (bio-data) |
| `screenshots/` | UI/figure captures (added as we ship) |

## Technologies

Python 3.10+ · pathlib · argparse · pandas · OpenTelemetry · Markdown reporting · local-first (no cloud, no patient-data upload).

## Roadmap

- [x] Pharmacogenomics Reporter (`pharmgx`)
- [x] **BioPaper AI** — literature review agent (PubMed / OpenAlex) — *v0.2*
- [x] **BioData** — dataset analysis (CSV/TSV/XLSX → stats + figures + notebook) — *v0.3*
- [x] **EvidenceTable** — verified evidence tables + citation checker (Crossref) — *v0.4*
- [ ] **BioLearn** — AI tutor: explanations, quizzes, flashcards
- [ ] **BioOutreach** — company research → personalized outreach
- [ ] Screenshots + one-minute demo GIF per project
- [ ] CI: tests on Python 3.10–3.12

## Safety

BioResearchOS is a **research and educational tool**. It is not a medical device and does not provide clinical diagnoses. Consult a healthcare professional before making any medical decisions.

## License

MIT — see `LICENSE`.

## Related

- [ClawBio](https://github.com/OpenClaw/ClawBio) — the underlying skill library
- [Service site](https://nkabandi.github.io/BioResearchOS/) — one-page offer/portfolio (source: `docs/index.html`)