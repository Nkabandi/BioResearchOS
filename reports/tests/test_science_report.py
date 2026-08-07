"""Runnable check for science_report: graph edges, normalization, gate flags."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import science_report as sr

def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "a").mkdir(); (td / "b").mkdir()
        hdr = "metric,claim,sources,verified,status,confidence,conf_score,ev_weight,max_tier,study_types,dois\n"
        (td / "a" / "verification.csv").write_text(hdr + "MRSA,MRSA 2.6-4%,2,y,VERIFIED,High,0.85,9,9,meta-analysis,10.1/x\n")
        (td / "b" / "verification.csv").write_text(hdr + "ESBL,ESBL 40-60%,1,n,CIRCULATING,Low,0.3,4,9,cohort,10.1/x\n")
        ev_hdr = "Paper,Status,Reference,Sample,Method,Finding,Limitations\n"
        (td / "a" / "evidence_table.csv").write_text(
            ev_hdr + "MRSA Review,VERIFIED,Journal X 10.1/x,Kenyan patients,meta-analysis,MRSA 2.6-4%,laboratory\n")
        (td / "b" / "evidence_table.csv").write_text(
            ev_hdr + "ESBL Notes,VERIFIED,Journal Y 10.1/x,Tanzania cohort,cross-sectional,ESBL 40-60%,single study\n")
        spec = [(td / "a", "alpha"), (td / "b", "beta")]
        nb = sr.build(spec)

        assert len(nb["claims"]) == 2
        mrsa = next(c for c in nb["claims"] if c["metric"] == "MRSA")
        esbl = next(c for c in nb["claims"] if c["metric"] == "ESBL")
        assert mrsa["dois"] == ["10.1/x"] and esbl["dois"] == ["10.1/x"]
        assert sr.review_flags(esbl) == ["UNVERIFIED source — do not reuse",
                                         "Single source — needs a second independent study",
                                         "Low confidence — treat as hypothesis"]
        assert sr.review_flags(mrsa) == []
        assert "Falsified if a new meta-analysis" in sr.falsified(mrsa)
        assert "Falsified if a higher-grade study" in sr.falsified(esbl)
        assert "Conflict" in sr.falsified({**mrsa, "contradiction": True})
        shared = [e for e in nb["edges"] if e[0].startswith("claim:") and e[1].startswith("claim:")]
        assert shared == [("claim:alpha:MRSA", "claim:beta:ESBL")], shared
        assert mrsa["provenance"] and mrsa["provenance"][0]["paper"] == "MRSA Review"
        assert mrsa["provenance"][0]["population"] == "Kenyan patients"
        assert mrsa["provenance"][0]["limitations"] == "laboratory"
        assert esbl["provenance"][0]["status"] == "VERIFIED"
    print("ok: science_report checks pass")


if __name__ == "__main__":
    main()