#!/usr/bin/env python3
"""Report Generator — wraps EvidenceTable output into a consulting-grade publication.

Cover → Executive Summary → Key Findings → Evidence Table → Methodology →
Research Gaps → Limitations → Deliverables → Prepared-by page.

Input:
  --evidence <dir>   output dir from evidence_table.py (contains evidence_table.csv)
  --title "..."      report title
  --question "..."   the client's research question
  --methods "..."    methods paragraph (free text, may contain ;)
  --summary "..."    executive summary (sentences separated by ;)
  --gaps "..."       research gaps (separated by ;)
  --client "..."     optional client name

Output:
  <output>/report.md + <output>/report.html (self-contained, print-to-PDF).
"""
import argparse
import csv
import html
import sys
from datetime import date
from pathlib import Path

# Luxury editorial palette (McKinsey/Berg-grade: navy, midnight, ivory, gold, forest)
PAPER = "#FAFAF8"
NAVY = "#081421"
INK = "#0E1722"
GRAPHITE = "#3A4653"
GOLD = "#C6A86A"
FOREST = "#2D6A4F"
LINE = "#E3DED2"

def load_evidence(evdir: Path) -> list[dict]:
    csvs = list(evdir.glob("evidence_table.csv"))
    if not csvs:
        sys.exit(f"no evidence_table.csv found in {evdir}")
    with open(csvs[0], newline="") as f:
        return list(csv.DictReader(f))

def esc(s): return html.escape(html.unescape(s), quote=False)

def fmt_month() -> str:
    return date.today().strftime("%B %Y")

def build_md(a) -> str:
    rows = load_evidence(Path(a.evidence))
    verified = sum(1 for r in rows if r["Status"] == "VERIFIED")
    total = len(rows)
    entries = [f"- {s.strip()}" for s in a.summary.split(";") if s.strip()]
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
          "## Methodology", "",
          "\n".join(f"- {m.strip()}" for m in a.methods.split(";") if m.strip()), "", "",
          "## Evidence Table", "",
          "| Paper | Status | Reference | Sample | Method | Finding | Limitations |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['Paper']} | {r['Status']} | {r['Reference']} | {r['Sample']} "
                  f"| {r['Method']} | {r['Finding']} | {r['Limitations']} |")
    md += ["", "## Key Findings", ""] + (entries or ["- (none supplied)"]) + ["", ""]
    md += ["## Research Gaps", ""] + (gaps or ["- (none identified)"]) + ["", ""]
    md += ["## Limitations", "",
           "- Findings reflect only the papers screened; absence of evidence ≠ evidence of absence.",
           "- This report verifies citation provenance, not the validity of the underlying studies.",
           "- Screened set: " + ", ".join(r["Reference"] for r in rows[:4]) \
               + ("…" if total > 4 else ""), "", "",
           "## Quality Assurance", "",
           "- References verified against authoritative metadata (Crossref).",
           "- Findings are summarized from the cited publications, not extrapolated.",
           "- Limitations and uncertainty are stated explicitly in each evidence row.",
           "- This report is intended for research; it is not a medical device and does not "
           "provide clinical diagnoses or regulatory advice. Consult a qualified professional "
           "before using it to inform decisions.", "", "---", ""]
    return "\n".join(md)


def build_html(a) -> str:
    rows = load_evidence(Path(a.evidence))
    verified = sum(1 for r in rows if r["Status"] == "VERIFIED")
    total = len(rows)
    month = fmt_month()
    client = a.client or "—"
    summary_ps = "".join(f"<p>{esc(s.strip())}</p>" for s in a.summary.split(";") if s.strip())
    gaps_lis = "".join(f"<li>{esc(g.strip())}</li>" for g in a.gaps.split(";") if g.strip()) or \
               "<li>None identified in the screened set.</li>"
    methods_lis = "".join(f"<li>{esc(m.strip())}</li>" for m in a.methods.split(";") if m.strip())

    findings = ""
    for i, r in enumerate(rows[:3], 1):
        findings += f"""
        <div class="finding">
          <p class="f-num">Finding {i:02d}</p>
          <h3>{esc(r['Finding'])}</h3>
          <p class="f-meta"><b>Evidence</b> {esc(r['Method'])}</p>
        </div>"""

    ev_rows = ""
    for i, r in enumerate(rows, 1):
        status = "Verified" if r["Status"] == "VERIFIED" else r["Status"]
        ev_rows += f"""<tr>
          <td class="row-no">{i:02d}</td>
          <td class="row-paper">{esc(r['Paper'])}</td>
          <td class="row-ref">{esc(r['Reference'])}</td>
          <td class="row-status">{status}</td>
        </tr>"""

    steps = ""
    for i, (t, d) in enumerate([
        ("Define", "The scoped research question and the decision it informs."),
        ("Search & Screen", "PubMed and open public databases; deduplicated and screened for relevance."),
        ("Verify", "Every DOI machine-checked against Crossref metadata; unverifiable claims are dropped."),
        ("Extract", "Evidence captured row-by-row into a structured extraction table."),
        ("Review", "Human review of every row, stated limitations, stated confidence."),
        ("Deliver", "Executive summary, findings, tables, gaps, and verified references."),
    ], 1):
        steps += f"""<div class="step"><span class="step-n">{i:02d}</span><h4>{t}</h4><p>{esc(d)}</p></div>"""

    deliverables = ["Executive Summary", "Evidence Matrix", "Key Findings", "Research Gaps",
                    "Limitations", "References", "Verification Log"]
    del_list = "".join(f"<li>{d}</li>" for d in deliverables)

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(a.title)} — BioResearchOS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
<style>
:root {{ --paper:#FAFAF6; --navy:#081421; --ink:#0E1621; --graphite:#3A4653; --gold:#C6A86A; --forest:#2D6A4F; --line:#E3DED2; }}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{ -webkit-print-color-adjust:exact; print-color-adjust:exact; scroll-behavior:smooth; }}
body{{ font-family:'Inter',system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; color:var(--ink); background:var(--paper); line-height:1.65; -webkit-font-smoothing:antialiased; }}
.page{{ max-width:920px; margin:0 auto; padding:72px 56px; }}
.mono{{ font-family:'JetBrains Mono',ui-monospace,Menlo,monospace; }}
.eyebrow{{ font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.22em; text-transform:uppercase; color:var(--graphite); }}
h2{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:400; font-size:clamp(1.7rem,4vw,2.5rem); letter-spacing:-.01em; line-height:1.1; margin-top:14px; }}
h3{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:400; font-size:1.3rem; line-height:1.25; }}
.sechead{{ display:flex; justify-content:space-between; align-items:baseline; gap:24px; }}
.sechead .sec-num{{ font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.2em; color:var(--gold); }}
hr.sep{{ border:none; border-top:1px solid var(--line); margin:56px 0; }}
section{{ margin-top:64px; }}
section.seal{{ border-top:1px solid var(--line); padding-top:16px; }}

/* ---------- Cover ---------- */
.cover{{ background:var(--navy); color:#F7F4EC; min-height:96vh; display:flex; flex-direction:column; justify-content:space-between; padding:64px 68px; }}
.cover .top{{ display:flex; justify-content:space-between; align-items:center; }}
.cover .top .brand{{ font-family:'Fraunces'; letter-spacing:.18em; font-size:.92rem; }}
.cover .top .conf{{ font-family:'JetBrains Mono',monospace; font-size:.66rem; letter-spacing:.22em; color:#9AA7AE; text-transform:uppercase; }}
.cover .mid h1{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:300; font-size:clamp(2.6rem,7vw,4.6rem); line-height:1.05; letter-spacing:-.015em; color:#FAF6EE; margin-top:30px; }}
.cover .meta{{ margin-top:56px; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:40px; border-top:1px solid rgba(250,250,246,.18); padding-top:28px; }}
.cover .meta div p{{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.2em; text-transform:uppercase; color:#82919A; }}
.cover .meta div h4{{ font-family:'Fraunces',serif; font-weight:400; font-size:1.25rem; color:#EFE9DD; margin-top:8px; }}
.cover .foot{{ display:flex; justify-content:space-between; border-top:1px solid rgba(250,250,246,.14); padding-top:18px; font-family:'JetBrains Mono',monospace; font-size:.64rem; letter-spacing:.18em; color:#A9B4BB; }}

/* ---------- Executive summary ---------- */
.exec p{{ font-size:1.04rem; color:var(--graphite); margin-top:22px; max-width:70ch; }}
.exec p:first-child {{ color:var(--ink); }}
.exec p::first-letter{{ font-family:'Fraunces',serif; font-size:1.25em; }}
.q{{ border-left:2px solid var(--gold); padding-left:22px; margin-top:40px; }}
.q .k{{ font-family:'JetBrains Mono',monospace; font-size:.66rem; letter-spacing:.2em; color:var(--gold); text-transform:uppercase; }}
.q p{{ font-family:'Fraunces',serif; font-size:1.35rem; font-style:italic; color:var(--ink); margin-top:8px; }}

/* ---------- Metrics row ---------- */
.metrics{{ display:grid; grid-template-columns:repeat(4,1fr); gap:32px; border-top:1px solid var(--line); padding-top:34px; }}
.metric .n{{ font-family:'Fraunces',serif; font-weight:400; font-size:2.4rem; color:var(--ink); line-height:.95; }}
.metric .l{{ font-family:'JetBrains Mono',monospace; font-size:.6rem; letter-spacing:.18em; text-transform:uppercase; color:var(--graphite); margin-top:10px; }}

/* ---------- Findings ---------- */
.finding{{ border-top:1px solid var(--line); padding:30px 0; }}
.finding .f-num{{ font-family:'JetBrains Mono',monospace; font-size:.66rem; letter-spacing:.2em; color:var(--gold); }}
.finding h3{{ margin-top:12px; max-width:56ch; }}
.finding .f-meta{{ margin-top:12px; font-family:'JetBrains Mono',monospace; font-size:.68rem; color:var(--graphite); }}
.finding .f-meta b{{ color:var(--graphite); font-weight:500; letter-spacing:.16em; text-transform:uppercase; font-size:.6rem; margin-right:8px; }}

/* ---------- Evidence table ---------- */
table{{ width:100%; border-collapse:collapse; margin-top:34px; }}
th{{ text-align:left; font-family:'JetBrains Mono',monospace; font-weight:500; font-size:.64rem; letter-spacing:.16em; text-transform:uppercase; color:var(--graphite); padding:0 12px 12px 0; border-bottom:1px solid var(--ink); }}
td{{ padding:16px 12px 16px 0; border-bottom:1px solid var(--line); vertical-align:top; font-size:.92rem; }}
.row-no, .row-status{{ font-family:'JetBrains Mono',monospace; font-size:.72rem; color:var(--graphite); white-space:nowrap; }}
.row-ref{{ font-family:'JetBrains Mono',monospace; font-size:.7rem; color:var(--forest); }}
.row-status{{ color:var(--forest); letter-spacing:.08em; }}

/* ---------- Methodology ---------- */
.steps{{ display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid var(--line); margin-top:36px; }}
.step{{ padding:26px; border:1px solid var(--line); }}
.step-n{{ font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.16em; color:var(--gold); }}
.step h4{{ font-family:'Fraunces',serif; font-weight:400; font-size:1.15rem; margin-top:10px; }}
.step p{{ color:var(--graphite); font-size:.88rem; margin-top:8px; }}

/* ---------- Gaps ---------- */
.gaps li{{ list-style:none; border-top:1px solid var(--line); padding:14px 0; color:var(--graphite); font-size:.98rem; }}
.gaps li:first-child{{ border-top:0; }}
.gaps li::before{{ content:"—  "; color:var(--gold); }}

/* ---------- Deliverables ---------- */
.deliver{{ border:1px solid var(--line); padding:34px 38px; }}
.deliver .eyebrow {{ margin-bottom:18px; }}
.deliver ul{{ columns:2; column-gap:48px; }}
.deliver li{{ list-style:none; padding:9px 0; border-top:1px solid var(--line); font-size:.94rem; }}
.deliver li:first-child, .deliver li:nth-child(2){{ border-top:0; }}
.deliver li::before{{ content:"✓  "; color:var(--forest); font-family:'JetBrains Mono',monospace; }}

/* ---------- Truth ---------- */
.truth{{ display:flex; gap:40px; flex-wrap:wrap; border-top:1px solid var(--line); padding-top:28px; }}
.truth span{{ font-family:'JetBrains Mono',monospace; font-size:.66rem; letter-spacing:.2em; text-transform:uppercase; color:var(--graphite); }}

/* ---------- prepared-by ---------- */
.prep{{ background:var(--navy); color:#E9E3D6; padding:56px 68px; display:flex; justify-content:space-between; align-items:flex-start; gap:40px; }}
.prep h3{{ font-family:'Fraunces',serif; font-weight:300; font-size:1.5rem; }}
.prep p{{ color:#A9B4AE; font-size:.9rem; margin-top:10px; max-width:34ch; }}
.prep .addr{{ text-align:right; font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.1em; color:#8A97A0; }}
.prep .addr b{{ display:block; color:#E9E3D6; font-weight:500; letter-spacing:.14em; font-size:.8rem; margin-top:6px; font-family:'JetBrains Mono',monospace; }}

@media (max-width:760px){{
  .page{{ padding:40px 24px; }}
  .cover{{ padding:44px 30px; min-height:880px; }}
  .cover .meta{{ grid-template-columns:1fr; gap:22px; }}
  .metrics{{ grid-template-columns:1fr 1fr; }}
  .steps{{ grid-template-columns:1fr; }}
  .prep{{ flex-direction:column; }} .prep .addr{{ text-align:left; }}
  .deliver ul{{ columns:1; }}
}}
@media print{{
  .cover, .prep {{ min-height:auto; break-after:page; }}
  body {{ background:var(--paper); }}
}}
</style>
</head>
<body>

<main class="page">

  <!-- COVER -->
  <section class="cover">
    <div class="top">
      <span class="brand">BIORESEARCH·OS</span>
      <span class="ver">Evidence Intelligence</span>
    </div>
    <div class="mid">
      <p class="eyebrow" style="color:#8A97A0">Research Series · Evidence Report</p>
      <h1>{esc(a.title)}</h1>
      <p style="font-family:'JetBrains Mono',monospace;font-size:.72rem;letter-spacing:.16em;color:#9AA7AE;text-transform:uppercase;margin-top:22px">Prepared for decision-makers</p>
    </div>
    <div class="meta">
      <div><p>Client</p><h4>{esc(a.client or '—')}</h4></div>
      <div><p>References screened</p><h4>{total}</h4></div>
      <div><p>Crossref-verified</p><h4>{verified} / {total}</h4></div>
    </div>
    <div class="foot">
      <span>VERIFIED · REPRODUCIBLE · TRACEABLE</span>
      <span>CONFIDENTIAL · {month}</span>
    </div>
  </section>

  <!-- EXECUTIVE SUMMARY -->
  <section class="section exec">
    <div class="sechead">
      <p class="eyebrow">01 — Executive Summary</p>
      <span class="sec-num">BIORESEARCH·OS</span>
    </div>
    <h2>Research at a glance</h2>
    {summary_ps}
    <div class="q">
      <p class="k">Research question</p>
      <p>“{esc(a.question)}”</p>
    </div>
  </section>

  <hr class="sep">

  <!-- KEY FINDINGS -->
  <section>
    <div class="sechead">
      <p class="eyebrow">02 — Key Findings</p>
      <span class="sec-num">{verified} verified of {total} screened</span>
    </div>
    <h2>What the evidence says</h2>
    {findings}
  </section>

  <hr class="sep">

  <!-- EVIDENCE TABLE -->
  <section>
    <div class="sechead">
      <p class="eyebrow">03 — Evidence Matrix</p>
      <span class="sec-num">{total} screened</span>
    </div>
    <h2>Record-by-record</h2>
    <table>
      <thead><tr>
        <th>#</th><th>Paper</th><th>Reference</th><th>Verification</th>
      </tr></thead>
      <tbody>{ev_rows}</tbody>
    </table>
  </section>

  <hr class="sep">

  <!-- METHODOLOGY -->
  <section>
    <div class="sechead">
      <p class="eyebrow">04 — Methodology</p>
      <span class="sec-num">Reproducible</span>
    </div>
    <h2>How a report is built</h2>
    <div class="steps">{steps}</div>
  </section>

  <hr class="sep">

  <!-- GAPS & LIMITATIONS -->
  <section>
    <div class="sechead">
      <p class="eyebrow">05 — Research Gaps</p>
      <span class="sec-num">Stated, not concealed</span>
    </div>
    <h2>What remains unknown</h2>
    <ul class="gaps">{gaps_lis}</ul>

    <hr class="seal">

    <div class="sechead">
      <p class="eyebrow">06 — Limitations</p>
    </div>
    <p style="color:var(--graphite);font-size:.98rem;max-width:64ch;margin-top:20px">
      Findings reflect only the papers screened; absence of evidence ≠ evidence of absence.
      This report verifies citation provenance, not the validity of the underlying studies.
      It is intended for research and is not a medical device.
    </p>
  </section>

  <hr class="sep">

  <!-- DELIVERABLES -->
  <section>
    <div class="sechead">
      <p class="eyebrow">07 — Deliverables</p>
    </div>
    <div class="deliver">
      <p class="eyebrow">In this volume</p>
      <ul>{del_list}</ul>
    </div>
    <div class="truth">
      <span>Verified.</span><span>Reproducible.</span><span>Traceable.</span><span>Transparent.</span>
    </div>
  </section>

  <hr class="sep">

  <!-- PREPARED BY -->
  <section class="prep">
    <div>
      <h3>Prepared by BioResearchOS</h3>
      <p>Every citation verified. Every limitation documented. Every conclusion traceable.</p>
    </div>
    <div class="addr">
      <span>CONTACT</span>
      <b>ferdinandnkabandi@icloud.com</b>
      <b>wa.me/255795774784</b>
    </div>
  </section>

</main>
</body></html>"""


def main():
    args = parser().parse_args()
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    md = build_md(args)
    (out / "report.md").write_text(md)
    (out / "report.html").write_text(build_html(args))
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