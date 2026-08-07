"""Evidence Engine — cross-verification, source scoring, contradiction
detection, and research memory for BioResearchOS.

Reads the two CSVs the report pipeline already writes per topic
(evidence_table.csv + citation_check.csv) and adds the verification
layers from the v2 intelligence spec:

  1. Source reliability scoring   (curated trust tiers per venue)
  2. Cross-verification          (same metric in >=2 independent sources)
  3. Contradiction detection     (non-overlapping ranges, same acronym)
  4. Confidence scoring          (High/Medium/Low per metric, derived)
  5. Research memory             (append verified claims to a JSON index)

Local-only: no network. CSV inputs already exist per topic.

Run:
  python reports/evidence_engine.py --evidence portfolio/amr-east-africa/evidence

Writes <evidence>/verification.csv and appends to reports/knowledge/memory.json.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Trust tiers for source venue (10 = primary/peer-reviewed, 1 = rumour).
_TIERS = [
    (("\bnature\b", "\bscience\b", "\bcell\b", "who", "fda", "ema", "clinicaltrials",
      "nih", "sec", "pubmed"), 10),
    (("preprint", "biorxiv", "medrxiv", "lay summary"), 7),
    (("linkedin",), 5),
    (("reddit",), 2),
    (("blog",), 1),
]


def tier(venue: str) -> int:
    v = (venue or "").lower()
    for patterns, score in _TIERS:
        if any(re.search(p, v) for p in patterns):
            return score
    return 9  # peer-reviewed journal


_PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)(?:-(\d{1,3}(?:\.\d+)?))?%")
# Evidence grade: label + weight, ordered strongest-first (meta-analysis > sys-review
# > RCT > cohort > case-control > cross-sectional > review > case report > opinion).
_GRADE = [
    (("meta-?analysis",), ("meta-analysis", 10)),
    (("systematic review",), ("systematic review", 9)),
    (("rct", "randomized", "randomised", "controlled trial"), ("RCT", 8)),
    (("cohort",), ("cohort", 6)),
    (("case[- ]control",), ("case-control", 5)),
    (("cross[- ]sectional", "survey"), ("cross-sectional", 4)),
    (("case report", "single patient"), ("case report", 2)),
    (("expert", "expert panel"), ("expert opinion", 1)),
    (("review of", "literature review"), ("review", 3)),
    ((), ("other", 4)),  # peer-reviewed row with no declared design
]


def study_grade(seg: str) -> tuple[str, int]:
    s = (seg or "").lower()
    for pats, grade in _GRADE:
        if any(re.search(p, s) for p in pats):
            return grade
    return ("other", 4)
_ACR = re.compile(r"\b([A-Z][A-Z0-9]{1,12})\b")
_WORD = re.compile(r"[a-z]{3,}")

_YEAR = re.compile(r"\((\d{4})\)")
_NUM_UNIT = re.compile(r"(\d{2,}(?:,\d{3})*)\s*(patients|samples|isolates|participants|"
                       r"studies|accessions|varieties|fields|genomes|farms|farmers|clones|subjects|rows)")


def year_of(src: str | None) -> int | None:
    m = _YEAR.search(src or "")
    return int(m.group(1)) if m else None


def sample_n(method: str, blob: str) -> float | None:
    """First confident N from method/sample text; None if no extractable size."""
    m = _NUM_UNIT.search(f"{method or ''} {blob or ''}")
    return int(m.group(1).replace(",", "")) if m else None


# Evidence quality from best study grade: meta->95 down to opinion->40.
_QUAL = {"meta-analysis": 95, "systematic review": 90, "RCT": 82, "cohort": 78,
         "case-control": 70, "cross-sectional": 64, "other": 60, "review": 55,
         "case report": 45, "expert opinion": 40}


def _age_score(year: int | None, this_year: int) -> int:
    if year is None:
        return 70  # unknown recency = neutral, no penalty
    age = max(0, this_year - year)
    return 95 if age <= 2 else 85 if age <= 6 else 70 if age <= 10 else 50 if age <= 15 else 35


def _sample_score(n: int | None) -> int | None:
    """Order-of-magnitude sample size -> score. Unit-agnostic (accessions vs
    patients share a scale by design); N=1k+ beats N=10 because it does, and
    that's the honest signal available. None when no size was extractable."""
    if n is None:
        return None
    return 92 if n >= 10000 else 84 if n >= 1000 else 72 if n >= 100 else 60 if n >= 10 else 45


# Overall component weights: quality dominates, recency matters least. Missing
# components (no extractable N, unknown year) are dropped and the rest renormalized.
_COMPONENT_WEIGHTS = {"quality": 0.45, "agreement": 0.30, "sample": 0.15, "recency": 0.10}


def components(acr: str, group: list[dict], conflict: bool, this_year: int) -> dict:
    """Evidence-weighting v2: decompose a verdict into quality/agreement/
    sample/recency + overall. Display-only — the High/Medium/Low gate is
    unchanged so confidence calibration does not drift."""
    best_grade = max(group, key=lambda c: c["weight"])["grade"]
    comp = {
        "quality": _QUAL[best_grade],
        "agreement": 55 if len(group) < 2 else 45 if conflict else 90,
        "sample": _sample_score(max((c["n"] for c in group if c["n"]), default=None)),
        "recency": _age_score(max((c["year"] for c in group if c["year"]), default=None), this_year),
    }
    present = {k: v for k, v in comp.items() if v is not None}
    total = sum(_COMPONENT_WEIGHTS[k] for k in present)
    comp["overall"] = round(sum(v * _COMPONENT_WEIGHTS[k] for k, v in present.items()) / total)
    return comp


def _acronym(seg: str) -> str:
    """Pick the most identifying acronym in a segment, or first keyword."""
    acrs = _ACR.findall(seg)
    acrs = [a for a in acrs if a.lower() not in ("who", "eac", "cm", "cl") or a == "WHO"]
    if acrs:
        return max(acrs, key=len)
    words = _WORD.findall(seg.lower())
    return " ".join(words[:3]) if words else ""


def _pcts(seg: str) -> list[tuple[float, float]]:
    out = []
    for a, b in _PCT.findall(seg):
        out.append((float(a), float(b) if b else float(a)))
    return out


def verify(ev_path: Path) -> dict:
    """Return per-metric verdicts + cross-source contradiction flags."""
    table = list(csv.DictReader(open(ev_path / "evidence_table.csv", encoding="utf-8")))
    checks = {}
    try:
        checks = {r["doi"]: r.get("status")
                  for r in csv.DictReader(open(ev_path / "citation_check.csv", encoding="utf-8"))}
    except FileNotFoundError:
        pass

    metrics = defaultdict(list)          # acronym -> segments (its sources)
    for row in table:
        src = row.get("Reference", "")
        doi_m = re.search(r"10\.\S+", src)
        doi = doi_m.group(0) if doi_m else ""
        verified = checks.get(doi) == "VERIFIED"
        t = tier(src)
        grade, weight = study_grade(row.get("Method") or "")
        year = year_of(src)
        n = sample_n(row.get("Method") or "", row.get("Sample") or "")
        for seg in (row.get("Finding") or "").split(";"):
            seg = seg.strip()
            if not seg:
                continue
            acr = _acronym(seg)
            if acr:
                metrics[acr].append({"seg": seg, "pcts": _pcts(seg), "tier": t,
                                     "verified": verified, "doi": doi, "source": src,
                                     "grade": grade, "weight": weight, "year": year, "n": n})

    # Contradiction: same acronym, non-overlapping numeric ranges.
    conflicts = []
    for acr, group in metrics.items():
        if len(group) < 2:
            continue
        ranges = [p for c in group for p in c["pcts"]]
        if not ranges:
            continue
        lows = [p[0] for p in ranges]
        highs = [p[1] for p in ranges]
        overlap = max(lows) <= min(highs)
        if not overlap:
            conflicts.append({"metric": acr, "range": f"{min(lows)}–{max(highs)}%",
                              "sources": [c["source"].split("(")[0].strip() for c in group]})

    # Confidence: High = verified, >=2 independent sources, no contradiction,
    # strongest evidence grade >= RCT (weight 8); Medium = verified but 1 source,
    # conflict-flagged, or weaker evidence design; Low = unverified.
    conflict_acrs = {x["metric"] for x in conflicts}
    this_year = datetime.now().year
    claims = []
    for acr, group in metrics.items():
        n = len(group)
        verified = any(c["verified"] for c in group)
        best = max(c["weight"] for c in group)
        conf = "High" if (verified and n >= 2 and acr not in conflict_acrs and best >= 8) \
            else ("Medium" if verified else "Low")
        # Calibrated numeric confidence, capped at 0.85: mirrors the "verified
        # claim" ceiling from the calibration spec — no pipeline claims >0.85
        # against ground truth (that would require a fact-checker we don't have).
        conf_scores = {"High": 0.85, "Medium": 0.6, "Low": 0.3}
        types: list[str] = []
        weights: list[int] = []
        for c in group:
            types.append(c["grade"])
            weights.append(c["weight"])
        claims.append({"metric": acr, "claim": group[0]["seg"], "sources": n,
                       "verified": verified, "dois": sorted({c["doi"] for c in group if c["doi"]}),
                       "confidence": conf, "conf_score": conf_scores[conf],
                       "status": "VERIFIED" if verified else "CIRCULATING",
                       "max_tier": max(c["tier"] for c in group),
                       "study_types": sorted(set(types)), "ev_weight": best,
                       "components": components(acr, group, acr in conflict_acrs, this_year)})

    return {"claims": sorted(claims, key=lambda c: -c["sources"]), "conflicts": conflicts}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", required=True)
    a = ap.parse_args()
    ev_path = Path(a.evidence)
    result = verify(ev_path)

    out = ev_path / "verification.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "claim", "sources", "verified", "status", "confidence", "conf_score",
                    "ev_weight", "max_tier", "study_types", "dois",
                    "quality", "agreement", "sample", "recency", "overall"])
        for c in result["claims"]:
            comp = c["components"]
            w.writerow([c["metric"], c["claim"][:100], c["sources"],
                        "y" if c["verified"] else "n", c["status"], c["confidence"],
                        c["conf_score"], c["ev_weight"], c["max_tier"], " ".join(c["study_types"]),
                        " ".join(c["dois"]),
                        comp["quality"], comp["agreement"], comp["sample"], comp["recency"], comp["overall"]])
    print(f"wrote {out}")

    conf_path = ev_path / "contradictions.csv"
    with open(conf_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "range", "sources"])
        for x in result["conflicts"]:
            w.writerow([x["metric"], x["range"], " | ".join(x["sources"])])
    print(f"wrote {conf_path}")

    mem_path = Path(__file__).resolve().parent / "knowledge" / "memory.json"
    mem = json.loads(mem_path.read_text()) if mem_path.exists() else []
    seen = {(m["metric"], m["claim"], tuple(m["dois"])) for m in mem}
    for c in result["claims"]:
        key = (c["metric"], c["claim"][:160], tuple(c["dois"]))
        if key in seen:
            continue
        mem.append({"metric": c["metric"], "claim": c["claim"][:160], "sources": c["sources"],
                    "verified": c["verified"], "confidence": c["confidence"],
                    "conf_score": c["conf_score"], "ev_weight": c["ev_weight"],
                    "study_types": c["study_types"], "dois": c["dois"]})
        seen.add(key)
    mem_path.parent.mkdir(parents=True, exist_ok=True)
    mem_path.write_text(json.dumps(mem, indent=2))

    print(f"metrics: {len(result['claims'])}")
    print(f"verified metrics: {sum(c['verified'] for c in result['claims'])}")
    print(f"contradictions: {len(result['conflicts'])}")
    for x in result["conflicts"]:
        print(f"  ! {x['metric']} — {x['range']}")
    for c in result["claims"]:
        print(f"  {'OK' if c['verified'] else '!!'} {c['metric']:>10} [{c['confidence']}] "
              f"x{c['sources']} w{c['ev_weight']} tier{c['max_tier']}")
    print(f"memory: {len(mem)} claims")


if __name__ == "__main__":
    main()