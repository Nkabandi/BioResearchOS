#!/usr/bin/env python3
"""Build a fully standalone copy of the BioResearchOS site into one file.

Homepage + all four portfolio reports inlined as real HTML sections (no
iframes, no external portfolio/ requests), CSS-scoped per report so nothing
collides.
Output: docs/index-standalone.html (the Downloads copy is cp'd by the caller).
"""
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "docs" / "index.html"
REPORTS = [
    ("amr-east-africa", "AMR Surveillance in East Africa"),
    ("malaria-resistance", "Malaria Resistance"),
    ("tb-diagnostics", "CRISPR Diagnostics for Tuberculosis"),
    ("agricultural-biotech", "Agricultural Biotechnology"),
]
OUT = ROOT / "docs" / "index-standalone.html"


def _find_brace(css: str, start: int) -> int:
    """Index of the '}' matching the '{' at start."""
    depth = 0
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(css)


def scope_css(css: str, prefix: str) -> str:
    """Prefix every selector with `prefix ` except :root and @-rule internals
    get recursively treated. Returns a valid stylesheet."""
    out = []
    i = 0
    n = len(css)
    while i < n:
        if css[i] == "@":
            j = css.find("{", i)
            if j == -1:
                out.append(css[i:])
                break
            prelude = css[i:j]
            k = _find_brace(css, j)
            inner = css[j + 1:k]
            out.append(prelude + "{")
            out.append(scope_css(inner, prefix))
            out.append("}")
            i = k + 1
        elif css[i] == "}":
            out.append("}")
            i += 1
        else:
            j = css.find("{", i)
            if j == -1:
                out.append(css[i:])
                break
            sel = css[i:j]
            k = _find_brace(css, j)
            body = css[j + 1:k]
            if ":root" not in sel:
                prefixed = ", ".join(
                    f"{prefix} {s.strip()}" for s in sel.split(",") if s.strip()
                )
                sel = prefixed
            out.append(sel + "{" + body + "}")
            i = k + 1
    return "".join(out)


def extract(path: Path) -> tuple[str, str]:
    s = path.read_text()
    css = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
    body = re.search(r"<body[^>]*>(.*?)</body>", s, re.S).group(1)
    return css, body


def main() -> None:
    site = SITE.read_text()

    for key, _ in REPORTS:
        site = site.replace(f'href="portfolio/{key}.html"', f'href="#report-{key}"')
    site = re.sub(r"\s*<section class=\"inline-reports\">.*?</section>\s*", "\n", site, flags=re.S)

    blocks = ['\n<!-- inline full reports (standalone build) -->', '<section class="inline-reports">']
    for i, (key, name) in enumerate(REPORTS):
        css, body = extract(ROOT / "docs" / "portfolio" / f"{key}.html")
        pid = f"rep_{key.replace('-', '_')}"
        blocks.append(
            f"""  <div class="ireport" id="report-{key}">
    <div class="ireport-head">
      <span class="eyebrow">{html.escape(name)}</span>
      <a href="#top">Back to top</a>
    </div>
    <style>{scope_css(css, "#" + pid)}</style>
    <div id="{pid}">{body}</div>
  </div>"""
        )
    blocks.append("</section>")
    inline = "\n".join(blocks)

    css_site = """/* standalone report blocks */
.inline-reports{padding:0 0 96px;border-top:1px solid var(--line)}
.ireport{margin-top:80px}
.ireport-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.ireport-head .eyebrow{color:var(--gold);font-size:.85rem;letter-spacing:.14em;text-transform:uppercase}
"""
    site = site.replace("</style>", css_site + "</style>", 1)
    site = site.replace('<header class="nav">', '<header class="nav" id="top">')
    site = site.replace("</body>", inline + "\n</body>")

    OUT.write_text(site)
    shutil.copy(OUT, "/home/nkabandi/Downloads/index(2).html")
    print("wrote", OUT, "and Downloads/index(2).html", len(site), "bytes")


if __name__ == "__main__":
    main()