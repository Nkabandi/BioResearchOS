#!/usr/bin/env python3
"""EvidenceTable — deliverable generator for BioResearchOS (client services).

The money-making artifact: a verified evidence table. Combines:
  1) CITATION CHECKER — every DOI is looked up on Crossref; anything you cite
     that returns no DOI, mismatched title, or wrong year is flagged. No
     hallucinated citations survive this pass.
  2) EVIDENCE TABLE — papers + agent/user-supplied Finding and Limitations
     rendered as a markdown table, each row "VERIFIED" or rejected.

Input: CSV with at least a `doi` column. Optional: finding, sample, method,
limitations, group. 
Output: evidence.md + citations.md + rejections.md + result.json.

Requires: pandas, requests-able stdlib (urllib).
"""
import argparse
import csv
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

CROSSREF = "https://api.crossref.org/works/{}"
VALID_STATUS = {"VERIFIED", "MISMATCH_TITLE", "MISMATCH_YEAR", "NOT_FOUND"}


def crossref(doi: str) -> dict | None:
    url = urllib.parse.quote(doi, safe="")
    for _ in range(3):
        try:
            with urllib.request.urlopen(f"{CROSSREF}{doi}", timeout=20) as r:
                return json.load(r)["message"]
        except Exception:
            time.sleep(2)
    return None


def norm(s) -> str:
    return (s or "").strip().lower().replace("ö", "o").replace("é", "e")


def check_record(row: dict) -> dict:
    doi = row.get("doi", "").strip()
    if not doi:
        return {"doi": "", "status": "MISSING_DOI", "title": row.get("title", ""),
                "journal": "", "year": "", "reason": "no DOI supplied — cannot verify."}
    msg = crossref(doi)
    if msg is None:
        return {"doi": doi, "status": "NOT_FOUND", "title": row.get("title", ""),
                "journal": "", "year": "", "reason": "Crossref lookup failed / DOI unregistered."}
    cr_title = (msg.get("title") or [""])[0]
    cr_journal = (msg.get("container-title") or [""])[0] or (msg.get("publisher") or "")
    cr_year = (msg["issued"]["date-parts"] or [[None]])[0][0]
    status, reason = "VERIFIED", ""
    if "title" in row and norm(row["title"]) and norm(row["title"])[:40] != norm(cr_title)[:40]:
        status, reason = "MISMATCH_TITLE", f"Crossref: '{cr_title[:60]}'"
    elif "year" in row and row["year"] and str(row["year"]) != str(cr_year):
        status, reason = "MISMATCH_YEAR", f"Crossref: {cr_year}"
    return {"doi": doi, "status": status, "title": cr_title, "journal": cr_journal,
            "year": cr_year, "reason": reason}


def build_row(checked: dict, row: dict) -> dict:
    return {
        "Paper": row.get("title", "") or checked.get("title", ""),
        "Status": checked.get("status", "?"),
        "Reference": f"{checked.get('journal', '')} ({checked.get('year', '')}) {checked['doi']}".rstrip(),
        "Sample": row.get("sample", ""),
        "Method": row.get("method", ""),
        "Finding": row.get("finding", ""),
        "Limitations": row.get("limitations", ""),
    }


def to_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    if len(sys.argv) < 3 or "--input" not in sys.argv and "--ref" not in sys.argv:
        sys.exit("usage: evidence_table.py --input papers.csv --output out/\n"
                 "CSV cols: doi,title,year,found,sample,method,nimitations,group (only doi required)")
    inp = Path(sys.argv[sys.argv.index("--input") + 1])
    out = Path(sys.argv[sys.argv.index("--output") + 1])
    out.mkdir(parents=True, exist_ok=True)

    with open(inp, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("input CSV is empty")

    checked, table = [], []
    for r in rows:
        c = check_record(r)
        checked.append(c)
        table.append(build_row(c, r))

    to_csv(checked, out / "citation_check.csv")
    to_csv(table, out / "evidence_table.csv")
    (out / "result.json").write_text(json.dumps({
        "total": len(rows),
        "verified": sum(1 for c in checked if c["status"] == "VERIFIED"),
        "rejects": [{"doi": c["doi"], "status": c["status"], "reason": c.get("reason", "")}
                    for c in checked if c["status"] != "VERIFIED"],
    }, indent=2))

    md_rej = "\n".join(f"- `{c['doi']}` — **{c['status']}** {c.get('reason','')}"
                       for c in checked if c["status"] != "VERIFIED") or "_all citations verified_"
    (out / "rejections.md").write_text(f"# Citation Check — Rejected\n\n{md_rej}\n")

    md = ["# Evidence Table", ""]
    v = sum(1 for c in checked if c["status"] == "VERIFIED")
    md.append(f"**{v}/{len(rows)} references verified against Crossref.**")
    md.append("")
    md.append("| Paper | Status | Reference | Sample | Method | Finding | Limitations |")
    md.append("|---|---|---|---|---|---|---|")
    for t in table:
        status = "VERIFIED" if t["Status"] == "VERIFIED" else t["Status"]
        md.append(f"| {t['Paper']} | {status} | {t['Reference']} | {t['Sample']} "
                  f"| {t['Method']} | {t['Finding']} | {t['Limitations']} |")
    md.append("")
    md.append("---")
    md.append("*Generated by EvidenceTable (BioResearchOS) — verify against primary sources before citing.*")
    (out / "evidence_table.md").write_text("\n".join(md))

    print(f"citations verified: {v}/{len(rows)}")
    print(f"evidence table -> {out / 'evidence_table.md'}")
    print(f"citation check -> {out / 'citation_check.csv'}")
    if v < len(rows):
        print("REJECTED rows:"); [print(f"  {c['doi']} - {c['status']} {c.get('reason','')}")
                                  for c in checked if c["status"] != "VERIFIED"]


if __name__ == "__main__":
    main()