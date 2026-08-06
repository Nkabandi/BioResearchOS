#!/usr/bin/env python3
"""Stats Engine — statistical analysis for BioResearchOS (v0.4).

Input:  CSV/TSV/XLSX with a numeric target column and a categorical group column.
Output: statistics.md + result.json with, for every test run: the question it
answers, assumptions, test statistic, p-value, effect size (where meaningful),
plain-language interpretation, and a caution.

Tests: descriptive stats + 95% CI, Shapiro-Wilk normality, independent
t-test (Welch), paired t-test, Wilcoxon signed-rank, one-way ANOVA,
Mann-Whitney U, chi-square (uniform fit), Pearson/Spearman correlations,
simple linear regression.

Requires: pandas, numpy, scipy. No statsmodels.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05


def read_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".tsv":
        return pd.read_csv(path, sep="\t")
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported input type: {path.suffix}")


def interpret(p: float) -> str:
    if p < ALPHA:
        return (f"p={p:.4f} < {ALPHA}: reject H0 — the result is unlikely "
                "under chance. A real effect is plausible.")
    return (f"p={p:.4f} >= {ALPHA}: do not reject H0 — insufficient evidence "
            "of an effect in this sample.")


def caution(p: float) -> str:
    if p < ALPHA:
        return ("Small p does not prove practical importance. Check the effect "
                "size, sample size, and whether sampling was representative "
                "before acting.")
    return ("Large p is not proof of 'no effect' — may simply be low power. "
            "Consider the effect size and a larger sample before concluding.")


def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return None
    sp2 = ((na - 1) * float(a.var(ddof=1)) + (nb - 1) * float(b.var(ddof=1))) / (na + nb - 2)
    if sp2 == 0:
        return None
    return (float(a.mean()) - float(b.mean())) / math.sqrt(sp2)


def eta_sq(F: float, df1: int, df2: int) -> float:
    return (df1 * F) / (df1 * F + df2)


def rank_biserial(U: float, n1: int, n2: int) -> float:
    if n1 * n2 == 0:
        return None
    return 1 - (2 * U) / (n1 * n2)


def ci_mean(x: np.ndarray) -> tuple[float, float]:
    if len(x) < 2:
        return float("nan"), float("nan")
    se = float(x.std(ddof=1)) / math.sqrt(len(x))
    t = stats.t.ppf(1 - ALPHA / 2, df=len(x) - 1)
    return float(x.mean() - t * se), float(x.mean() + t * se)


def group_values(df: pd.DataFrame, target: str, group: str) -> dict[str, np.ndarray]:
    return {
        str(g): pd.to_numeric(grp[target], errors="coerce").dropna().to_numpy(dtype=float)
        for g, grp in df.groupby(group, observed=True)
        if pd.to_numeric(grp[target], errors="coerce").dropna().size
    }


def run_tests(df: pd.DataFrame, target: str, group: str) -> list[dict]:
    g = group_values(df, target, group)
    names = list(g)
    r: list[dict] = []

    desc = [{"group": n, "n": int(len(g[n])), "mean": round(float(g[n].mean()), 4),
             "sd": round(float(g[n].std(ddof=1)), 4),
             "ci95_low": round(ci_mean(g[n])[0], 4), "ci95_high": round(ci_mean(g[n])[1], 4)}
            for n in names]
    r.append({"test": "descriptive_and_ci",
              "question": "What are the mean, spread, and 95% CI of the target per group?",
              "assumptions": "Continuous numeric data.",
              "statistic": "mean / sd / 95% CI",
              "p_value": None, "effect_size": None,
              "interpretation": "Descriptive summary of the target column.",
              "caution": "CIs are normal approximation; small n -> check raw data.",
              "detail": desc})

    shapiro = []
    for n in names:
        d = g[n]
        if 8 <= len(d) <= 2000:
            W, p = stats.shapiro(d)
            shapiro.append({"group": n, "shapiro_W": round(float(W), 4),
                            "p": round(float(p), 4)})
    if shapiro:
        sig = any(round(s["p"], 3) < ALPHA for s in shapiro)
        r.append({"test": "normality_shapiro",
                  "question": "Is the target normally distributed within each group?",
                  "assumptions": "Random samples.",
                  "statistic": "Shapiro-Wilk W",
                  "p_value": None, "effect_size": None,
                  "interpretation": ("Departures from normality (p<0.05) suggest "
                                     "using nonparametric tests for that group." if sig else
                                     "No major normality departures detected."),
                  "caution": "Shapiro is sample-size sensitive; interpret alongside QQ plots.",
                  "detail": shapiro})

    if len(names) == 2:
        a, b = g[names[0]], g[names[1]]
        t, p = stats.ttest_ind(a, b, equal_var=False)  # Welch, assumption-light
        d = cohens_d(a, b)
        r.append({"test": "independent_t_welch",
                  "question": f"Do '{names[0]}' and '{names[1]}' differ?",
                  "assumptions": "Independent samples, approx. continuous; Welch tolerates unequal variance.",
                  "statistic": round(float(t), 4), "p_value": round(float(p), 4),
                  "effect_size": round(d, 4) if d is not None else None,
                  "interpretation": interpret(p), "caution": caution(p)})

        u, pu = stats.mannwhitneyu(a, b, alternative="two-sided")
        r_b = rank_biserial(u, len(a), len(b))
        r.append({"name": "mann_whitney_u",
                  "question": "Do the two groups' central tendencies differ (nonparametric)?",
                  "assumptions": "Two independent samples, any distribution (weaker than t-test).",
                  "statistic": round(float(u), 4), "p_value": round(float(pu), 4),
                  "effect_size": round(abs(r_b), 4) if r_b is not None else None,
                  "interpretation": interpret(pu), "caution": caution(pu)})

        if len(a) == len(b):
            tp, pp = stats.ttest_rel(a, b)
            d = cohens_d(a, b)
            w, pw = stats.wilcoxon(a, b)
            z = stats.norm.ppf(pw / 2)
            rbis = abs(z) / math.sqrt(2 * len(a))
            r.append({"name": "paired_t_test",
                      "question": "Are the paired measurements' means different?",
                      "assumptions": "Paired samples (same units), approx. normal differences.",
                      "statistic": round(float(tp), 4), "p_value": round(float(pp), 4),
                      "effect_size": round(d, 4) if d is not None else None,
                      "interpretation": interpret(pp), "caution": caution(pp)})
            r.append({"name": "wilcoxon_signed_rank",
                      "question": "Are the paired medians different (nonparametric)?",
                      "assumptions": "Paired samples, symmetric differences.",
                      "statistic": round(float(w), 4), "p_value": round(float(pw), 4),
                      "effect_size": round(rbis, 4),
                      "interpretation": interpret(pw), "caution": caution(pw)})

    if len(names) >= 3:
        F, pa = stats.f_oneway(*[g[n] for n in names])
        r.append({"name": "one_way_anova",
                  "question": "Do the group means differ across all groups?",
                  "assumptions": "Independent groups, approx. normal, homogeneity of variance.",
                  "statistic": round(float(F), 4), "p_value": round(float(pa), 4),
                  "effect_size": round(eta_sq(F, len(names) - 1, sum(len(g[n]) for n in names) - len(names)), 4),
                  "interpretation": interpret(pa),
                  "caution": caution(pa) + " Which groups differ needs pairwise post-hoc — not included."})

    counts = [len(g[n]) for n in names]
    if len(counts) >= 2 and min(counts) >= 1:
        chi2, pch = stats.chisquare(counts)
        r.append({"name": "chi_square_gof",
                  "question": "Are samples evenly distributed across groups?",
                  "assumptions": "Observed counts; expected uniform.",
                  "statistic": round(float(chi2), 4), "p_value": round(float(pch), 4),
                  "effect_size": round(math.sqrt(chi2 / (sum(counts) * (len(counts) - 1))), 4),
                  "interpretation": interpret(pch),
                  "caution": caution(pch) + " Unbalanced experiments should use expected proportions, not uniform."})

    numcols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target]
    for other in numcols:
        d = df[[target, other]].dropna()
        if len(d) >= 5:
            rp, pp = stats.pearsonr(d[target], d[other])
            rs, ps = stats.spearmanr(d[target], d[other])
            r.append({"name": "correlations",
                      "question": f"Is '{target}' linearly (or monotonically) related to '{other}'?",
                      "assumptions": "Pearson: linear relation, no big outliers. Spearman: monotone.",
                      "statistic": f"r={rp:.3f} / ρ={rs:.3f}",
                      "p_value": round(float(min(pp, ps)), 4),
                      "effect_size": round(abs(rp), 3),
                      "interpretation": interpret(min(pp, ps)),
                      "caution": caution(min(pp, ps)) + " Correlation ≠ causation."})

    for other in numcols:
        d = df[[target, other]].dropna()
        if len(d) >= 5:
            res = stats.linregress(d[other], d[target])
            r.append({"name": "simple_linear_regression",
                      "question": f"Does '{other}' predict '{target}'?",
                      "assumptions": "linearity, homoscedasticity, independence, residual normality.",
                      "statistic": f"slope={res.slope:.3f}, intercept={res.intercept:.3f}, R²={res.rvalue**2:.3f}",
                      "p_value": round(float(res.pvalue), 4),
                      "effect_size": round(res.rvalue ** 2, 4),
                      "interpretation": interpret(res.pvalue),
                      "caution": caution(res.pvalue) + " Extrapolating outside observed range is risky."})

    return r


def demo_df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 60
    return pd.DataFrame({
        "sample_id": [f"S{i:03d}" for i in range(2 * n)],
        "expression": np.concatenate([rng.normal(10, 1.5, n), rng.normal(13.5, 1.6, n)]).round(3),
        "dose": rng.uniform(1, 20, 2 * n).round(2),
        "group": ["control"] * n + ["treated"] * n,
    })


def write_report(results, out: Path) -> Path:
    md = ["# Statistics Engine Report", "",
          f"α = {ALPHA}  ·  tests: {len(results)}", ""]
    for t in results:
        md.append(f"## {' '.join(word.capitalize() for word in t.get('test', t.get('name', '?')).split('_'))}")
        md.append(f"- **Question:** {t['question']}")
        md.append(f"- **Assumptions:** {t['assumptions']}")
        md.append(f"- **Statistic:** {t['statistic']}")
        if t.get("p_value") is not None:
            md.append(f"- **p-value:** {t['p_value']}")
        if t.get("effect_size") is not None:
            md.append(f"- **Effect size:** {t['effect_size']}")
        md.append(f"- **Interpretation:** {t['interpretation']}")
        if t.get("caution"):
            md.append(f"- **Caution:** {t['caution']}")
        if "detail" in t:
            md.append("")
            cols = list(t["detail"][0].keys())
            md.append("| " + " | ".join(cols) + " |")
            md.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for row in t["detail"]:
                md.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        md.append("")
    md.append("---")
    md.append("*Generated by Stats Engine (BioResearchOS) — research/educational, not medical/statistical advice.*")
    p = out / "statistics.md"
    p.write_text("\n".join(md))
    return p


def main():
    ap = argparse.ArgumentParser(description="Stats Engine")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path, default=Path("out"))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--target", default="expression")
    ap.add_argument("--group", default="group")
    a = ap.parse_args()
    if a.demo:
        df = demo_df()
    elif a.input:
        df = read_input(a.input)
    else:
        ap.error("need --input or --demo")
    a.output.mkdir(parents=True, exist_ok=True)
    results = run_tests(df, a.target, a.group)
    report = write_report(results, a.output)
    (a.output / "result.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"Statistics report -> {report}")
    print(f"result.json       -> {a.output / 'result.json'}")


if __name__ == "__main__":
    main()