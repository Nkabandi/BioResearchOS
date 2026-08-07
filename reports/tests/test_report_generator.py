"""One runnable check for report_generator — no network needed."""
import importlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
rg = importlib.import_module("report_generator")


def main():
    with tempfile.TemporaryDirectory() as td:
        ev = Path(td)
        (ev / "evidence_table.csv").write_text(
            "Paper,Status,Reference,Sample,Method,Finding,Limitations\n"
            "mrsa1,VERIFIED,Lancet 10.1000/mrsa1,,,MRSA resistance 40-60%\n"
        )
        out = Path(td) / "out"
        args = rg.parser().parse_args(["--evidence", str(ev), "--output", str(out)])
        md = rg.build_md(args)
        assert "MRSA" in md
        assert "Consultat a healthcare professional" not in md  # disclaimer lives in html
        html = rg.build_html(args)
        assert "<h1>" in html and "title>" in html
        print("ok: report_generator checks pass")


if __name__ == "__main__":
    main()