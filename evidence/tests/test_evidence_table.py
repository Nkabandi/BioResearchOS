"""One runnable check for evidence_table — no network needed."""
import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ev = importlib.import_module("evidence_table")


def norm(*args, **kw):
    return ev.norm(*args, **kw)


def check(*args, **kw):
    return ev.check_record(*args, **kw)


def main():
    # norm: case/whitespace-insensitive
    assert ev.norm(" Synergistic Drug Combinations ") == ev.norm("synergistic drug combinations")
    # MISSING_DOI
    assert ev.check_record({"doi": ""})["status"] == "MISSING_DOI"


if __name__ == "__main__":
    main()
    print("ok: evidence_table checks pass")