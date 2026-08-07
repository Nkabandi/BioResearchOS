#!/usr/bin/env python3
"""Science Report — knowledge graph + claim normalization + human review gate.

Combines the per-topic verification outputs into one Claude-Science-style
notebook: every claim carries a verdict (confidence / evidence weight / study
grades), a falsifiable test statement, a review flag, and full provenance back
to its source rows (Study / DOI / Method / Population / Result / Limitations).
Claims are linked into a small knowledge graph over three edge types:

  CLAIM -> TOPIC       (claim held in this topic)
  CLAIM -> DOI         (claim grounded in this source, normalized DOI key)
  CLAIM -DOI- CLAIM    (two claims citing the same source)

Which is enough to see cross-topic reuse and source overlap without a
database. Official connectors (PubMed / OpenAlex / ClinicalTrials.gov) are not
called here — this is a local static build; add a connector only when a client
report needs a live source fetch (PMID/URL resolution happens there).

Run:
  python reports/science_report.py --topics portfolio/amr-east-africa/evidence \\
    portfolio/malaria-resistance/evidence portfolio/tb-diagnostics/evidence \\
    portfolio/agricultural-biotech/evidence [--out <file.md>] [--graph <graph.json>]

Writes one markdown notebook and an optional knowledge-graph JSON.
"""
import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_evidence(ev: Path) -> dict:
    """source rows keyed by normalized DOI; provenance / population / limitations."""
    prov = {}
    for r in csv.DictReader(open(ev / "evidence_table.csv", encoding="utf-8")):
        doi_m = re.search(r"10\.\S+", r.get("Reference", ""))
        if not doi_m:
            continue
        doi = doi_m.group(0).lower()
        prov.setdefault(doi, []).append({"paper": r.get("Paper", "").strip(),
                                         "doi": doi,
                                         "reference": r.get("Reference", "").strip(),
                                         "status": r.get("Status", "").strip(),
                                         "sample": (r.get("Sample") or "").strip(),
                                         "method": (r.get("Method") or "").strip(),
                                         "population": (r.get("Sample") or "").strip(),
                                         "limitations": (r.get("Limitations") or "").strip()})
    return prov


def load_verif(ev: Path) -> tuple[list[dict], dict]:
    table = list(csv.DictReader(open(ev / "verification.csv", encoding="utf-8")))
    contradicted = set()
    try:
        contradicted = {r["metric"].strip()
                        for r in csv.DictReader(open(ev / "contradictions.csv", encoding="utf-8"))}
    except FileNotFoundError:
        pass
    prov = load_evidence(ev)
    for c in table:
        c["contradiction"] = c["metric"] in contradicted
        c["dois"] = [d for d in c["dois"].split() if d]
        c["sources_n"] = int(c["sources"])
        c["verified"] = c["verified"] == "y"
        c["provenance"] = [s for d in c["dois"] for s in prov.get(d.lower(), [])]
        c["components"] = {k: (int(v) if v.strip() else None)
                           for k, v in ({"quality": c.get("quality", ""),
                                         "agreement": c.get("agreement", ""),
                                         "sample": c.get("sample", ""),
                                         "recency": c.get("recency", ""),
                                         "overall": c.get("overall", "")}).items()}
    return table, prov


def build(spec: list[tuple[Path, str]]) -> dict:
    """Claims + graph edges (claim->topic, claim->doi, claim~claim shared doi)."""
    claims, by_doi = [], {}
    for i, (ev, topic) in enumerate(spec):
        rows, _prov = load_verif(ev)
        for row in rows:
            nid = f"{topic}:{row['metric']}"
            claims.append({"id": nid, "topic": topic, "metric": row["metric"],
                           "claim": row["claim"], "verified": row["verified"],
                           "confidence": row["confidence"],
                           "conf_score": float(row["conf_score"]),
                           "ev_weight": int(row["ev_weight"]),
                           "study_types": row["study_types"].split(),
                           "sources_n": row["sources_n"], "dois": row["dois"],
                           "contradiction": row["contradiction"],
                           "components": row["components"],
                           "provenance": row["provenance"]})
            for d in row["dois"]:
                by_doi.setdefault(d.lower(), []).append(nid)   # claim -> doi
    edges = []
    for c in claims:
        edges.append((f"claim:{c['id']}", f"topic:{c['topic']}"))
        edges.append((f"claim:{c['id']}", f"source:{d.lower()}"))     # claim -> doi
    shared = {(u, v) for ids in by_doi.values() for u in ids for v in ids if u < v}
    edges += [(f"claim:{u}", f"claim:{v}") for u, v in sorted(shared)]
    return {"claims": claims, "edges": edges}


def falsified(c: dict) -> str:
    pcts = [(float(a), float(b) if b else float(a))
            for a, b in re.findall(r"(\d{1,3}(?:\.\d+)?)(?:-(\d{1,3}(?:\.\d+)?))?%", c["claim"])]
    if not pcts:
        return "No numeric range — cannot test against screened sources."
    if c["contradiction"]:
        return "Conflict: source ranges do not overlap."
    lo = min(p[0] for p in pcts); hi = max(p[1] for p in pcts)
    f = lambda x: f"{x:g}" if x == int(x) else f"{x:.1f}"
    rival = ("a new meta-analysis" if c["confidence"] == "High"
             else "a higher-grade study")
    return (f"Falsified if {rival} reports a range outside "
            f"{f(lo)}–{f(hi)}% for this population.")


def review_flags(c: dict) -> list[str]:
    out = []
    if not c["verified"]:
        out.append("UNVERIFIED source — do not reuse")
    if c["contradiction"]:
        out.append("Contradicting ranges across sources")
    if c["sources_n"] == 1:
        out.append("Single source — needs a second independent study")
    if c["confidence"] == "Low":
        out.append("Low confidence — treat as hypothesis")
    return out


def build_md(nb: dict) -> str:
    lines = ["# BioResearchOS — Science Report", "",
             f"*{date.today().isoformat()} · {len(nb['claims'])} claims · "
             f"topics: {', '.join(sorted({c['topic'] for c in nb['claims']}))}*", "",
             "Components: Evidence quality · Agreement · Sample size · Recency · Overall. "
             "Overall is the weighted mean of available components (quality .45, agreement .30, "
             "sample .15, recency .10); missing sample size drops that factor.", "",
             "## Claim Verdicts", "", "| Claim | Topic | Confidence | Weight | Grades | "
             "Components | Fails if | Review flag |", "|---|---|---|---|---|---|---|---|"]
    for c in sorted(nb["claims"], key=lambda x: (x["topic"], -x["conf_score"])):
        flagged = "; ".join(review_flags(c)) or "—"
        comp = c["components"]
        comp_s = f"q{comp['quality']}/a{comp['agreement']}/n{comp['sample'] or '?'}/r{comp['recency']}/{comp['overall']}"
        lines.append(f"| {c['claim'][:80]} | {c['topic']} | {c['confidence']} "
                     f"({c['conf_score']}) | {c['ev_weight']} | {', '.join(c['study_types'])} | "
                     f"{comp_s} | {falsified(c)} | {flagged} |")
    lines += ["", "## Provenance", "",
              "Every claim traces to its source rows: study, DOI, population, "
              "method, and stated limitations.", ""]
    for c in sorted(nb["claims"], key=lambda x: (x["topic"], x["metric"])):
        if not c["provenance"]:
            continue
        lines.append(f"### {c['metric']} — {c['claim'][:110]}")
        lines.append("")
        for s in c["provenance"]:
            lines.append(f"- **{s['paper'][:90]}** · `{s['doi']}` · {s['status']}")
            if s["population"]:
                lines.append(f"  - Population: {s['population'][:160]}")
            if s["method"]:
                lines.append(f"  - Method: {s['method'][:160]}")
            if s["limitations"]:
                lines.append(f"  - Limitations: {s['limitations'][:160]}")
        lines.append("")
    lines += ["## Knowledge Graph", "",
              f"{len(nb['edges'])} edges: claim→topic, claim→DOI, shared-DOI links.", "",
              "```json", json.dumps(nb, indent=2)[:8000], "```", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topics", nargs="+", required=True,
                    help="evidence dirs (dir parent = topic name)")
    ap.add_argument("--out", default=str(ROOT / "reports" / "science_report.md"))
    ap.add_argument("--graph", default="")
    a = ap.parse_args()
    spec = [(Path(p), Path(p).parent.name) for p in a.topics]
    nb = build(spec)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_md(nb))
    if a.graph:
        Path(a.graph).write_text(json.dumps(nb, indent=2))
        print(f"graph -> {a.graph}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()