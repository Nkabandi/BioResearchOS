# BioData

**Turns any CSV, TSV, or Excel dataset into a publication-ready analysis — summary, statistics, figures, and a notebook — in one command.**

For biotechnology coursework: every statistics assignment becomes a reproducible artifact instead of a one-off spreadsheet.

## Input

```
csv | tsv | xlsx
```

## Output

| Artifact | What it is |
|----------|-----------|
| `report.md` / `report.html` | Summary, missing-value report, descriptive statistics |
| `tables/summary.csv` | Per-column dtype + missing counts |
| `tables/describe.csv` | Descriptive statistics (mean, std, quartiles...) |
| `tables/correlation.csv` | Correlation matrix |
| `figures/hist_*.png` | Distribution plots per numeric column |
| `figures/correlation.png` | Correlation heatmap |
| `figures/pca.png` | PCA of numeric columns (when ≥2) |
| `result.json` | Structured summary (rows, columns, dtypes, missing) |
| `notebook.ipynb` | Minimal reproducible analysis notebook |

## Usage

```bash
# demo (deterministic, seed=42 — same output every run)
python bio_data.py --demo --output out/

# your own data
python bio_data.py --input data.csv --output out/
```

Requires: `pandas`, `numpy`, `matplotlib`, `scikit-learn`.

## Example

`sample_input/sample_dataset.csv` — synthetic dose–response experiment (200 samples, 4 intentional missing values per numeric column). `sample_output/` is the complete generated analysis.

## Why it's reproducible

The demo uses a fixed RNG seed and pure derived statistics (no inference to fit), so `--demo` produces byte-identical reports every run. Good for demos, tests, and PR evidence.

## Roadmap

- v0.4: statistical test engine (t-test, ANOVA, correlation significance)
- v0.5: publication figures styling (matplotlib rcParams presets)
- v0.6: experiment assistant (group comparisons + report assembly)