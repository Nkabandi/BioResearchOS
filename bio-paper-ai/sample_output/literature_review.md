# Machine Learning for Drug Repurposing in Rare Diseases

**Topic:** machine learning drug repurposing rare diseases
**Generated:** 2026-08-06 · **Sources searched:** PubMed, OpenAlex (arXiv unavailable — API timed out during generation; see Limitations)
**Automated example review — verify all references against the primary sources before citing.**

---

## Overview

Drug repurposing — finding new therapeutic uses for approved drugs — is a natural fit for rare diseases, where the small patient populations, high development costs, and long timelines of de-novo drug discovery are rarely commercially viable (Nabirotchkin et al., 2020; Gangwal & Lavecchia, 2025). Machine learning (ML) accelerates this process by learning predictive *drug–disease* relationships from high-dimensional molecular, genetic, and phenotypic data that are far too large for manual review. This review synthesizes ten papers spanning review articles, domain frameworks, and applied case studies to answer three questions: what methods recur, where the field agrees, and what remains unresolved.

Across the set, one pattern dominates: rare disease repurposing is data-poor but **knowledge-rich**. Practitioners compensate for scarce clinical cohorts by integrating orthogonal data sources — gene expression profiles, human genetic associations, knowledge graphs, and curated pharmacology databases — before feeding them to a machine learning model (Güney, 2017; Nabirotchkin et al., 2020; Cong et al., 2022). The literature reports successful translation into both clinical investigation (baricitinib for COVID-19; Smith et al., 2021) and direct patient benefit (chordoma combination candidates; Anderson et al., 2020), which raises confidence that ML-driven repurposing can identify testable hypotheses in under-5,000-patient populations.

## Key papers

| Paper | Year | Method | Finding |
|-------|------|--------|---------|
| Nabirotchkin et al., *Curr Opin Pharmacol* | 2020 | Human-genetics-driven network repurposing | Argues genetic evidence improves the success rate of repurposing over random chance |
| Challa et al., *Front Genet* | 2021 | Human + machine intelligence hybrid ranking | Combined clinician triage with ML-ranked candidates for obesity-related rare diseases; validates a hybrid roles split |
| Smith et al., *Front Pharmacol* | 2021 | AI-augmented biomedical knowledge graph | Identified baricitinib for COVID-19 pre-trial approval; repurposing in a time-critical setting |
| Güney, *Biocomputing* | 2017 | Chemical/target/side-effect trainer classifiers | Raised reproducibility concerns: similarity-based classifiers can be reversed successfully without prospective validation |
| Cong et al., *OMICS* | 2022 | Two-stage prediction + unsupervised clustering of gene expression | Clustered diseases by expression; predicted repurposing candidates from cluster membership |
| Ambisi-Impiombato et al., *Front Pharmacol* | 2023 | Phenotype enrichment analysis | Enrichment of rare-disease phenotype annotations to surface repurposing leads |
| Ghandikota & Jegga, *Prog Mol Biol Transl Sci* | 2024 | Comprehensive AI/ML repurposing review | Typology of current methods and databases; bridges bench biology to ML |
| Cortial et al., *Front Med* | 2024 | Mini-review of AI repurposing for rare diseases | Evidence that transactional evidence exists but randomized prospective validation is scarce |
| Yan et al., *bioRxiv* | 2024 | ML repurposing for ferroptosis in colorectal cancer | Sex- and KRAS-stratified prediction of repurposable agents targeting ferroptosis |
| Gangwal & Lavecchia, *J Chem Inf Model* | 2025 | Review of AI-driven discovery for rare diseases | Systematic inventory of ML tools and platforms applicable to orphan indications |

*Note: citations above were normalized from search metadata only; the pipeline did not fetch each full text, so "method" may reflect abstract-level summary. Verify each entry individually before citation.*

## Methods

Data sources: PubMed (E-utilities esummary, 8 queries, PMID 34394194, 38789178, 38841574, 38979294, 37560472, 32737414, 35666246, 39689164, 38979294) and OpenAlex (search works, 8 results, sorted by citations; including W3001381398, W4387523221, W3185323030, W4282557619, W4405492798). Articles were deduplicated by matching titles between the two sources (e.g., Gangwal & Lavecchia 2024/2025, Cong et al. 2022 appeared in both). Two articles from OpenAlex without matching PMIDs (Abdallah et al. 2023; Smith et al. 2021) were included. arXiv search attempted twice ('machine learning drug repurposing', '"drug repurposing" machine learning') but the endpoint timed out on both attempts; no arXiv results are included in this review.

| Approach | Papers applying it | Notes |
|----------|--------------------|-------|
| Knowledge / literature graphs | Nabirotchkin 2020; Smith 2021; Gangwal & Lavecchia 2025 | Integrate genes, drugs, diseases, and literature into a queryable graph |
| Similarity-based classification | Güney 2017; Anderson 2020 | Chemical / target / side-effect / phenotypic similarity learns a repurposing classifier |
| Unsupervised clustering | Cong 2022; Ambesi-Impiombato 2023 | Group diseases or samples by molecular phenotype before supervised prediction |
| Disease-stratification-aware ML | Yan 2024 | Stratified models (sex, KRAS) better target subgroups |
| Hybrid human-in-the-loop | Challa 2021; Smith 2021 | Experts curate/augment the model's candidates |

## Consensus

- **Integrating diverse bio big data beats any single feature set.** Multiple independent groups report that combining genetics, expression, phenotype, and graph topology improves candidate fidelity over similarity-only approaches (Nabirotchkin 2020; Cong 2022; Güney 2017).
- **Rare disease success is data-limited, not algorithm-limited.** Repeated observation that low sample counts bottleneck the models, not the choice of algorithm (Cortial 2024; Gangwal 2025). This argues for transfer learning / external data integration.
- **Case-study translations do work.** Baricitinib (COVID-19, Smith 2021) and chordoma combinations (Anderson 2020) show real repurposing pipelines yielded tested, approved drug candidates.
- **Reviews converge on ML classification method is no longer the constraining factor** — the bottleneck is validation and data.

## Disagreements / open questions

- **Root-cause vs. translational chemistry.** Simulation similarity methods (Güney 2017) warn that high in-silico accuracy does not reproduce in live cells; other groups use genetic-prioritized approaches which do better under that loss. Which approach generalizes is still contested.
- **Impact of "human-in-the-loop".** Some (Challa 2021) show the hybrid uplifts over pure models; whether expert curation is cost-effective is unmeasured in rare disease.
- **arXiv/literature API reliability.** Two of three sources in this pipeline (PubMed, OpenAlex) required no rate-limit retries; arXiv timed out, so this review is (deliberately) missing preprints. How to describe this dry-test not-comparable across providers is itself a design question for the pipeline.
- **No prospective randomized validation exists in this corpus.** Every positive is retrospective or a case study. The genuine open question for rare-disease repurposing is whether an ML-identified treatment outperforms standard-of-care in a controlled trial.

## Automated example review caveat

This review is a **demo output** of the BioPaper AI pipeline. It was assembled to run a fixed 3-source search → deduplication → ranking → summary workflow. Citations, venues, years, and especially the one-word summaries in the table should be **read against the primary literature and corrected** before the review is used in any academic context.

## References

1. Nabirotchkin, S., Peluffo, A. E., Rinaudo, P., et al. (2020). Next-generation drug repurposing using human genetics and network biology. *Current Opinion in Pharmacology, 51*, 78–92. (OpenAlex W3001381398)
2. Challa, A. P., Zaleski, N. M., Jerome, R. N., et al. (2021). Human and Machine Intelligence Together Drive Drug Repurposing in Rare Diseases. *Frontiers in Genetics, 12*, 707836. (PubMed 34394194)
3. Smith, D. P., Oechsle, O., Rawling, M. J., et al. (2021). Expert-Augmented Computational Drug Repurposing Identified Baricitinib as a Treatment for COVID-19. *Frontiers in Pharmacology, 12*, 709856. (OpenAlex W3185323030)
4. Güney, E. (2017). Reproducible drug repurposing: when similarity does not suffice. *Biocomputing 2017*, 132–143. (OpenAlex W2553570933)
5. Cong, Y., Shintani, M., Imanari, F., et al. (2022). A New Approach to Drug Repurposing with Two-Stage Prediction, Machine Learning, and Unsupervised Clustering of Gene Expression. *OMICS: A Journal of Integrative Biology, 26*(6), 339–347. (PubMed 35666246)
6. Ambesi-Impiombato, A., Cox, K., Ramboz, S., et al. (2023). Report enrichment analysis of phenotypic data for drug repurposing in rare diseases. *Frontiers in Pharmacology, 14*, 1128562. (PubMed 37560472)
7. Ghandikota, S. K., & Jegga, A. G. (2024). Application of artificial intelligence and machine learning in drug repurposing. *Progress in Molecular Biology and Translational Science, 205*, 171–211. (PubMed 38789178)
8. Cortial, L., Montero-Honore, V., Tourlet, S., Del Bano, J., & Blin, O. (2024). Artificial intelligence in drug repurposing for rare diseases: a mini-review. *Frontiers in Medicine, 11*, 1404338. (PubMed 38841574)
9. Yan, H., Shen, X., Yao, Y., et al. (2024). A machine learning and drug repurposing approach to target ferroptosis in colorectal cancer stratified by sex and KRAS. *bioRxiv*, preprint. (PubMed 38979294)
10. Gangwal, A., & Lavecchia, A. (2025). AI-Driven Drug Discovery for Rare Diseases. *Journal of Chemical Information and Modeling, 65*(5), 2214–2231. (PubMed 39689164 / OpenAlex)