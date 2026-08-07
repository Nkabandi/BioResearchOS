"""One runnable check for evidence_engine — no network needed.

Exercises all five verification behaviors:
  - overlapping pct ranges, 2 verified sources        -> High, no conflict
  - verified but 1 source                             -> Medium
  - non-overlapping ranges, both verified             -> conflict flagged
  - a citation_check.csv with VERIFIED + FAILED       -> FAILED is unverified
  - DOI absent from citation_check                    -> Low

Note on confidence: the engine scores High for verified && sources>=2 and
Medium for verified && sources==1. There is no input where a 2-row group with
1 verified source is Medium (it is High), so the Medium case is a single
verified row, per the engine's own branch.
"""
import importlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ee = importlib.import_module("evidence_engine")

TABLE = "Paper,Status,Reference,Sample,Method,Finding,Limitations\n"

ROWS = [
    "mrsa1,VERIFIED,African Journal of Laboratory Medicine 10.1000/mrsa1,,,MRSA resistance 40-60%,small n",
    "mrsa2,VERIFIED,PLOS ONE 10.1000/mrsa2,,systematic review + meta-analysis,MRSA resistance 45-55%,",
    "esbl,VERIFIED,Lancet 10.1000/esbl1,,systematic review + meta-analysis of 24 studies,ESBL resistance 40%,ok",
    "hdy1,VERIFIED,Nature 10.1000/hdy1,,,HDY 90-95%,",
    "hdy2,VERIFIED,Science 10.1000/hdy2,,,HDY 10-15%,",
    "trx,FAILED,blog 10.1000/trx9,,RCT,TRX 50%,",
    "fct,VERIFIED,clinicaltrials 10.7777/fct1,,,FCT 5%,",
]
CHECKS = [
    "doi,status\n",
    "10.1000/mrsa1,VERIFIED\n",
    "10.1000/mrsa2,VERIFIED\n",
    "10.1000/esbl1,VERIFIED\n",
    "10.1000/hdy1,VERIFIED\n",
    "10.1000/hdy2,VERIFIED\n",
    "10.1000/trx9,FAILED\n",
]


def main():
    with tempfile.TemporaryDirectory() as td:
        ev = Path(td)
        (ev / "evidence_table.csv").write_text(TABLE + "\n".join(ROWS) + "\n")
        (ev / "citation_check.csv").write_text("".join(CHECKS))
        res = ee.verify(ev)
        claims = {c["metric"]: c for c in res["claims"]}

        assert claims["MRSA"]["confidence"] == "High"
        assert claims["MRSA"]["sources"] == 2
        assert claims["MRSA"]["conf_score"] == 0.85
        assert claims["MRSA"]["status"] == "VERIFIED"
        assert not any(x["metric"] == "MRSA" for x in res["conflicts"])

        assert claims["ESBL"]["confidence"] == "Medium"
        assert claims["ESBL"]["verified"]
        assert claims["ESBL"]["sources"] == 1
        assert claims["ESBL"]["dois"] == ["10.1000/esbl1"]

        assert "meta-analysis" in claims["ESBL"]["study_types"]
        assert "RCT" in claims["TRX"]["study_types"]
        assert claims["MRSA"]["ev_weight"] >= 8
        assert claims["ESBL"]["ev_weight"] == 10

        assert any(x["metric"] == "HDY" for x in res["conflicts"])
        hdy = next(x for x in res["conflicts"] if x["metric"] == "HDY")
        assert "10.0–95.0%" in hdy["range"]
        assert claims["HDY"]["confidence"] != "High"

        assert claims["TRX"]["verified"] is False
        assert claims["TRX"]["confidence"] == "Low"
        assert claims["TRX"]["status"] == "CIRCULATING"
        assert claims["TRX"]["conf_score"] == 0.3

        assert claims["FCT"]["confidence"] == "Low"
        assert claims["FCT"]["verified"] is False
    print("ok: evidence engine checks pass")


if __name__ == "__main__":
    main()