#!/usr/bin/env python3
"""Report Generator — wraps EvidenceTable output into a consulting-grade report.

Cover → Executive Summary → Research Question → Methods → Evidence Table →
Key Findings → Limitations → Research Gaps → References.

Input:
  --evidence <dir>   output dir from evidence_table.py (contains evidence_table.csv)
  --title "..."      report title
  --question "..."   the client's research question
  --methods "..."    methods paragraph (free text)
  --findings "..."   key findings, one per line
  --client "..."     optional client name
  --deadline YYYY-MM-DD (optional)

Output:
  <output>/report.md  + <output>/report.html (self-contained, print-to-PDF).

The HTML is kept inline (no deps, no CDN) so any browser does File → Print → Save as PDF.
"""
import argparse
import csv
import html
import sys
from datetime import date
from pathlib import Path

DISCLAIMER = ("ClawBio is a research and educational tool. It is not a medical device and "
              "does not provide clinical diagnoses. Consult a healthcare professional before "
              "making any medical decisions.")

def load_evidence(evdir: Path) -> list[dict]:
    csvs = list(evdir.glob("evidence_table.csv"))
    if not csvs:
        sys.exit(f"no evidence_table.csv found in {evdir}")
    with open(csvs[0], newline="") as f:
        return list(csv.DictReader(f))

def build_md(a) -> str:
    rows = load_evidence(Path(a.evidence))
    verified = sum(1 for r in rows if r["Status"] == "VERIFIED")
    total = len(rows)
    findings = [f"- {f.strip()}" for f in a.summary.split(";") if f.strip()]
    gaps = [f"- {g.strip()}" for g in a.gaps.split(";") if g.strip()] if a.gaps else []

    md = [f"# {a.title}", "",
          f"**Client:** {a.client or '—'}   "
          f"**Report date:** {date.today().isoformat()}   "
          f"**References screened:** {total}   "
          f"**Verified against Crossref:** **{verified}/{total}**", "",
          "---", "",
          "## Executive Summary", "",
          a.summary.replace(";", "  \n"), "",
          "## Research Question", "",
          a.question, "",
          "## Methods", "",
          "\n".join(f"- {m.strip()}" for m in a.methods.split(";") if m.strip()), "", "",
          "## Evidence Table", "",
          "| Paper | Status | Reference | Sample | Method | Finding | Limitations |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['Paper']} | {r['Status']} | {r['Reference']} | {r['Sample']} "
                  f"| {r['Method']} | {r['Finding']} | {r['Limitations']} |")
    md += ["", "## Key Findings", ""] + (findings or ["- (none supplied)"]) + ["", ""]
    md += ["## Research Gaps", ""] + (gaps or ["- (none identified)"]) + ["", ""]
    md += ["## Limitations", "",
           "- Findings reflect the papers screened; absence of evidence ≠ evidence of absence.",
           "- This report verifies citation provenance, not the validity of the underlying studies.",
           "- Screened set: " + ", ".join(r["Reference"] for r in rows[:4]) \
               + ("…" if total > 4 else ""), "", "",
           "---", "", "*" + DISCLAIMER + "*", ""]
    return "\n".join(md)

def md_to_html(md: str, title: str) -> str:
    """Minimal markdown→HTML: handles #/##/###, tables, lists, bold, em. No deps."""
    out, in_table, in_list = [], False, False
    def close_all():
        nonlocal in_table, in_list
        if in_table: out.append("</table>"); in_table = False
        if in_list: out.append("</ul>"); in_list = False
    def esc(s): return html.escape(s, quote=False)
    def inline(s):
        s = esc(s)
        s = s.replace("**", "<strong>", 1) if s.count("**") >= 2 else s
        # handle bold pairs cleanly
        parts = s.split("**")
        if len(parts) >= 3:
            s = parts[0] + "<strong>" + parts[1] + "</strong>" + parts[2]
        return s
    for line in md.splitlines():
        if line.startswith("# "):
            close_all(); out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("## "):
            close_all(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not in_table:
                out.append("<table>"); in_table = True
                if "---" in "".join(cells[:4]):
                    continue
                header = cells
                out.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        elif line.startswith("- "):
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif line == "---":
            close_all(); out.append("<hr>")
        elif not line.strip():
            close_all(); out.append("<p></p>")
        else:
            close_all(); out.append(f"<p>{inline(line)}</p>")
    close_all()
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{ --ink:#1a202c; --mut:#6b7280; --accent:#0d9488; --bg:#f8fafc; }}
body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink);
       background:var(--bg); margin:0; padding:40px 24px; line-height:1.55; }}
main {{ max-width:900px; margin:0 auto; background:#fff; border:1px solid #e2e8f0;
        border-radius:12px; padding:48px 56px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
h1 {{ border-bottom:3px solid var(--accent); padding-bottom:12px; margin-top:0; color:#0f172a; }}
h2 {{ color:#0f172a; margin-top:2em; }}
table {{ border-collapse:collapse; width:100%; font-size:.9em; margin:16px 0; }}
th {{ background:#f1f5f9; text-align:left; }}
th, td {{ border:1px solid #e2e8f0; padding:8px 10px; vertical-align:top; }}
hr {{ border:none; border-top:1px solid #e2e8f0; margin:32px 0; }}
p, li {{ color:var(--ink); }}
ul {{ padding-left:24px; }}
em {{ color:var(--mut); font-size:.85em; }}
@media print {{ body {{ background:#fff; padding:0; }} main {{ box-shadow:none; border:none; max-width:100%; }} }}
</style></head><body><main>
{''.join(out)}
</main></body></html>"""

def main():
    args = parser().parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    md = build_md(args)
    (out / "report.md").write_text(md)
    (out / "report.html").write_text(md_to_html(md, args.title))
    print(f"report.md  -> {out / 'report.md'}")
    print(f"report.html (print->PDF) -> {out / 'report.html'}")
    print("open the .html in a browser, File->Print->Save as PDF")

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence", required=True, help="dir with evidence_table.csv")
    p.add_argument("--output", required=True, help="output dir")
    p.add_argument("--title", default="Literature Evidence Review")
    p.add_argument("--client", default="")
    p.add_argument("--question", default="")
    p.add_argument("--methods", default="PubMed/OpenAlex literature search; DOI verification against Crossref")
    p.add_argument("--summary", default="")
    p.add_argument("--gaps", default="")
    return p

if __name__ == "__main__":
    main()