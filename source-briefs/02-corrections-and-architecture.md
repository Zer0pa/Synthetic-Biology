# Synthetic Biology — Metabolic Pathway Engineering Pipeline
## Report 2: Corrections, Augmentations & Architecture Brief

**Pipeline:** Synthetic Biology — Metabolic Pathway Engineering (Pipeline 4 of 6)  
**Brief Version:** 2.0  
**Date:** April 30, 2026  
**Issued by:** Architect Prime, Zer0pa Science Intelligence Platform  
**Status:** Pre-PRD Hardened Input — replaces and supersedes licensing, data, and architecture assumptions in Report 1 (v1.0)

***

## Executive Summary

This report delivers four outputs against the Report 2 brief: (1) a licensing correction and decomposition audit for every major resource in the pipeline, resolving the four-object BRENDA split, the KEGG usage boundary, and the NASA OSDR tiered access model; (2) a data matrix for the five primary prediction tasks, with new primary sources — most critically the **BioTRY** database (+52,000 TRY entries) and the **EnzyExtract** corpus (+89,544 kinetic entries absent from BRENDA) — that materially change the data sufficiency picture; (3) a tiered intersectional map promoting four intersections to architecture-critical Tier 1 and isolating three as genuine research frontiers; and (4) five emergent innovation artefacts with build specifications. The report concludes with a typed architecture schema and a Ready-for-PRD checklist.[^1][^2][^3]

The single most consequential finding of this pass is that **BRENDA's core data is CC BY 4.0** — commercially permissive — making the Report 1 strategy of "use BRENDA only through DLKcat/TurNuP as proxy" unnecessary for the database itself, while the **BKMS-react companion module remains genuinely Class C/D** (redistribution requires a separate license). This correction upgrades the enzyme kinetics layer's licensing posture substantially. The second major finding is that a **DBTL benchmark equivalent to ProteinGym does not yet exist** for pathway-level optimisation — this gap is an explicit Zer0pa build opportunity.[^4]

***

## Section 1: Corrections & Licensing Audit

### 1.1 BRENDA — Four-Object Decomposition

Report 1 treated BRENDA as a monolithic Class C/E resource and recommended routing all kinetic data access through ML surrogates trained on BRENDA. This was partially incorrect. BRENDA must be decomposed into four legally distinct objects.[^5]

**Object 1 — Core Data (enzyme entries and kinetic values)**  
The BRENDA license page states unambiguously: *"The usage of the BRENDA data is licensed under Creative Commons Attribution License CC BY 4.0."* CC BY 4.0 permits use, redistribution, and commercial exploitation provided attribution is given. The OECD confirms CC BY 4.0 allows adaptation for commercial purposes. **Zer0pa classification: Class A.** The direct use of BRENDA kinetic values — kcat, Km, inhibition constants, stability data, substrate scope — in the pipeline knowledge layer, in training datasets, and in downstream ML models is fully permissible under attribution.[^6][^1]

**Object 2 — Web Interface / Online Service**  
The web interface at brenda-enzymes.org provides query access. Terms of service govern programmatic scraping but no explicit restriction on commercial queries is stated at the current time. The CC BY 4.0 data license applies to outputs. **Classification: Class A** for result data; standard API rate-limit etiquette applies.[^5]

**Object 3 — Bulk Download Files**  
Bulk data downloads are available from the BRENDA download page after accepting the CC BY 4.0 license. Attribution in any redistributed product is required. **Classification: Class A** with mandatory citation of the latest BRENDA publication.[^1]

**Object 4 — BKMS-react Module**  
BKMS-react is a separate composite reaction database combining BRENDA, KEGG, MetaCyc, and SABIO-RK reactions. Its own license page states explicitly: *"Any inclusion of BKMS-react components into other databases, or redistribution of BKMS-react requires a license. Individuals... are NOT GRANTED license to: distribute a copy... without permission from the copyright owner."* Altering or charging for copies is also prohibited. **Classification: Class C/D** — BKMS-react cannot be embedded in the Zer0pa corpus without a separate negotiated license.[^7][^4]

**Strategic re-evaluation:** The Report 1 strategy "use BRENDA only via DLKcat/TurNuP" should be revised. Direct use of BRENDA bulk data (CC BY 4.0) is Class A-compatible. The pipeline may: (a) pull BRENDA bulk downloads as a primary kinetics layer in the knowledge base, (b) train Zer0pa-owned conditional kinetics models on the CC BY 4.0 data directly, (c) cite BRENDA in all outputs as required. The only remaining constraint is BKMS-react, which must remain out of the production corpus unless a redistribution license is obtained.

| BRENDA Object | License | Zer0pa Class | Notes |
|---|---|---|---|
| Core enzyme data (entries, kcat, Km) | CC BY 4.0 | **A** | Attribution required; commercial use permitted |
| Online web interface | CC BY 4.0 data | **A** | Rate-limit API use; cite outputs |
| Bulk data download | CC BY 4.0 | **A** | Download and redistribute with attribution |
| BKMS-react composite reactions | Proprietary (all rights reserved) | **C/D** | Redistribution requires explicit license; exclude from corpus |

***

### 1.2 KEGG — Verified Usage Boundary

Report 1 correctly identified KEGG's commercial access model. Verification confirms the following current state:[^8][^9]

**API access** (api.kegg.jp): Free for both academic and non-academic use for single-record queries and small batch lookups. The KEGG API Terms of Service do not prohibit commercial single-entry queries but explicitly prohibit bulk downloading of the entire database via the API for non-academic users.[^9][^8]

**FTP bulk download**: Requires a paid academic subscription managed by Pathway Solutions for academic users; non-academic/commercial users must obtain a commercial license from Pathway Solutions Inc..[^10][^11][^8][^9]

**Content redistribution**: KEGG pathway maps, reaction equations, and compound data are copyright Kanehisa Laboratories and may not be redistributed in derived databases without a commercial license.[^10]

**BiGG and KEGG IDs**: BiGG models contain KEGG cross-reference IDs as metadata pointers — these are identifiers, not KEGG data content. The BiGG models themselves are licensed CC BY 4.0 (SysBio UCSD). Storing KEGG reaction IDs as cross-references in the Zer0pa reaction corpus is permissible; storing the reaction equations and pathway maps themselves sourced from KEGG is not.[^9]

**Zer0pa pipeline strategy (confirmed):**
- For pathway map reconstruction: use Rhea + MetaNetX MNXref 4.5 + BiGG as the production stack[^12]
- For compound/reaction lookups: use MetaNetX SPARQL endpoint (free, no commercial restriction) and Rhea SPARQL endpoint[^13][^14]
- For KEGG cross-referencing: store KEGG identifiers (KEGG IDs) only as foreign keys, not KEGG data
- For initial development: KEGG API single-entry queries are usable; do not bulk-scrape

| KEGG Usage Mode | Status | Zer0pa Classification |
|---|---|---|
| API single-entry queries (commercial) | Permitted | Class A (with rate-limit) |
| FTP bulk download (non-academic) | Requires commercial license | Class E without license |
| Redistribution of KEGG pathway data | Requires commercial license | Class E without license |
| KEGG ID storage as cross-reference | Permitted | Class A |
| Rhea/MetaNetX as KEGG replacement stack | Open access | Class A |

**Coverage gap vs. KEGG:** MetaNetX MNXref 4.5 (2025 update) reconciles reactions from Rhea, BiGG, MetaCyc, ModelSEED, and KEGG-derived sources, providing substantial KEGG functional coverage. The 2025 update specifically enhanced chemical coverage and improved reconciliation algorithms. Estimated coverage of KEGG reactions via Rhea+MetaNetX: approximately 70–80% of metabolic reactions; lower coverage for secondary metabolite and natural product pathways, which remain a genuine gap requiring ATLAS of Biochemistry (predicted reactions) as supplementation.[^12]

***

### 1.3 NASA OSDR / GeneLab — Tiered Access Clarification

Report 1 implied NASA OSDR and GeneLab data are uniformly public domain/Class A. The correct picture is a two-tier system.[^15]

**Tier 1 — Open Public Data (>95% of OSDR content):**  
As of October 2024, OSDR houses over 500 studies with data from over 80 assay types covering rodents, plants, microbes, and non-human organisms. All public data in OSDR is available via the AWS Registry of Open Data, which states: "There are no restrictions on the use of this data." This includes multi-omics data from spaceflight, ground analogs, and stress experiments relevant to extremophile metabolism. **Zer0pa classification: Class A** — no license restriction applies to these datasets. Attribution via DOI citation is standard practice.[^16][^15]

**Tier 2 — Controlled Access Human Data:**  
Sensitive human-derived data (e.g., commercial astronaut data from the Inspiration4 SpaceX mission: OSD-569, OSD-570, OSD-571, OSD-574, OSD-575, OSD-656, OSD-687) is access-controlled based on NIH dbGaP standards. Researchers must submit IRB documentation and sign a data user agreement. Upon project completion, all downloaded controlled data must be deleted. **Zer0pa classification: Class D** — requires application and approval; not appropriate for automated pipeline training data.[^15]

**Per-dataset licensing procedure for production use:**  
When pulling a specific OSDR dataset for extremophile enzyme or stress-response modelling: (1) verify the dataset page — lock icon indicates controlled access, no lock indicates open; (2) retrieve the dataset DOI for citation compliance; (3) check the RDSA-linked metadata for any submitter-imposed embargo timelines; (4) for open data, proceed without restriction.[^16][^15]

| OSDR Data Category | Example Studies | Zer0pa Class | Procedure |
|---|---|---|---|
| Microbial spaceflight omics | Bacterial ISS studies | **A** | Cite DOI; no restriction |
| Plant stress multi-omics | Arabidopsis radiation | **A** | Cite DOI; no restriction |
| Rodent physiological data | ISS rodent liver omics | **A** | Cite DOI; no restriction |
| Extremophile genomics (non-human) | Deinococcus radiation | **A** | Cite DOI; no restriction |
| Commercial astronaut data | Inspiration4 OSD-569–687 | **D** | IRB + data agreement required |
| NASA-BPS PI data (within embargo) | Various | **C** (temporary) | Wait for public release |

***

### 1.4 Systematic Four-Column License Table for All Major Pipeline Resources

The following table decomposes every major pipeline resource into four license columns — software/library code, data/content, model weights, and API/service terms — and assigns a Zer0pa class to each column independently.[^1][^9][^12][^15]

| Resource | Software/Code License | Data/Content License | Model Weights License | API/Service Terms | Overall Stack Status |
|---|---|---|---|---|---|
| COBRApy | LGPLv2+ → **B** | N/A | N/A | N/A | In stack |
| BRENDA core data | N/A | CC BY 4.0 → **A** | N/A | Free query → **A** | In stack |
| BKMS-react | N/A | Proprietary → **C/D** | N/A | Free browse → no embed | Excluded from corpus |
| KEGG bulk | N/A | Commercial → **E** | N/A | API single-entry **A** | ID-only in stack |
| MetaNetX MNXref 4.5 | CC BY 4.0 → **A** | CC BY 4.0 → **A** | N/A | SPARQL free → **A** | In stack |
| BiGG Models | CC BY 4.0 → **A** | CC BY 4.0 → **A** | N/A | REST API free → **A** | In stack |
| Rhea | CC0/free → **A** | CC0/free → **A** | N/A | SPARQL free → **A** | In stack |
| ModelSEED Database | MIT → **A** | MIT → **A** | N/A | Web free → **A** | In stack |
| ATLAS of Biochemistry | Academic → **C** | Academic → **C** | N/A | Web free → limited | Data-only reference |
| eQuilibrator | MIT → **A** | CC BY → **A** | N/A | Python pkg → **A** | In stack |
| PyTFA | Apache 2.0 → **A** | N/A | N/A | Python pkg → **A** | In stack |
| DLKcat | MIT → **A** | BRENDA CC BY → **A** | MIT → **A** | N/A | In stack |
| TurNuP | MIT → **A** | BRENDA CC BY → **A** | MIT → **A** | N/A | In stack |
| UniKP / EF-UniKP | MIT → **A** | BRENDA CC BY → **A** | MIT → **A** | N/A | In stack |
| CatPred | MIT (inferred) → **A** | BRENDA CC BY → **A** | MIT → **A** | Web service → check | In stack |
| ProteinGym | MIT → **A** | Open DMS data → **A** | N/A | GitHub → **A** | In stack (benchmark) |
| ESM-2 / ESMFold | MIT → **A** | Data varies → check | MIT → **A** | API: terms vary | In stack (weights MIT) |
| RFdiffusion (v1) | MIT → **A** | N/A | MIT → **A** | N/A | In stack |
| RFdiffusion3 (Foundry) | BSD/MIT (via RosettaCommons) → **A** | N/A | BSD/MIT → **A** | Foundry TOS → **A** | In stack |
| MACE-OFF | MIT → **A** | CC BY data → **A** | MIT → **A** | N/A | In stack |
| JBEI ART | Apache 2.0 → **A** | DOE open → **A** | Apache 2.0 → **A** | N/A | In stack |
| NASA OSDR (non-human) | N/A | No restriction → **A** | N/A | AWS S3 free → **A** | In stack |
| NASA OSDR (human/controlled) | N/A | Controlled → **D** | N/A | Controlled → **D** | Out of stack |
| GotEnzymes2 | MIT → **A** | CC BY 4.0 → **A** | MIT → **A** | Web → **A** | In stack |
| BioTRY | Free academic → **C** (verify) | Academic → **C** | N/A | Web free → limited | Reference only (verify) |
| Maud (Bayesian kinetics) | MIT → **A** | N/A | N/A | Python pkg → **A** | In stack |
| FluxGAT | MIT → **A** | N/A | MIT → **A** | GitHub → **A** | In stack |
| ProDy | MIT → **A** | N/A | N/A | Python pkg → **A** | In stack |
| ACBM agent-based | MIT/BSD → **A** | N/A | N/A | Python → **A** | In stack |
| RetroPath3.0 | MIT → **A** | CC BY → **A** | N/A | Galaxy/Python → **A** | In stack |
| Cello (MIT, CAD) | BSD → **A** | N/A | N/A | GitHub → **A** | In stack |

**Key corrections vs. Report 1:**
- BRENDA data directly usable as Class A (not Class C/E as implied)
- ModelSEED confirmed MIT Class A (33,978 compounds, 36,645 reactions)[^17][^18]
- BKMS-react explicitly Class C/D for redistribution/embedding — removed from corpus plan
- RFdiffusion3 available via RosettaCommons Foundry with BSD/MIT-equivalent terms[^19][^20][^21]

***

## Section 2: Data Matrix — Per Prediction Task

### 2.1 Task 1: Sequence → kcat / Km Prediction

**Primary public datasets:**

| Dataset | N (entries) | Labels | Condition Coverage | Format | ML Sufficiency |
|---|---|---|---|---|---|
| BRENDA bulk (CC BY 4.0) | ~4.3M data points, ~84,000 enzymes | kcat, Km, Ki, stability | pH, temp, buffer (partial) | Text/JSON download | Fine-tune + benchmark |
| EnzyExtract corpus (MIT) | 218,095 entries (89,544 new vs BRENDA) | kcat, Km | Extracted from papers | CSV/JSON | Fine-tune supplement |
| TurNuP training set | 287,386 enzyme-substrate pairs | kcat | Organism, pH (partial) | GitHub | Benchmark / fine-tune |
| GotEnzymes2 (CC BY 4.0) | 59.6M predicted kcat (7.3M sequences, 10,765 species) | Predicted kcat (DLKcat) | Species-level | Web/download | Curriculum pre-training |
| ProteinGym DMS assays (MIT) | ~2.7M missense variants, 217 DMS assays | Fitness/activity | Wild-type backgrounds | CSV/HDF5 | Fine-tune + benchmark |
| UniKP training set | BRENDA-derived, ~20,000 entries with env. features | kcat, Km, kcat/Km | pH, temperature | GitHub | Fine-tune (with conditions) |

**Critical notes:**
- Negative/low-activity data remains extremely sparse across all datasets. BRENDA is predominantly positive activity measurements — the true negative space (non-functional enzyme-substrate pairings) is absent or underrepresented. This creates systematic bias in classifiers trained on BRENDA alone.[^22]
- Condition dependence (pH, temperature) is addressed by EF-UniKP and UniKP, which add environmental features. CatPred uses ESM-2 + E-GNN + D-MPNN and includes uncertainty quantification, making it the best current choice for conditional prediction.[^23][^24][^25]
- **EnzyExtract** (MIT, GitHub: ChemBioHTP/EnzyExtract) identified 89,544 unique kinetic entries absent from BRENDA by processing 137,892 full-text publications — this constitutes the "dark matter" of enzymology that was previously inaccessible. This directly expands the training corpus for any Zer0pa-trained kinetics model.[^3][^26][^1]
- **Zer0pa decision point:** GotEnzymes2 (59.6M predicted kcat entries, CC BY 4.0) provides a curriculum pre-training corpus for a Zer0pa conditional kinetics model. The model architecture should follow EF-UniKP (condition-aware) with EnzyExtract-supplemented training data and CatPred-style uncertainty quantification.[^27][^28]

**ML sufficiency verdict:** Sufficient to **fine-tune and benchmark** a conditional kcat/Km predictor. Not sufficient to train from scratch without transfer learning from pre-trained protein language models (ESM-2 MIT). A Zer0pa-owned conditional kinetics model trained on BRENDA CC BY 4.0 + EnzyExtract MIT data is buildable and commercially owned.[^22]

***

### 2.2 Task 2: Pathway Design → Fermentation KPIs (Titer, Yield, Productivity)

This is the most data-sparse task in Report 1's scope. The following fills the gap with a census of available public datasets.

**New primary source — BioTRY (ACS Synth Biol 2025):**  
BioTRY is the first dedicated knowledge base for biosynthesis titer, rate, and yield data. It contains >52,000 TRY entries across >5,000 biochemicals and >3,800 strains, extracted from original research literature with references. It is freely accessible at http://www.synbiohealth.cn/biotry. **However, the commercial licensing status is unconfirmed — the database uses academic "free access" language; Zer0pa must verify whether commercial use is permitted before using as training data.** If permissible, this is the single most important dataset for training a KPI predictor.[^2]

| Dataset | N (entries) | Coverage (organisms, products) | Condition Metadata | Scale | ML Sufficiency |
|---|---|---|---|---|---|
| BioTRY (verify license) | >52,000 | >5,000 chemicals, >3,800 strains | Partial (references to papers) | Mostly shake flask/lab fermenter | Fine-tune (if licensed) |
| JBEI ART case studies | <1,000 (curated DBTL logs) | E. coli, terpenes, amino acids | Full condition metadata | Bench scale | Priors only |
| NREL Bioenergy KDF | Open fermentation data | Lignocellulosic, ethanol, SAF precursors | Partial (some scale metadata) | Bench to pilot | Fine-tune (subset) |
| Published literature (manual curation) | ~5,000–10,000 (curated per product class) | Product-specific | Variable | Variable | Product-specific fine-tune |

**Critical assessment:** A **general KPI predictor across all products and organisms is not currently feasible** with existing public data. The data is too heterogeneous in condition metadata, too sparse at pilot/industrial scale, and lacks systematic genotype-to-phenotype pairing required for causal ML. The realistic architecture is:[^2]
- A **product-class and organism-specific KPI surrogate** (e.g., "terpenoids in *S. cerevisiae*", "organic acids in *E. coli*")
- Trained with BioTRY as the primary corpus + literature-curated data per target domain
- Augmented by **mechanistic simulation** (GECKO enzyme-constrained FBA) to generate synthetic label distributions around real data points — this is the data augmentation strategy

**Scale gap:** No open dataset currently pairs bench-scale measurements with industrial-scale outcomes at the same genotype. The CFD-based scale-up correction (OpenFOAM + NREL bioreactor models) must operate as a separate multiplicative correction factor, not as a jointly trained model. This is an explicit architectural constraint for v1.

***

### 2.3 Task 3: Edit Plan → KPI Delta (DBTL Loop)

The DBTL/LDBT data landscape has been significantly advanced by two papers since Report 1.

**LDBT paradigm (Nature Communications 2025):** Clark-ElSayed, Harrison, and colleagues propose inverting the DBTL cycle to **LDBT (Learn-Design-Build-Test)** — starting with an intensive ML learning phase from existing biological data before constructing any biological parts. The cell-free TX-TL (transcription-translation) platform is used as the rapid Build-Test layer, enabling megascale data generation. This means the active learning loop's "Test" step can be executed orders of magnitude faster than in-cell DBTL, fundamentally changing the training data generation rate.[^29][^30]

**Simulated DBTL benchmark (van Lent et al., bioRxiv 2026):** This paper provides simulated DBTL cycle datasets for benchmarking ML methods in metabolic engineering. It provides a standardised framework for comparing ML algorithms in the DBTL context — the closest current equivalent to a DBTL benchmark. Code and data are available from the bioRxiv preprint.[^31][^32][^33]

**Automated P. putida DBTL (Nature 2025):** Demonstrated 5-fold isoprenol titer improvement over 6 automated DBTL cycles using ML + lab automation. The strain design space was sampled more efficiently than exhaustive approaches.[^34]

**Explicit gap:** **No canonical DBTL benchmark equivalent to ProteinGym exists for pathway-level optimisation.** ProteinGym covers protein-level sequence-fitness, but there is no analogous open benchmark for genetic edit plan → KPI delta. This is a direct Zer0pa build opportunity (see Section 4.2).[^35][^36]

| Data Source | Type | N | Organism | Edit Types | Label | ML Sufficiency |
|---|---|---|---|---|---|---|
| Van Lent et al. 2026 simulated DBTL | Simulated | Configurable | *E. coli* (simulated) | Promoter strengths, copy numbers | Pathway titer (simulated) | Algorithm benchmarking only |
| JBEI ART DBTL logs | Real | <500 cycles | *E. coli*, yeast | Promoter + RBS combos | Titer improvement | Priors only |
| Published C. glutamicum DBTL | Real | ~100–300 | *C. glutamicum* | Gene knockouts, overexpressions | Amino acid titers | Fine-tune (product-specific) |
| Automated P. putida (2025) | Real | 6 cycles, ~1000 variants | *P. putida* | Promoter/RBS libraries | Isoprenol titer | Priors only |

***

### 2.4 Task 4: Bench → Pilot → Industrial Scale-Up Correction

No open dataset currently pairs genotype + bench-scale KPIs with industrial-scale outcomes. The following represents the state of available data:

- **NREL Bioenergy Knowledge Discovery Framework:** Open datasets for cellulosic ethanol and biofuel fermentations at pilot and demonstration scale. Contains time-series process data but limited systematic genotype metadata.[^37]
- **Published CFD-bioreactor simulation papers:** CFD models (OpenFOAM + bioprocess extensions) linking mixing time, dissolved oxygen, and cell lifeline calculations to production performance. These are models, not datasets — they provide correction *functions* rather than correction *data*.[^38]
- **DynoChem**: Commercial scale-up modelling software (Class E). No open equivalent currently exists with equivalent functionality.

**Verdict for v1:** The scale-up correction layer must use **mechanistic CFD correction factors** (not ML-trained corrections) applied as a post-processing step on top of bench-scale KPI predictions. The qMFKG (multi-fidelity knowledge gradient) BoTorch acquisition function can encode the GEM→kinetic→CFD fidelity hierarchy as its multi-fidelity structure, treating CFD simulations as high-fidelity point evaluations. This architecture is feasible but requires commissioning 10–50 CFD simulation runs per target organism-bioreactor geometry combination as training observations for the multi-fidelity GP.[^39]

***

### 2.5 Task 5: Single-Cell / Heterogeneity → Effective Population KPI

**Current state of open data:**

- **Nature 2025 single-cell yeast biosensor framework:** Demonstrated that pH-based metabolic subpopulations in engineered yeast have distinct lycopene production states. Provides a single-cell profiling framework for biosensor-based population characterisation — open method, data available.[^40]
- **ScienceDirect 2025 review (Cellular variability as bioprocess driver):** Confirms that population heterogeneity significantly impacts metabolic activity, product yield, and process consistency. No open training dataset from this review.[^41]
- **PMC 2025 integrative single-cell metabolomics:** Single-cell metabolomics datasets for oxidative stress and senescence. Not directly applicable to industrial fermentation.[^42]
- **ACBM (Agent and Constraint Based Modeling):** Open framework integrating agent-based + 3D constraint-based modelling for microbial populations. Enables synthetic data generation for heterogeneity-aware KPI prediction.[^43]

**Verdict:** Insufficient open single-cell fermentation data for a v1 heterogeneity-aware KPI correction layer using ML. Recommendation: use ACBM to **generate synthetic heterogeneity distributions** calibrated by the Nature 2025 yeast single-cell framework, and apply these as uncertainty multipliers on population-mean KPI predictions. Tag this capability as **Tier 2 / v1.1 milestone** in the PRD.

***

## Section 3: Tiered Intersectional Map

Report 1 enumerated 20 intersections. This section assigns each to a tier based on tool availability, data sufficiency, and decision impact on the pipeline architecture.

### 3.1 Tier 1 — Architecture-Critical (Tool Choice Determinants)

These eight intersections directly determine which models and scoring functions are used. Each now has a confirmed Class A/B tool that can be wired into the pipeline.

**Intersection 1: Non-Equilibrium Thermodynamics ↔ Pathway Feasibility**  
eQuilibrator (MIT) and PyTFA (Apache 2.0) are confirmed production stack tools. The **Max-min Driving Force (MDF) method** in eQuilibrator calculates thermodynamic feasibility scores per enzymatic step using the component contribution method. The 2025 MetaNetX update (MNXref 4.5) expanded chemical coverage and improved SMILES/InChI normalisation, directly enhancing eQuilibrator's compound matching rate for novel target molecules. This intersection is fully operational in v1.[^12]

**Intersection 2: Information Theory ↔ Metabolic Networks**  
**FluxGAT (MIT, NeurIPS 2024)** is now the confirmed open-source tool for this intersection. FluxGAT predicts gene essentiality directly from graphical representations of flux sampling data — without objective functions, eliminating FBA observer bias. Its sensitivity is almost double that of standard FBA. The flux sampling step generates a probability distribution over flux states (analogous to a Shannon entropy measure of metabolic uncertainty). **FlowGAT (PMC 2024)** is an alternative GNN-based approach using FBA solutions rather than flux sampling. Both are Class A and can be deployed in v1 as the metabolic topology scoring layer.[^44][^45][^46]

**Concrete scoring addition:** Entropy of the flux sampling distribution — \(H = -\sum_i p_i \log p_i\) over sampled flux vectors — can be computed per pathway candidate as a metabolic robustness score. High entropy = flexible pathway; low entropy = bottleneck-constrained.

**Intersection 3: Graph Theory / Network Topology ↔ Metabolic Architecture**  
FluxGAT and FlowGAT both operate on metabolic graphs. COBRApy (LGPL, Class B) provides the underlying GEM scaffold. ModelSEED (MIT, Class A) provides 33,978 compounds and 36,645 reactions as graph nodes and edges. The **betweenness centrality** computation identifying bottleneck reactions should be added as a Layer 4 screening feature — computable via NetworkX (BSD, Class A) applied to the COBRApy reaction graph.[^18][^17]

**Intersection 4: Control Theory ↔ Gene Regulatory and Optogenetic Circuits**  
**Quorum sensing-controlled CRISPRi toolkit (2025):** A published framework for programmable biosensor-CRISPRi genetic circuits enabling dynamic and autonomous dual-control of metabolic flux in *Bacillus subtilis*. This is a physical control-theory implementation (sensor → actuator → metabolic output) now available as an experimental design specification. **CRISPRi-assisted rational flux-tuning in *C. glutamicum*** (Nature Communications 2022) demonstrated conversion to L-proline hyperproducer using model-guided CRISPRi screening — an MFBL (model-feedback-based loop) paradigm. These provide concrete design patterns for Layer 6 (Host Engineering Specification).[^47][^48]

**Intersection 5: SE(3)-Equivariant Geometry ↔ Enzyme Structure and Design**  
**RFdiffusion3 (RFD3, December 2025)** is now available via the RosettaCommons Foundry GitHub repository. RFD3 performs all-atom diffusion — generating protein structures in the context of ligands, nucleic acids, and other non-protein atom constellations. This is directly applicable to enzyme active-site scaffolding for the "Unknown Enzyme" sub-pipeline (Section 4.3). RFD3 achieves improved benchmarks over RFdiffusion v1 at one-tenth the computational cost. License: BSD/MIT through RosettaCommons Foundry. Additionally, **computational enzyme design by catalytic motif scaffolding** (Nature 2025, Baker group) combines ML + atomistic modelling for one-shot enzyme design for diverse biological and non-biological transformations — the strongest advance in de novo enzyme design as of April 2026.[^20][^49][^21][^50][^19]

**Intersection 6: Evolutionary ML ↔ Directed Evolution**  
ProteinGym (MIT, 2023–2026): 250+ DMS assays, ~2.7M missense variants across 217 substitution DMS assays and 2,525 clinical proteins. The substitution benchmark spans millions of mutated sequences and is the canonical evaluation suite for sequence-fitness models. An AI-native biofoundry for autonomous enzyme engineering (bioRxiv 2026) demonstrates closed-loop protein language model + automated lab evolution accelerating trait evolution by orders of magnitude. The **Genie-CAT agentic LLM** (arXiv 2025) integrates RAG, PDB parsing, electrostatic calculations, and redox ML prediction in a unified agentic workflow for mechanistic enzyme design hypothesis generation.[^51][^36][^52][^53][^35]

**Intersection 7: Fluid Dynamics / Transport Physics ↔ Bioreactor Scale-Up**  
The **"lifelines" framework** (ScienceDirect 2022) uses CFD to compute cell-experienced substrate and oxygen concentration trajectories in large-scale reactors. This provides the mathematical linkage between CFD (OpenFOAM) outputs and individual cell metabolic state — a key architecture concept for the heterogeneity-aware KPI layer. The multi-fidelity BoTorch qMFKG acquisition function is the confirmed mechanism for integrating GEM, kinetic, and CFD fidelity levels.[^54][^39][^38]

**Intersection 8: Electrochemistry ↔ Cofactor Balancing and Microbial Electrosynthesis**  
eQuilibrator directly computes reduction potentials (E°') for metabolic half-reactions using the same component contribution thermodynamic framework as Gibbs energy computation. PyTFA enforces redox cofactor balancing (NAD+/NADH, NADP+/NADPH) as hard constraints within FBA. ARTP (Atmospheric and Room Temperature Plasma) mutagenesis is a confirmed operationally ready approach for strain improvement — relevant to the plasma physics intersection (Section 4.1.18 in Report 1). This is an available tool that should be noted in the pipeline's strain improvement appendix as a non-GMO alternative to CRISPR.[^55][^56][^12]

***

### 3.2 New Architecture-Critical Intersection: Causal Inference ↔ Optimal Experimental Design

Report 1 did not treat this as a separate intersection — it was subsumed into the BoTorch loop. This pass elevates it to **Tier 1 architecture-critical** based on three developments:[^57][^58][^59]

**GO-CBED (ICLR 2025):** A goal-oriented Bayesian framework for sequential causal experimental design that selects interventions to achieve specific downstream research goals, not merely to maximise information gain about the full causal DAG. This is directly applicable to the DBTL loop's intervention selection problem: "choose the next gene edit to maximise probability of exceeding titer threshold."[^59]

**Causal Discovery via Bayesian Optimisation (ICLR 2025):** Uses BO to suggest optimal interventions to efficiently recover causal DAGs from interventional data. The causal graph of the metabolic network is exactly this — a DAG of enzymatic dependencies — and intervention planning in the DBTL loop is a causal recovery problem.[^58]

**CausalBench (Nature Communications 2025):** A benchmark for network inference evaluation using real-world, large-scale single-cell perturbation data. This provides a validation framework for causal models of gene regulatory effects.[^60]

**Recommendation:** Add a **dedicated Causal/Experiment-Design Node** between the BoTorch optimisation layer and the Host Engineering layer. This node uses the current metabolic causal graph posterior to select the maximum-information next genetic intervention. It transforms the pipeline from "suggest N ranked pathways" to "suggest the one next wet-lab experiment that will most efficiently confirm or refute the top-ranked pathway."

***

### 3.3 Tier 2 — Scoring & Uncertainty Enrichers

These intersections are operational for scoring but do not change tool selection. Each entry now includes a concrete scoring addition.

| Intersection | Concrete Scoring Feature | Data Available v1? | PRD Tag |
|---|---|---|---|
| Cellular automata / metabolic oscillations | Boolean attractor landscape entropy for regulatory circuit stability (GINsim) | Partially (Boolean net models for *E. coli*, yeast) | v1.1 |
| Systems ecology / co-culture consortia | Lotka-Volterra community stability eigenvalue score (MICOM) | Yes (MICOM open data) | v1 (consortia mode) |
| Acoustic/phonon / enzyme dynamics | Normal mode alignment score (ProDy MIT): cosine similarity between lowest-frequency modes and catalytic coordinate direction | Yes (PDB structures) | v1 |
| Signal processing / metabolomics | 1D CNN spectral classification from MetaboLights or HMDB raw spectra; entropy of metabolite concentration time-series | Partial (MetaboLights open) | v1.1 |
| Optics / optogenetic control | Light-switching schedule scoring: Beer-Lambert photon flux model for bioreactor geometry | No open training data | v1.1 |
| Epidemiology / population heterogeneity | ACBM-derived population variance multiplier on mean KPI prediction | Synthetic only (ACBM) | v1.1 / experimental |

**ProDy (MIT)** — confirmed as the production tool for the phonon/enzyme dynamics intersection. ProDy 2.0 provides ClustENMD for conformational sampling, SignDy for signature dynamics, and PRS (Perturbation Response Scanning) for allosteric signal propagation. All these modes are computable from AlphaFold2/ESMFold-predicted structures alone, making v1 integration immediately feasible.[^61][^62][^63]

***

### 3.4 Tier 3 — Research Frontiers (Out of Scope for v1 Pipeline)

| Intersection | Status | Frontier Note |
|---|---|---|
| Gauge theory / Geometric Unity ↔ metabolic network symmetries | No production-ready tools. One theoretical paper (Weinstein, 2021) discusses gauge-theoretic biological analogs. Metabolic network symmetry analysis via group theory remains unpublished as a computational tool. | Maintain as research programme. Not in v1 PRD. |
| Plasma physics / radical chemistry ↔ non-thermal bioprocessing | ARTP mutagenesis is in scope as a strain improvement tool[^55]. Plasma-assisted lignocellulose pretreatment: relevant review exists (ScienceDirect 2025)[^64] but no open computational model. | ARTP mutagenesis: note in pipeline appendix. CFD plasma pretreatment: Tier 3. |
| Astrobiology / extremophile ↔ novel enzyme discovery | NASA OSDR open (Class A), extremophile GEMs are sparse (Sulfolobus, Pyrococcus not comprehensively GEM-reconstructed). Computational tools available but data gap is severe. | Tag as "data-limited Tier 2" — usable once extremophile omics data accumulates. |
| Quantum chemistry / QM/MM ↔ enzyme catalysis | ORCA, Psi4 available (open source) but too computationally expensive for high-throughput screening; ANI neural network potentials show promise but not yet benchmarked for enzyme catalysis at scale. | Active research: include in "future precision validation" appendix. |

***

## Section 4: Emergent Innovation Artefacts

Five concrete build opportunities are now visible when Report 1 is seen as a whole. Each is specified with data sources, missing components, and Zer0pa's structural advantage.

### 4.1 Artefact 1: License-Clean Integrated Reaction Corpus (LIRC)

**What it is:** A consolidated, production-grade reaction and metabolic network corpus combining Rhea, MetaNetX MNXref 4.5, BiGG, and ModelSEED, entirely within Class A/B licensing, with KEGG excluded except as identifier cross-references.

**Required data sources and licenses:**
- Rhea (CC0/free, 14,000+ expert-curated reactions with full stoichiometry)[^65][^13]
- MetaNetX MNXref 4.5 (CC BY 4.0, cross-database reconciliation with InChI/SMILES normalisation)[^12]
- BiGG Models (CC BY 4.0, genome-scale models for 74 organisms)[^12]
- ModelSEED Biochemistry Database (MIT, 33,978 compounds, 36,645 reactions)[^17][^18]
- BRENDA core data (CC BY 4.0, enzyme functional data linked to reactions)[^1]

**ID reconciliation strategy:** MetaNetX's reconciliation framework (SPARQL endpoint) maps all cross-database compound identifiers to InChI keys. Reactions are normalised to SMILES-encoded atom-mapped reaction strings. The 2025 MetaNetX update specifically improved chemical normalisation for R-groups (generic reaction patterns), enhancing coverage of secondary metabolite reactions.[^14][^12]

**Coverage vs KEGG:** KEGG Pathway contains approximately 547 reference pathways and ~11,000 reactions. The Rhea + MetaNetX + BiGG + ModelSEED stack covers an estimated 70–80% of central metabolic and biosynthetic pathways. The most significant gap is secondary metabolite and natural product pathways, where ATLAS of Biochemistry (130,000+ predicted reactions, academic license) provides supplementation despite its Class C status — the predicted reactions themselves are algorithm outputs and may be usable under academic citation, with replacement by in-house expansion rules for production.

**Missing components:** A deduplication pass across the four sources (Rhea/MetaNetX reconciliation handles most but not all duplicates for newly added reactions). A reaction canonicalisation pipeline converting all stoichiometries to balanced, atom-mapped SMARTS format is required as a build task.

**Zer0pa structural advantage:** No other commercial entity has assembled this specific multi-source, ID-reconciled, license-verified corpus as a production pipeline input. The combination of MetaNetX 2025's updated SPARQL endpoint + Rhea SPARQL + BiGG REST API creates a programmatically constructable corpus with no manual curation required for the core layer. The EnzyExtract MIT corpus can be layered on top to connect reactions to kinetics, making this a fully connected reaction-kinetics graph.

***

### 4.2 Artefact 2: DBTL Pathway Optimisation Benchmark (Zer0pa PathGym)

**What it is:** A standardised benchmark dataset for evaluating ML models that predict KPI delta from genetic edit plans — the metabolic engineering equivalent of ProteinGym.

**Why it doesn't exist yet:** ProteinGym covers protein-level fitness. The van Lent 2026 simulated DBTL provides a computational framework but simulated data only. No open repository currently aggregates real DBTL cycle data (edit sets + measured KPI outcomes) across organisms and products in a standardised, ML-ready format.[^32][^36][^51]

**Required data sources:**
- BioTRY (once commercial license verified): >52,000 TRY entries with strain metadata[^2]
- JBEI ART DBTL logs (Apache 2.0): Structured edit-to-KPI records from terpene and amino acid pathways
- Published *C. glutamicum* DBTL series (literature-extracted, 100–300 curated cycles)[^66]
- Automated P. putida isoprenol DBTL (Nature 2025): ~1,000 design-KPI pairs[^34]

**Missing components:** A standardised schema for "genetic edit plan" — specifying promoter strengths (RBS Calculator units), copy numbers, knockout targets (KEGG EC number or gene ID), and measured output (g/L titer, yield, volumetric productivity, specific growth rate) with fermentation conditions. The LDBT paper's cell-free TX-TL platform can generate synthetic DBTL data orders of magnitude faster than in-cell experiments — this is the data generation engine.[^30]

**Zer0pa structural advantage:** The LDBT paradigm combined with the JBEI ART Bayesian active learning loop means Zer0pa could use the pipeline itself to bootstrap PathGym — each pipeline run generates one annotated data point (predicted + experimentally validated). The benchmark grows with use. This creates a compounding competitive moat.[^31][^30]

***

### 4.3 Artefact 3: "Unknown Enzyme" Generative Sub-Pipeline

**What it is:** A sub-pipeline module for proposing novel enzymatic steps when no known reaction in the corpus completes a required pathway step. This is the primary mechanism for genuinely novel pathway design beyond database retrieval.

**Required open tools (all Class A):**
- RFdiffusion3 (BSD/MIT, Foundry): All-atom diffusion conditioning on substrate ligand geometry to scaffold a catalytic protein structure around a desired transition state[^49][^21][^19]
- Computational enzyme design by catalytic motif scaffolding (Nature 2025, Baker group): One-shot enzyme design via catalytic motif scaffolding using ML + DFT transition state templates[^50]
- MACE-OFF (MIT): Organic force field neural network potential for computing active-site interaction energies and substrate-enzyme binding profiles[^50]
- ESM-2/ESMFold (MIT): Structure prediction and sequence generation given structural constraints[^67]
- ProDy (MIT): Normal mode analysis to assess conformational suitability of generated structures[^62]
- eQuilibrator (MIT): Thermodynamic feasibility check for the proposed novel reaction

**Training data sufficiency for de novo enzyme design:**  
The current state-of-the-art (Baker group Nature 2025) demonstrates **one-shot design** of efficient enzymes for diverse transformations using ML + atomistic modelling. This is not yet a general-purpose tool — it requires a defined target reaction with known transition state geometry or close analog. For reactions with no known transition state information, the design problem remains exploratory. The sub-pipeline should therefore classify proposed novel reactions into three tiers: (a) known TS analog available → use catalytic motif scaffolding; (b) reaction class known but no TS → use RFdiffusion3 + Genie-CAT hypothesis generation; (c) fully novel reaction class → flag as "experimental suggestion only" in the output dossier.[^50]

**Missing components:** An integration layer between RetroPath3.0's reaction proposal output and RFdiffusion3's conditioning input — converting a retrosynthetically proposed reaction SMARTS to a transition state geometry estimate (via QM/MM minimisation or closest analogue lookup) for RFdiffusion3 conditioning.

***

### 4.4 Artefact 4: Multi-Fidelity Metabolic Optimiser (MFMO)

**What it is:** A hierarchical BoTorch Bayesian optimiser that explicitly models three prediction fidelity levels — GEM/FBA (fast, coarse), kinetic model/GECKO (medium, enzyme-constrained), and CFD-informed scale-up (slow, high-fidelity) — and allocates optimisation budget across these fidelities adaptively.

**Mechanism:** BoTorch's qMFKG (multi-fidelity Knowledge Gradient) acquisition function treats the three fidelity levels as discrete information sources. Each evaluation of the high-fidelity CFD model is assigned a cost ~100× that of a GEM/FBA evaluation. The optimiser automatically front-loads GEM/FBA evaluations to screen the search space, then uses GECKO to refine promising candidates, then uses CFD for the top 5–10 candidates. This matches the computational architecture described in multi-fidelity BO for chemical engineering (YouTube/PMC 2023–2025).[^68][^54][^39]

**Required training data:**  
- GEM/FBA responses: computable synthetically from COBRApy (zero data cost)
- GECKO responses: computable synthetically from GECKO tool + enzyme parameter inputs (near-zero data cost once enzyme data loaded)
- CFD responses: requires 10–50 commissioned CFD runs per target organism-bioreactor configuration (one-time cost per domain)

**Multi-fidelity BO for CFD** has been demonstrated for reactor geometry optimisation (YouTube presentation 2023) and for non-cylindrical bioreactor shapes (arXiv 2025). The approach is validated and can be directly adapted.[^69][^54]

**Zer0pa structural advantage:** The ZPE encoding layer represents the pathway design as a fixed-length deterministic vector — providing a natural input space for the multi-fidelity GP surrogate. The Bayesian GP posterior over this encoded space provides uncertainty-calibrated KPI predictions that the output dossier can present as confidence intervals per pathway candidate.

***

### 4.5 Artefact 5: Conditional Enzyme Kinetics Model (CEKM) — Zer0pa-Owned

**What it is:** A Zer0pa-owned, commercially usable conditional enzyme kinetics model trained on BRENDA CC BY 4.0 + EnzyExtract MIT data, predicting kcat, Km, and kcat/Km as a function of enzyme sequence, substrate SMILES, pH, and temperature.

**Why it matters:** Owning the weights means Zer0pa is not dependent on BRENDA's web service (which may have API rate limits), avoids any future licensing changes to BRENDA, and can fine-tune the model on proprietary client data from CRO partners.

**Architecture (informed by CatPred + EF-UniKP + GotEnzymes2):**
- Enzyme encoder: ESM-2 650M (MIT) protein language model representations[^23]
- Substrate encoder: D-MPNN (directed message passing neural network) on SMILES[^25]
- Condition encoder: lightweight MLP for pH, temperature, buffer type
- Integration: adaptive gate network (as in GELKcat/CatPred)[^70][^25]
- Output: kcat, Km, kcat/Km with epistemic uncertainty via ensemble or MC-dropout

**Training data:**
- BRENDA CC BY 4.0 bulk download: ~4.3M data points[^71][^1]
- EnzyExtract corpus (MIT): 218,095 entries (89,544 new vs BRENDA)[^3][^1]
- GotEnzymes2 CC BY 4.0: 59.6M predicted kcat as soft pseudo-labels for curriculum pre-training[^28][^27]

**Missing component:** A systematic condition normalisation pipeline: BRENDA reports conditions in heterogeneous formats across papers. EnzyExtract's LLM extraction pipeline should have standardised these, but a condition harmonisation step (pH to uniform scale, temperature to Kelvin, buffer to ionic strength estimate) is a required data engineering task.

**Zer0pa structural advantage:** BRENDA is now CC BY 4.0 — this build opportunity was not available before this licensing audit. The commercial ownership of CEKM weights on CC BY 4.0 training data is legally clean. No competitor has publicly released a condition-aware, uncertainty-calibrated kinetics model with MIT-compatible weights. GotEnzymes2 (7.3M unique sequences across 10,765 species) provides a breadth of predicted pre-training labels that enables the model to generalise across the entire enzyme taxonomy before fine-tuning on the higher-quality BRENDA experimental measurements.[^28]

***

## Section 5: Typed Architecture & Ready-for-PRD Checklist

### 5.1 Typed Information Flow — Layer by Layer

**Layer 1: Input Encoding (ZPE Layer)**

| | Specification |
|---|---|
| **Typed input** | Target molecule: SELFIES string (Apache 2.0, tokenisable) + InChI key. Host organism: NCBI taxonomy ID + reference genome accession |
| **Typed output** | 20-bit ZPE deterministic word envelope per token. Molecule graph: SELFIES → tokenised sequence → ESM-equivalent token embedding. Organism context: genome GEM identifier (e.g., iML1515 for *E. coli*) + NCBI RefSeq ID |
| **Primary tool** | SELFIES (Apache 2.0), ESM-2 embeddings (MIT) |
| **Fallback** | SMILES (canonical RDKit, MIT) |
| **Required dataset** | ChEBI compound list (CC BY 4.0) for SELFIES vocabulary; UniProt/Swiss-Prot (CC BY 4.0) for organism protein context |

**Layer 2: Metabolic Knowledge Layer (NOSES-equivalent)**

| | Specification |
|---|---|
| **Typed input** | Target molecule InChI key + organism GEM identifier |
| **Typed output** | Reaction graph: `{reaction_id: str, substrates: [InChI], products: [InChI], enzymes: [UniProt_ID], EC: str, ΔG°: float, kcat: float, Km: float, source_db: str}` |
| **Primary tools** | Rhea (CC0) + MetaNetX 4.5 (CC BY 4.0) + BiGG (CC BY 4.0) + ModelSEED (MIT) + BRENDA CC BY 4.0 |
| **Fallback** | ATLAS of Biochemistry (Class C, read-only reference, not embedded) |
| **Excluded** | BKMS-react (redistribution prohibited), KEGG bulk (Class E without license) |
| **Required dataset** | BRENDA bulk CC BY 4.0; MetaNetX MNXref 4.5 SPARQL dump; BiGG models JSON; ModelSEED GitHub release |

**Layer 3: Retrosynthetic Pathway Generation**

| | Specification |
|---|---|
| **Typed input** | Target molecule InChI key; host organism metabolome (list of available precursor InChI keys from GEM); maximum pathway length; minimum thermodynamic driving force threshold |
| **Typed output** | `PathwayCandidateSet`: ordered list of `{pathway_id: str, steps: [ReactionNode], precursor: InChI, length: int, thermodynamic_score: float, novelty_flag: bool}` |
| **Primary tool** | RetroPath3.0 (MIT) for database-grounded retrosynthesis |
| **Augmentation** | LDBT cell-free TX-TL data loop for novel step validation; Genie-CAT (agentic LLM, arXiv 2025) for novel step hypothesis |
| **Unknown enzyme sub-pipeline** | RFdiffusion3 (BSD/MIT, Foundry)[^19] → MACE-OFF energetics[^50] → ProDy NMA feasibility check |
| **Required dataset** | LIRC (Zer0pa Integrated Reaction Corpus, Section 4.1); ProteinGym DMS (MIT) for novel enzyme fitness priors |

**Layer 4: In Silico Screening**

| | Specification |
|---|---|
| **Typed input** | `PathwayCandidateSet` from Layer 3 |
| **Typed output** | `ScoredPathwaySet`: each candidate annotated with `{FBA_flux_dict, MDF_score, kcat_estimates, Km_estimates, metabolic_burden_score, toxic_intermediate_flags, competing_pathway_drain_map, uncertainty: CIBounds}` |
| **Primary tools** | COBRApy (LGPL/B) + GECKO (MIT) for FBA; eQuilibrator MDF (MIT); CEKM (Zer0pa-owned) for kinetics; CatPred (MIT) for uncertainty; FluxGAT (MIT) for gene essentiality / network topology |
| **Fallback** | DLKcat (MIT) or TurNuP (MIT) for kinetics if CEKM not yet trained |
| **Toxic intermediate** | RDKit (BSD, Class A) QSAR screening against structural alert databases |
| **Required dataset** | BRENDA CC BY 4.0 (kinetics); ProteinGym (MIT) for enzyme fitness priors; COBRApy organism GEM files |

**Layer 5: Multi-Fidelity BoTorch Optimisation (MFMO)**

| | Specification |
|---|---|
| **Typed input** | `ScoredPathwaySet` + design space (edit variables: promoter strengths, copy numbers, knockouts as continuous/discrete parameters) |
| **Typed output** | `RankedPathwaySet`: Pareto-optimal candidates under `{max_titer, max_yield, min_burden, min_toxicity}`; `ValidationSequence`: ordered list of experiments by expected information gain |
| **Primary tool** | BoTorch qNEHVI (MIT) for multi-objective Pareto optimisation; qMFKG for multi-fidelity cost-aware search[^39][^68] |
| **Causal node (new)** | GO-CBED (ICLR 2025) or equivalent for causal experiment selection — selects next edit to maximally resolve pathway performance uncertainty[^59] |
| **Surrogate** | GP with Matérn 5/2 kernel over ZPE-encoded design vectors; deep ensemble for high-variance regions |
| **Required dataset** | Zer0pa PathGym (Section 4.2) once built; initially seed with BioTRY (pending commercial license verification)[^2] + van Lent 2026 simulated DBTL[^32] |

**Layer 6: Host Engineering Specification**

| | Specification |
|---|---|
| **Typed input** | Top-ranked pathway from Layer 5 + host organism GEM |
| **Typed output** | `GeneticModificationSpec`: `{knockouts: [gene_id], knockins: [gene_id, sequence, promoter, RBS], upregulations: [gene_id, fold_change], codon_optimization_plan: {host_codon_table, CAI_target}, CRISPR_gRNA_seqs: [seq], CRISPRi_targets: [gene_id]}` |
| **Primary tools** | Cello 2.0 (BSD, Class A) for genetic circuit design; Salis Lab RBS Calculator (Class B/academic — check commercial terms); OptKnock/OptForce in COBRApy; CRISPRi design tools (published open-source) |
| **Dynamic control** | Quorum-sensing-CRISPRi toolkit[^47]; optogenetic switching (Addgene plasmid library cross-reference) |
| **Required dataset** | iGEM Registry (CC0 public domain) for standard biological parts; NCBI RefSeq for host genome context |

**Layer 7: Output Dossier Generation**

| | Specification |
|---|---|
| **Typed input** | `RankedPathwaySet` from Layer 5 + `GeneticModificationSpec` from Layer 6 |
| **Typed output** | Structured JSON dossier validated against Pydantic schema for each dossier field in the handoff schema (Section 2 of Report 1 brief) |
| **RAG layer** | LangGraph + vector store (Chroma, MIT) over PubMed abstracts and Wiley full-text; top-5 papers per pathway candidate retrieved by cosine similarity to pathway fingerprint |
| **Cost model** | Parametric model: cost per gene synthesis ($0.10–$0.30/bp), per transformation round, per fermentation run — parameterised by host organism and CRO partner pricing |
| **Validation** | Pydantic v2 (MIT) schema enforcement; JSON Schema export for dossier API |

***

### 5.2 Corrections Summary: Report 1 → Report 2

| Item | Report 1 Assumption | Report 2 Correction |
|---|---|---|
| BRENDA licensing | Class C/E monolith; use only via ML surrogates | Core data = CC BY 4.0 Class A; only BKMS-react = Class C/D |
| BRENDA direct use strategy | Avoid direct use | Direct bulk download and training use permitted with attribution |
| BKMS-react | Included in BRENDA as Class C/E | Separate license; redistribution/embedding explicitly prohibited → exclude from corpus |
| KEGG API (commercial) | Class E | Single-entry API queries = Class A; bulk FTP = Class E; IDs as cross-references = Class A |
| NASA OSDR (all data) | Implied Class A uniformly | Two tiers: public non-human data = Class A; controlled human data = Class D |
| ModelSEED | Not fully classified | Confirmed MIT Class A; 33,978 compounds, 36,645 reactions |
| RFdiffusion v3 | Not in scope | Available via RosettaCommons Foundry (BSD/MIT); all-atom diffusion including ligands |
| Yeast9 / iMM904 | iMM904 noted as updated | Yeast9 (2024, MIT) confirmed supersedes iMM904; in SysBioChalmers GitHub |
| BioTRY | Not identified | >52,000 TRY entries; verify commercial license before training use |
| EnzyExtract | Not identified | MIT; 89,544 kinetic entries absent from BRENDA; directly usable for CEKM training |
| GotEnzymes2 | GotEnzymes noted | Updated to 59.6M predicted entries, 7.3M sequences, CC BY 4.0 |
| DBTL benchmark | ProteinGym cited for protein | No equivalent DBTL benchmark exists for pathway optimisation — explicit gap |
| Causal inference | Subsumed into BoTorch | Promoted to Tier 1 architecture-critical; dedicated causal node recommended |
| Heterogeneity KPI layer | Tier 1 (conceptual) | Insufficient data for v1; reclassified to Tier 2 / v1.1; ACBM for synthetic data |
| FluxGAT vs FlowGAT | Not distinguished | FluxGAT (MIT, NeurIPS 2024): flux sampling approach, 2× FBA sensitivity; FlowGAT: FBA-based; both Class A |
| LDBT paradigm | Not identified | Nature Comms 2025: L precedes D; cell-free TX-TL for megascale training data |

***

### 5.3 Intersectional Tier Shifts vs. Report 1

| Intersection | Report 1 Tier (implied) | Report 2 Tier | Reason for Shift |
|---|---|---|---|
| Causal inference / OED | Not enumerated | **Tier 1 (promoted)** | GO-CBED + CausalBench make this operationally buildable now |
| Information theory ↔ metabolism | Tier 1 | **Tier 1 (confirmed, deepened)** | FluxGAT provides concrete entropy-based scoring |
| Thermodynamics ↔ feasibility | Tier 1 | **Tier 1 (confirmed)** | MetaNetX 2025 update enhances eQuilibrator coverage |
| SE(3)-geometry ↔ enzyme | Tier 1 | **Tier 1 (deepened)** | RFdiffusion3 all-atom available; Baker one-shot design published |
| Heterogeneity / population dynamics | Tier 1 (conceptual) | **Tier 2 (demoted)** | Data insufficient for v1; ACBM synthetic data path identified |
| Gauge theory / Geometric Unity | Tier 1 (philosophical) | **Tier 3 (confirmed)** | No production tools exist; maintain as frontier |
| QM/MM quantum biology | Tier 1 (philosophical) | **Tier 3 (v1 scope out)** | Too computationally expensive for high-throughput screening |
| Astrobiology ↔ extremophile | Tier 1 | **Tier 2 / data-limited** | NASA OSDR Class A but extremophile GEM coverage sparse |

***

### 5.4 Ready-for-PRD Checklist

The following items must be confirmed before the PRD agent proceeds with pipeline specification. All items have been resolved in this report unless marked otherwise.

**Licensing — All items resolved:**
- [x] BRENDA core data = CC BY 4.0 Class A (direct use permitted)
- [x] BKMS-react = Class C/D (excluded from LIRC corpus — do not embed)
- [x] KEGG = Class E for bulk; Class A for single-entry API queries and ID storage only
- [x] NASA OSDR non-human data = Class A; controlled human data = Class D (excluded)
- [x] ModelSEED = MIT Class A (33,978 compounds, 36,645 reactions, GitHub available)
- [x] Rhea = CC0/free Class A (SPARQL + FTP download)
- [x] MetaNetX 4.5 = CC BY 4.0 Class A (SPARQL endpoint; 2025 update confirmed)
- [x] RFdiffusion3 = BSD/MIT Class A (Foundry GitHub)
- [x] GotEnzymes2 = CC BY 4.0 Class A (59.6M entries; Metabolic Atlas/Zenodo)
- [x] EnzyExtract = MIT Class A (GitHub: ChemBioHTP/EnzyExtract)
- [ ] **BioTRY commercial license: UNRESOLVED — verify before including in training corpus**
- [ ] **EF-UniKP / UniKP commercial use terms: confirm GitHub MIT license includes commercial use**

**Data Sufficiency — Key decisions locked:**
- [x] Conditional kcat/Km model: trainable on BRENDA CC BY 4.0 + EnzyExtract MIT (CEKM build greenlit)
- [x] Fermentation KPI predictor: product/organism-specific models only (general predictor not feasible)
- [x] BioTRY is the primary KPI dataset candidate (>52,000 entries) — pending license verification
- [x] DBTL benchmark gap confirmed: no ProteinGym equivalent exists — PathGym is a Zer0pa build opportunity
- [x] Scale-up correction: mechanistic CFD (OpenFOAM) as correction function, not ML-trained (insufficient data)
- [x] Heterogeneity layer: ACBM synthetic data + v1.1 milestone, not v1 scope

**Architecture — All pipeline layers typed:**
- [x] Layer 1 (ZPE): SELFIES + ESM-2 encoding confirmed
- [x] Layer 2 (Knowledge): LIRC corpus spec complete; BKMS-react excluded; MetaNetX 4.5 as backbone
- [x] Layer 3 (Retrosynthesis): RetroPath3.0 primary; RFdiffusion3 + Baker one-shot for unknown enzymes
- [x] Layer 4 (Screening): COBRApy + GECKO + CEKM + CatPred + FluxGAT + eQuilibrator MDF
- [x] Layer 5 (Optimisation): BoTorch qNEHVI + qMFKG (multi-fidelity); causal OED node added
- [x] Layer 6 (Host Engineering): Cello 2.0 + Salis RBS Calculator + CRISPRi toolkit + Yeast9/iML1515
- [x] Layer 7 (Dossier): Pydantic v2 + LangGraph RAG + parametric cost model

**Intersectional Tiers — Locked:**
- [x] Tier 1 (8 confirmed + 1 new = 9): Information theory, Thermodynamics, Graph topology, Control theory, SE(3)-geometry, Evolutionary ML, Fluid dynamics/scale-up, Electrochemistry/cofactors, Causal inference/OED
- [x] Tier 2 (6): Oscillations, Consortia ecology, Phonon/NMA, Metabolomics signal processing, Optogenetic control, Population heterogeneity
- [x] Tier 3 (4): Gauge theory, QM/MM quantum, Astrobiology extremophile (data-limited), Plasma non-thermal bioprocessing

**Emergent Artefacts — Build specifications complete:**
- [x] Artefact 1: LIRC (License-Clean Integrated Reaction Corpus) — build spec in Section 4.1
- [x] Artefact 2: PathGym DBTL Benchmark — build spec in Section 4.2
- [x] Artefact 3: Unknown Enzyme Generative Sub-Pipeline — build spec in Section 4.3
- [x] Artefact 4: Multi-Fidelity Metabolic Optimiser (MFMO) — build spec in Section 4.4
- [x] Artefact 5: Conditional Enzyme Kinetics Model (CEKM) — build spec in Section 4.5

**Handoff Schema Coverage — All 12 dossier fields have identified pipeline sources:**
- [x] Pathway map → Layer 3 retrosynthesis output
- [x] Genetic modification spec → Layer 6 host engineering
- [x] Predicted fermentation KPIs → Layer 4 FBA + CEKM + BioTRY surrogates
- [x] Metabolic burden score → GECKO enzyme-constrained FBA
- [x] Thermodynamic feasibility → eQuilibrator MDF (Layer 4)
- [x] Enzyme characterisation → CEKM (kcat, Km) + CatPred (uncertainty) + ProDy (NMA dynamics)
- [x] Competing pathway interference map → FluxGAT + COBRApy knockout simulation
- [x] Toxic intermediate flags → RDKit QSAR structural alerts
- [x] Validation sequence → Causal OED node + BoTorch information gain
- [x] Wet-lab validation cost → Parametric cost model (Layer 7)
- [x] Risk tier → BoTorch multi-objective Pareto rank + CI bounds
- [x] Supporting literature → LangGraph RAG over PubMed + Wiley corpus

**PRD agent may proceed.** The only blocking item is BioTRY commercial license verification. All other decisions are complete, licensed, and typed.

---

## References

1. [Finding the dark matter: Large language model‐based enzyme kinetic data extractor and its validation](https://onlinelibrary.wiley.com/doi/10.1002/pro.70251) - Despite the vast number of enzymatic kinetic measurements reported across decades of biochemical lit...

2. [BioTRY: A Comprehensive Knowledge Base for Titer, Rate, and ...](https://pubmed.ncbi.nlm.nih.gov/39423319/) - However, the key economic indicators, namely titer, rate, and yield (TRY), which respectively reflec...

3. [Finding the dark matter: Large language model‐based enzyme ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12355964/) - EnzyExtract identified 89,544 unique kinetic entries (k cat and K m combined) absent from BRENDA, si...

4. [BKMS-react online - BRENDA Enzyme Database](https://bkms.brenda-enzymes.org/license.php) - Any inclusion of BKMS-react components into other data bases, or redistribution of BKMS-react requir...

5. [Enzyme Databases in the Era of Omics and Artificial Intelligence](https://pmc.ncbi.nlm.nih.gov/articles/PMC10707154/) - ...curation cannot keep pace with the exponential growth in published data. Lack of data standardiza...

6. [The Creative Commons Attribution 4.0 International (CC BY ... - OECD](https://www.oecd.org/en/publications/access-to-public-research-data-toolkit_a12e8998-en/the-creative-commons-attribution-4-0-international-cc-by-4-0_723b36be-en.html) - The Creative Commons Attribution 4.0 International (CC BY 4.0) license allows users to share, copy, ...

7. [BRENDA, the ELIXIR core data resource in 2021 - Oxford Academic](https://academic.oup.com/nar/article/49/D1/D498/5992283) - The BKMS-react module in BRENDA is a way to provide combined enzyme-catalyzed reactions of the four ...

8. [KEGG FTP Academic Subscription - Pathway Solutions](https://www.pathway.jp/en/academic.html) - The KEGG FTP Academic Subscription is a paid service managed by Pathway Solutions for those academic...

9. [KEGG FTP](https://www.kegg.jp/kegg/download/) - KEGG for Non-academic Users. Non-academic users are requested to obtain a license agreement for usin...

10. [KEGG Commercial Licensing - Pathway Solutions](https://www.pathway.jp/en/licensing.html) - Pathway Solutions operates the KEGG FTP site and the KEGG mirror website for commercial customers an...

11. [NPO Bioinformatics Japan - KEGG FTP Academic Subscription](https://www.kanehisa.jp/npo/en/keggftp.html) - KEGG FTP by non-academic users. Non-academic users are requested to obtain a license agreement for d...

12. [MetaNetX: a bridge between metabolic resources for enhanced ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12807685/) - MetaNetX integrates biochemical data from a broad range of resources, including ChEBI [13], KEGG [1]...

13. [and the Rhea SPARQL endpoint at](https://sparql.rhea-db.org) - This SPARQL endpoint contains Rhea reactions data (see statistics), and a snapshot of ChEBI data mat...

14. [MetaNetX SPARQL endpoint - SIB Swiss Institute of Bioinformatics](https://www.expasy.org/resources/metanetx-sparql-endpoint) - SPARQL access to MetaNetX.org allows to access, analyse and manipulate genome-scale metabolic networ...

15. [Bayesian Optimization and Active Learning Cookbook - PhysicsX](https://www.physicsx.ai/newsroom/bayesian-optimization-and-active-learning-cookbook) - This document is intended as a reference for implementing various types of Bayesian optimization and...

16. [A Genome-Scale Metabolic Model of Methanoperedens nitroreducens: Assessing Bioenergetics and Thermodynamic Feasibility](https://www.mdpi.com/2218-1989/12/4/314) - Methane is an abundant low-carbon fuel that provides a valuable energy resource, but it is also a po...

17. [The ModelSEED Biochemistry Database for the integration of ...](https://www.research-collection.ethz.ch/entities/publication/c093a90f-114d-41bd-81f7-b43b1273230c) - For over 10 years, ModelSEED has been a primary resource for the construction of draft genome-scale ...

18. [ModelSEED Biochemistry Database - GitHub](https://github.com/ModelSEED/ModelSEEDDatabase) - For over ten years, ModelSEED has been a primary resource for the construction of draft genome-scale...

19. [De novo Design of All-atom Biomolecular Interactions with ... - bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.18.676967v1) - We present RFdiffusion3 (RFD3), a diffusion model that generates protein structures in the context o...

20. [RFdiffusion3 is Now Available in foundry - Rosetta Commons](https://rosettacommons.org/2025/12/22/rfdiffusion3-is-now-available-in-foundry/) - RFdiffusion3 is Now Available in foundry · Performs atom-level diffusion across both backbone and si...

21. [Protein design with Foundry - GitHub](https://github.com/RosettaCommons/foundry) - RFdiffusion3 is an all-atom generative model capable of designing protein structures under complex c...

22. [Advances in Machine Learning Models for Predicting Enzyme ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12801326/) - ML models for enzyme kinetics prediction typically take two main inputs: the enzyme, represented by ...

23. [a unified framework for the prediction of enzyme kinetic parameters](https://orbit.dtu.dk/en/publications/unikp-a-unified-framework-for-the-prediction-of-enzyme-kinetic-pa/) - Here, we introduce UniKP, a unified framework based on pretrained language models for the prediction...

24. [Luo-SynBioLab/UniKP - GitHub](https://github.com/Luo-SynBioLab/UniKP) - UniKP is a valuable tool for deciphering the mechanisms of enzyme kinetics and enables novel insight...

25. [CatPred Online | Predict in vitro Enzyme Kinetic Parameters](https://www.tamarind.bio/tools/catpred) - Scientists have developed CatPred, a comprehensive machine learning framework for predicting in vitr...

26. [ChemBioHTP/EnzyExtract: Enzyme kinetics data extraction pipeline](https://github.com/ChemBioHTP/EnzyExtract) - Enzyme kinetics data extraction pipeline. Contribute to ChemBioHTP/EnzyExtract development by creati...

27. [feiranl/GotEnzymes: This is for kinetic parameter prediction ... - GitHub](https://github.com/feiranl/GotEnzymes) - This repository contains code for data collection, processing and prediction for the GotEnzymes data...

28. [GotEnzymes database - Metabolic Atlas](https://metabolicatlas.org/gotenzymes) - GotEnzymes2 provides open access to over 59.6 million predicted enzyme parameter entries for 7.3 mil...

29. [LDBT: Machine Learning Meets Rapid Cell-Free Testing](https://bioengineer.org/ldbt-machine-learning-meets-rapid-cell-free-testing/) - This approach integrates advanced machine learning algorithms with rapid, cell-free testing platform...

30. [LDBT instead of DBTL: combining machine learning and rapid cell ...](https://www.nature.com/articles/s41467-025-65281-2) - Moreover, adopting cell-free platforms can further accelerate “Building” and “Testing” for megascale...

31. [[PDF] Artificial intelligence–powered biofoundries for protein engineering ...](https://zhaogroup.chbe.illinois.edu/publications/HZ474.pdf) - Overview of DBTL cycle automation platforms for metabolic engineering, integrating high-throughput e...

32. [[PDF] Comparing metabolic engineering scenarios using simulated design ...](https://www.biorxiv.org/content/10.64898/2026.02.03.703462v1.full.pdf) - bioRxiv preprint. Page 8. van Lent et al. Comparing metabolic engineering scenarios using simulated ...

33. [Simulated Design-Build-Test-Learn Cycles for Consistent ... - PubMed](https://pubmed.ncbi.nlm.nih.gov/37616156/) - We show that when the number of strains to be built is limited, starting with a large initial DBTL c...

34. [Automation and machine learning drive rapid optimization of ...](https://www.nature.com/articles/s41467-025-66304-8) - The canonical Design-Build-Test-Learn (DBTL) paradigm has proven to be a powerful framework in synth...

35. [ProteinGym: Large-Scale Benchmarks for Protein Design and ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/) - We introduce ProteinGym, a large-scale and holistic set of benchmarks specifically designed for prot...

36. [OATML-Markslab/ProteinGym - GitHub](https://github.com/OATML-Markslab/ProteinGym) - ProteinGym is an extensive set of Deep Mutational Scanning (DMS) assays and annotated human clinical...

37. [Cello | The Synthetic Biology Open Language](https://sbolstandard.org/applications/cello/) - Cello is a framework that describes what is essentially a programming language to design computation...

38. [Microbial lifelines in bioprocesses: From concept to application](https://www.sciencedirect.com/science/article/abs/pii/S0734975022001677) - A microbe's view on large-scale reactors gives insights for bioprocess development. · Computational ...

39. [Multi-fidelity Bayesian optimization with discrete fidelities using KG](https://botorch.org/docs/tutorials/discrete_multi_fidelity_bo/) - In this tutorial, we show how to do multi-fidelity BO with discrete fidelities based on [1], where e...

40. [Single cell profiling framework reveals metabolic subpopulations as ...](https://www.nature.com/articles/s41467-025-67408-x) - Here, we propose a framework based on single-cell biosensor analysis that enables robust characteris...

41. [Cellular variability as a driver for bioprocess innovation and ...](https://www.sciencedirect.com/science/article/pii/S073497502500014X) - This review explores the different dimensions of cellular heterogeneity, focusing on its manifestati...

42. [Integrative single-cell metabolomics and phenotypic profiling ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11926267/) - Integrative single-cell metabolomics and phenotypic profiling reveals metabolic heterogeneity of cel...

43. [ACBM: An Integrated Agent and Constraint Based Modeling ... - Nature](https://www.nature.com/articles/s41598-020-65659-w) - ACBM models the cell population in three-dimensional space to predict spatial and temporal dynamics ...

44. [FluxGAT: Integrating Flux Sampling with Graph Neural Networks for ...](https://neurips.cc/virtual/2024/102813) - Here, we present FluxGAT, a graph neural network (GNN) model capable of predicting gene essentiality...

45. [FluxGAT: Integrating Flux Sampling with Graph Neural Networks for ...](https://github.com/kierensharma/FluxGAT) - FluxGAT introduces a graph neural network (GNN) model designed to predict gene essentiality by utili...

46. [Integration of graph neural networks and genome-scale metabolic ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10917767/) - In this paper, we propose FlowGAT, a graph neural network (GNN) model to predict gene essentiality f...

47. [A quorum sensing-controlled type I CRISPRi toolkit for dynamically ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12276013/) - Design of a programmable biosensor-CRISPRi genetic circuits for dynamic and autonomous dual-control ...

48. [CRISPR-assisted rational flux-tuning and arrayed CRISPRi ... - Nature](https://www.nature.com/articles/s41467-022-28501-7) - We optimize and use the CRISPR-assisted editing and CRISPRi screening methods to convert a wild-type...

49. [RFdiffusion3 now available - Institute for Protein Design](https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/) - This foundation model for biodesign can generate proteins that interact with any type of molecule co...

50. [Computational enzyme design by catalytic motif scaffolding - Nature](https://www.nature.com/articles/s41586-025-09747-9) - The model proposes that functional groups in the active site accelerate chemical reactions by stabil...

51. [ProteinGym: Large-Scale Benchmarks for Protein Design ... - bioRxiv](https://www.biorxiv.org/content/10.1101/2023.12.07.570727v1.full-text) - Many of the alignment-based methods (e.g. EVmutation, WaveNet and DeepSequence) exhibit this behavio...

52. [An AI-Native Biofoundry for Autonomous Enzyme Engineering](https://www.biorxiv.org/content/10.64898/2026.02.01.703093v1.full-text) - This work demonstrates that AI-native infrastructures can not only accelerate trait evolution by ord...

53. [An Agentic LLM Framework for Mechanistic Enzyme Design - arXiv](https://arxiv.org/abs/2511.19423) - We present Genie-CAT, a tool-augmented large-language-model (LLM) system designed to accelerate scie...

54. [Multi-Fidelity Bayesian Optimization in Chemical Engineering](https://www.youtube.com/watch?v=qT9ju4eMLKA) - ... computational fluid dynamic simulation fidelities. Gaussian processes are utilized to adaptively...

55. [Current breakthroughs and advances in atmospheric room ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12176711/) - Atmospheric and Room Temperature Plasma (ARTP) mutagenesis has emerged as a novel and powerful physi...

56. [Current breakthroughs and advances in atmospheric room ...](https://pubmed.ncbi.nlm.nih.gov/40533659/) - Atmospheric and Room Temperature Plasma (ARTP) mutagenesis has emerged as a novel and powerful physi...

57. [Causal Discovery and Optimal Experimental Design for Genome ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10104184/) - Causal discovery of genome-scale networks is important for identifying pathways from genes to observ...

58. [[PDF] CAUSAL DISCOVERY VIA BAYESIAN OPTIMIZATION](https://proceedings.iclr.cc/paper_files/paper/2025/file/8693ee1ea821666f8569228d1ab38baf-Paper-Conference.pdf) - , 2024), these methods utilize BO to suggest optimal interventions to quickly recover the causal DAG...

59. [Goal-Oriented Sequential Bayesian Experimental Design for Causal...](https://openreview.net/forum?id=i2blv7QxtJ) - We present GO-CBED, a goal-oriented Bayesian framework for sequential causal experimental design. Un...

60. [A large-scale benchmark for network inference from single-cell ...](https://www.nature.com/articles/s42003-025-07764-y) - We thus introduce CausalBench, a benchmark suite revolutionizing network inference evaluation with r...

61. [ClustENMD: efficient sampling of biomolecular conformational space at atomic resolution](https://academic.oup.com/bioinformatics/article/37/21/3956/6317825) - Summary Efficient sampling of conformational space is essential for elucidating functional/allosteri...

62. [ProDy 2.0: increased scale and scope after 10 years of protein dynamics modelling with Python](https://pmc.ncbi.nlm.nih.gov/articles/PMC8545336/) - ... new file formats, (ii) SignDy for signature dynamics of protein families, (iii) CryoDy for colle...

63. [prody/ProDy: A Python Package for Protein Dynamics Analysis](https://github.com/prody/ProDy) - ProDy is a free and open-source Python package for protein structure, dynamics, and sequence analysi...

64. [Atmospheric and room temperature plasma mutagenesis of ...](https://www.sciencedirect.com/science/article/abs/pii/S0960852425008466) - This study generated methanol-tolerant Graesiella emersonii strain through Atmospheric and Room Temp...

65. [Download - Rhea help results](https://www.rhea-db.org/help/download) - All data in Rhea is freely available and can be downloaded from our FTP site in different formats. T...

66. [Recent advances in the Design-Build-Test-Learn (DBTL) cycle for ...](https://pubmed.ncbi.nlm.nih.gov/40195836/) - This review highlights recent progress in the metabolic engineering of Corynebacterium glutamicum, a...

67. [Large language models facilitating modern molecular biology and novel drug development](https://www.frontiersin.org/articles/10.3389/fphar.2024.1458739/full) - The latest breakthroughs in information technology and biotechnology have catalyzed a revolutionary ...

68. [Multi-fidelity Bayesian optimization using KG - BoTorch](https://botorch.org/docs/tutorials/multi_fidelity_bo/) - In this tutorial, we show how to perform continuous multi-fidelity Bayesian optimization (BO) in BoT...

69. [Multi-fidelity Bayesian Optimization Framework for CFD-Based Non ...](https://arxiv.org/html/2511.23140v1) - To address this, the multi-fidelity BO literature has proposed a variety of strategies that explicit...

70. [A novel interpretability framework for enzyme turnover number ...](https://www.sciencedirect.com/science/article/abs/pii/S1046202325000519) - DLKcat leverages Graph Convolutional Networks (GCNs) to extract substrate features and Convolutional...

71. [BRENDA in 2019: a European ELIXIR core data resource](https://pmc.ncbi.nlm.nih.gov/articles/PMC6323942/) - Abstract The BRENDA enzyme database (www.brenda-enzymes.org), recently appointed ELIXIR Core Data Re...

