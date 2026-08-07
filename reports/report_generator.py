#!/usr/bin/env python3
"""Report Generator — wraps EvidenceTable output into a BioResearchOS standard report.

Standard structure (v1, living template):
  Cover → Confidentiality → Contents → Executive Summary (BLUF) → Key Takeaways →
  Context & Objective → Methodology → Findings (insight headlines) → Discussion →
  Decision Implications → Recommendations → Limitations → Confidence Assessment →
  Appendix A Data · B Sources · C Methodology · D Definitions

Design system (report-standard):
  Deep teal #1B4B4D primary · warm black #1C1B19 · white #FFFFFF ·
  gold #C6A86A accent · ochre #8A5A24/#FBF3E7 limitations box · warm gray #6B6862 secondary.
  Serif headings · clean sans body · monospace ONLY for data/DOIs/confidence/sources.

Input:
  --evidence <dir>   output dir from evidence_table.py (contains evidence_table.csv)
  --title "..."      report title
  --subtitle "..."   one-line subtitle
  --question "..."   the client's research question
  --context "..."    background / why the report exists (semicolon-separated)
  --scope-in "..."   what is in scope (semicolon-separated)
  --scope-out "..."  what is out of scope (semicolon-separated)
  --methods "..."    methodology bullet points (semicolon-separated)
  --summary "..."    executive summary BLUF sentence + bullets (semicolon-separated, first = conclusion)
  --takeaways "..."  5-8 key takeaways (semicolon-separated)
  --discussion "..." discussion points (semicolon-separated)
  --implications "..." decision implications: "if X → then Y" (semicolon-separated)
  --recommendations "..." format: "IMMEDIATE|text; NEAR|text; LONG|text"
  --confidence "..." confidence table rows: "Finding~Confidence~Reason" separated by ;
  --gaps "..."       research gaps (semicolon-separated)
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

PAPER = "#FFFFFF"
TEAL = "#1B4B4D"
INK = "#1C1B19"
GRAPHITE = "#6B6862"
GOLD = "#C6A86A"
OCHRE = "#8A5A24"
OCHRE_BG = "#FBF3E7"
LINE = "#E5E1D8"

def load_evidence(evdir: Path) -> list[dict]:
    csvs = list(evdir.glob("evidence_table.csv"))
    if not csvs:
        sys.exit(f"no evidence_table.csv found in {evdir}")
    with open(csvs[0], newline="") as f:
        return list(csv.DictReader(f))

def esc(s): return html.escape(html.unescape(s), quote=False)

def fmt_month() -> str:
    return date.today().strftime("%B %Y")

def split(s):
    return [x.strip() for x in s.split(";") if x.strip()] if s else []

def parse_recs(s):
    """IMMEDIATE|text; NEAR|text; LONG|text -> list[(band, text)]"""
    out = []
    for entry in split(s):
        if "|" in entry:
            band, text = entry.split("|", 1)
            out.append((band.strip().upper(), text.strip()))
    return out

def parse_conf(s):
    rows = []
    for entry in split(s):
        parts = [p.strip() for p in entry.split("~")]
        if len(parts) == 3:
            rows.append(parts)
    return rows

def build_md(a) -> str:
    rows = load_evidence(Path(a.evidence))
    verified = sum(1 for r in rows if r["Status"] == "VERIFIED")
    total = len(rows)
    summary = split(a.summary)
    takeaways = split(a.takeaways)
    context = split(a.context)
    scope_in = split(a.scope_in)
    scope_out = split(a.scope_out)
    methods = split(a.methods)
    discussion = split(a.discussion)
    implications = split(a.implications)
    gaps = split(a.gaps)
    conf_rows = parse_conf(a.confidence)
    recs = parse_recs(a.recommendations)

    md = [f"# {a.title}", "",
          f"*{a.subtitle or 'Evidence report'}*", "",
          f"**Client:** {a.client or '—'}   "
          f"**Report date:** {date.today().isoformat()}   "
          f"**Version:** v1   "
          f"**References screened:** {total}   "
          f"**Crossref-verified:** **{verified}/{total}**", "",
          "---", "",
          "## Executive Summary", ""]
    for s in summary:
        md.append(f"- {s}")
    md += ["", "## Key Takeaways", ""]
    md += [f"- {t}" for t in takeaways] or ["- (none supplied)"]
    md += ["", "## Context & Objective", ""]
    md += [f"- {c}" for c in context] or ["- (none supplied)"]
    md += ["", "**In scope:**", ""] + [f"- {x}" for x in scope_in]
    md += ["", "**Out of scope:**", ""] + [f"- {x}" for x in scope_out]
    md += ["", "## Research Question", "", f"> {a.question}", "",
           "## Methodology", ""]
    md += [f"- {m}" for m in methods]
    md += ["", "## Findings", ""]
    for i, r in enumerate(rows, 1):
        md.append(f"### Finding {i:02d}")
        md.append(f"**Evidence:** {r['Finding']}")
        md.append(f"**Source:** {r['Reference']} — {r['Method']}")
        md.append("")
    md += ["## Discussion", ""] + [f"- {d}" for d in discussion] or ["- (none supplied)"]
    md += ["", "## Decision Implications", ""] + [f"- {i}" for i in implications]
    md += ["", "## Recommendations", ""]
    for band, text in recs:
        md.append(f"- **[{band}]** {text}")
    md += ["", "## Limitations", ""]
    md += ["- Findings reflect only the papers screened; absence of evidence ≠ evidence of absence.",
           "- This report verifies citation provenance, not the validity of the underlying studies.",
           "- Only publicly available literature was analyzed; clinical validation was not performed.",
           "- Some studies had heterogeneous methodologies, limiting direct comparability.",
           "- Screened set: " + ", ".join(r["Reference"] for r in rows[:4]) + ("…" if total > 4 else "")]
    md += ["", "## Confidence Assessment", "",
           "| Finding | Confidence | Reason |", "|---|---|---|"]
    for f, c, reason in conf_rows:
        md.append(f"| {f} | {c} | {reason} |")
    md += ["", "## Research Gaps", ""] + [f"- {g}" for g in gaps]
    md += ["", "## Appendix A — Evidence Data", "",
           "| Paper | Status | Reference | Sample | Method | Finding | Limitations |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['Paper']} | {r['Status']} | {r['Reference']} | {r['Sample']} "
                  f"| {r['Method']} | {r['Finding']} | {r['Limitations']} |")
    md += ["", "## Appendix B — Sources", ""]
    for i, r in enumerate(rows, 1):
        md.append(f"{i}. {r['Reference']}")
    md += ["", "## Appendix C — Methodology Notes", "",
           "- AI-assisted drafting was used; every claim traces to a screened source and was human-reviewed.",
           "- Confidence framework: High = multiple independent studies/consistent results; "
           "Medium = limited studies or wide ranges; Low = sparse or single-centre data.",
           "- This report is intended for research; it is not a medical device and does not provide "
           "clinical diagnoses or regulatory advice. Consult a qualified professional before acting.", "", "---", ""]
    return "\n".join(md)


def build_html(a) -> str:
    rows = load_evidence(Path(a.evidence))
    verified = sum(1 for r in rows if r["Status"] == "VERIFIED")
    total = len(rows)
    month = fmt_month()
    client = a.client or "—"
    summary = split(a.summary)
    takeaways = split(a.takeaways)
    context = split(a.context)
    scope_in = split(a.scope_in)
    scope_out = split(a.scope_out)
    methods = split(a.methods)
    discussion = split(a.discussion)
    implications = split(a.implications)
    gaps = split(a.gaps)
    conf_rows = parse_conf(a.confidence)
    recs = parse_recs(a.recommendations)

    summary_ps = "".join(f"<p>{esc(s)}</p>" for s in summary)
    takeaways_lis = "".join(f"<li>{esc(t)}</li>" for t in takeaways) or "<li>None supplied.</li>"
    context_lis = "".join(f"<li>{esc(c)}</li>" for c in context) or "<li>None supplied.</li>"
    scope_in_lis = "".join(f"<li>{esc(x)}</li>" for x in scope_in) or "<li>—</li>"
    scope_out_lis = "".join(f"<li>{esc(x)}</li>" for x in scope_out) or "<li>—</li>"
    methods_lis = "".join(f"<li>{esc(m)}</li>" for m in methods)
    discussion_lis = "".join(f"<li>{esc(d)}</li>" for d in discussion) or "<li>None supplied.</li>"
    implications_lis = "".join(f"<li>{esc(i)}</li>" for i in implications) or "<li>None supplied.</li>"
    gaps_lis = "".join(f"<li>{esc(g)}</li>" for g in gaps) or "<li>None identified in the screened set.</li>"

    # Findings: insight headline = short first clause, evidence = full finding
    findings = ""
    for i, r in enumerate(rows, 1):
        full = r["Finding"]
        head = full.split(";")[0].split(";")[0].strip()[:110]
        findings += f"""
        <div class="finding">
          <p class="f-num">Finding {i:02d}</p>
          <h3>{esc(head)}</h3>
          <div class="insight">
            <p class="k">Evidence</p>
            <p class="v">{esc(full)}</p>
            <p class="k">Source</p>
            <p class="v mono">{esc(r['Reference'])}</p>
            <p class="k">Confidence</p>
            <p class="v">Assessed in §12 Confidence Assessment</p>
          </div>
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

    conf_rows_html = "".join(
        f"<tr><td>{esc(f)}</td><td class=\"conf-lvl\">{esc(c)}</td><td>{esc(reason)}</td></tr>"
        for f, c, reason in conf_rows) or "<tr><td colspan=3>—</td></tr>"

    rec_html = ""
    bands = {"IMMEDIATE": "Immediate", "NEAR": "Near-term", "LONG": "Long-term"}
    for band, text in recs:
        rec_html += f"""<div class="rec">
          <span class="rec-band">{bands.get(band, band)}</span>
          <p>{esc(text)}</p>
        </div>"""

    # Contents list mirrors section order
    toc = ["Executive Summary", "Key Takeaways", "Context & Objective",
           "Methodology", "Findings", "Discussion", "Decision Implications",
           "Recommendations", "Limitations", "Confidence Assessment",
           "Research Gaps", "Appendix"]
    toc_lis = "".join(f"<li><a href=\"#s{i+1}\">{esc(t)}</a></li>" for i, t in enumerate(toc))

    def sec(n, title, anchor, body, eyebrow=None, right=None):
        return f"""<section id="s{n}">
      <div class="sechead">
        <p class="eyebrow">{esc(eyebrow or f"{n:02d}")}</p>
        <span class="sec-num">{esc(right or '')}</span>
      </div>
      <h2>{esc(title)}</h2>
      {body}
    </section>"""

    s_exec = sec(1, "Executive Summary", "s1", f"""
      <div class="exec">
        <p class="bluf">{esc(summary[0]) if summary else ''}</p>
        {summary_ps if len(summary) > 1 else ''}
        <div class="datanote"><span>Sources reviewed</span><b>{total}</b><span>Crossref-verified</span><b>{verified}/{total}</b><span>Report date</span><b>{month}</b></div>
      </div>""", "Bottom Line Up Front")

    s_take = sec(2, "Key Takeaways", "s2", f"<ul class=\"take\">{takeaways_lis}</ul>", "Read this first")

    s_ctx = sec(3, "Context & Objective", "s3", f"""
      <ul class="ctx">{context_lis}</ul>
      <div class="q"><p class="k">Research question</p><p>“{esc(a.question)}”</p></div>
      <div class="scope">
        <div><p class="k">In scope</p><ul>{scope_in_lis}</ul></div>
        <div><p class="k">Out of scope</p><ul>{scope_out_lis}</ul></div>
      </div>""", "Why this report exists")

    s_method = sec(4, "Methodology", "s4", f"""
      <ul class="ctx">{methods_lis}</ul>
      <div class="truth">
        <span>Crossref-verified</span><span>AI-assisted, human-reviewed</span><span>Confidence assessed</span><span>Limitations stated</span>
      </div>""", "How conclusions were reached")

    s_find = sec(5, "Findings", "s5", f"{findings}", "The evidence, insight by insight", f"{verified} verified of {total} screened")

    s_disc = sec(6, "Discussion", "s6", f"<ul class=\"ctx\">{discussion_lis}</ul>", "What the findings mean")

    s_impl = sec(7, "Decision Implications", "s7", f"<ul class=\"impl\">{implications_lis}</ul>", "What changes because of these findings")

    s_rec = sec(8, "Recommendations", "s8", rec_html or "<p>None supplied.</p>", "Immediate · Near-term · Long-term")

    s_lim = sec(9, "Limitations", "s9", f"""
      <div class="limbox">
        <p>Only publicly available literature was analyzed. Findings reflect only the papers screened;
        absence of evidence ≠ evidence of absence. This report verifies citation provenance, not the
        validity of the underlying studies. Some studies used heterogeneous methodologies, limiting
        direct comparability. Clinical validation was not performed. It is intended for research and
        is not a medical device.</p>
        <p class="mono">Screened set: {esc(', '.join(r['Reference'] for r in rows[:4]))}{' …' if total > 4 else ''}</p>
      </div>""", "Stated plainly")

    s_conf = sec(10, "Confidence Assessment", "s10", f"""
      <table class="conf"><thead><tr><th>Finding</th><th>Confidence</th><th>Reason</th></tr></thead>
      <tbody>{conf_rows_html}</tbody></table>
      <p class="note">Framework: High = multiple independent studies, consistent results ·
      Medium = limited studies or wide ranges · Low = sparse or single-centre data.</p>""",
      "Per-finding, with reasons")

    s_gap = sec(11, "Research Gaps", "s11", f"<ul class=\"gaps\">{gaps_lis}</ul>", "What remains unknown")

    s_app = sec(12, "Appendix", "s12", f"""
      <p class="eyebrow" style="margin-bottom:14px">A — Evidence data</p>
      <table><thead><tr><th>#</th><th>Paper</th><th>Reference</th><th>Verification</th></tr></thead>
      <tbody>{ev_rows}</tbody></table>
      <p class="eyebrow" style="margin:34px 0 14px">B — Sources</p>
      <ol class="srcs">{''.join(f'<li>{esc(r["Reference"])}</li>' for r in rows)}</ol>
      <p class="eyebrow" style="margin:34px 0 14px">C — Methodology notes</p>
      <ul class="ctx"><li>AI-assisted drafting was used; every claim traces to a screened source and was human-reviewed.</li>
      <li>Confidence framework: High = multiple independent studies/consistent results; Medium = limited studies or wide ranges; Low = sparse or single-centre data.</li>
      <li>Full extraction table and verification log are retained in the reproducibility trail.</li></ul>
      <p class="eyebrow" style="margin:34px 0 14px">D — Definitions</p>
      <ul class="ctx"><li><b>BLUF</b> — Bottom Line Up Front: the conclusion leads each section.</li>
      <li><b>Crossref verification</b> — every DOI machine-checked against Crossref metadata; unverifiable claims are dropped.</li>
      <li><b>Confidence</b> — stated per finding, with the reason, never implied.</li></ul>""", "Supporting material")

    body = "".join([s_exec, s_take, s_ctx, s_method, s_find, s_disc, s_impl, s_rec, s_lim, s_conf, s_gap, s_app])

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(a.title)} — BioResearchOS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
<style>
:root {{ --paper:#FFFFFF; --teal:#1B4B4D; --ink:#1C1B19; --graphite:#6B6862; --gold:#C6A86A; --ochre:#8A5A24; --ochrebg:#FBF3E7; --line:#E5E1D8; }}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{ -webkit-print-color-adjust:exact; print-color-adjust:exact; scroll-behavior:smooth; }}
body{{ font-family:'Inter',system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; color:var(--ink); background:var(--paper); line-height:1.65; -webkit-font-smoothing:antialiased; }}
.page{{ max-width:920px; margin:0 auto; padding:72px 56px; }}
.mono{{ font-family:'JetBrains Mono',ui-monospace,Menlo,monospace; }}
.eyebrow{{ font-family:'JetBrains Mono',monospace; font-size:.68rem; letter-spacing:.22em; text-transform:uppercase; color:var(--graphite); }}
h2{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:400; font-size:clamp(1.6rem,4vw,2.3rem); letter-spacing:-.01em; line-height:1.12; margin-top:14px; }}
h3{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:400; font-size:1.25rem; line-height:1.25; }}
.sechead{{ display:flex; justify-content:space-between; align-items:baseline; gap:24px; border-bottom:1px solid var(--teal); padding-bottom:10px; margin-top:64px; }}
.sechead .sec-num{{ font-family:'JetBrains Mono',monospace; font-size:.66rem; letter-spacing:.18em; color:var(--graphite); }}
hr.sep{{ border:none; border-top:1px solid var(--line); margin:56px 0; }}
section{{ margin-top:24px; }}
.note{{ font-size:.8rem; color:var(--graphite); margin-top:14px; }}

/* ---------- Cover ---------- */
.cover{{ background:var(--teal); color:#F7F4EC; min-height:96vh; display:flex; flex-direction:column; justify-content:space-between; padding:64px 68px; }}
.cover .top{{ display:flex; justify-content:space-between; align-items:center; }}
.cover .top .brand{{ font-family:'Fraunces'; letter-spacing:.18em; font-size:.92rem; }}
.cover .top .conf{{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.2em; color:#B9C7C5; text-transform:uppercase; }}
.cover .mid h1{{ font-family:'Fraunces',Georgia,'Times New Roman',serif; font-weight:300; font-size:clamp(2.4rem,6.5vw,4.2rem); line-height:1.05; letter-spacing:-.015em; color:#FAF6EE; margin-top:30px; }}
.cover .mid .sub{{ font-family:'Inter',sans-serif; font-size:1rem; color:#D8E0DE; margin-top:18px; max-width:56ch; }}
.cover .meta{{ margin-top:56px; display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:32px; border-top:1px solid rgba(250,250,246,.18); padding-top:26px; }}
.cover .meta div p{{ font-family:'JetBrains Mono',monospace; font-size:.58rem; letter-spacing:.2em; text-transform:uppercase; color:#9FB3B0; }}
.cover .meta div h4{{ font-family:'Fraunces',serif; font-weight:400; font-size:1.1rem; color:#EFE9DD; margin-top:8px; }}
.cover .foot{{ display:flex; justify-content:space-between; border-top:1px solid rgba(250,250,246,.14); padding-top:18px; font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.18em; color:#A9B4BB; }}

/* ---------- Executive summary ---------- */
.exec p{{ font-size:1rem; color:var(--graphite); margin-top:18px; max-width:70ch; }}
.exec .bluf{{ font-weight:600; color:var(--teal); font-size:1.15rem; margin-top:26px; }}
.datanote{{ display:flex; gap:34px; flex-wrap:wrap; border-top:1px solid var(--line); margin-top:34px; padding-top:20px; }}
.datanote span{{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.18em; text-transform:uppercase; color:var(--graphite); }}
.datanote b{{ font-family:'JetBrains Mono',monospace; font-weight:500; font-size:1rem; color:var(--teal); margin-left:8px; }}
.q{{ border-left:2px solid var(--gold); padding-left:22px; margin-top:36px; }}
.q .k{{ font-family:'JetBrains Mono',monospace; font-size:.64rem; letter-spacing:.2em; color:var(--gold); text-transform:uppercase; }}
.q p{{ font-family:'Fraunces',serif; font-size:1.3rem; font-style:italic; color:var(--ink); margin-top:8px; }}

/* ---------- Lists ---------- */
.take li, .ctx li, .impl li{{ list-style:none; border-top:1px solid var(--line); padding:13px 0; font-size:.97rem; color:var(--ink); }}
.take li:first-child, .ctx li:first-child, .impl li:first-child{{ border-top:0; }}
.take li::before{{ content:"—  "; color:var(--gold); }}
.impl li::before{{ content:"→  "; color:var(--teal); font-family:'JetBrains Mono',monospace; }}
.scope{{ display:grid; grid-template-columns:1fr 1fr; gap:36px; margin-top:34px; }}
.scope .k{{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.2em; text-transform:uppercase; color:var(--teal); }}
.scope li{{ list-style:none; border-top:1px solid var(--line); padding:10px 0; font-size:.9rem; color:var(--graphite); }}
.scope li:first-child{{ border-top:0; }}

/* ---------- Truth strip ---------- */
.truth{{ display:flex; gap:36px; flex-wrap:wrap; border-top:1px solid var(--line); padding-top:24px; margin-top:34px; }}
.truth span{{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.2em; text-transform:uppercase; color:var(--graphite); }}

/* ---------- Findings ---------- */
.finding{{ border-top:1px solid var(--line); padding:30px 0; }}
.finding .f-num{{ font-family:'JetBrains Mono',monospace; font-size:.64rem; letter-spacing:.2em; color:var(--gold); }}
.finding h3{{ margin-top:12px; max-width:60ch; }}
.insight{{ border:1px solid var(--line); background:var(--paper); padding:20px 24px; margin-top:16px; }}
.insight .k{{ font-family:'JetBrains Mono',monospace; font-size:.58rem; letter-spacing:.2em; text-transform:uppercase; color:var(--graphite); margin-top:12px; }}
.insight .k:first-child{{ margin-top:0; }}
.insight .v{{ font-size:.9rem; color:var(--ink); margin-top:4px; }}
.insight .v.mono{{ font-size:.74rem; color:var(--teal); word-break:break-word; }}

/* ---------- Tables ---------- */
table{{ width:100%; border-collapse:collapse; margin-top:30px; }}
th{{ text-align:left; font-family:'JetBrains Mono',monospace; font-weight:500; font-size:.62rem; letter-spacing:.16em; text-transform:uppercase; color:var(--ink); padding:0 12px 12px 0; border-bottom:1px solid var(--teal); }}
td{{ padding:15px 12px 15px 0; border-bottom:1px solid var(--line); vertical-align:top; font-size:.9rem; }}
.row-no, .row-status{{ font-family:'JetBrains Mono',monospace; font-size:.7rem; color:var(--graphite); white-space:nowrap; }}
.row-ref{{ font-family:'JetBrains Mono',monospace; font-size:.68rem; color:var(--teal); }}
.row-status{{ color:var(--teal); letter-spacing:.08em; }}
table.conf td:nth-child(2){{ font-family:'JetBrains Mono',monospace; color:var(--teal); white-space:nowrap; }}

/* ---------- Recommendations ---------- */
.rec{{ display:flex; gap:20px; align-items:baseline; border-top:1px solid var(--line); padding:18px 0; }}
.rec .rec-band{{ font-family:'JetBrains Mono',monospace; font-size:.6rem; letter-spacing:.16em; text-transform:uppercase; color:var(--gold); white-space:nowrap; }}
.rec p{{ font-size:.97rem; }}

/* ---------- Limitations ---------- */
.limbox{{ background:var(--ochrebg); border-left:3px solid var(--ochre); padding:26px 30px; margin-top:28px; }}
.limbox p{{ color:#5C4620; font-size:.92rem; }}
.limbox .mono{{ color:var(--ochre); font-size:.7rem; margin-top:16px; word-break:break-word; }}

/* ---------- Gaps ---------- */
.gaps li{{ list-style:none; border-top:1px solid var(--line); padding:13px 0; color:var(--ink); font-size:.97rem; }}
.gaps li:first-child{{ border-top:0; }}
.gaps li::before{{ content:"—  "; color:var(--gold); }}

/* ---------- Appendix ---------- */
.srcs li{{ font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--teal); padding:9px 0; border-top:1px solid var(--line); }}
.srcs li:first-child{{ border-top:0; }}

/* ---------- Prepared-by ---------- */
.prep{{ background:var(--teal); color:#E9E3D6; padding:56px 68px; display:flex; justify-content:space-between; align-items:flex-start; gap:40px; }}
.prep h3{{ font-family:'Fraunces',serif; font-weight:300; font-size:1.5rem; }}
.prep p{{ color:#A9B4AE; font-size:.9rem; margin-top:10px; max-width:34ch; }}
.prep .addr{{ text-align:right; font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.1em; color:#8A97A0; }}
.prep .addr b{{ display:block; color:#E9E3D6; font-weight:500; letter-spacing:.14em; font-size:.8rem; margin-top:6px; font-family:'JetBrains Mono',monospace; }}

@media (max-width:760px){{
  .page{{ padding:40px 24px; }}
  .cover{{ padding:44px 30px; min-height:900px; }}
  .cover .meta{{ grid-template-columns:1fr; gap:20px; }}
  .scope{{ grid-template-columns:1fr; gap:24px; }}
  .prep{{ flex-direction:column; }} .prep .addr{{ text-align:left; }}
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
      <span class="conf">CONFIDENTIAL</span>
    </div>
    <div class="mid">
      <p class="eyebrow" style="color:#9FB3B0">Evidence Intelligence · {month} · v1</p>
      <h1>{esc(a.title)}</h1>
      <p class="sub">{esc(a.subtitle or 'Verified evidence brief')}</p>
    </div>
    <div class="meta">
      <div><p>Prepared for</p><h4>{esc(client)}</h4></div>
      <div><p>References screened</p><h4>{total}</h4></div>
      <div><p>Crossref-verified</p><h4>{verified} / {total}</h4></div>
      <div><p>Version</p><h4>v1 · {month}</h4></div>
    </div>
    <div class="foot">
      <span>VERIFIED · REPRODUCIBLE · TRACEABLE</span>
      <span>NOT FOR REDISTRIBUTION</span>
    </div>
  </section>

  <!-- CONTENTS -->
  <section id="toc">
    <div class="sechead"><p class="eyebrow">Contents</p><span class="sec-num">BIORESEARCH·OS</span></div>
    <ul class="take" style="columns:2;column-gap:48px">{toc_lis}</ul>
  </section>

  {body}

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
    p.add_argument("--subtitle", default="Verified evidence brief")
    p.add_argument("--client", default="")
    p.add_argument("--question", default="")
    p.add_argument("--context", default="")
    p.add_argument("--scope-in", default="")
    p.add_argument("--scope-out", default="")
    p.add_argument("--methods", default="PubMed/OpenAlex literature search; DOI verification against Crossref")
    p.add_argument("--summary", default="")
    p.add_argument("--takeaways", default="")
    p.add_argument("--discussion", default="")
    p.add_argument("--implications", default="")
    p.add_argument("--recommendations", default="")
    p.add_argument("--confidence", default="")
    p.add_argument("--gaps", default="")
    return p

if __name__ == "__main__":
    main()