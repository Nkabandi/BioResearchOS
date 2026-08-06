#!/usr/bin/env python3
"""Generate the four portfolio evidence CSVs.

Only DOIs are hand-written here; evidence_table.py resolves every DOI on
Crossref and pulls the authoritative title/journal/year into the report, so
no hand-transcribed citation can corrupt the output. Findings/Limitations are
short restatements of the abstracts verified in session. Deliberately no fake
rows. Regen: python portfolio/build_inputs.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (doi, sample, finding, limitations)
TOPICS = {
"amr-east-africa": [
    ("10.1186/s13756-025-01662-y",  # PMID 41199307
     "EAC national public health labs / expert panel (Burundi, Kenya, Rwanda, South Sudan, Tanzania, Uganda)",
     "Progress on sustainable AMR-NAP implementation ranges 7% (Burundi) to 94% (Kenya); WHO AMR-surveillance checklist completion 44-100%; gaps in lab capacity, representativeness, integration and financing",
     "Qualitative NAP/report synthesis by expert panel; no quantitative outcomes"),
    ("10.4102/ajlm.v5i1.432",  # PMID 28879114
     "12 East African studies (2005+, PubMed + AJOL), mostly bloodstream infections",
     "High resistance to first-line drugs 50-100% (ampicillin, cotrimoxazole), emerging ceftriaxone resistance (46-69%) in Gram-negatives, mainly Klebsiella and E. coli; MRSA 2.6-4%",
     "Small body of heterogeneous studies; not a meta-analysis"),
    ("10.1371/journal.pone.0145632",  # PMID 26700032
     "469 consecutively enrolled patients, Mnazi Mmoja Hospital, Zanzibar",
     "Pathogenic bacteria in 14% of patients; first report of community-acquired ESBL Enterobacteriaceae bloodstream infections in Zanzibar; 6/7 Salmonella Typhi isolates multidrug resistant",
     "Single-centre study; small number of ESBL isolates"),
    ("10.4102/ajlm.v7i2.796",  # PMID 30568902
     "Systematic review 2010-2017, 35 African studies (>60% East Africa)",
     "HCAI driven by Klebsiella, S. aureus, E. coli, Pseudomonas; MRSA 3.9-56.8%; ESBL Gram-negatives 1.9-53%; surveillance sparse",
     "Heterogeneous primary studies; review not meta-analysis"),
],
"malaria-resistance": [
    ("10.1016/S1473-3099(24)00141-5",  # PMID 38552654
     "Multi-institution review incl. WHO (Rossert HQ colleagues, Uganda/Tanzania/Rwanda)",
     "ART-R has emerged in multiple East African countries and is now a priority; recommended expansion of genomic surveillance, clinical efficacy trials, ex-vivo susceptibility testing, policy adaptation",
     "Review / recommendation piece, no new primary data"),
    ("10.1186/s12936-025-05447-x",  # PMID 40598187
     "173 P. falciparum-positive children, Mwanza, Tanzania (2016-2022), 143 Pfk13 sequenced",
     "7.0% non-synonymous Pfk13 mutations incl. WHO-validated R561H (2 patients, 2022); pfmdr1 N86 invariable; mean MOI 1.5; suggests emerging lumefantrine tolerance",
     "Single site; Sanger sequencing"),
    ("10.1371/journal.pone.0354429",  # PMID 42520053
     "Systematic review + meta-analysis of 24 studies (2014-2024), East Africa",
     "Pooled non-synonymous PfKelch13 prevalence 5.0% (Cl 3.0-7.0%); R561H and A675V most common; mutations associated with higher risk of treatment failure (log OR -2.06)",
     "High between-study heterogeneity"),
    ("10.1186/s12936-021-03987-6",  # PMID 34856982
     "87 studies, 37,864 isolates across 29 African countries",
     "Five validated pfk13 ART-R markers in Africa: R561H (Rwanda, Tanzania), M476I (Tanzania), C580Y (Ghana), F446I (Mali), P553L (Angola); distribution central to East Africa",
     "Aggregation of heterogeneous surveillance studies"),
    ("10.4269/ajtmh.25-0114",  # PMID 40664184
     "Symptomatic malaria patients at primary centres, central Ethiopia, 2023 (220 isolates)",
     "Validated ART-R marker pfk13 R622I in ~2/174 (1.1%); pfmdr1 pattern consistent with reduced lumen sensitivity; high HRP2/3-deletion prevalence (HRP2 del 24%, HRP3 del 79%, dual 22.7%)",
     "Limited genotyping denominators; season-emergency only"),
    ("10.7554/eLife.105544",  # PMID 41037007
     "Aggregation of 112,933 P. falciparum samples (1980-2023), review",
     "ART-R in Africa follows the Southeast Asia pattern 10-15 years earlier; kelch13 data aggregated into a single surveillance resource with focus on East Africa",
     "Depends on public metadata quality"),
    ("10.1016/j.mib.2022.102193",  # PMID 36007459
     "Review of artemisinin-based combination therapy resistance (Pfk13, partner drugs)",
     "ART resistance is mediated by kelch13; ACTs remain effective but partner-drug vulnerabilities and regional spread of markers demand continual monitoring",
     "Review perspective; necessarily summary-level"),
],
"agricultural-biotech": [
    ("10.3390/v16111691",  # PMID 39599806 — cassava mosaic, not the West Africa
     "country-wide survey, Guinea April 2024; + 2022 Kambia (Sierra Leone) samples",
     "EACMV-Ug (Uganda 1990s pandemic strain) detected across Guinea and Sierra Leone; spread via infected cuttings; all 63 cultivated accessions susceptible; established eastward front developing in West Africa",
     "Single-country scope; survey not controlled trial"),
    ("10.1016/j.virusres.2003.12.021",  # PMID 15036844
     "Review of field survey methods, whitefly IPM across Africa",
     "Standardised survey methods required to map the ongoing CMD pandemic, because whitefly (Bemisia tabaci) dynamics govern epidemic spread",
     "Methods review; not incidence data"),
    ("10.1016/j.coviro.2018.08.016",  # PMID 30243102
     "Review of whitefly-transmitted viruses (CMG & CBSV), endosymbiont work",
     "Separateness and superabundant whitefly populations drive CMG/CBSV pandemic evolution; southern diversity and complex interactions need integrated surveillance",
     "Review opinion focus"),
    ("10.1016/bs.aivir.2014.10.001",  # PMID 25591878
     "Comprehensive review of cassava virus biology, epidemiology, management",
     "Cassava mosaic disease caused by begomoviruses; pandemic spread linked to recombinates and high vector abundance; management via diagnostics, phytosanitation, breeding resistant or immune varieties",
     "Global scope; regional data variable"),
    ("10.3390/v16091469",  # PMID 39339946
     "Field surveys 2022-2023 in six western Kenya counties; 29 varieties recorded",
     "CMD incidence 26.4% (2022) vs 10.1% (2023); whitefly-mediated transmission share rose to 50.6% in 2023; improved varieties had far lower CMD (~-30 pt) than locals",
     "Observational survey; multi-year variation"),
    ("10.3390/v18030319",  # PMID 41902227
     "Côte d'Ivoire border surveys 2022 + 2025 (west border)",
     "EACMV-Ug confirmed in Côte d'Ivoire for the first time; higher infection along Liberia border (28.85%) than Guinea border (17.07%); all varieties susceptible; cuttings main route",
     "Recent-detection report; broader survey recommended"),
    ("10.1016/j.jafr.2025.101827",  # PMID 40487127
     "305 farmers + 77 fields, Benin; PSM analysis",
     "Awareness campaigns increased CMD knowledge and adoption of practices but CMD still present in majority of fields because healthy planting material/scarcity or whiteflies in surplus",
     "PSM observational; residual confounding possible"),
],
"tb-diagnostics": [
    ("10.1126/scitranslmed.adp6411",  # PMID 40203083
     "Children 1-16y (serum cfDNA) + adults (sputum/saliva)",
     "Portable lab-in-tube RPA+CRISPR-Cas12a assay detected MTB DNA with 81% sensitivity vs culture (68% GeneXpert) and 94% specificity, meeting WHO TPP for non-sputum TB; result within 1 h",
     "Adult/child validation; needs field-scale confirmation"),
    ("10.1016/S2666-5247(22)00087-8",  # PMID 35659882
     "Adults, children incl. HIV-positive, Eswatini + Kenya (archived serum)",
     "CRISPR-TB: 96% sensitivity / 94% specificity adults; 83%/95% children; 100% in CLHIV; seropositivity positively hazard; signal cleared by 6 months of treatment",
     "Retrospective archived serum; segmented cohorts"),
    ("10.1038/s41467-023-37183-8",  # PMID 37002219
     "Plasma from active pulmonary TB patients (proof-of-concept)",
     "WATSON (pooled genomic tiling + CRISPR/Cas13) detects Mtb-cfDNA with higher sensitivity than singleton target for whole-genome, and compatible with lateral flow tradu in future",
     "Proof-of-feasibility laboratory assay"),
    ("10.1128/spectrum.02652-24",  # PMID 40488470
     "Clinical sputum: 73 true positive samples + 40 negative controls",
     "RPA/CRISPR-Cas12f1_ge4.1 dual-set fluorescence/lateral flow: LOD 10 copies/µL (FL), 100 (LT); sensitivity vs qPCR 94.5-91.4 with 100% specificity; <1h",
     "Moderate cohort; dual-readout validation required on-site"),
    ("10.1016/j.aca.2026.345085",  # PMID 41611404
     "microfluidic cfDNA enrichment + CRISPR/Cas12a, 20 clinical specimens (7 NTM/MTB, 13 controls)",
     "Species-level MTB/MAC/MAB differentiation; all mycobacterial positives called correctly, no false positives; 2-hour workflow",
     "Very small validation set; assay-level not yet clinical routine"),
    ("10.1016/j.tube.2023.102340",  # PMID 37031646
     "Review of TB diagnostics (conventional to molecular/nano)",
     "Conventional microscure/X-ray/PPD limitations; molecular (incl. CRISPR-Cas/MiRNA) and nano-approaches improve sensitivity/specificity, argued cost-effective for POC",
     "Review; several technologies pre-clinical"),
],
}

def main():
    for name, rows in TOPICS.items():
        path = HERE / name / "input" / "papers.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["doi", "method", "finding", "limitations"])
            w.writeheader()
            for doi, sample, finding, limitations in rows:
                w.writerow({"doi": doi, "method": sample, "finding": finding,
                            "limitations": limitations})
        print(f"wrote {path} ({len(rows)} rows)")

if __name__ == "__main__":
    main()