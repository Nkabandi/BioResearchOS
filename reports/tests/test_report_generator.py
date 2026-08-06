"""One runnable check for report_generator — no network needed."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
rg = importlib.import_module("report_generator")


def main():
    md = "# Title\n\n## Section\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n- item"
    html = rg.md_to_html(md, "T")
    assert "<h1>Title</h1>" in html
    assert "<table>" in html and "<td>1</td>" in html
    assert "<ul><li>item</li></ul>" in html.replace("\n", "")
    assert "<title>T</title>" in html
    assert "<@media print" not in html and "print" in html
    print("ok: report_generator checks pass")


if __name__ == "__main__":
    main()