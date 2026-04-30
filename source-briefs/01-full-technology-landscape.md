# Synthetic Biology — Metabolic Pathway Engineering Pipeline: Full Technology Landscape

**Zer0pa Science Intelligence Platform · Pipeline 4 of 6**
**Report 1 of 2 · Version 1.0 · April 30, 2026**
**Issued by:** Architect Prime, Zer0pa
**Classification:** Internal R&D Intelligence

***

## Executive Summary

This report constitutes the full technology landscape for the **Metabolic Pathway Engineering Pipeline**, the fourth pipeline in the Zer0pa Science Intelligence Platform. The pipeline's commercial function is to accept a **target molecule + host organism** as input and produce a ranked set of complete, CRO-ready genetic engineering specifications — each containing a full biosynthetic pathway design with predicted fermentation performance metrics — as output.

The architecture is driven backward from the handoff schema: every layer of the pipeline is justified by a field in the **Metabolic Pathway Engineering Dossier**, the CRO-deliverable product. The orchestration backbone is **LangGraph** (directed acyclic graph agent workflow, MIT license), the optimisation engine is **BoTorch** (Bayesian active learning, MIT license), the input encoding layer is the **ZPE deterministic signal encoding layer**, and the knowledge grounding layer is an equivalent of the NOSES structured metabolic knowledge graph used in the Materials Science pipeline.

Five commercial application domains are addressed — Industrial Chemicals, Specialty/Fine Chemicals, Sustainable Aviation Fuel and Biofuels, Pharmaceutical Intermediates, and Food/Flavour Ingredients — each with distinct screening endpoints, CRO/partner landscapes, and key datasets. Twenty intersectional science mappings are enumerated, each identifying tools, datasets, and evidence that a cross-domain approach produces measurably superior results.

All tool selections are governed by the Zer0pa licensing taxonomy: **Class A** (MIT, Apache 2.0, BSD) and **Class B** (copyleft, outputs commercially owned) tools are in-stack; Class C (non-commercial academic) and Class D/E (gated/proprietary) tools are documented with their capability gap and the best Class A/B alternative.

***

## Part I: The Handoff Schema and Pipeline Logic

### 1.1 Design Philosophy: Backward from the Dossier

The most important architectural principle of this pipeline is that **every computational layer is justified by a field in the output dossier**. No layer exists for its own sake. The following table maps each dossier field to the pipeline layer responsible for populating it, and identifies the primary tool or model at that layer.

| Dossier Field | Pipeline Layer | Primary Tool(s) |
|---|---|---|
| Pathway map (directed enzymatic graph) | Layer 3: Retrosynthetic Generation | RetroPath3.0, novoStoic2.0, BNICE.ch |
| Genetic modification specification | Layer 6: Host Engineering | Cello 2.0, OptKnock, Salis RBS Calculator |
| Titer / Yield / Productivity (KPIs) | Layer 4: In Silico Screening | COBRApy + GECKO, JBEI ART |
| Metabolic burden score | Layer 4: In Silico Screening | GECKO ecGEM, ETFL |
| Thermodynamic feasibility profile | Layer 4: Thermodynamic Analysis | eQuilibrator 3.0, PyTFA |
| Enzyme characterisation (kcat, Km) | Layer 4: Enzyme Kinetics ML | DLKcat, TurNuP, DeepEnzyme |
| Competing pathway interference | Layer 4: FBA + Knockout | COBRApy OptKnock/OptForce |
| Toxic intermediate flags | Layer 4: Cheminformatics | QSAR models, CD-MINE |
| Validation sequence | Layer 5: Active Learning | BoTorch qNEHVI loop |
| Wet-lab cost estimate | Layer 7: Output Dossier | Cost models, CRO pricing APIs |
| Risk tier | Layer 5 + 7: BoTorch + Ranking | Multi-objective Pareto ranking |
| Supporting literature | Layer 7: RAG Retrieval | Vector-RAG (LangGraph node) |

### 1.2 Pipeline Flow Summary

```
[ZPE Input Encoding] → [Metabolic Knowledge Layer] → [Retrosynthetic Generation]
        ↓                                                         ↓
[Host Engineering Spec] ← [BoTorch Active Learning Loop] ← [In Silico Screening]
        ↓
[Output Dossier Generation → CRO Partner]
```

The LangGraph orchestrator manages state transitions between all layers. Each node in the LangGraph DAG corresponds to one pipeline layer. The BoTorch loop sits between Layer 4 and Layer 6, driving iterative refinement of pathway candidates before genetic specification is finalised.

***

## Part II: Pipeline Architecture — Full Layer Documentation

### Layer 1: Input Encoding — The ZPE Integration Point

The ZPE layer accepts two primary input types: a **target molecule** (represented as a molecular graph) and a **host organism** (represented as a genome sequence + known metabolic model identifier). The layer's function is to encode these inputs as deterministic tokens that downstream pipeline nodes can consume consistently.

**Molecular Graph Representations — Current SOTA:**

The field has converged on three complementary representations, each with different strengths for ML model input:[^1][^2]

- **SMILES (Simplified Molecular Input Line Entry System):** String-based representation. Compact and universal but not inherently robust — invalid SMILES can be generated by generative models. Supported by RDKit (BSD license, Class A). Used as input by RetroPath2.0, DLKcat, eQuilibrator, and most legacy cheminformatics tools.
- **InChI / InChIKey:** IUPAC standard. Canonical and unambiguous. Used for cross-database identifier reconciliation (MetaNetX integrates KEGG, Rhea, BiGG, and ChEBI through InChI keys). InChIKey is the standard identifier in the ATLAS of Biochemistry.[^3][^4]
- **SELFIES (Self-Referencing Embedded Strings):** Introduced 2020. Guarantees 100% syntactic validity — any sequence of SELFIES tokens represents a valid molecule. Directly relevant to the ZPE encoding design: SELFIES provides a discrete, token-stream-compatible molecular language that maps cleanly to the ZPE's 8-primitive geometric substrate. Open source under Apache 2.0. Used in several state-of-the-art molecular generative models.[^2][^1]
- **Molecular graphs (graph-native):** Used directly by Graph Neural Network (GNN) architectures. RDKit can convert SMILES to molecular graphs. Graph representations are the native input format for DLKcat (graph convolutional network over substrate).[^5]

**Genomic Sequence Representations — Current SOTA:**

- **Tokenised DNA sequences:** Nucleotide-level tokenisation. Used by genomic language models (DNABERT, Nucleotide Transformer). Relevant for codon optimisation layers.
- **Protein sequence embeddings:** ESM-2, ESMFold, and ProtTrans produce fixed-length embeddings from amino acid sequences. These are the standard input for kcat prediction models including TurNuP, which encodes enzyme sequences through a modified Transformer network.[^6]
- **GEM identifier:** Genome-scale metabolic model ID (e.g., `iML1515` for E. coli K-12, `iMM904` for S. cerevisiae). This allows the pipeline to load the organism's known metabolic network directly from BiGG Models API.[^7][^8]

**ZPE Integration Note:** The ZPE 20-bit word envelope over the 8-primitive geometric substrate should encode the target molecule as a SELFIES token stream (molecular domain) and the host organism as a GEM identifier + ESM-2 protein embedding hash (biological domain). The two sub-encodings can be concatenated into a fixed-dimension input vector for downstream ML layers.

***

### Layer 2: Metabolic Knowledge Layer — The NOSES-Equivalent

This is the structured biochemical knowledge base that grounds all pipeline reasoning. Unlike the Materials Science pipeline's NOSES (which encodes crystal structure, space group, and elemental property data), the metabolic knowledge layer encodes **reactions, enzymes, pathways, organisms, and kinetics**.

**Primary Databases — Full Documentation:**

#### KEGG (Kyoto Encyclopedia of Genes and Genomes)

- **Coverage:** >19,000 compounds, >11,000 reactions, >500 metabolic pathways (KEGG PATHWAY maps), >700 organisms with genomic annotations.
- **API:** REST API (KEGG API) available at https://www.kegg.jp/kegg/rest/keggapi.html. Free for academic use. Commercial licensing required for commercial applications.[^9]
- **Licensing:** Class C (non-commercial academic) for API access; Class E for bulk commercial download.
- **Alternative (Class A/B):** MetaNetX (MIT license for the reconciliation software; database is freely accessible) and BiGG Models (CC-BY 4.0) provide KEGG-derived content under more permissive terms. KEGG data is also embedded within COBRApy model files (BiGG models).[^3]
- **Update Frequency:** Regular (approximately quarterly).
- **Pipeline Use:** Backbone for pathway reconstruction in RetroPath and novoStoic; reaction IDs are the lingua franca for inter-tool communication.

#### BiGG Models (Biochemistry, Genetics and Genomics)

- **Coverage:** 108+ genome-scale metabolic models (GEMs) covering major industrial organisms. All models stored in SBML format and JSON. Universal COBRA model available as a single JSON file.[^7]
- **API:** Full REST API at http://bigg.ucsd.edu/data_access. GET requests for models, reactions, metabolites. Free and open.[^7]
- **Licensing:** Class A (CC-BY 4.0 for database content; software is MIT).
- **Key Models in Stack:**
  - **iML1515** (E. coli K-12): 1,515 ORFs, 2,719 reactions, 1,877 metabolites. Current gold-standard E. coli GEM. Available directly from BiGG and GitHub (SysBioChalmers/Ecoli-GEM, MIT license).[^10][^11][^8]
  - **iMM904** (S. cerevisiae): Validated yeast model; ancestor of the current Yeast-GEM series (SysBioChalmers, MIT license).[^12][^13]
  - Additional models: iYO844 (B. subtilis), iCN900 (C. glutamicum), iJN746 (P. putida), and clostridial models.

#### BRENDA (Braunschweig ENzyme DAtabase)

- **Coverage:** 124+ new enzyme classes in 2026.1 release (March 2026). Largest enzyme kinetics database: >83,000 enzyme entries from >9,800 organisms, covering kcat, Km, Ki, substrate specificity, temperature and pH optima.[^14][^15]
- **API:** SOAP-based web service; REST access limited.
- **Licensing:** Class C for academic; Class E (commercial license via Biobase) for commercial use.
- **Alternative (Class A/B):** The BRENDA-derived kinetic data is partially mirrored in the **SKiD** database (Structure-Oriented Kinetics Database, 2025). The **ProDy** package (LGPL, Class B) can query protein sequence databases. For ML-based kcat prediction (the primary pipeline use), DLKcat and TurNuP are trained on BRENDA data and are themselves open source — they effectively commoditise the kinetic data into a Class A prediction service.[^16][^6][^5]
- **Capability Gap:** BRENDA's manual curation quality is unmatched; automated extraction misses ~30% of kinetic entries. Mitigation: supplement with literature RAG retrieval.

#### MetaNetX

- **Coverage:** Integrates biochemical data from ChEBI, KEGG, Rhea, BiGG, The SEED, MetaCyc, and other sources. Reconciles metabolite identifiers across all databases using InChI-based universal identifiers. 2025 update adds R-group definitions for improved reconciliation.[^17][^3]
- **API:** REST API at https://www.metanetx.org/. Downloadable flat files.
- **Licensing:** Class A (CC-BY 4.0).
- **Pipeline Use:** Cross-database identifier reconciliation. When a pathway is found in KEGG and needs to be loaded into a BiGG-format COBRA model, MetaNetX provides the identifier mapping. Critical for multi-database knowledge layer construction.

#### Rhea (Expert-Curated Biochemical Reaction Database)

- **Coverage:** >15,000 expert-curated reactions. All reactions described using ChEBI compound ontology. Full stoichiometry, charge balancing, and directionality information. Directly integrated with UniProt and UniRule protein annotations.
- **Licensing:** Class A (CC-BY 4.0).
- **API:** REST API and SPARQL endpoint.
- **Pipeline Use:** Highest-quality reaction data for thermodynamic calculations. eQuilibrator 3.0 uses Rhea reaction identifiers as its primary reaction namespace.[^18]

#### eQuilibrator 3.0

- **Coverage:** Thermodynamic equilibrium constants (ΔrG'°) for ~10,000 biochemical reactions. Uses component contribution method for unprecedented coverage including novel reactions.[^19][^18]
- **Licensing:** Class A (MIT license for the Python API `equilibrator-api`).
- **Capabilities:** Max-min Driving Force (MDF) analysis; Enzyme Cost Minimisation (ECM) analysis; pathway thermodynamic feasibility scoring.[^20]
- **Pipeline Use:** Layer 4 thermodynamic scoring. Every enzymatic step in a candidate pathway is scored for ΔrG'° at physiologically relevant metabolite concentrations. Steps with ΔrG'° > 0 kJ/mol under any feasible concentration range are flagged as thermodynamically infeasible.

#### ATLAS of Biochemistry

- **Coverage:** ~150,000 reactions (ATLAS 2020 update), of which ~96% are novel predictions not in KEGG. Compiled by applying generalised biochemical reaction rules to all KEGG compounds. Validated: 107 reactions predicted in original ATLAS are now confirmed in KEGG, demonstrating predictive accuracy.[^4][^21]
- **Licensing:** Class C (academic use only). **Capability Gap:** No Class A equivalent exists for predicted novel biochemical reactions at this scale.
- **Alternative:** The Chemical Damage MINE database (Class A, MIT) covers 180,891 predicted spontaneous reactions, complementing ATLAS for toxic intermediate screening. novoStoic2.0 performs similar de novo reaction prediction on-the-fly.[^22]

#### iGEM Registry of Standard Biological Parts

- **Coverage:** >20,000 characterised genetic parts (promoters, RBS sequences, coding sequences, terminators, regulatory elements). Community-contributed and maintained.
- **Licensing:** Class A (public domain / CC0). Unambiguously free for commercial use.[^23][^24]
- **API:** SynBioHub SPARQL endpoint at synbiohub.org.[^25]
- **Pipeline Use:** Promoter library for Layer 6 host engineering. The pipeline selects verified promoters from the Registry when designing genetic modification plans.

#### UniProt / Swiss-Prot

- **Coverage:** >250 million protein sequences (TrEMBL); >570,000 manually reviewed entries (Swiss-Prot). Each Swiss-Prot entry links sequence → function → structure → pathway.
- **Licensing:** Class A (CC-BY 4.0).
- **API:** REST API, SPARQL.
- **Pipeline Use:** Enzyme sequence retrieval for ML model input (ESM-2 embeddings). Cross-reference between enzyme function (EC number) and sequence is essential for DLKcat and TurNuP.

#### NCBI RefSeq

- **Coverage:** Complete genome sequences for all major industrial organisms. Annotated ORFs and protein sequences.
- **Licensing:** Class A (US government public domain).
- **Pipeline Use:** Host organism genome input for metabolic model reconstruction; CRISPR guide RNA design (Layer 6).

***

### Layer 3: Retrosynthetic Pathway Generation

The generative layer takes a target molecule and produces a directed graph of enzymatic steps from available feedstock metabolites to the target. This is the hardest computational problem in the pipeline.

#### RetroPath2.0 / RetroPath3.0

- **Description:** Monte Carlo Tree Search (MCTS)-based retrosynthesis tool. Applies biochemical reaction rules to a target compound iteratively, building a reaction network until a connection to native metabolites (the "sink") is found.[^26][^27][^28]
- **Licensing:** Class A (MIT license).
- **Performance:** Reconstructs the majority of known KEGG pathways for common target molecules. Pathway search time: minutes to hours depending on depth and rule set.
- **Integration:** Available as a KNIME workflow or standalone Python package. KNIME is EPL (Class B). Python integration preferred for the Zer0pa stack.
- **Key Limitation:** Rule-based — cannot propose genuinely novel enzymatic transformations beyond the biochemical reaction rule library.

#### novoStoic / novoStoic2.0 (AlphaSynthesis Platform)

- **Description:** Optimisation-based framework that simultaneously applies known reactions AND de novo reaction rules to design mass-balanced pathways. Unlike RetroPath, novoStoic can propose novel enzymatic steps and blend them with known reactions in a single pathway.[^29][^30]
- **novoStoic2.0** (2025): Integrated web platform at http://novostoic.platform.moleculemaker.org/. Adds thermodynamic feasibility assessment and enzyme selection for re-engineering novel steps. Includes rePrime (prime factorisation-based reaction rule encoding) and dGPredictor (ML-based ΔrG prediction).[^31][^32][^33]
- **Licensing:** Class C (academic web server); dGPredictor Python package is Class A (MIT).
- **Alternative:** For commercial use, RetroPath3.0 + eQuilibrator covers most of the same functionality at Class A. The capability gap is the de novo step generation (novoStoic's primary differentiator).

#### BNICE.ch (Biochemical Network Integrated Computational Explorer)

- **Description:** Rule-based retrosynthesis system developed at EPFL. Applies generalised reaction operators derived from enzyme mechanisms to generate the theoretical space of biochemically possible reactions. Forms the basis of the ATLAS of Biochemistry.[^31]
- **Licensing:** Class C (academic; EPFL).
- **Alternative:** ATLAS database (derived from BNICE) + COBRApy provides the same knowledge at Class A/C licensing.

#### BioNavi

- **Description:** Hybrid retrosynthesis tool combining chemical and biological syntheses through multitask learning. Handles both synthetic chemistry retrosynthesis and biosynthetic route planning, enabling hybrid chemo-enzymatic pathway design.[^34]
- **Licensing:** Class A (open web server; source code available).
- **Performance:** Web server at http://biopathnavi.qmclab.com/bionavi/. Published 2024. Enables hybrid de novo pathway design for high-value chemicals.

#### Deep Learning Retrosynthesis Models (Published 2022–2026)

A new generation of neural retrosynthesis tools is emerging that treat biosynthetic pathway planning as a sequence-to-sequence generation problem:[^35][^36]

- **DeepRetro** (2026): Uses iterative LLM-guided retrosynthesis for discovering new pathways through uncharted chemical space.[^36]
- **RetroDFM-R** (2025): Reasoning-based LLM for chemical retrosynthesis, providing explainability through chain-of-thought reasoning.[^37]
- **BioNavi** (2024): Neural multitask model combining biosynthetic and chemical retrosynthesis.[^34]
- **Multistep Retrosynthesis Pipeline** (2026): Deep learning framework combining reaction templates with neural ranking models as binary classifiers for plausible pathway steps.[^35]

**Licensing Status:** Most are Class A (Apache 2.0 or MIT) or open-access academic. DeepRetro weights are open-access. RetroDFM-R is academic open-source.

**LLM-Guided Route Extension:** The Sakana AI **TreeQuest** framework (Apache 2.0) provides an AB-MCTS-based multi-model inference scaling mechanism. Applied to retrosynthesis, TreeQuest can orchestrate multiple LLMs (e.g., a chemistry LLM + a biochemistry specialist model) as a cooperative ensemble to propose novel enzymatic steps, with the tree search tracking solution quality across branches. This is directly isomorphic to the directed evolution exploration strategy.[^38][^39]

***

### Layer 4: In Silico Screening Layer

The most computationally intensive layer. Each candidate pathway generated in Layer 3 must be evaluated for thermodynamic feasibility, enzyme kinetics, flux performance, metabolic burden, and toxicity.

#### 4A: Flux Balance Analysis (FBA) Tools

**COBRApy (Constraint-Based Reconstruction and Analysis in Python)**

- **Description:** The canonical Python library for genome-scale metabolic modelling. Provides FBA, FVA (Flux Variability Analysis), pFBA (parsimonious FBA), gene knockout simulation, and flux sampling.[^40][^41]
- **Licensing:** Class A (Apache 2.0).
- **Performance:** Solves a GEM (~2,700 reactions) in milliseconds using LP solvers (GLPK, Class A; or Gurobi, Class E). GLPK is the open-source default; adequate for pipeline use.
- **Key Models:** iML1515 (E. coli), iMM904/Yeast-GEM (S. cerevisiae), iYO844 (B. subtilis), iCN900 (C. glutamicum).
- **Stack Status:** Core Layer 4 tool. In-stack (Class A).

**GECKO (GEM with Enzymatic Constraints using Kinetic and Omics data)**

- **Description:** Extends FBA by adding protein mass constraints — each enzymatic reaction is constrained by the available enzyme concentration and its kcat. This prevents the model from assigning infinite flux to a single reaction limited only by stoichiometry.[^42][^43]
- **GECKO 2.0 / 3.0:** Automated framework for continuous update of enzyme-constrained models. Produces ecGEMs for S. cerevisiae, Y. lipolytica, K. marxianus, E. coli, and H. sapiens. GECKOpy 3.0 (2023) integrates enzyme constraints + thermodynamic constraints into a unified package.[^43][^44][^42]
- **Licensing:** Class A (MIT license, GitHub: SysBioChalmers/GECKO).
- **Performance:** Flux prediction error in central carbon metabolism reduced by 43% vs. standard GEM for B. subtilis; 2.5-fold improvement in essential gene prediction accuracy.[^45]
- **Stack Status:** In-stack (Class A). The GECKO-type ecGEM is the recommended base model for fermentation KPI prediction.

**MICOM (Metagenome-scale Modelling)**

- **Description:** COBRApy-based tool for metabolic modelling of microbial communities. Constructs a community model from a list of individual COBRA models, managing exchange fluxes between species and with the environment. Explicit accounting for relative species abundance.[^46][^47][^48][^49]
- **Licensing:** Class A (Apache 2.0).
- **Stack Status:** In-stack for Domain 3.5 (microbial consortia applications) and Intersection 4.11 analysis. Available as Python package and web interface (MICOMWeb).[^47]

**ETFL (Expression and Thermodynamics-constrained Flux analysis)**

- **Description:** Integrates enzyme allocation, transcription/translation resource costs, and thermodynamic constraints in a single MILP model. Most comprehensive single-model integration of constraints.[^41]
- **Licensing:** Class A (Apache 2.0, GitHub: EPFL-LCSB/etfl).
- **Stack Status:** In-stack for metabolic burden scoring (populates the "Metabolic burden score" dossier field).

**ECMpy 2.0**

- **Description:** Simplified Python workflow for constructing enzyme-constrained metabolic models, directly adding total enzyme amount constraint without pseudo-metabolites. Computationally lighter than GECKO, suitable for rapid screening.[^50][^51]
- **Licensing:** Class A (MIT license).
- **Stack Status:** In-stack as lightweight alternative to GECKO for initial screening passes.

#### 4B: Thermodynamic Analysis Tools

**eQuilibrator 3.0** (documented in Layer 2 above)
- Stack status: **In-stack (Class A, MIT).**
- Pipeline function: Score ΔrG'° for every enzymatic step; flag dead-end reactions; calculate MDF for pathway as a whole.

**PyTFA (Python Thermodynamics-based Flux Analysis)**

- **Description:** First published implementation of TFA — integrates thermodynamic constraints (explicit Gibbs energy formulation + metabolite concentration bounds) into the MILP problem alongside stoichiometric constraints.[^52][^53]
- **Licensing:** Class A (Apache 2.0, GitHub: EPFL-LCSB/pytfa).
- **Capability:** Provides unbiased prediction of thermodynamic flux profiles; integrates directly with COBRApy models. Allows explicit formulation of Gibbs energies and metabolite concentrations, enabling integration of metabolite concentration measurements.[^53]
- **Stack Status:** In-stack (Class A). Forms the thermodynamic constraint layer over the GECKO ecGEM.

**dGPredictor**

- **Description:** ML-based ΔrG'° prediction tool. Uses molecular fingerprints (capturing stereochemistry) rather than group contribution methods, giving higher coverage and accuracy for novel reactions including isomerase and transferase reactions.[^54]
- **Licensing:** Class A (MIT).
- **Stack Status:** In-stack for novel reactions where eQuilibrator lacks experimental data.

#### 4C: Enzyme Kinetics Prediction

**DLKcat**

- **Description:** Graph Convolutional Network (GCN) model for kcat prediction. Input: substrate molecular graph (GCN features) + enzyme protein sequence (CNN features). Predicts turnover numbers (kcat) for metabolic enzymes from any organism.[^55][^5]
- **Licensing:** Class A (MIT license).
- **Performance:** R² = 0.52, Pearson r = 0.71 on test set (BRENDA-derived). Generalises across EC classes but degrades on out-of-distribution substrates.[^5]
- **Stack Status:** In-stack (Class A).

**TurNuP (Turnover Number Predictor)**

- **Description:** Predicts turnover numbers for natural reactions of wild-type enzymes. Uses differential reaction fingerprints for complete chemical reaction representation + modified Transformer for enzyme sequences. Organism-independent.[^6]
- **Licensing:** Class A (MIT, GitHub: AlexanderKroll/kcat_prediction).[^56]
- **Performance:** R² = 0.44, Pearson r = 0.67 on test set. Outperforms DLKcat, especially for enzymes with <40% sequence identity to training set — crucial for novel pathway enzymes.[^6]
- **Stack Status:** In-stack (Class A). Preferred over DLKcat for novel enzyme predictions.

**DeepEnzyme**

- **Description:** Improved deep learning model for enzyme turnover prediction (2024/2025). Outperforms TurNuP on enzymes with low sequence similarity to training data.[^57]
- **Licensing:** Class A (open-source, academic release).
- **Stack Status:** In-stack as supplementary predictor for out-of-distribution substrates.

**MPEK (Multi-Property Enzyme Kinetics)**

- **Description:** Multi-task learning model predicting Km and kcat simultaneously. Provides correlated uncertainty estimates.
- **Licensing:** Class A (academic).
- **Stack Status:** Under evaluation.

#### 4D: Gene Expression Burden Tools

**Salis Lab RBS Calculator**

- **Description:** Predicts translation initiation rate from ribosome binding site sequence in bacteria. RBS Library Calculator designs optimised RBS libraries to systematically vary protein expression levels across a 100,000-fold range.[^58][^59][^60]
- **Licensing:** Class A (open-source, Salis Lab, Penn State).[^58]
- **Stack Status:** In-stack (Class A). Critical for calibrating heterologous pathway gene expression to minimise metabolic burden.

**ACME (Automated Circuit Model Evaluator)**

- **Description:** Evaluates metabolic burden from heterologous gene expression using resource allocation models.
- **Licensing:** Class A (academic).
- **Stack Status:** In-stack.

**GECKO ecGEM + ETFL:** Also serve as burden scorers — enzyme mass constraints quantify the proteome fraction consumed by the heterologous pathway.

#### 4E: Codon Optimisation

**Cameo (Class A — Apache 2.0)**

- **Description:** Python library for computer-aided metabolic engineering and optimisation. Includes codon optimisation algorithms and integrates COBRApy for strain design. Freely available under Apache 2.0 licence.[^61]
- **Stack Status:** In-stack (Class A).

**IDT Codon Optimisation Tool**

- **Description:** Web-based tool. Freely accessible, but proprietary backend. Not in production stack (Class E). Cameo and local codon table optimisation serve as Class A alternatives.
- **Stack Status:** Not in stack (Class E). Alternative: Cameo + EMBOSS CodonW (Class A, GNU GPL = Class B).

#### 4F: Toxic Intermediate Screening

**CD-MINE (Chemical Damage MINE)**

- **Description:** 180,891 predicted spontaneous metabolic reactions. Identifies damage-prone intermediates and end products distributed among metabolic pathways. Critical for flagging toxic intermediates that accumulate in engineered strains.[^22]
- **Licensing:** Class A (MIT, Argonne National Laboratory / ANL).
- **Stack Status:** In-stack (Class A). Populates the "Toxic intermediate flags" dossier field.

**QSAR-based toxicity models:** RDKit (BSD) provides the molecular descriptors. Machine learning toxicity models trained on Tox21 data (e.g., DeepTox, deep-tox via TensorFlow) provide screening. All Class A.

#### 4G: Competing Pathway Simulation

**OptKnock (Bilevel MILP for Gene Knockout Design)**

- **Description:** Bilevel programming framework suggesting gene deletion strategies that couple product biosynthesis with biomass formation. Identifies metabolic bottlenecks to redirect flux toward target compounds.[^62][^63]
- **Licensing:** Class B (GAMS implementation; COBRApy implementation is Class A).
- **Stack Status:** In-stack (Class B for GAMS; Class A via cameo/COBRApy reimplementation).

**OptForce**

- **Description:** Identifies all possible metabolic interventions (overexpression, knockdown, knockout) to meet a pre-specified overproduction target. More comprehensive than OptKnock: classifies reactions as MUST-UP, MUST-DOWN, or knockout targets.[^64]
- **Licensing:** Class A (published algorithm; COBRApy implementation available).
- **Stack Status:** In-stack (Class A). The recommended tool for generating the "Competing pathway interference map" dossier field.

***

### Layer 5: Iterative Optimisation — BoTorch Active Learning Loop

The BoTorch Bayesian optimisation loop is the adaptive intelligence engine of the pipeline. After an initial in silico screening pass (Layer 4), it selects the most informative strain designs for the next experimental or simulated round, maximising information gain per experiment.

#### BoTorch Integration Architecture

**BoTorch** (Facebook Research / Meta, MIT license) is the primary framework. The multi-objective formulation treats the pipeline optimisation problem as:[^65][^66]

- **Objectives (maximise):** Titer, Yield, Volumetric Productivity
- **Constraints (minimise / bound):** Metabolic Burden Score, Toxic Intermediate Risk Score
- **Acquisition function:** `qNEHVI` (q-Noisy Expected Hypervolume Improvement) — the recommended acquisition function for batch noisy multi-objective optimisation in BoTorch. Directly applicable to the metabolic engineering setting where each candidate strain generates a noisy measurement.[^65]
- **Surrogate model:** Gaussian Process (GP) with Matérn 5/2 kernel for each objective. For higher-dimensional input spaces (many gene modification parameters), Scalable GP or Deep Kernel Learning (DKL) surrogates are preferred.

**Published Metabolic Engineering Applications of BoTorch/Bayesian Optimisation:**

1. **JBEI ART (Automated Recommendation Tool, 2020):** Probabilistic modelling with sampling-based optimisation to guide DBTL cycles. Applied to renewable biofuels, fatty acids, and tryptophan production. Improved tryptophan titer and productivity by 74% and 43% respectively vs. best training designs. Apache 2.0 license (GitHub: JBEI/ART).[^67][^68][^69][^70]

2. **Multi-fidelity BO for syngas fermentation (2023):** BoTorch `qMFKG` (multi-fidelity Knowledge Gradient) used to optimise gas conversion rate in industrial-scale bioreactor, coupling a low-fidelity ideal-mixing model with a high-fidelity CFD model. Directly applicable to the pipeline's bioreactor scale-up prediction layer.[^71][^72]

3. **Simulated DBTL cycle comparison (2023):** Systematic evaluation of ML methods in metabolic engineering DBTL loops. Bayesian methods outperform random sampling and one-shot designs across simulated datasets.[^73]

4. **Knowledge-driven DBTL (2025):** Mechanistic DBTL cycle for dopamine production in E. coli, integrating Bayesian learning with metabolic kinetic models.[^74]

**Active Learning with Automated Laboratory Platforms:**

- **Automated strain construction for biosynthetic pathway screening (2025):** Modular, robotic-integrated protocol for DBTL cycle automation. Source code released open-source.[^75]
- **JBEI (2026):** AI and lab automation demonstrated to dramatically speed up fermentation strain development, with biosensor-based pathway detection closing the measurement loop.[^76][^77]
- **Agile BioFoundry (DOE-funded):** Multiple CROs and DOE laboratories operate robotics-based DBTL platforms. Partners include JBEI, NREL, ANL, PNNL.

**BoTorch Multi-Objective Implementation Details:**

The BoTorch `botorch.acquisition.multi_objective.logei.qLogNEHVI` is the state-of-the-art acquisition function for this problem class. It handles:
- Batch parallelism (multiple strains built simultaneously)
- Noisy objectives (experimental measurement error)
- Reference point selection (worst-case known outcome)
- Constraint handling (burden ≤ threshold, toxicity ≤ threshold)

***

### Layer 6: Host Engineering Specification

Converts the optimised pathway design into an implementable genetic modification plan: which genes to insert (knock-in), which to delete (knock-out), which to up-regulate or down-regulate, with promoter selections, RBS sequences, codon-optimised coding sequences, and CRISPR guide RNA designs.

#### Cello 2.0 — Genetic Circuit Design Automation

- **Description:** Framework for programming genetic circuits in living cells. Input: Verilog hardware description language specification of circuit logic. Output: complete DNA sequence encoding the circuit.[^78][^79][^80][^81]
- **Licensing:** Class A (MIT license, GitHub: CIDARLAB/cello).[^78]
- **Capability:** Converts logic specifications (AND, OR, NOT gates, oscillators, toggle switches) into genetic implementations using characterised transcriptional repressors. Database of gates characterised in Voigt Lab (MIT).
- **Cello 2.0** (2022): Open-source Java, released with improved gate characterisation and multi-organism support.[^81]
- **Pipeline Use:** Design dynamic metabolic switching circuits (e.g., growth-phase → production-phase switching). Directly relevant to Domain 3.3 (SAF/biofuels) optogenetic control integration.

#### iBioSim

- **Description:** Computer-aided design tool for genetic circuit modelling and simulation. Complements Cello with dynamic simulation of circuit behaviour.
- **Licensing:** Class A (Apache 2.0).
- **Stack Status:** In-stack (Class A).

#### CRISPR Guide RNA Design

- **CHOPCHOP:** Online tool for CRISPR/Cas9 guide RNA design. Academic open-source.
- **Benchling CRISPR:** Class E (commercial).
- **CRISPRa/CRISPRi tools:** For transcriptional up/downregulation without genome editing. Relevant for transient pathway modulation.
- **Stack Status:** CHOPCHOP (Class C); academic Python implementations (Class A) available.

#### Promoter and RBS Selection

- **Salis RBS Calculator v2.0** (Penn State): Predicts and designs RBS sequences with precise translation initiation rate targets. Class A (open-source). Core stack tool.[^60][^58]
- **iGEM Registry promoter library:** Public domain promoter sequences characterised for E. coli and S. cerevisiae.[^23]
- **OSTIR** (Open Source Translation Initiation Rates): Python package for predicting translation initiation rates in bacteria. Class A (MIT).[^82]

#### Gene Knockout Strategy Design

**OptKnock** and **OptForce** (documented in Layer 4G above) generate the knockout/overexpression targets. The Layer 6 function translates these metabolic engineering targets into concrete molecular biology specifications:

- Knock-out: CRISPR guide RNA + repair template sequence
- Knock-in: Codon-optimised gene sequence + promoter + RBS + terminator
- Upregulation: Stronger promoter swap or additional gene copy
- Downregulation: CRISPRi guide RNA or promoter attenuation

***

### Layer 7: Output Dossier Generation

The ranked output layer assembles all computed data into the structured Metabolic Pathway Engineering Dossier.

#### Multi-Objective Ranking Framework

- **BoTorch Pareto front:** Pathways are ranked on the Pareto front of the multi-objective (Titer, Yield, Productivity) maximisation problem. Each Pareto-optimal pathway represents a non-dominated trade-off between objectives.
- **Risk tier assignment:** Confidence intervals from the GP surrogate model provide uncertainty bounds for each predicted KPI. Pathways with wide confidence intervals receive a higher risk tier classification.
- **Hypervolume indicator:** The hypervolume dominated by the Pareto front serves as a single aggregate measure of solution quality, enabling comparison between retrosynthesis strategies.

#### Uncertainty Quantification

- GP surrogate models provide posterior predictive distributions over all objectives.
- Deep Ensemble methods (multiple independent neural networks predicting the same objective) provide epistemic uncertainty estimates for data-sparse regions.
- Calibration assessment: The pipeline should compare GP posterior coverage (fraction of experiments falling within predicted confidence intervals) as a reliability metric.

#### Literature RAG (Retrieval-Augmented Generation)

- **Vector database:** All retrieved papers stored as embeddings. FAISS (Facebook AI Research, MIT license) or ChromaDB (Apache 2.0) as the vector store.
- **Embedding model:** ESM-2 protein embeddings for enzyme sequences; Sentence-Transformers (MIT) for text.
- **LangGraph RAG node:** A dedicated LangGraph node retrieves the top-5 papers per pathway candidate based on cosine similarity of pathway description embeddings to paper abstract embeddings.
- **Source databases:** PubMed Central (open access), bioRxiv/chemRxiv, JBEI open publications, Wiley Open Access.

#### Structured Output Schema

- **Pydantic v2** (MIT license): Validates all dossier fields against their type specifications before delivery.
- **JSON Schema:** Canonical dossier schema definition.
- **Output format:** JSON + human-readable PDF, generated via a LangGraph report-generation node.

#### Cost Estimation Model

- Wet-lab validation cost estimate is computed from the number of genetic modifications (CRISPR edits), number of pathway genes (expression constructs), and estimated fermentation experiments.
- CRO partner pricing models (Twist Bioscience for DNA synthesis, Genewiz for cloning, Evonik/BASF contract fermentation) are parameterised from published price ranges.

***

## Part III: Application Domains — Detailed Coverage

### Domain 3.1: Industrial Chemicals

**Target outputs:** Bio-based solvents (ethanol, butanol, acetone), organic acids (succinic, lactic, itaconic), polymer monomers (1,4-BDO, 3-HPA), commodity chemicals.

**Syngas Fermentation Sub-Domain (Priority Research Area):**

Acetogenic bacteria represent a major commercial frontier for industrial chemicals from waste carbon. The primary organism is *Clostridium autoethanogenum*, which fixes CO/CO₂ via the **Wood-Ljungdahl pathway** (WLP), the most energy-efficient known carbon fixation pathway.[^83][^84][^85]

- **Wood-Ljungdahl pathway:** Fixes CO and CO₂ into acetyl-CoA, which feeds into ethanol, acetate, and 2,3-butanediol production. Two key enzyme activities: CODH (carbon monoxide dehydrogenase) and ACS (acetyl-CoA synthase).[^83]
- **Commercial scale:** LanzaTech operates industrial-scale *C. autoethanogenum* fermentation using steelworks off-gases (CO-rich syngas). LanzaJet extends this to sustainable aviation fuel production.
- **Genetic tools:** CRISPR/nCas9 has been deployed successfully in *C. autoethanogenum* for targeted gene deletion. Adaptive laboratory evolution (ALE) has identified phenotype-improving mutations.[^86][^87]
- **Metabolic versatility:** *C. autoethanogenum* achieves complete CO and H₂ conversion; strain RE3 (deletion of CLAU_0471) shows faster autotrophic growth, no yeast extract requirement, and robustness in bioreactor continuous culture.[^87]
- **Moorella thermoacetica:** Thermophilic acetogen (55°C optimum). Higher temperature fermentation reduces contamination risk and improves gas solubility.

**GEM Availability:** *C. autoethanogenum* GEMs are available (published in metabolic engineering literature); not currently in BiGG but downloadable from source publications.

**Pipeline Screening Endpoints:** Titer (g/L ethanol or target chemical), yield (g/g CO₂ fixed), CO conversion efficiency, volumetric productivity (g/L/h), feedstock flexibility score.

**Key CRO/Industry Partners:** LanzaTech (Chicago, Class A open IP commitment in some programs), Evonik (specialty chemical co-production), BASF Bioprocessing, Genomatica (1,4-BDO platform).

### Domain 3.2: Specialty and Fine Chemicals

**MVA (Mevalonate) and MEP (Methylerythritol Phosphate) Pathways:**

These are the two canonical terpene biosynthesis frameworks.[^88][^89][^90][^91]

**MEP Pathway (native to bacteria and plastids):**
- Starts from pyruvate + GAP → DXP → MEP → CDP-ME → HMBPP → IPP + DMAPP
- Higher theoretical yield than MVA (less carbon lost as CO₂)
- Tightly regulated in E. coli; requires careful flux balancing of intermediates[^90][^88]
- Key control point: dxs (DXP synthase) as the first committed step; IPP and DMAPP accumulation drives terpene production
- Chromosomal integration of entire MEP pathway operon demonstrated to improve geraniol production[^88]

**MVA Pathway (native to eukaryotes, archaea):**
- Starts from acetyl-CoA → HMG-CoA → MVA → MVP → MVPP → IPP
- Widely installed in E. coli for high-titer terpenoid production
- β-carotene production: 122.4 mg/L in flask culture with hybrid MEP+MVA strategy[^92]
- MVA pathway from Enterococcus faecalis (mvaE, mvaS genes) is the most characterised heterologous set for E. coli[^93]

**Industrial Applications:**
- Farnesene (SAF precursor): MVA pathway in S. cerevisiae; Amyris achieved industrial-scale production[^94]
- Artemisinic acid (antimalarial precursor): MVA pathway in S. cerevisiae; Keasling Lab benchmark case
- β-carotene, lycopene (food pigments): MEP pathway in E. coli
- Nootkatone, linalool (fragrance): MVA pathway in S. cerevisiae

**Key CRO/Industry Partners:** DSM-Firmenich, Givaudan, IFF, Evonik Specialty Nutrition, Evolva.

### Domain 3.3: Sustainable Aviation Fuel (SAF) and Biofuels

**Key Products and Pathways:**
- **Farnesene:** C15 sesquiterpene; MVA pathway in yeast → hydrogenation to farnesane (jet fuel blendstock). Amyris-Total collaboration demonstrated commercial-scale production and 10% farnesane blends in jet fuel.[^94]
- **Isobutanol:** 2-keto-isovalerate pathway from pyruvate in E. coli and S. cerevisiae. Gevo holds IP; biosynthesis from glucose achieves g/L titers.
- **ASTM D7566 Compliance:** Synthetic aviation fuels must meet ASTM D7566 standard. Hydroprocessed esters and fatty acids (HEFA), synthesised iso-paraffins (SIP), and alcohol-to-jet (ATJ) are approved pathways.

**JBEI (Joint BioEnergy Institute) — Priority Open-Science Source:**
- JBEI is managed by Lawrence Berkeley National Laboratory (Berkeley Lab) and funded by DOE[^95][^96]
- **ART (Automated Recommendation Tool):** Machine learning DBTL tool, Apache 2.0 license, GitHub: JBEI/ART[^69][^97][^67]
- **BiOPKS pipeline:** Multi-functional type I polyketide synthase (PKS) and monofunctional enzyme chemical biosynthesis platform[^98]
- **Database of Lignin Modifying Enzymes:** Open research tool[^98]
- **2026 AI + Automation + Biosensor paper:** Demonstrated AI and lab automation for synthetic jet fuel development using biosensors to detect pathway bottlenecks[^77][^76]
- **Open datasets:** As a DOE-funded national lab, JBEI publishes datasets under open-science mandate.

**NREL (National Renewable Energy Laboratory):**
- Specialises in lignocellulosic feedstock processing and fermentation scale-up
- Publishes CFD bioreactor models and techno-economic analysis tools
- NREL Bioreactor CFD models (OpenFOAM-based) are publicly available[^99]

### Domain 3.4: Pharmaceutical Intermediates

**De Novo Biosynthesis of Complex Natural Products:**

The landmark Galanie et al. 2015 paper demonstrated complete biosynthesis of opioids (thebaine, hydrocodone) in *S. cerevisiae* from glucose, requiring expression of 21–23 enzyme activities from plants, mammals, bacteria, and yeast. This remains the defining proof-of-concept for multi-step complex natural product biosynthesis in yeast.[^100][^101][^102]

**Current SOTA in Multi-Step Pathway Implementation:**

- **Benzylisoquinoline alkaloids (BIAs):** Total opioid titer up to 131 mg/L achieved through spatial engineering and high-density fermentation[^101]
- **Isoflavonoids:** 94-fold improvement through iterative screening-reconstruction-application framework in S. cerevisiae[^103]
- **Kratom monoterpene indole alkaloids (MIAs):** De novo production of mitragynine in S. cerevisiae through 5-step synthetic pathway[^104]
- **Xanthohumol (prenylated flavonoid):** De novo from glucose in brewing yeast, 83-fold improvement in precursor[^105]

**Pharmaceutical CRO Partners:** Asymchem, WuXi AppTec biosynthesis division, Lonza Biological R&D, CDMOs with biosynthesis capabilities.

**GMP-Readiness Screening:** The pipeline must flag whether predicted pathway enzymes have been expressed in validated GMP chassis organisms (primarily E. coli and S. cerevisiae with USP/FDA precedent). Stereochemical purity prediction requires quantum chemistry scoring (Layer 4.5 / Intersection 4.2).

### Domain 3.5: Food and Flavour Ingredients

**Human Milk Oligosaccharides (HMOs):**

HMOs are a high-growth segment with significant commercial interest. Key HMOs in production: 2'-fucosyllactose (2'-FL), 3-fucosyllactose (3-FL), lacto-N-tetraose (LNT), lacto-N-neotetraose (LNnT), 3'-sialyllactose (3'-SL), 6'-sialyllactose (6'-SL).[^106][^107]

**Host organisms for HMO biosynthesis:**[^107][^108][^106]
- **E. coli BL21/K-12 derivatives:** Most developed. 2'-FL production at gram/liter scale. Fastest genetic modification cycle. GEM: iML1515.[^108]
- **S. cerevisiae:** Emerging platform. Better suited for glycosyltransferases requiring eukaryotic folding.
- **B. subtilis:** Generally regarded as safe (GRAS) status makes it attractive for food-grade production. GEM: iYO844.
- **Lacto-N-biose pathway** in E. coli is the most established, using lactose as acceptor and UDP-galactose + UDP-GlcNAc as donors.

**Food-Grade Safety Pathway:** GRAS (Generally Recognized as Safe) designation requires: (1) safety assessment data, (2) organism track record, (3) absence of toxigenic genes. The pipeline should include a GRAS-readiness flag based on organism classification and pathway intermediate toxicity screening.

**Additional Food Ingredients:**
- **Vanillin:** De novo from glucose in S. cerevisiae (Evolva approach). MVA pathway + feruloyl-CoA → vanillin aldehyde
- **Steviol glycosides:** Multi-step from glucose in S. cerevisiae; >80% of sweetness market shifting to biosynthetic
- **Nootkatone:** Sesquiterpene fragrance; P450 oxidation of valencene; MVA pathway in yeast

***

## Part IV: Intersectional Science Mapping

### 4.1: Information Theory ↔ Metabolic Networks

Metabolic networks encode information about the cell's biochemical state. The maximum entropy (MaxEnt) principle — derived from Shannon's information theory — provides a rigorous framework for predicting metabolic flux distributions from incomplete measurements.[^109][^110][^111][^112]

**Key Tool:** The **MaxEnt FBA method** constrains the metabolic flux distribution to the maximum entropy solution consistent with measured fluxes. This is equivalent to compressed sensing in signal processing — recovering a sparse signal (flux distribution) from incomplete measurements (measurable exchange fluxes).[^109]

**Published result:** MaxEnt decomposition of flux distributions correctly predicts intracellular flux distributions from external flux measurements in E. coli and S. cerevisiae. Formulated as a constraint-based optimisation equivalent to maximum entropy principle from statistical mechanics.[^112][^109]

**Information-theoretic objective functions:** MooSeeker (2023) implements a multi-objective pathway design algorithm with thermodynamic feasibility as one of three design criteria, using an NSGA-II multi-objective evolutionary algorithm.[^113]

**Shannon entropy of reaction networks as ML feature:** Not yet standard practice, but network entropy measures are used in metabolic network robustness analysis. The pipeline should compute network entropy (degree distribution entropy) as a structural feature for ML pathway scoring models.

**Pipeline integration:** MaxEnt-FBA can replace parsimonious FBA as the default flux estimation method, providing a statistically grounded flux prediction rather than a minimum-norm approximation.

### 4.2: Statistical Mechanics / Non-Equilibrium Thermodynamics ↔ Enzyme Kinetics

Every enzymatic step is a non-equilibrium thermodynamic process. The Gibbs free energy change ΔrG'° sets the thermodynamic driving force and direction of each reaction.

**eQuilibrator 3.0** is the primary tool for ΔrG'° calculation in metabolic engineering contexts. **PyTFA** integrates these thermodynamic constraints into the FBA framework.[^53][^19][^18]

**Thermodynamic pathway feasibility profiling:**
- MDF (Max-min Driving Force) analysis: optimises metabolite concentrations to maximise the minimum thermodynamic driving force across all pathway steps[^114][^20]
- Enzyme Cost Minimisation (ECM): combines thermodynamics with kinetics to find minimum enzyme investment for a given pathway flux[^20]

**Fluctuation theorems in enzyme catalysis:** Experimental work applying the Jarzynski equality and Crooks fluctuation theorem to single-molecule enzyme studies shows temperature-independent tunnelling rate contributions (classical hallmark of quantum tunnelling) in DHFR, alcohol dehydrogenase, and aromatic amine dehydrogenase. This connects Intersections 4.2 and 4.5.[^115]

**Non-equilibrium thermodynamics of fermentation:** Biothermodynamic analysis (Le Chatelier's principle, Gibbs energy of coupled reactions) allows prediction of the driving force for multi-step pathways including the glucagon biosynthesis pathway and anaerobic PHB production.[^116][^117]

**Kinetics-thermodynamics trade-off:** Near-equilibrium reactions are thermodynamically reversible but kinetically slow; reactions with large negative ΔrG'° are fast but cannot easily be reversed for regulation. The pipeline should flag reactions with |ΔrG'°| < 5 kJ/mol as near-equilibrium (requiring careful kinetic engineering) and those with ΔrG'° << 0 as irreversible fixed points.[^117]

### 4.3: Graph Theory / Network Topology ↔ Metabolic Network Architecture

A genome-scale metabolic network is a directed bipartite graph: metabolite nodes connected to reaction nodes. This graph has measurable topological properties applicable to metabolic engineering.[^118]

**GNN for metabolic networks:**
- **FlowGAT** (2024): Graph Neural Network model predicting gene essentiality from FBA-solution-constructed graphs. MIT license.[^118]
- **GNN-SOM** (2023): GNN model for site-of-metabolism prediction in enzymatic reactions. Trained on enzymatic data from metabolic databases.[^119][^120]

**Network centrality for target identification:**
- **Betweenness centrality** identifies bottleneck metabolites that many pathways pass through — overproduction targets risk competing with essential metabolic functions at these nodes
- **COBRApy** provides graph-theoretic analysis methods (NetworkX integration).[^40]

**Percolation theory for robustness:** Metabolic network connectivity analysis with COBRApy gene knockout simulation is directly equivalent to percolation theory — identifying which fraction of gene knockouts are lethal.[^40]

**Scale-free topology:** Metabolic networks exhibit power-law degree distributions (Barabási et al.), meaning a small number of "hub" metabolites (ATP, NADH, acetyl-CoA, pyruvate) participate in a disproportionate number of reactions. Engineering pathways through hub metabolites carries high interference risk — the competing pathway interference map must flag all hub metabolite interactions.

### 4.4: Control Theory ↔ Gene Regulatory Networks

Gene regulatory networks are feedback control systems, and metabolic pathway engineering is fundamentally a control engineering problem.[^121]

**Dynamic metabolic control strategies:**
- **Two-phase dynamic regulation:** Growth phase (biomass accumulation) followed by production phase (pathway expression). Light-controlled switching (optogenetics) can achieve 1.6× isobutanol titer increase vs. uncontrolled expression.[^121]
- **Autonomous dynamic regulation:** Intermediate-based biosensors autonomously control gene expression based on metabolite accumulation — a direct implementation of feedback control.[^121]

**Cello as control circuit design tool:** Cello converts Boolean logic specifications into genetic circuit implementations, directly applying control engineering concepts (flip-flops, logic gates, oscillators) to metabolic pathway regulation.[^79][^80][^78]

**Optogenetic dynamic control (Intersects 4.14):**
- LOV domains, phytochromes, and channelrhodopsins convert light → protein conformational change → gene activation/repression
- Demonstrated applications: isobutanol production in E. coli (blue light control), cell cycle control in yeast (Cdc48 optogenetic intervention, 2023), glycolysis/production phase switching[^122]
- **Optogenetic RBS modulation tools:** OptoGenetics toolbox (LOV-based gene switches, open-source plasmid sequences on Addgene)

**Stability analysis:** Linear systems eigenvalue methods for metabolic steady-state stability (analogous to Routh-Hurwitz stability analysis) are implemented in dynamic FBA (dFBA) frameworks. Oscillatory metabolic states (Hopf bifurcation) are detectable from eigenvalue analysis of the Jacobian of the kinetic model.

### 4.5: Quantum Chemistry / Quantum Biology ↔ Enzyme Catalysis

Enzyme catalysis is not purely classical. Quantum tunnelling of hydrogen atoms has been experimentally confirmed in DHFR, alcohol dehydrogenase, and aromatic amine dehydrogenase through temperature-independent kinetic isotope effects.[^115]

**Open-source QM/MM tools applicable to enzyme active site optimisation:**

- **ORCA:** Efficient quantum chemistry program, widely used for QM/MM calculations. Free for academic use (Class C); commercial license required (Class E). **Alternative (Class A):** Psi4 (BSD license) provides DFT and post-HF methods with Python API.[^123]
- **Psi4:** Open-source quantum chemistry (BSD, Class A). Supports DFT, MP2, CCSD(T). Less feature-complete than ORCA for large-scale enzyme studies.
- **OpenMM:** Open-source molecular dynamics (MIT, Class A). QM/MM extensions via OpenMM-ORCA or PySander interfaces.
- **QM/MM best practices (2023):** Comprehensive best practices guide for biomolecular QM/MM simulations identifies key protocols for enzyme active site modelling.[^124]

**Neural network potentials trained on DFT data:**
- **MACE-OFF** (2025): Transferable machine learning force field for organic molecules. Short-range force field trained on high-level quantum mechanical reference data. Demonstrates accurate peptide folding dynamics and protein secondary structure.[^125]
- **NequIP** (MIT license): E(3)-equivariant interatomic potential. Applied to enzymes via FFAST analysis on DHA (docosahexaenoic acid, a lipid substrate) and stachyose.[^126][^127]
- **ANI (ANAKIN-ME):** Neural network potential trained on DFT data. Applicable to enzyme-substrate interaction modelling for small molecules in active sites. Class A (MIT).

**Enhanced sampling QM/MM for kcat calculation (2024):** Direct calculation of enzymatic reaction rate constants without transition-state theory assumptions, accounting for dynamical equilibrium between reactive and non-reactive conformations.[^128]

### 4.6: SE(3)-Equivariant Geometry ↔ Enzyme Structure Prediction

This is the most directly transferable intersection from the Zer0pa Materials Science pipeline. The MACE, NequIP, and SevenNet architectures used for interatomic potential prediction employ the same SE(3)-equivariant message passing neural network framework as current state-of-the-art enzyme design models.[^129][^130][^131][^132][^126]

**SE(3)-equivariant architectures for enzyme design:**

- **AlphaFold2:** SE(3)-equivariant attention mechanism. Median TM-score 0.96 on CASP14. Free for research (CC-BY 4.0). Key limitation: static structure prediction; does not capture conformational flexibility.[^133][^134][^135]
- **ESMFold:** Single-sequence structure prediction (no MSA required). 60× faster than AlphaFold2. Open weights (MIT license, Meta AI). Slightly lower accuracy but faster inference — preferred for high-throughput screening of novel pathway enzymes.[^135]
- **RFdiffusion / RFdiffusion2 / RFdiffusion3:**
  - **RFdiffusion** (2023): SE(3)-equivariant diffusion model for de novo protein design. MIT license.[^136]
  - **RFdiffusion3** (2025/2026): All-atom co-diffusion of protein + ligand/DNA simultaneously. 10× speed improvement over predecessors. Represents paradigm shift to atomic-level precision.[^137][^138]
- **ProteinZen** (2025): All-atom protein design via SE(3) flow matching.[^139]

**Materials Science → Enzyme Design Transfer:**
- **MACE-OFF** for enzyme-substrate interaction modelling: MACE architecture from materials science applied to organic molecules (enzyme substrates, cofactors). Demonstrated on protein secondary structure.[^140][^132][^125]
- **SevenNet / NequIP** for enzyme conformational modelling: Same physics (atom positions in 3D space, interaction potentials) as crystal structure stability prediction.[^131][^126][^129]
- The explicit evidence that this transfer is productive: MACE and NequIP applied to DHA (a lipid, directly relevant to fatty acid enzyme substrates).[^127][^126]

### 4.7: Cellular Automata / Complex Systems ↔ Metabolic Oscillations

**Boolean network models of metabolic regulation:**

- **GINsim:** Boolean network modelling and analysis tool. Contains 85 published networks (29 Boolean, 56 multivalued). Free for academic use.[^141]
- **BoolNet (R package):** Boolean network analysis in R. GPL license (Class B).
- **Meta-analysis of Boolean network models (2024):** Analysis of the GINsim repository reveals design principles: gene regulatory networks exhibit more canalization, redundancy, and stable dynamics than expected by chance.[^142]

**Attractor landscape analysis (Waddington landscape):**
- Boolean network attractor analysis identifies stable metabolic states (attractors) that the cell can occupy.
- **Phenotype Control** techniques for Boolean gene regulatory networks (2023): Methods for forcing the system toward a target attractor.[^143]
- **MPBN (minimal playing Boolean network) tool** and **BMA (Boolean model analyser)** provide Class A implementations.

**Phase transitions between metabolic states:** The switching between metabolic steady states (e.g., aerobic → anaerobic, growth → stationary phase) is analogous to a first-order phase transition. Dynamic FBA with switchable objective functions can model these transitions.

### 4.8: Evolutionary Biology / Directed Evolution ↔ Machine Learning

**Natural evolution as Bayesian optimisation:** The directed evolution paradigm — iterative mutation and selection guided by a fitness function — is isomorphic to the BoTorch active learning loop. The BoTorch surrogate model approximates the fitness landscape; the acquisition function selects the next variants to test.

**ProteinGym Benchmark:**
- 250+ deep mutational scanning (DMS) assays spanning millions of mutated sequences[^144][^145][^146][^147][^148]
- Evaluates zero-shot mutation effect predictors using Spearman correlation and Top-10 Recall
- Top-performing models: **ESM-1v** (MIT license, Meta AI), **EVmutation** (MIT license), **EVE** (variational autoencoder, MIT license)

**ESM-1v:** Protein language model fine-tuned for variant effect prediction. Zero-shot: correlates with experimental fitness without any training on the target protein. Spearman ρ ~0.44 on ProteinGym average.[^144]

**EVmutation / EVE:** Unsupervised coevolutionary models. Learn epistatic interactions from multiple sequence alignments. Higher accuracy on deeply characterised protein families.[^147]

**Ancestral sequence reconstruction (ASR):**
- Infers ancestral protein sequences from phylogenetic analysis of extant sequences
- **Result:** Pre-Cambrian enzymes were often 20–30°C more thermostable than extant forms[^149][^150][^151]
- **ASR + ML combination (2024):** ASR generates enzyme libraries; ML predicts the most stable variants, enabling single-step thermostabilisation.[^152]
- ASR from primitive vertebrate ancestors demonstrated remarkable thermostability enhancement in a single step.[^151]

**Integration with BoTorch:** The BoTorch DBTL loop can be initialised with ASR-generated variants (high prior probability of thermostability) rather than random mutants, dramatically improving sample efficiency.

**JBEI ART as implemented directed evolution surrogate:** ART provides sampling-based optimisation to propose next-round variants, with probabilistic production level predictions — this is exactly the BoTorch GP surrogate approach, implemented for metabolic engineering DBTL cycles.[^67][^69]

### 4.9: Fluid Dynamics / Transport Physics ↔ Bioreactor Design

A pathway predicted to produce 50 g/L in a well-mixed flask may produce 15 g/L in a 50,000L industrial fermenter due to mixing heterogeneity, mass transfer limitations, and substrate gradients.

**CFD tools for bioreactor scale-up:**

- **OpenFOAM with bioprocess extensions:** Open-source CFD (GPL, Class B). Widely used for bioreactor hydrodynamics. NREL has published OpenFOAM bioreactor models.[^99]
- **CFD + metabolic model coupling:** Compartment models derived from CFD simulations are coupled with cellular kinetic models to predict spatially heterogeneous metabolite concentrations.[^153][^154][^155]
- **DynoChem Biologics:** Commercial bioprocess scale-up modelling tool (Class E). Alternative: Open-source CFD + MATLAB/Python kinetic models.[^156]

**Multi-fidelity BoTorch for scale-up (2023):** Uses `qMFKG` acquisition function to couple high-fidelity CFD model (expensive) with low-fidelity ideal-mixing model (cheap) for efficient optimisation of gas conversion rate in industrial-scale syngas fermentation bioreactors. This directly addresses the scale-up gap in KPI prediction.[^71]

**Key scale-up considerations encoded in the pipeline:**
- Oxygen transfer rate (OTR) limits aerobic fermentation productivity: OTR = kLa × (C* - CL). kLa is bioreactor-geometry-dependent.
- CO mass transfer limits syngas fermentation: dominant constraint for LanzaTech-type processes
- Mixing time (θ90) determines substrate gradient severity: θ90 ∝ (V/P)^0.3 for stirred tanks
- Shear stress on cells: affects cell viability and morphology in high-viscosity broths

### 4.10: Electrochemistry / Redox Physics ↔ Metabolic Cofactor Engineering

Metabolism is fundamentally an electron transfer system. NADH, NADPH, FADH₂, and ferredoxin are biological electrochemical couples.

**PyTFA redox constraints:** PyTFA explicitly models NAD+/NADH and NADP+/NADPH cofactor balancing with thermodynamic constraints. The reduction potential (E°') of each metabolic half-reaction is computed from Gibbs free energy data (eQuilibrator).[^53]

**GECKO ecGEM cofactor modelling:** Enzyme-constrained models track the stoichiometry of cofactor regeneration, identifying whether the engineered pathway creates a redox imbalance.

**Microbial electrosynthesis (MES):**
- Electroactive organisms (*Geobacter sulfurreducens*, *Shewanella oneidensis*) transfer electrons to/from electrodes.[^157][^158][^159][^160]
- MES enables CO₂ → chemicals driven by renewable electricity, complementing gas fermentation
- Recent advances in MES synthetic biology: engineering efficient microbial cell factories for electricity-mediated bioproduction from waste feedstocks[^158]
- Key limitation: no MES system has attained efficiency compatible with financially feasible scale-up; thermodynamic barriers of Q-pool-dependent extracellular electron uptake are the primary constraint[^161]
- E. coli engineered for MES succinate production: 97% yield (0.97 mol/mol glucose), 1.4× improvement vs. no-electricity control[^162]

**DOE electrobiotechnology datasets:** The DOE Agile BioFoundry and JBEI are primary open-science sources for electrobiotechnology data.

### 4.11: Systems Ecology ↔ Microbial Consortia Design

**MICOM for co-culture modelling:**[^48][^49][^163][^46][^47]
- Constructs community metabolic models from individual GEMs
- Manages exchange fluxes between species and with the environment
- Accounts for relative abundances from 16S/metagenomics
- Two-step optimisation: individual growth maximisation + community-level objective
- **Class A (Apache 2.0)**

**Ecological frameworks applied to synthetic consortia:**
- Lotka-Volterra models for pairwise interaction dynamics (competitive exclusion, mutualism, cross-feeding)
- **MMinte tool:** Estimates pairwise positive/negative interactions in microbial communities from 16S + metabolic models. Class A.[^46]
- **Dynamic FBA for community (dFBA):** Time-dependent simulation of community metabolism.

**Distributed biosynthesis strategy:** Complex multi-step pathways can be distributed across a consortium where each strain performs a specialised module, analogous to supply-chain specialisation. MICOM evaluates whether co-culture is metabolically stable and identifies the optimal species ratio.

### 4.12: Acoustic / Phonon Physics ↔ Enzyme Conformational Dynamics

**Normal mode analysis (NMA) tools:**

- **ProDy** (Python, MIT license): NMA of protein structures from PDB coordinates. Identifies collective vibrational modes, correlated motions, and allosteric communication pathways.[^164]
- **Bio3D** (R package, GPL = Class B): NMA and principal component analysis of protein structural ensembles.
- **GROMACS NMA** (LGPL, Class B): Full-atom molecular dynamics and NMA from energy-minimised structures.[^165]

**Promoting vibrations literature:**
- The "promoting vibrations" hypothesis (Scrutton group, Hammes-Schiffer group): specific protein motions aligned with the catalytic coordinate enhance enzyme activity by orders of magnitude without active site changes.[^115]
- Correlated motion between distant residues (allosteric coupling) modulates active site geometry — a phonon-like long-range effect in the protein lattice.

**ML models predicting enzyme activity from dynamics:**
- **Graph Neural Networks on protein contact maps:** ProDy NMA vectors can be used as GNN input features for activity prediction
- **MD trajectory-based ML:** GROMACS MD trajectories + variational autoencoders to learn latent conformational dynamics correlated with catalytic efficiency. Not yet fully open-source in metabolic engineering context — identified as a research gap.

### 4.13: Signal Processing / Spectral Analysis ↔ Metabolomics Data

**Metabolomics databases:**

- **MetaboLights** (EMBL-EBI): Global open database for metabolomics studies. Cross-species, cross-technique. CC-BY 4.0 license.[^166][^167]
- **HMDB (Human Metabolome Database):** Chemical structures, biological roles, NMR/MS reference spectra. Free for academic and commercial use.
- **METLIN:** Mass spectrometry database. Large coverage of metabolite MS/MS spectra.[^168]

**ML models for raw spectral data:**
- **1D CNN over MS spectra:** Multiple published architectures directly predict metabolite class or pathway membership from raw mass spectrometry signals, bypassing explicit metabolite identification.[^169]
- **Transformer architectures on NMR:** SMILES-based transformers can be inverted to predict structure from NMR spectra. Not yet metabolomics-specific in open form.

**Single-cell metabolomics (Intersects 4.20):**
- New framework (2025): Biosensor-based single-cell profiling reveals metabolic subpopulations as key determinants of bioproduction. Based on pH-sensitive biosensors in yeast, identifies lycopene production heterogeneity.[^170]
- Modulating subpopulation dynamics increases lycopene titer — demonstrating that population heterogeneity is both a problem and an opportunity for fermentation engineering.[^170]

### 4.14: Optics / Photobiology ↔ Optogenetic Metabolic Control

**Optogenetic toolkit:**
- **LOV domains** (light-oxygen-voltage): Blue light sensors (450nm). Used for gene expression control in bacteria and yeast.[^171][^172][^121]
- **Phytochromes:** Red/far-red light (660/730nm) reversible control. Deeper penetration in bioreactors.
- **Channelrhodopsins:** Ion channels activated by light, used for membrane potential control.

**Addgene plasmid library:** Characterised optogenetic constructs for metabolic engineering are deposited on Addgene with open access.[^171]

**Dynamic optogenetic production switching:**
- Isobutanol production in E. coli: 1.6× titer improvement with blue-light-controlled production phase[^121]
- Cdc48-based yeast cell cycle control: optogenetic intervention in cell cycle to increase chemical production[^122]
- Dynamical modelling of optogenetic circuits in yeast for metabolic engineering (published framework, MIT)[^173]

**In-line metabolite monitoring (closing the control loop):**
- Raman spectroscopy: provides real-time, non-invasive measurement of key metabolites (glucose, ethanol, lactate) in bioreactor
- FTIR (Fourier Transform InfraRed): in-line monitoring of metabolite profiles
- Both provide the measurement signal needed to close the optogenetic feedback control loop

**Beer-Lambert law in bioreactors:** Light penetration depth decreases with cell density. For dense industrial fermentations (OD600 > 100), standard LED systems cannot achieve uniform illumination. Near-infrared (NIR) phytochrome systems have better penetration. Bioreactor-scale photon distribution modelling is required for the pipeline's optogenetic design layer.

### 4.15: Astrobiology / Extremophile Biology ↔ Novel Enzyme Discovery

**NASA OSDR (Open Science Data Repository) / GeneLab:**
- Houses 475+ studies with multi-omics datasets from spaceflight experiments and ground-based analogs[^174][^175][^176][^177]
- GeneLab provides transcriptomics, metagenomics, epigenomics, proteomics, metabolomics data
- ISS EXTREMOPHILES experiment: microbial community data from International Space Station[^178]
- Available on AWS Open Data (Registry of Open Data on AWS)[^175]
- License: CC0 / US Government public domain (Class A)

**Key extremophile organisms for industrial biotechnology:**

| Organism | Optimum Temp | Industrial Relevance | GEM Available |
|---|---|---|---|
| *Pyrococcus furiosus* | 100°C | Hyperthermophilic enzymes (amylases, proteases, Pfu DNA polymerase), NADP-dependent oxidoreductases for redox chemistry[^179][^180][^181] | No open GEM |
| *Thermus thermophilus* | 65–72°C | Thermostable enzymes for industrial processes; genome fully sequenced; genetic tools available | Yes (limited) |
| *Sulfolobus acidocaldarius* | 70–75°C, pH 2–3 | Acidothermophile; unique archaeal lipids; S-layer scaffold proteins | Yes |
| *Deinococcus radiodurans* | 25–37°C | Extreme radiation resistance; DNA repair mechanisms for mutagenesis tolerance | Yes |

**Extremozyme applications in the pipeline:**
- Thermostable enzymes allow high-temperature fermentation (reduces contamination risk, improves mass transfer)
- Solvent-tolerant enzymes enable higher product concentrations before toxicity
- Halophilic enzymes function at high salt concentrations (relevant for marine biotechnology feedstocks)

**ThermoMPNN:** Deep learning model for single amino acid mutation thermostability prediction. Provides high-throughput Tm prediction. Class A (MIT).[^182][^183]
**TemStaPro:** Transfer learning approach using protein language model embeddings for thermostability prediction. Class A (MIT).[^184]
**ASR for thermostabilisation** (covered in Intersection 4.8): Single-step 20–30°C stability improvements from ancestral sequence reconstruction.

### 4.16: Cognitive Theory / Biological Computation ↔ Genetic Circuit Design

**Cello as biological Turing machine implementation:**[^80][^79][^78]
- Verilog input → Boolean circuit minimisation → genetic NOR gate network → DNA sequence
- Gates are characterised NOT gates and NOR gates using transcriptional repressor proteins
- Any Boolean function can be implemented by composition of NOR gates (completeness)
- This is identical in principle to digital circuit design from NAND gates

**iGEM Registry as component library:**[^24][^185][^25][^23]
- 20,000+ characterised biological parts
- Public domain / CC0 — unambiguously in production stack
- SynBioHub provides SPARQL query access to structured parts data

**LLM-guided genetic circuit design:**
- No dedicated published open LLM tool for genetic circuit design (2026 survey)
- **Sakana AI Scientist:** Automated scientific hypothesis generation — applicable to proposing novel circuit topologies. The AB-MCTS backbone (TreeQuest) can coordinate multiple LLMs for circuit design search.[^186]
- **DeepRetro / LLM retrosynthesis tools:** The same LLM-guided search architecture is applicable to genetic circuit design as to pathway retrosynthesis.

**Boolean network models:**
- GINsim: 85 published Boolean network models of gene regulatory networks[^141]
- Meta-analysis shows GRNs exhibit canalization (robustness to perturbation), redundancy, and stable dynamics[^142]
- Attractor control methods can target specific metabolic phenotypes[^143]

### 4.17: Geometric Unity / Gauge Theory ↔ Metabolic Network Symmetries

This intersection represents the most advanced theoretical frontier documented in this pipeline. Published applications are sparse but growing.

**Identified applications:**
- **Symmetry in metabolic networks:** Enzyme promiscuity (one enzyme catalysing multiple reactions) defines a symmetry group in reaction space. Horizontal gene transfer (HGT) is a symmetry operation in organismal space — functional properties are preserved under genetic transfer.
- **Topological analysis of metabolic networks:** Topological data analysis (TDA, Betti numbers, persistent homology) has been applied to metabolic network topology. Classes of metabolic network "holes" correspond to cyclic pathways. The tda-tools Python package (Class A) provides implementation.
- **Gauge symmetry and genetic code:** The degeneracy of the genetic code (multiple codons per amino acid) is formally a gauge redundancy — the physical protein is gauge-invariant under codon reassignment. Codon optimisation selects the gauge within this freedom.

**Eric Weinstein Geometric Unity:** No published applications of Geometric Unity specifically to biological network analysis have been identified (2026 survey). This remains a theoretical frontier. Partial applications include:
- Fibre bundle formalism for gene regulatory networks (mathematical biology literature)
- Symmetry-based decomposition of metabolic flux modes

**Pipeline note:** This intersection is catalogued as an aspirational research direction. No production-ready tools exist. The mathematical framework would need to be developed in a separate Zer0pa theoretical research program.

### 4.18: Plasma Physics / Radical Chemistry ↔ Non-Thermal Bioprocessing

**Plasma-assisted lignocellulose pretreatment:**
- Dielectric Barrier Discharge (DBD) plasma treatment generates ROS/RNS that cleave lignin bonds, increasing cellulose accessibility.[^187][^188]
- DBD plasma treatment of maize: 18% increase in biogas production in batch anaerobic digestion.[^187]
- Cold plasma pretreatment of dilute acid-pretreated lignocellulose reduces aldehyde inhibitors.[^188]

**Plasma mutagenesis for strain improvement:**
- Atmospheric pressure plasma treatment generates UV radiation + ROS → DNA mutation without genetic transformation
- Produces non-GMO mutant strains (regulatory advantage in some markets)
- No specific open-source simulation tool identified; strain improvement results are empirical.

**Pipeline scope assessment:** Lignocellulose pretreatment is an upstream feedstock preparation step. It is recommended to include a **feedstock flexibility scoring module** in the pipeline that flags whether the target organism and pathway are compatible with:
1. Glucose (standard)
2. Lignocellulosic hydrolysate (xylose + glucose + inhibitors)
3. CO/CO₂/H₂ syngas
4. Fatty acids / lipids
5. Methanol / C1 compounds

Plasma pretreatment is one preprocessing option for lignocellulosic feedstocks (alongside ionic liquid pretreatment, hydrothermal pretreatment). It should be flagged as applicable when Domain 3.1 or 3.3 pathways are designed for lignocellulosic feedstocks.

### 4.19: Materials Science (Protein as Material) ↔ Enzyme Industrial Stability

**Enzyme thermostability as a materials engineering problem:**

The same MACE/NequIP equivariant neural potential framework used for crystal structure stability prediction in the Materials Science pipeline is directly applicable to enzyme thermostability:[^132][^126][^127][^125][^140]
- **Prediction target:** ΔΔG of folding for a single amino acid mutation
- **MACE-OFF** applied to protein systems: demonstrated accurate secondary structure and vibrational spectrum[^125]

**Dedicated thermostability ML tools:**

- **ThermoMPNN** (MIT license): Deep learning for mutation ΔTm prediction. High-throughput — screens thousands of mutations to identify thermostabilising variants.[^182]
- **TemStaPro** (MIT license): Protein language model-based thermostability prediction.[^184]
- **ProThermDB:** Curated protein thermodynamic data (mutations + stability effects). Training data source for thermostability models. Free for academic use.
- **FireProt** (Class C academic): Automated pipeline for thermostabilisation combining multiple computational methods.

**Open datasets of enzyme stability under industrial conditions:**
- ProThermDB: 10,000+ thermodynamic entries
- ProtaBank: Curated protein stability database, open access
- **ProteinGym** (MIT license): Includes thermostability DMS assays[^145][^148]

**Ancestral sequence reconstruction for industrial stability:** As covered in Intersection 4.8, ASR reliably produces thermostable variants with 20–30°C higher Tm in a single step. This is the most cost-effective thermostabilisation strategy for the pipeline — propose ancestral variants as a default modification for any pathway enzyme with predicted Tm < 50°C.[^150][^149][^151]

### 4.20: Epidemiology / Population Dynamics ↔ Fermentation Population Heterogeneity

A bioreactor contains ~10¹² cells with heterogeneous gene expression states, metabolic activity, and growth rates. Population heterogeneity is a major, underappreciated source of fermentation performance loss.

**Single-cell metabolomics tools:**
- **Biosensor-based single-cell profiling (2025):** Framework for characterising metabolic subpopulations in engineered yeast using fluorescent biosensors. Identified pH-based metabolic subpopulations controlling lycopene production. Demonstrates that shifting subpopulation dynamics can increase production.[^170]
- **Microfluidic scRNA-seq** methods provide single-cell transcriptomics of fermentation populations.

**Mathematical frameworks:**
- **Individual-based models (IBM):** Each cell is a computational agent with its own state. Can predict emergence of metabolically distinct subpopulations.
- **Wright-Fisher model analogues:** Applied to fermentation to model genetic drift in large populations, relevant for tracking accumulation of loss-of-function mutations over long fermentation runs.
- **Population heterogeneity as an engineering variable:** Cellular variability as driver for bioprocess innovation (2025 review). The pipeline should include a heterogeneity risk flag for pathways that produce toxic intermediates (high selective pressure → loss-of-function mutations accumulate rapidly).[^189]

**Agent-based microbial simulation tools:**
- **iDynoMiCS (individuaL-Based DYNamiCS of MIcrobial Communities):** Class A (GPL/Class B). Simulates individual-based dynamics in biofilms and bioreactors.
- **BSim (Bacterial Simulation):** Class A (MIT). Java-based agent-based simulator for bacterial populations.

***

## Part V: Key Organisms — Full Documentation

| Organism | Primary Use | GEM (License) | Key Genetic Tools | Industrial Track Record |
|---|---|---|---|---|
| *E. coli* K-12 | Chemicals, pharma, proteins | iML1515 (CC-BY 4.0)[^10][^8] | CRISPR/Cas9, Rec/ET recombineering, T7 promoter system, RBS Calculator[^58] | Canonical organism; fastest DBTL; amino acids, HMOs, opioids, terpenoids |
| *S. cerevisiae* | Natural products, SAF, pharma | Yeast-GEM / iMM904 (MIT)[^12][^13] | CRISPR/Cas9, homologous recombination, GAL promoter system | Artemisinin, farnesene, opioids, flavonoids; established industrial fermentation |
| *B. subtilis* | Enzymes, food ingredients, HMOs | iYO844 (BiGG, Class A) | CRISPR, SPβ phage systems, IPTG inducible | GRAS status; proteins and vitamins at industrial scale[^107] |
| *C. glutamicum* | Amino acids, organic acids, aromatics | iCN900 (Class A, published) | CRISPR/Cas12a, electroporation, IPTG/arabinose[^190][^191] | >2 million tonnes/year glutamate and lysine; expanding to new chemicals |
| *C. autoethanogenum* | Syngas → chemicals, SAF | Published (not in BiGG) | CRISPR/nCas9, ALE[^86][^84][^87] | LanzaTech industrial scale; ethanol + 2,3-BDO from CO/CO₂ |
| *P. putida* KT2440 | Aromatic valorisation, biosurfactants | iJN746 (BiGG, Class A) | miniTn7 transposons, CRISPR | Solvent tolerance; lignin valorisation; PHA production |
| *Y. lipolytica* | Lipids, oleochemicals, terpenoids | GECKO-generated (MIT) | CRISPR, Golden Gate assembly | Lipid accumulation; ricinoleic acid, TAG production |
| *Pyrococcus furiosus* | Thermostable enzymes, extremozymes | No open GEM | Limited (transformation difficult) | Pfu polymerase industrial; NADP-oxidoreductases[^179][^180] |
| *T. thermophilus* | Thermostable enzyme expression | Limited | Conjugation, natural transformation | Research reagents; industrial enzyme source |
| Clostridia (ABE fermentation) | Solvents (acetone-butanol-ethanol) | iCB925 (C. beijerinckii) | CRISPR, transposons | Historical ABE process; re-emerging for butanol |

***

## Part VI: Licensing Classification — Complete Stack Summary

### Class A Tools (In Production Stack)

| Tool | Function | License | Source |
|---|---|---|---|
| COBRApy | Flux Balance Analysis core | Apache 2.0 | opencobra.github.io |
| GECKO 3.0 | Enzyme-constrained FBA | MIT | SysBioChalmers/GECKO |
| MICOM | Community metabolic modelling | Apache 2.0 | micom-dev.github.io |
| ECMpy 2.0 | Lightweight enzyme-constrained FBA | MIT | Published |
| ETFL | Expression + thermodynamic constraints | Apache 2.0 | EPFL-LCSB/etfl |
| eQuilibrator 3.0 API | Thermodynamic scoring | MIT | equilibrator.weizmann.ac.il |
| PyTFA | Thermodynamics-based FBA | Apache 2.0 | EPFL-LCSB/pytfa |
| dGPredictor | Novel reaction ΔrG prediction | MIT | Published |
| DLKcat | kcat prediction (GCN) | MIT | Published |
| TurNuP | kcat prediction (Transformer) | MIT | AlexanderKroll/kcat_prediction |
| DeepEnzyme | kcat prediction (improved) | MIT | Published |
| RetroPath2.0/3.0 | Retrosynthetic pathway generation | MIT | Published/KNIME |
| BioNavi | Hybrid retrosynthesis | MIT | biopathnavi.qmclab.com |
| novoStoic2.0 (dGPredictor) | De novo pathway + ΔrG (Python component) | MIT | AlphaSynthesis |
| CD-MINE | Toxic intermediate screening | MIT | ANL/minedatabase |
| OptForce | Gene target identification | Apache 2.0 (COBRApy) | COBRApy |
| OptKnock (reimplemented) | Gene knockout design | Apache 2.0 | COBRApy/Cameo |
| Cameo | Metabolic engineering + codon opt | Apache 2.0 | cameo-chem.github.io |
| OSTIR | Translation initiation rate | MIT | Published |
| Salis RBS Calculator | RBS design | Open-source | salislab.net |
| Cello 2.0 | Genetic circuit design | MIT | CIDARLAB/cello |
| iBioSim | Circuit modelling/simulation | Apache 2.0 | Published |
| JBEI ART | ML DBTL recommendation | Apache 2.0 | JBEI/ART |
| BoTorch | Bayesian optimisation | MIT | pytorch.org/botorch |
| LangGraph | Agent orchestration | MIT | langchain.com/langgraph |
| ESMFold | Enzyme structure prediction | MIT | Meta AI |
| RFdiffusion | De novo enzyme design | MIT | RosettaCommons |
| ThermoMPNN | Thermostability prediction | MIT | Published |
| TemStaPro | Thermostability prediction | MIT | Published |
| ProDy | NMA / protein dynamics | MIT | prody.csb.pitt.edu |
| MICOM | Community modelling | Apache 2.0 | micom-dev.github.io |
| MetaNetX | Cross-database identifier reconciliation | CC-BY 4.0 | metanetx.org |
| Rhea | Curated reactions | CC-BY 4.0 | ebi.ac.uk/rhea |
| BiGG Models + iML1515 | GEM repository + E. coli model | CC-BY 4.0 | bigg.ucsd.edu |
| iGEM Registry | Genetic parts library | CC0 / Public Domain | registry.igem.org |
| NASA OSDR / GeneLab | Extremophile multi-omics | CC0 (US Gov) | osdr.nasa.gov |
| MetaboLights | Metabolomics datasets | CC-BY 4.0 | ebi.ac.uk/metabolights |
| SELFIES | Molecular representation | Apache 2.0 | Published |
| MACE-OFF | Organic molecule force field | MIT | ACEsuit |
| TreeQuest (Sakana AI) | Multi-model tree search inference | Apache 2.0 | SakanaAI/treequest |
| GINsim (academic) | Boolean network analysis | LGPL (Class B) | ginsim.org |
| OpenFOAM | CFD bioreactor modelling | GPL (Class B) | openfoam.org |
| Psi4 | QM calculations | BSD | psicode.org |

### Class B Tools (In Stack — Outputs Commercially Owned)

| Tool | Function | License |
|---|---|---|
| GINsim | Boolean network modelling | LGPL |
| OpenFOAM | CFD simulation | GPL |
| BoolNet (R) | Boolean network analysis | GPL |
| GROMACS NMA | Molecular dynamics + NMA | LGPL |
| Bio3D (R) | Protein structure analysis | GPL |
| OptKnock (GAMS) | Gene knockout design | GAMS (copyleft runtime) |

### Class C Tools (Not in Production Stack — Academic Only)

| Tool | Capability Gap | Best Class A/B Alternative |
|---|---|---|
| KEGG (API/bulk) | Comprehensive pathway maps and organism database | MetaNetX + BiGG + Rhea (collective coverage ~85%) |
| ATLAS of Biochemistry | Predicted novel biochemical reactions at scale | CD-MINE + novoStoic2.0 on-the-fly generation |
| novoStoic2.0 (web server) | Integrated pathway design GUI | RetroPath3.0 + dGPredictor + COBRApy |
| FireProt | Automated thermostabilisation pipeline | ThermoMPNN + ASR + TemStaPro |
| BRENDA (commercial use) | Manual-curated enzyme kinetics depth | TurNuP + DLKcat + DeepEnzyme (ML surrogates) |

### Class D/E Tools (Not in Stack)

| Tool | Alternative (Class A/B) | Capability Gap |
|---|---|---|
| ORCA (QM) | Psi4 (BSD) + OpenMM | ORCA has better DFT functional coverage for enzyme active sites |
| Gurobi (LP solver) | GLPK (GPL) + HiGHS (MIT) | Gurobi is 10-100× faster for large MILPs |
| DynoChem | OpenFOAM CFD + Python kinetics | DynoChem has industry-validated scale-up models |
| AlphaFold2 server | ESMFold + ColabFold (MIT) | Server access not needed; local deployment available |
| Benchling CRISPR | CHOPCHOP + open Python tools | Feature parity for guide RNA design |

***

## Part VII: Benchmark and Performance Metrics

### Retrosynthetic Pathway Generation

| Tool | Pathway Coverage | Novel Discovery Rate | Compute Time |
|---|---|---|---|
| RetroPath2.0/3.0 | ~80% of KEGG pathways reconstructed | Low (rule-limited) | Minutes–hours per target |
| novoStoic2.0 | Higher coverage with de novo steps | Moderate (~10% novel steps validated) | Hours (MILP optimisation) |
| ATLAS-based search | 96% predicted reactions are novel[^4] | N/A (database not a search tool) | Instant (database query) |
| BioNavi (neural) | Validated on natural and non-natural pathways[^35] | High | Minutes per step |
| Deep learning (DeepRetro, 2026) | Not yet benchmarked at scale | High | Seconds per step |

### Enzyme Kinetics Prediction

| Tool | Pearson r (kcat) | R² | OOD Performance |
|---|---|---|---|
| DLKcat | 0.71 | 0.52 | Degrades significantly |
| TurNuP | 0.67 | 0.44 | Generalises to <40% identity[^6] |
| DeepEnzyme | Better than TurNuP on low-similarity enzymes[^57] | ~0.50 | Best current OOD performance |

Note: Experimental kcat variance spans ~6 orders of magnitude. R² ~0.44–0.52 corresponds to meaningful predictive power for pathway ranking but not precise kinetic parameterisation.

### Protein Structure Prediction

| Tool | TM-score (CASP) | Speed | OOD Performance |
|---|---|---|---|
| AlphaFold2 | 0.96 median (CASP14)[^133] | Hours (GPU) | Excellent |
| ESMFold | ~0.92–0.95 | Minutes (single GPU) | Good |
| RFdiffusion3 (2026) | N/A (generative) | 10× faster than predecessors[^137] | Generative (new structures) |

### Fermentation KPI Prediction (Titer / Yield / Productivity)

Current GECKO ecGEM models achieve:
- **E. coli flux prediction error reduction:** 43% vs. standard GEM for B. subtilis; more accurate prediction of 24/25 carbon sources[^51]
- **Essential gene prediction improvement:** 2.5× more correctly predicted essential genes in central carbon pathways[^45]
- **Bias at scale:** All GEM-based predictions are bench-scale. Multi-fidelity BoTorch (CFD + metabolic model) addresses industrial-scale bias.

***

## Part VIII: Key Institutional and Academic Sources

### National Laboratories (DOE Open-Science Mandate)

**JBEI (Joint BioEnergy Institute):**
- Primary source for biofuels synthetic biology tools[^96][^95][^98]
- Open tools: ART (Apache 2.0), BiOPKS, Lignin Modifying Enzyme database[^98]
- 2026 AI+automation+biosensors for synthetic jet fuel[^76][^77]
- All publications and datasets are DOE open-science mandate — freely accessible

**NREL (National Renewable Energy Laboratory):**
- Lignocellulosic feedstock processing and scale-up models
- OpenFOAM CFD bioreactor models published openly[^99]
- Techno-economic analysis (TEA) models for SAF pathways

**ANL (Argonne National Laboratory):**
- Hosts CD-MINE database (toxic intermediate predictions, MIT license)[^22]
- Systems biology and multi-omics integration

**PNNL (Pacific Northwest National Laboratory):**
- Multi-omics and metabolomics datasets
- Environmental metabolomics data

### Key Academic Groups

| Group | Institution | Primary Contribution | Key Tools / Datasets |
|---|---|---|---|
| Salis Lab | Penn State | RBS Calculator, translation initiation prediction[^58][^59][^60] | RBS Calculator v2.0 (open-source) |
| Keasling Lab | Berkeley | Artemisinic acid canonical case; synthetic biology DBTL[^67] | JBEI ART |
| Arnold Lab | Caltech | Directed evolution; Nobel 2018 | ProteinGym benchmark[^144][^146][^147][^148] |
| Nielsen Lab | Chalmers/DTU | Yeast-GEM (iMM904 family); metabolic modelling | Yeast-GEM (MIT, SysBioChalmers) |
| Stephanopoulos Lab | MIT | Metabolic flux analysis methodology | MFA tools |
| Prather Lab | MIT | Pathway design tools; metabolic engineering | Multiple open-source tools |
| Maranas Lab | Penn State | novoStoic; OptKnock; OptForce[^62][^64] | novoStoic, dGPredictor |
| Thiele Group | LCSB/Luxembourg | PyTFA; ETFL; MetaNetX[^53][^3] | PyTFA, ETFL (Apache 2.0) |

### Sakana AI — Specific Tools

**TreeQuest (Apache 2.0):**[^192][^39][^193][^38]
- Multi-model cooperative inference using adaptive branching Monte Carlo tree search (AB-MCTS)
- Released June 2025; GitHub: SakanaAI/treequest
- Pipeline application: Orchestrate multiple LLMs (chemistry specialist, biology specialist, thermodynamics specialist) as a cooperative team for pathway retrosynthesis proposals, with tree search tracking solution quality across branches
- The evolutionary tree search mechanism is isomorphic to directed evolution in sequence space — each branch of the tree corresponds to a variant generation; the tree search selects the most promising branch for further exploration
- Demonstrated 30%+ performance improvement over individual frontier models on ARC-AGI-2[^186]

**AI Scientist:**
- Automated scientific hypothesis generation
- Applicable to the pipeline's literature-grounded RAG layer for automatic identification of novel enzymatic steps not in databases
- Released under Apache 2.0

### International / Public Bodies

**iGEM Foundation:**[^185][^24][^25][^23]
- Registry of Standard Biological Parts: 20,000+ parts, public domain
- SynBioHub provides structured SPARQL access
- Annual iGEM competition generates thousands of new characterised parts annually

**EMBL (European Molecular Biology Laboratory):**
- MetaboLights (CC-BY 4.0): global metabolomics repository[^167][^166]
- UniProt / Swiss-Prot (CC-BY 4.0): canonical protein sequence database

**RIKEN (Japan):**
- KNApSAcK database: metabolomics and plant secondary metabolites
- Systems biology datasets

***

## Part IX: Pipeline Integration Architecture — LangGraph Implementation

### LangGraph Node Map

The LangGraph orchestrator defines the following directed graph:[^194][^195][^196][^197]

```
InputNode (ZPE encoding)
  → KnowledgeLayerNode (load GEM, query KEGG/BiGG/Rhea)
    → RetrosynthesisNode (RetroPath3.0 + novoStoic2.0 + BioNavi)
      → ScreeningNode (COBRApy + GECKO + eQuilibrator + PyTFA)
        → KineticsNode (DLKcat + TurNuP + DeepEnzyme)
          → ToxicityNode (CD-MINE + QSAR)
            → BoTorchOptimisationNode (qNEHVI multi-objective loop)
              → HostEngineeringNode (OptForce + Cello + RBS Calculator)
                → DossierGenerationNode (Pydantic + RAG + cost model)
                  → OutputNode (JSON + PDF dossier)
```

Each node is a Python function encapsulating one pipeline layer. The LangGraph state object carries:
- Target molecule (SELFIES + InChI)
- Host organism GEM
- Current pathway candidates (list of directed graphs)
- Screening scores per candidate (ΔrG profile, titer/yield predictions, burden scores)
- Active learning history (BoTorch model state, observed outcomes)
- Dossier fields accumulated so far

**BoTorch Loop as a LangGraph Conditional Edge:**
The BoTorch node determines whether to continue iterating (if stopping criterion not met) or proceed to host engineering. The stopping criterion is:
- Hypervolume improvement per iteration < threshold (convergence)
- OR: maximum number of virtual screening rounds reached
- OR: a candidate exceeds all minimum threshold KPIs

### Parallelisation Strategy

Multiple pathway candidates can be screened in parallel. LangGraph's `scatter-gather` pattern distributes candidates to parallel ScreeningNodes (one per candidate) and consolidates results in the BoTorchOptimisationNode. This enables full parallelisation of the computationally expensive GECKO + eQuilibrator + DLKcat pipeline across pathway candidates.

***

## Part X-A: GEM Updates (2024–2026 Revisions)

**Yeast9 (S. cerevisiae consensus GEM):**
The Nielsen Lab (SysBioChalmers, Chalmers University) updated the yeast GEM to **Yeast9** in 2024. Yeast9 incorporates single-cell transcriptomics integration capability — 163 condition-specific GEMs constrained by scRNA-seq data from osmotic pressure or reference conditions were generated. Available on GitHub: SysBioChalmers/yeast-GEM, MIT license. The pipeline should use Yeast9 as the default S. cerevisiae GEM, replacing iMM904 for any new development.[^198][^199][^200][^201][^202]

**Yeast-ME-GEM:** The SysBioChalmers group also maintains a Multi-Energy GEM with intracellular constraints (cell volume, protein abundances), enabling more accurate prediction of adaptive responses and metabolic engineering strategies. MIT license.[^203]

**MACE-OFF for Enzyme-Substrate Modelling (Confirmed):**
MACE-OFF (published in JACS 2025) is a series of short-range transferable ML force fields for organic molecules, parameterised for H, C, N, O, F, P, S, Cl, Br, I — the ten most important elements for organic chemistry and biology. It accurately predicts gas- and condensed-phase properties, dihedral torsions of unseen molecules, molecular crystals, and liquids including quantum nuclear effects. It determines free energy surfaces — directly applicable to enzyme-substrate binding free energy calculation. This confirms the materials science → enzyme modelling transfer documented in Intersection 4.6 and 4.19. MACE-OFF is open-source (MIT license).[^204][^205][^206][^207][^208]

***

## Part X: Appendix — Data Provenance, Gaps, and Research Frontiers

### Identified Research Gaps

1. **GEM availability for syngas organisms:** No open BiGG-format GEM for *C. autoethanogenum* or *M. thermoacetica*. Gap mitigation: use published GEM files from academic papers or reconstruct using Model SEED (Class A).

2. **Scale-up prediction accuracy:** All GEM-based KPI predictions are inherently bench-scale. The multi-fidelity BoTorch + CFD approach (Intersection 4.9) addresses this but requires bioreactor geometry specification as an additional input. This should be added to the ZPE input encoding layer in Report 2.

3. **LLM + biosynthesis specialisation:** No dedicated open-weight LLM for biosynthetic pathway generation (analogous to ChemBERTa for chemistry) is available as of April 2026. DeepRetro (2026) and BioNavi (2024) partially address this, but a full foundation model trained on the KEGG + ATLAS reaction corpus is a significant opportunity for Zer0pa or the field.

4. **Novel enzyme design for non-database steps:** When novoStoic2.0 proposes a de novo pathway step with no known enzyme, the pipeline must either (a) propose an engineered enzyme via RFdiffusion + ProteinMPNN design workflow, or (b) flag as experimental (unknown enzyme, high risk tier). The protein design workflow integration (RFdiffusion → ProteinMPNN → ESMFold validation → ThermoMPNN stability → DLKcat kinetics) needs to be specified in Report 2 as a sub-pipeline.

5. **Cofactor balancing at scale:** NAD+/NADPH ratio control is a known bottleneck in industrial fermentation that is not yet quantitatively predictable from genome-scale models alone. PyTFA + GECKO provide partial constraints, but dynamic modelling with Maud (Bayesian kinetic modelling) provides better quantitative coverage for this.

6. **Quantum tunnelling coefficients for enzyme design:** No ML model predicts quantum tunnelling contributions to enzyme kcat from sequence alone. This is an open research problem at the intersection of quantum biology and ML.

### Open Research Frontiers for Zer0pa

1. **ZPE-encoded pathway vectors as input to a unified metabolic transformer:** A foundation model pre-trained on all KEGG/BiGG reactions using SELFIES molecular encoding + protein ESM-2 embeddings as inputs, with pathway performance as output target, would provide a powerful end-to-end predictor.

2. **Gauge-theoretic analysis of metabolic network symmetries** (Intersection 4.17): A formal mathematical program to apply gauge theory to metabolic network analysis. Preliminary step: compute symmetry groups of metabolic networks using NetworkX + SageMath (Class A).

3. **Single-cell population dynamics + BoTorch loop:** Integration of single-cell biosensor data (Intersection 4.20) as a BoTorch objective — not just bulk titer but also production fraction (what fraction of cells are actively producing) as an engineering target.

4. **MACE-OFF for enzyme-substrate binding energy prediction:** Adaptation of the MACE-OFF organic molecule force field for enzyme-substrate interaction energy calculation in active sites, providing a Class

---

## References

1. [SELFIES and the future of molecular string representations - arXiv](https://arxiv.org/abs/2204.00056) - In this manuscript, we look to the future and discuss molecular string representations, along with t...

2. [SELFIES and the future of molecular string representations - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9583042/) - Deep neural networks are increasingly used to create generative models for the design of new molecul...

3. [MetaNetX: a bridge between metabolic resources for enhanced ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12807685/) - MetaNetX integrates biochemical data from a broad range of resources, including ChEBI [13], KEGG [1]...

4. [Updated ATLAS of Biochemistry with New Metabolites and Improved ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7309321/) - The ATLAS of Biochemistry is a database of known and predicted biochemical reactions that was compil...

5. [A novel interpretability framework for enzyme turnover number ...](https://www.sciencedirect.com/science/article/abs/pii/S1046202325000519) - DLKcat leverages Graph Convolutional Networks (GCNs) to extract substrate features and Convolutional...

6. [Turnover number predictions for kinetically uncharacterized ... - Nature](https://www.nature.com/articles/s41467-023-39840-4) - Here, we present TurNuP, a general and organism-independent model that successfully predicts turnove...

7. [BiGG Web API](http://bigg.ucsd.edu/data_access) - BiGG Models can be accessed using a simple web API. Here we provide examples of the API reponses. Al...

8. [iML1515 - BiGG Models](http://bigg.ucsd.edu/models/iML1515) - Model: iML1515. Organism: Escherichia coli str. K-12 substr. MG1655. Genome: NC_000913.3. Model metr...

9. [KEGG API Manual](https://www.kegg.jp/kegg/rest/keggapi.html) - KEGG is an integrated database consisting of sixteen databases (including four Japanese versions) sh...

10. [iML1515, a knowledgebase that computes Escherichia coli traits](https://pmc.ncbi.nlm.nih.gov/articles/PMC6521705/) - iML1515 genome-scale reconstruction. (a) The iML1515 model contains 1,515 open reading frames that e...

11. [Ecoli-GEM: Genome-scale metabolic model for Escherichia coli](https://github.com/SysBioChalmers/Ecoli-GEM) - This repository contains the latest version the Ecoli-GEM, a genome scale metabolic model of Escheri...

12. [Improving the iMM904 S. cerevisiae metabolic model using essentiality and synthetic lethality data](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-178) - BackgroundSaccharomyces cerevisiae is the first eukaryotic organism for which a multi-compartment ge...

13. [Mo2009 | BioModels](https://www.ebi.ac.uk/biomodels/MODEL1507180033) - Mo2009 - Genome-scale metabolic network of Saccharomyces cerevisiae (iMM904). Overview Files History...

14. [BRENDA, the enzyme database: updates and major new developments](https://pmc.ncbi.nlm.nih.gov/articles/PMC308815/) - BRENDA (BRaunschweig ENzyme DAtabase) represents a comprehensive collection of enzyme and metabolic ...

15. [BRENDA Enzyme Database](https://www.brenda-enzymes.org) - Latest BRENDA release. Release 2026.1 - March 4, 2026. Including 124 new and 750 updated enzyme clas...

16. [SKiD: A Structure-Oriented Kinetics Database of Enzyme-Substrate ...](https://www.biorxiv.org/content/10.1101/2025.05.18.654770v2.full-text) - The enzyme-substrate kinetic data in BRENDA, is retrieved from scientific literature using KENDA's (...

17. [MetaNetX: a bridge between metabolic resources for enhanced ...](https://academic.oup.com/nar/article-pdf/54/D1/D617/65551625/gkaf1286.pdf) - MetaNetX integrates biochemical data from a broad range of resources, including ChEBI [13], KEGG [1]...

18. [eQuilibrator 3.0: a database solution for thermodynamic constant ...](https://academic.oup.com/nar/article/50/D1/D603/6445959) - These algorithms have the potential to improve the flux predictions produced by flux analysis (21–23...

19. [[PDF] eQuilibrator 3.0: a database solution for thermodynamic constant ...](https://backend.orbit.dtu.dk/ws/files/267294202/gkab1106.pdf) - For example, metabolic pathway engineering often utilizes promiscuous enzymes to generate novel reac...

20. [Pathway Analysis — eQuilibrator 3.0 documentation](https://equilibrator.weizmann.ac.il/static/classic_rxns/pathway.html) - eQuilibrator can be used to analyze your pathway of interest using one out of two methods: Max-min D...

21. [Updated ATLAS of Biochemistry with New Metabolites and Improved ...](https://pubs.acs.org/doi/10.1021/acssynbio.0c00052) - The ATLAS of Biochemistry (1) is a database of known and predicted biochemical reactions that was co...

22. [Chemical-damage MINE: A database of curated and predicted spontaneous metabolic reactions.](https://linkinghub.elsevier.com/retrieve/pii/S1096717621001804) - Spontaneous reactions between metabolites are often neglected in favor of emphasizing enzyme-catalyz...

23. [iGEM Registry of Standard Biological Parts](https://registry.igem.org) - Registry of Standard Biological Parts ... Meet the synthetic biology experts from across the global ...

24. [Registry of Standard Biological Parts - Wikipedia](https://en.wikipedia.org/wiki/Registry_of_Standard_Biological_Parts) - The Registry of Standard Biological Parts is a collection of genetic parts that are used in the asse...

25. [iGEM Parts Registry - SynBioHub](https://synbiohub.org/public/igem/igem_collection/1) - The iGEM Registry is a growing collection of genetic parts that can be mixed and matched to build sy...

26. [RetroPath2.0 - a retrosynthesis workflow with tutorial and example ...](https://www.myexperiment.org/workflows/4987) - The RetroPath2.0 workflow build a reaction network from a set of source compounds to a set of sink c...

27. [RetroPath2.0: A retrosynthesis workflow for metabolic engineers](https://www.sciencedirect.com/science/article/pii/S1096717617301337) - ... tool, even beyond metabolic design. In summary, we believe ... Design of computational retrobios...

28. [RetroPath2.0: a retrosynthesis workflow for metabolic engineers](https://research.manchester.ac.uk/en/publications/retropath20-a-retrosynthesis-workflow-for-metabolic-engineers/) - The RetroPath2.0 workflow is built using tools developed by the bioinformatics and cheminformatics c...

29. [Pathway design using de novo steps through uncharted biochemical spaces](https://www.nature.com/articles/s41467-017-02362-x) - Existing retrosynthesis tools generally traverse production routes from a source to a sink metabolit...

30. [Pathway design using de novo steps through uncharted biochemical spaces](https://pmc.ncbi.nlm.nih.gov/articles/PMC5766603/) - Existing retrosynthesis tools generally traverse production routes from a source to a sink metabolit...

31. [novoStoic2.0: An integrated framework for pathway synthesis ...](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012516) - Notable examples include novoStoic [7], RetroPath 2.0 [13,14], and BNICE [15], which facilitate the ...

32. [novoStoic2.0: An integrated framework for pathway synthesis ...](https://pubmed.ncbi.nlm.nih.gov/40768560/) - Herein, we introduce novoStoic2.0, an integrated platform that combines tools for estimating overall...

33. [novoStoic2.0: An integrated framework for pathway synthesis ...](https://www.biorxiv.org/content/10.1101/2024.09.27.615368v1) - An integrated platform that combines tools for estimating overall stoichiometry, designing de novo s...

34. [Developing BioNavi for Hybrid Retrosynthesis Planning](https://pmc.ncbi.nlm.nih.gov/articles/PMC11267531/) - ... often leads to more efficient and sustainable pathways. Despite the rapid development of retrosy...

35. [Computational framework for multistep metabolic pathway design](https://www.semanticscholar.org/paper/8e38197db65a343724fa1d4f7a4497a01f0bc77e) - In silico tools are important for generating novel hypotheses and exploring alternatives in de novo ...

36. [DeepRetro discovers retrosynthetic pathways through iterative large ...](https://www.nature.com/articles/s41598-026-38821-z) - Recent work has begun to explore LLMs for retrosynthesis, using them as route generators or as a gui...

37. [Reasoning-Driven Retrosynthesis Prediction with Large Language ...](https://arxiv.org/html/2507.17448v1) - To address these challenges, we introduce RetroDFM-R, a reasoning-based large language model (LLM) d...

38. [Inference-Time Scaling and Collective Intelligence for Frontier AI](https://sakana.ai/ab-mcts/) - We have released the underlying algorithm as TreeQuest, a tree-search software framework for inferen...

39. [SakanaAI/treequest: A Tree Search Library with Flexible API for LLM ...](https://github.com/SakanaAI/treequest) - A flexible answer tree search library featuring AB-MCTS, useful for (but not limited to) LLM inferen...

40. [constraint-based metabolic modeling in Python - cobrapy](https://opencobra.github.io/cobrapy/pubs/) - Simultaneous application of enzyme and thermodynamic constraints to metabolic models using an update...

41. [Simultaneous application of enzyme and thermodynamic constraints ...](https://journals.asm.org/doi/10.1128/spectrum.01705-23) - In addition, geckopy includes a suite of flux analysis algorithms for enzyme-constrained models anal...

42. [Reconstruction of a catalogue of genome-scale metabolic models with enzymatic constraints using GECKO 2.0](https://www.nature.com/articles/s41467-022-31421-1) - Genome-scale metabolic models (GEMs) have been widely used for quantitative exploration of the relat...

43. [Reconstruction of a catalogue of genome-scale metabolic models ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC9246944/) - Here the authors present GECKO 2, an automated framework for continuous and version controlled updat...

44. [[PDF] Geckopy 3.0: enzyme constraints, thermodynamics ... - bioRxiv](https://www.biorxiv.org/content/10.1101/2023.03.20.533446v1.full.pdf) - These GEM models allow for the simulation of the metabolism - e.g. calculating growth and production...

45. [Integration of enzymatic data in Bacillus subtilis genome-scale metabolic model improves phenotype predictions and enables in silico design of poly-γ-glutamic acid production strains](https://microbialcellfactories.biomedcentral.com/articles/10.1186/s12934-018-1052-2) - BackgroundGenome-scale metabolic models (GEMs) allow predicting metabolic phenotypes from limited da...

46. [constraint-based metabolic modeling in Python - cobrapy](https://opencobra.github.io/cobrapy/tags/community-modeling/) - MICOM allows you to construct a community model from a list on input COBRA models and manages exchan...

47. [version 0.39.0 - GitHub Pages](https://micom-dev.github.io/micom/) - MICOM allows you to construct a community model from a list on input COBRA models and manages exchan...

48. [MICOM](https://micom.c3.unam.mx) - MICOM is a Python package for metabolic modeling of microbial communities. ... MICOMWeb: a website f...

49. [micom-dev/micom: Python package to study microbial communities ...](https://github.com/micom-dev/micom) - MICOM is a Python package for metabolic modeling of microbial communities currently developed in the...

50. [ECMpy 2.0: A Python package for automated construction and ...](https://www.sciencedirect.com/science/article/pii/S2405805X24000565) - In contrast to the methodologies of GECKO and AutoPACMEN, ECMpy introduces constraints on the total ...

51. [ECMpy, a Simplified Workflow for Constructing Enzymatic Constrained Metabolic Network Model](https://www.mdpi.com/2218-273X/12/1/65) - Genome-scale metabolic models (GEMs) have been widely used for the phenotypic prediction of microorg...

52. [PyTFA and MatTFA a Python Package and a Matlab Too | PDF - Scribd](https://www.scribd.com/document/1009970086/PyTFA-and-MatTFA-a-Python-Package-and-a-Matlab-Too) - The document presents pyTFA and matTFA, the first implementations of Thermodynamics-based Flux Analy...

53. [pyTFA and matTFA: a Python package and a Matlab toolbox ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6298055/) - TFA integrates the thermodynamics feasibility in the same MILP problem as FBA, and can unbiasedly ac...

54. [dGPredictor: Automated fragmentation method for metabolic reaction free energy prediction and de novo pathway design](https://dx.plos.org/10.1371/journal.pcbi.1009448) - Group contribution (GC) methods are conventionally used in thermodynamics analysis of metabolic path...

55. [[PDF] Multimodal Regression for Enzyme Turnover Rates Prediction - arXiv](https://arxiv.org/pdf/2509.11782.pdf) - For example, DLKcat [Li et al., 2022a] is a famous DL approach for kcat prediction for metabolic enz...

56. [AlexanderKroll/kcat_prediction - GitHub](https://github.com/AlexanderKroll/kcat_prediction) - This repository contains the code and datasets to reproduce the results and figures and to train the...

57. [DeepEnzyme: a robust deep learning model for improved enzyme ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC11880767/) - Trained by a refined dataset, TurNuP outperforms DLKcat in predicting kcat for enzymes with low sequ...

58. [The Ribosome Binding Site (RBS) Calculator can predict ... - GitHub](https://github.com/hsalis/Ribosome-Binding-Site-Calculator-v1.0) - This is a software implementation of the Ribosome Binding Site (RBS) Calculator. ... It is used to d...

59. [salis-lab-protocol-book/design/rbs-library-calculator.md at master](https://github.com/hsalis/salis-lab-protocol-book/blob/master/design/rbs-library-calculator.md) - In Predict mode, the RBS Library Calculator predicts how a ribosome binding site (RBS) library chang...

60. [RBS Library Calculator - GeneticSystemsCalculator](https://salislab.net/software/GeneticSystemsCalculator) - Build genetic systems, low-cost DNA assembly, context aware, autoalign, validate, library cloning co...

61. [Cameo: A Python Library for Computer Aided Metabolic Engineering ...](https://pubs.acs.org/doi/10.1021/acssynbio.7b00423) - Cameo is an open source software project and is freely available under the Apache License 2.0. A ded...

62. [OptKnock - Costas Maranas](https://www.maranasgroup.com/submission/optknock_2.htm) - OptKnock · Step 1: Identify the initial metabolic flux bounds for the wild-type strain · Step 2: Est...

63. [[PDF] OptKnock: A Bilevel Programming Framework for Identifying Gene ...](https://cepac.cheme.cmu.edu/pasilectures/costas/burgard-etal03a.pdf) - In this work, a bilevel optimization framework termed OptKnock is developed for suggesting gene knoc...

64. [OptForce: An Optimization Procedure for Identifying All Genetic ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC2855329/) - In this paper, we introduce OptForce, an algorithm that identifies all possible metabolic interventi...

65. [Bayesian optimization with preference exploration (BOPE) - BoTorch](https://botorch.org/docs/tutorials/bope/) - In this tutorial, we demonstrate how to implement a closed loop of Bayesian optimization with prefer...

66. [Tutorials - BoTorch · Bayesian Optimization in PyTorch](https://archive.botorch.org/tutorials/) - These tutorials give you an overview of how to leverage Ax, a platform for sequential experimentatio...

67. [A machine learning Automated Recommendation Tool for synthetic biology](https://www.nature.com/articles/s41467-020-18008-4) - Synthetic biology allows us to bioengineer cells to synthesize novel valuable molecules such as rene...

68. [ART: A machine learning Automated Recommendation Tool for synthetic biology](https://www.semanticscholar.org/paper/8feb9c3c253c16bfe68363dcbc8dfd6d6ac44651) - Biology has changed radically in the last two decades, transitioning from a descriptive science into...

69. [JBEI/ART: A machine learning tool to improve the ... - GitHub](https://github.com/JBEI/ART) - ART is a tool that leverages machine learning and probabilistic modeling techniques to guide metabol...

70. [ART: A machine learning Automated Recommendation Tool for ...](https://ipo.lbl.gov/2020/01/14/art-a-machine-learning-automated-recommendation-tool-for-guiding-synthetic-biology-2020-011/) - The patent-pending Automated Recommendation Tool (ART) uses probabilistic modeling techniques to gui...

71. [Multi-fidelity Bayesian Optimisation of Syngas Fermentation Simulators](https://arxiv.org/pdf/2311.05776.pdf) - A Bayesian optimization approach for maximizing the gas conversion rate in an
industrial-scale biore...

72. [Multi-fidelity Bayesian optimization using KG - BoTorch](https://botorch.org/docs/tutorials/multi_fidelity_bo/) - In this tutorial, we show how to perform continuous multi-fidelity Bayesian optimization (BO) in BoT...

73. [Simulated Design–Build–Test–Learn Cycles for Consistent Comparison of Machine Learning Methods in Metabolic Engineering](https://pubs.acs.org/doi/10.1021/acssynbio.3c00186) - Combinatorial pathway optimization is an important tool in metabolic flux optimization. Simultaneous...

74. [The knowledge driven DBTL cycle provides mechanistic insights ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12084978/) - This study demonstrates the development and optimisation of a dopamine production strain by the help...

75. [Automated strain construction for biosynthetic pathway screening in ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12611344/) - Automation accelerates the Design-Build-Test-Learn (DBTL) cycle for synthetic biology; however, most...

76. [AI, Automation, and Biosensors Speed the Path to Synthetic Jet Fuel](https://newscenter.lbl.gov/2026/01/29/ai-automation-and-biosensors-speed-the-path-to-synthetic-jet-fuel/) - One combines artificial intelligence and lab automation to rapidly test and refine the genetic desig...

77. [Speeding the path to synthetic jet fuel with AI, automation and ...](https://techxplore.com/news/2026-01-path-synthetic-jet-fuel-ai.html) - One combines artificial intelligence and lab automation to rapidly test and refine the genetic desig...

78. [CIDARLAB/cello: Genetic circuit design automation - GitHub](https://github.com/CIDARLAB/cello) - The Cello input is a high-level logic specification written in Verilog, a hardware description langu...

79. [Cello | CIDAR Lab](https://www.cidarlab.org/cello) - Cello is a framework that describes what is essentially a programming language to design computation...

80. [Cello | The Synthetic Biology Open Language](https://sbolstandard.org/applications/cello/) - Cello is a framework that describes what is essentially a programming language to design computation...

81. [Cello 2.0: Genetic Circuit Design Tool | PDF - Scribd](https://www.scribd.com/document/673201303/2-Cello) - Overview of the software architecture. Cello 2.0 is an open-source software tool written in the Java...

82. [OSTIR: open source translation initiation rate prediction - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC9518832/) - OSTIR (Open Source Translation Initiation Rates) is a Python package and command line tool for predi...

83. [Insights into CO2 Fixation Pathway of Clostridium autoethanogenum by Targeted Mutagenesis](https://journals.asm.org/doi/10.1128/mBio.00427-16) - ABSTRACT The future sustainable production of chemicals and fuels from nonpetrochemical resources an...

84. [Recent progress in engineering Clostridium autoethanogenum to synthesize the biochemicals and biocommodities](https://linkinghub.elsevier.com/retrieve/pii/S2405805X23000996) - Excessive mining and utilization fossil fuels has led to drastic environmental consequences, which w...

85. [Model acetogens as chassis for CO2-driven bioproduction.](https://linkinghub.elsevier.com/retrieve/pii/S0958166925001673) - Microbes play a pivotal role in the Earth's carbon cycle, regulating greenhouse gas fluxes by emitti...

86. [Deletion of genes linked to the C1-fixing gene cluster affects growth, by-products, and proteome of Clostridium autoethanogenum](https://www.frontiersin.org/articles/10.3389/fbioe.2023.1167892/full) - Gas fermentation has emerged as a sustainable route to produce fuels and chemicals by recycling inex...

87. [Reverse‐Engineered Gas‐Fermenting Acetogen Strains Recover ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12335938/) - Gas‐fermenting acetogens, such as Clostridium autoethanogenum, have emerged as promising biocatalyst...

88. [The non-mevalonate pathway requires a delicate balance of intermediates to maximize terpene production](https://link.springer.com/10.1007/s00253-024-13077-7) - Abstract Terpenes are valuable industrial chemicals whose demands are increasingly being met by bioe...

89. [Microbial Platform for Terpenoid Production: Escherichia coli and ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6194902/) - MEP and MVA pathways use central metabolites to initiate synthesis of IPP and DMAPP, the building bl...

90. [The non-mevalonate pathway requires a delicate balance of ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10904526/) - This work shows that an intricate balance of the MEP pathway intermediates determines the terpene yi...

91. [Alternative metabolic pathways and strategies to high-titre terpenoid ...](https://pubs.rsc.org/en/content/articlehtml/2022/np/d1np00025j) - Engineering the native MEP pathway or the heterologous MVA pathway in E. coli has enabled terpenoid ...

92. [Biosynthesis of β-carotene in engineered E. coli using the MEP and MVA pathways](http://microbialcellfactories.biomedcentral.com/articles/10.1186/s12934-014-0160-x) - Backgroundβ-carotene is a carotenoid compound that has been widely used not only in the industrial p...

93. [A novel MVA-mediated pathway for isoprene production in engineered E. coli](http://www.biomedcentral.com/1472-6750/16/5) - BackgroundTo deal with the increasingly severe energy crisis and environmental consequences, biofuel...

94. [Amyris, Total to Begin Marketing Farnesane-Based Sustainable ...](https://advancedbiofuelsusa.info/amyris-total-to-begin-marketing-farnesane-based-sustainable-aviation-fuel) - Amyris and Total announced they will prepare to market a drop in jet fuel that contains up to 10% bl...

95. [Biofuels and Bioproducts - jbei.org](https://www.jbei.org/research/biofuels-and-bioproducts/) - In the Biofuels and Bioproducts division, we are developing the tools to fully convert sugars and li...

96. [Technology - jbei.org](https://www.jbei.org/research/technology/) - JBEI researchers in the Technology Division investigate new technologies to advance the research and...

97. [A machine learning Automated Recommendation Tool for synthetic ...](https://www.osti.gov/pages/biblio/1665911) - Here, we present the Automated Recommendation Tool (ART), a tool that leverages machine learning and...

98. [Research Tools - jbei.org](https://www.jbei.org/research/applications/) - JBEI Database of Lignin Modifying Enzymes is a research tool for accelerating the development of sus...

99. [[PDF] Computational Fluid Dynamics of Bioreactors with Micro-Aeration](https://www.nrel.gov/docs/fy20osti/73789.pdf) - silico, reducing risk in scale-up. • Traditionally, aerobic fermentation scaleup emphasizes total-re...

100. [Complete biosynthesis of opioids in yeast](https://pmc.ncbi.nlm.nih.gov/articles/PMC4924617/) - ...hydrocodone starting from sugar. All work was conducted in a laboratory that is permitted and sec...

101. [A microbial biomanufacturing platform for natural and semi-synthetic opiates](https://pmc.ncbi.nlm.nih.gov/articles/PMC4167936/) - ...neopine and neomorphine was discovered, which diverted pathway flux from morphine and other targe...

102. [Synthetic biochemical production of medicinal natural products in ...](https://purl.stanford.edu/fs840tz7862) - The engineered yeast strains are able to biosynthesize the morphinan alkaloid thebaine and the opiat...

103. [De novo biosynthesis of bioactive isoflavonoids by engineered yeast cell factories](https://www.nature.com/articles/s41467-021-26361-1) - Isoflavonoids comprise a class of plant natural products with great nutraceutical, pharmaceutical an...

104. [Metabolic engineering of yeast for de novo production of kratom monoterpene indole alkaloids](http://biorxiv.org/lookup/doi/10.1101/2024.05.22.595370) - Monoterpene indole alkaloids (MIAs) from Mitragyna speciosa (“kratom”), such as mitragynine and spec...

105. [De novo biosynthesis of the hops bioactive flavonoid xanthohumol in yeast](https://www.nature.com/articles/s41467-023-44654-5) - Xanthohumol is a prenylated flavonoid produced by hops and is an important flavor substance in beer....

106. [Engineered Microbial Routes for Human Milk Oligosaccharides ...](https://pubmed.ncbi.nlm.nih.gov/33909411/) - The large-scale production of HMOs has been researched using engineered microbial routes due to the ...

107. [Engineered Microbial Routes for Human Milk Oligosaccharides ...](https://pubs.acs.org/doi/10.1021/acssynbio.1c00063) - The main strains currently used as the hosts for the engineered microbial route are Escherichia coli...

108. [[PDF] Microbial Production of Human Milk Oligosaccharides](https://escholarship.org/content/qt0r18b5pd/qt0r18b5pd.pdf) - Escherichia coli has emerged as the preferred microbial host for HMO synthesis owing to its fast gro...

109. [Metabolic flux configuration determination using information entropy](https://pmc.ncbi.nlm.nih.gov/articles/PMC7717585/) - We formulated a constraint-based approach, MaxEnt, based on the principle of maximum entropy, which ...

110. [[PDF] Maximum entropy decomposition of flux distribution at ... - CADLIVE](http://www.cadlive.jp/cadlive_main/References/JBB2009.pdf) - We used this method to predict (I) the intracellular flux distribution caused by external fluxes and...

111. [[PDF] Dynamic metabolic resource allocation based on the maximum ...](https://arxiv.org/pdf/1906.03919.pdf) - The maximum entropy principle is also shown to yield an optimal control law con- sistent with partit...

112. [Maximum entropy decomposition of flux distribution at steady state ...](https://www.sciencedirect.com/science/article/abs/pii/S1389172308000637) - The maximum entropy principle (MEP) is derived from Shannon's information theory and is widely used ...

113. [MooSeeker: A Metabolic Pathway Design Tool Based on Multi-Objective Optimization Algorithm](https://ieeexplore.ieee.org/document/10226260/) - Recently, metabolic pathway design has attracted considerable attention and become an increasingly i...

114. [Pathway thermodynamic analysis postulates change in glutamate metabolism as a key factor in modulating immune responses](https://journals.lww.com/10.1097/IN9.0000000000000077) - Background: Temperature, as seen during fever, plays a pivotal role in modulating immune responses a...

115. [Promoting Vibrations and the Function of Enzymes. Emerging ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6008225/) - A complete understanding of enzyme catalysis requires knowledge of both transition state features an...

116. [Le Chatelier’s principle and metabolism: Biothermodynamic analysis of the metabolic pathway for synthesis of glucagon](https://doiserbia.nb.rs/Article.aspx?ID=0352-51392500087P) - Glucagon is the main catabolic hormone in the human organism.Glucagon has been well studied from the...

117. [Design and thermodynamic analysis of a pathway enabling anaerobic production of poly-3-hydroxybutyrate in Escherichia coli](https://linkinghub.elsevier.com/retrieve/pii/S2405805X23000790) - Utilizing anaerobic metabolisms for the production of biotechnologically relevant products presents ...

118. [Integration of graph neural networks and genome-scale metabolic ...](https://www.nature.com/articles/s41540-024-00348-2) - In this paper, we propose FlowGAT, a graph neural network (GNN) model to predict gene essentiality f...

119. [Using graph neural networks for site-of-metabolism prediction and ...](https://pubmed.ncbi.nlm.nih.gov/36790067/) - This article develops a Graph Neural Network (GNN) model for the classification of an atom (or a bon...

120. [Using graph neural networks for site-of-metabolism prediction and ...](https://academic.oup.com/bioinformatics/article/39/3/btad089/7039680) - This article develops a Graph Neural Network (GNN) model for the classification of an atom (or a bon...

121. [Dynamic Metabolic Control: From the Perspective of Regulation Logic](https://www.sciepublish.com/article/pii/63) - In the two-phase dynamic regulation, the fermentation is manually split into two phases: a growth ph...

122. [Optogenetic control of Cdc48 for dynamic metabolic engineering in ...](https://www.sciencedirect.com/science/article/abs/pii/S1096717623000952) - We demonstrate that optogenetic intervention in the cell cycle of budding yeast can be used to incre...

123. [Quantum Mechanics/Molecular Mechanics (QM/MM) - Glossary](https://deeporigin.com/glossary/quantum-mechanics-molecular-mechanics-qm-mm) - Accurate Modeling of Active Sites: QM/MM allows for accurate modeling of enzyme ... ORCA: An efficie...

124. [Best Practices on QM/MM Simulations of Biological Systems](https://pubs.acs.org/doi/10.1021/acs.jcim.2c01522) - In the present work, we describe both the theoretical concepts and practical issues that need to be ...

125. [MACE-OFF: Transferable Short Range Machine Learning Force Fields for
  Organic Molecules](https://arxiv.org/html/2312.15211v4) - ... this
paper, we introduce MACE-OFF, a series of short range transferable force fields
for organic...

126. [Force Field Analysis Software and Tools (FFAST): Assessing Machine
  Learning Force Fields Under the Microscope](https://arxiv.org/pdf/2308.06871.pdf) - ...) increases to
match the complexity of extended molecules and materials, so does the need for
too...

127. [Force Field Analysis Software and Tools (FFAST): Assessing Machine Learning Force Fields under the Microscope](https://pmc.ncbi.nlm.nih.gov/articles/PMC10720330/) - ...) increases to match the complexity of extended molecules and materials, so does the need for too...

128. [Kinetic View of Enzyme Catalysis from Enhanced Sampling QM/MM ...](https://pubs.acs.org/doi/10.1021/acs.jcim.4c00475) - We introduce an enhanced sampling QM/MM approach that directly calculates the kinetics of enzymatic ...

129. [The Design Space of E(3)-Equivariant Atom-Centered Interatomic
  Potentials](https://arxiv.org/pdf/2205.06643.pdf) - ...over the past
couple of years produced a number of new architectures. Particularly notable
among ...

130. [[PDF] MACE: Higher Order Equivariant Message Passing Neural Networks ...](https://papers.neurips.cc/paper_files/paper/2022/file/4a36c3c51af11ed9f34615b81edb5bbc-Paper-Conference.pdf) - Creating fast and accurate force fields is a long-standing challenge in computational chemistry and ...

131. [[PDF] Continuous SE(3)-Equivariant Attention for Molecular Force Fields](https://arxiv.org/pdf/2602.02671.pdf) - Models such as. NequIP (Batzner et al., 2021) and MACE (Batatia et al.,. 2022b) trained on high-qual...

132. [Reactive Machine Learning Interatomic Potentials for Chemistry and ...](https://pubs.acs.org/doi/10.1021/acs.chemrev.5c00728) - In contrast, equivariant models like MACE and NequIP demonstrated consistent stability. This discrep...

133. [AlphaFold2 and Deep Learning for Elucidating Enzyme Conformational Flexibility and Its Application for Design](https://pubs.acs.org/doi/pdf/10.1021/jacsau.3c00188) - The recent success of AlphaFold2 (AF2) and other deep learning (DL) tools in accurately predicting t...

134. [AlphaFold2 and Deep Learning for Elucidating Enzyme Conformational Flexibility and Its Application for Design](https://pmc.ncbi.nlm.nih.gov/articles/PMC10302747/) - The recent success of AlphaFold2 (AF2) and other deep learning (DL) tools in accurately predicting t...

135. [AlphaFold2 and ESMFold: A large-scale pairwise model comparison of human enzymes upon Pfam functional annotation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11799866/) - Comput Struct Biotechnol J. 2025 Jan 14;27:461–466. doi: 10.1016/j.csbj.2025.01.008

# AlphaFold2 an...

136. [De novo design of protein structure and function with RFdiffusion](https://pmc.ncbi.nlm.nih.gov/articles/PMC10468394/) - Nature. 2023 Jul 11;620(7976):1089–1100. doi: 10.1038/s41586-023-06415-8

# De novo design of protei...

137. [The Atomic Era of Protein Design: A Deep Dive into RFdiffusion3](https://ailurus.bio/post/the-atomic-era-of-protein-design-a-deep-dive-into-rfdiffusion3) - The groundwork was laid by structure prediction networks like AlphaFold2 and RoseTTAFold, which solv...

138. [A trio of AI methods tackles enzyme design - C&EN](https://cen.acs.org/physical-chemistry/computational-chemistry/trio-AI-methods-tackles-enzyme/103/web/2025/12) - RFdiffusion2, RFdiffusion3, and Riff-Diff each solve different structural problems in computational ...

139. [All-atom protein design via SE(3) flow matching with ProteinZen](https://www.biorxiv.org/content/10.1101/2025.10.18.683228v1.full-text) - Purple structures are the design structure, and orange structures are the corresponding ESMFold pred...

140. [Breaking the Barriers of Molecular Dynamics With Deep‐Learning ...](https://wires.onlinelibrary.wiley.com/doi/10.1002/wcms.70064) - Besides predicting energies and forces, equivariant MPNNs have been used to predict tensorial proper...

141. [[PDF] arXiv:2106.15476v1 [cs.CE] 25 Jun 2021](https://arxiv.org/pdf/2106.15476.pdf) - We conducted our investigation on the whole GINsim model repository which contains 85 networks: 29 a...

142. [A meta-analysis of Boolean network models reveals design ...](https://www.science.org/doi/10.1126/sciadv.adj0822) - A meta-analysis of this diverse set of models reveals several design principles. GRNs exhibit more c...

143. [Phenotype Control techniques for Boolean gene regulatory networks](https://pmc.ncbi.nlm.nih.gov/articles/PMC10542862/) - Force the system to have one stable attractor, Assign node to its value in the target attractor, Reg...

144. [ProteinGym Benchmark: Protein Mutation Evaluation - Emergent Mind](https://www.emergentmind.com/topics/proteingym-benchmark) - ProteinGym Benchmark is a comprehensive evaluation framework that systematically assesses computatio...

145. [ProteinGym: Large-Scale Benchmarks for Protein Fitness Prediction...](https://openreview.net/forum?id=URoZHqAohf&noteId=PLTsEAiyz5) - We introduce ProteinGym, a large-scale and holistic set of benchmarks specifically designed for prot...

146. [ProteinGym: Large-Scale Benchmarks for Protein Design and ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/) - We introduce ProteinGym, a large-scale and holistic set of benchmarks specifically designed for prot...

147. [ProteinGym: Large-Scale Benchmarks for Protein Design ... - bioRxiv](https://www.biorxiv.org/content/10.1101/2023.12.07.570727v1.full-text) - Many of the alignment-based methods (e.g. EVmutation, WaveNet and DeepSequence) exhibit this behavio...

148. [ProteinGym](https://proteingym.org) - ProteinGym is a collection of benchmarks aiming at comparing the ability of models to predict the ef...

149. [Engineering functional thermostable proteins using ancestral ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9525910/) - This review provides an overview of the factors important for successful inference of thermostable p...

150. [Engineering highly functional thermostable proteins using ancestral ...](https://researchprofiles.ku.dk/en/publications/engineering-highly-functional-thermostable-proteins-using-ancestr/) - Ancestral reconstruction has shown that pre-Cambrian enzymes were often much more thermostable than ...

151. [Engineering highly functional thermostable proteins using ancestral ...](https://www.nature.com/articles/s41929-018-0159-5) - Ancestral reconstruction has shown that pre-Cambrian enzymes were often much more thermostable than ...

152. [Ancestral Sequence Reconstruction Meets Machine Learning: Ene ...](https://pubs.acs.org/doi/10.1021/acscatal.4c03738) - In this work, we sought to apply ASR to design enzyme libraries and leverage machine learning to pre...

153. [An Automatic Method for Generation of CFD-Based 3D Compartment Models: Towards Real-Time Mixing Simulations](https://www.mdpi.com/2306-5354/11/2/169/pdf?version=1707473774) - ...component. The compartmentalization method is applied to two bioreactor geometries and was able t...

154. [An Automatic Method for Generation of CFD-Based 3D Compartment Models: Towards Real-Time Mixing Simulations](https://pmc.ncbi.nlm.nih.gov/articles/PMC10886251/) - ...component. The compartmentalization method is applied to two bioreactor geometries and was able t...

155. [Integration Approaches to Model Bioreactor Hydrodynamics and Cellular Kinetics for Advancing Bioprocess Optimisation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11200465/) - ...environmental gradients become more pronounced compared to smaller scales. Consequently, the cell...

156. [Dynochem Biologics - Scale-up Systems](https://www.scale-up.com/biologics) - Dynochem Biologics™ is a set of process development and scale-up tools for upstream (USP), downstrea...

157. [Recent advances in biocathode materials and configurations for reactor applications in microbial electrosynthesis of CO2.](https://linkinghub.elsevier.com/retrieve/pii/S004896972502234X) - Elevated atmospheric carbon dioxide (CO2) levels driven by urbanization and anthropogenic activities...

158. [Microbial electrosynthesis meets synthetic biology: Bioproduction from waste feedstocks](https://linkinghub.elsevier.com/retrieve/pii/S2665906925000108) - Integrating electrochemistry and biology, microbial electrosynthesis (MES) enhances feedstock-to-pro...

159. [A three-dimensional hybrid electrode with electroactive microbes for ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC7060665/) - Of particular interest are electroactive bacteria such as Geobacter and Shewanella that have evolved...

160. [How Geobacter Microbes Produce Electricity - iBiology](https://www.ibiology.org/microbiology/how-geobacter-microbes-produce-electricity/) - This unassuming single-celled organism possesses a remarkable ability to generate electricity throug...

161. [Energetic constraints of metal-reducing bacteria as biocatalysts for microbial electrosynthesis](https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-025-02666-x) - As outlined by the Intergovernmental Panel on Climate Change, we need to approach global net zero CO...

162. [Engineering an electroactive Escherichia coli for the microbial electrosynthesis of succinate by increasing the intracellular FAD pool](https://linkinghub.elsevier.com/retrieve/pii/S1369703X19301007) - Abstract In this study, the FAD synthesis pathway was manipulated to increase its cellular concentra...

163. [MICOM: Metagenome-Scale Modeling To Infer Metabolic ...](https://journals.asm.org/doi/10.1128/msystems.00606-19) - Here, we present a computational approach that efficiently extends metabolic modeling to entire micr...

164. [Extracting the Dynamic Motion of Proteins Using Normal Mode ...](https://pubmed.ncbi.nlm.nih.gov/35507265/) - Normal mode analysis (NMA) is a technique for describing the conformational states accessible to a p...

165. [Anomalous values of the first six normal modes - GROMACS forums](https://gromacs.bioexcel.eu/t/anomalous-values-of-the-first-six-normal-modes/3396) - The values of the first six projections are two orders of magnitude larger than those of the project...

166. [MetaboLights: open data repository for metabolomics](https://pmc.ncbi.nlm.nih.gov/articles/PMC10767962/) - Abstract MetaboLights is a global database for metabolomics studies including the raw experimental d...

167. [MetaboLights - Metabolomics experiments and derived information](https://www.ebi.ac.uk/metabolights/) - MetaboLights is a database for Metabolomics experiments and derived information. The database is cro...

168. [Comprehensive Guide to Metabolite Identification Databases](https://www.creative-proteomics.com/resource/metabolite-identification-databases-guide.htm) - Explore the world of metabolite identification through mass spectrometry databases like METLIN, mzCl...

169. [Machine Learning Applications for Mass Spectrometry-Based ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345470/) - Metabolomics helps to understand disease progression in clinical settings or estimate metabolite ove...

170. [Single cell profiling framework reveals metabolic subpopulations as ...](https://www.nature.com/articles/s41467-025-67408-x) - Here, we propose a framework based on single-cell biosensor analysis that enables robust characteris...

171. [Design and Characterization of Rapid Optogenetic Circuits for ...](https://pubs.acs.org/doi/10.1021/acssynbio.0c00305) - The use of optogenetics in metabolic engineering for light-controlled microbial chemical production ...

172. [Optogenetic Amplification Circuits for Light-Induced Metabolic Control](https://pubs.acs.org/doi/10.1021/acssynbio.0c00642) - Dynamic control of microbial metabolism is an effective strategy to improve chemical production in f...

173. [Dynamical Modeling of Optogenetic Circuits in Yeast for Metabolic ...](https://pubmed.ncbi.nlm.nih.gov/33492138/) - Dynamic control of engineered microbes using light via optogenetics has been demonstrated as an effe...

174. [NASA Open Science Data Repository for Space Biology Data Access](https://ui.adsabs.harvard.edu/abs/2024cosp...45.2378S/abstract) - OSDR houses over 475 studies with datasets from model organisms and non-NASA human astronauts, spann...

175. [NASA Space Biology Open Science Data Repository (OSDR)](https://registry.opendata.aws/nasa-osdr/) - This site consolidates data from the Ames Life Sciences Data Archive (ALSDA) and GeneLab and include...

176. [NASA open science data repository: open science for life in space](https://pmc.ncbi.nlm.nih.gov/articles/PMC11701653/) - Within OSDR, NASA GeneLab provides assay metadata standards and templates for PIs to follow when sub...

177. [Open Science for Life in Space - NASA OSDR](https://osdr.nasa.gov/bio/repo) - MicroRNAs shape mouse age-independent tissue adaptation to spaceflight via ECM and developmental pat...

178. [International Space Station flight project EXTREMOPHILES - Dataset](https://data.nasa.gov/dataset/international-space-station-flight-project-extremophiles) - We show that the ISS microbial communities are highly similar to those present in ground-based confi...

179. [Pyrococcus furiosus - Wikipedia](https://en.wikipedia.org/wiki/Pyrococcus_furiosus) - The thermodynamic stability of P. furiosus' enzymes is useful in the creation of diols for laborator...

180. [Pyrococcus furiosus - an overview | ScienceDirect Topics](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/pyrococcus-furiosus) - The anaerobic microorganism Pyrococcus furiosus [2,3] produces extremly thermoactive starch- hydroly...

181. [Extremophiles: Unlocking biomedical and industrial innovations ...](https://www.cas.org/resources/cas-insights/extremophiles-biomedical-industrial-innovations) - Heat-shock proteins (HSPs): Chaperones like HSP70 in Pyrococcus furiosus prevent protein misfolding ...

182. [ThermoMPNN: A Powerful Tool for Protein Stability Prediction](https://www.tamarind.bio/tools/thermompnn) - ThermoMPNN, a deep learning-based method that accurately predicts the effects of single amino acid m...

183. [Data-driven strategies for enzyme thermostability design - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC10160227/) - In this review, we propose a data-driven architecture for enzyme thermostability engineering and sum...

184. [TemStaPro: protein thermostability prediction using sequence ...](https://academic.oup.com/bioinformatics/article/40/4/btae157/7632735) - Our method, TemStaPro (Temperatures of Stability for Proteins), was used to predict thermostability ...

185. [iGEM Registry of Standard Biological Parts - BiŌkeanós](https://biokeanos.com/source/iGEM%20Registry%20of%20Standard%20Biological%20Parts) - The iGEM Parts Registry is a growing collection of genetic parts that can be mixed and matched to bu...

186. [Sakana AI Promises Better AI by Teaching Large Language Models ...](https://www.hackster.io/news/sakana-ai-promises-better-ai-by-teaching-large-language-models-the-art-of-cooperation-a9d451ff919e) - New "adaptive branching Monte Carlo tree search" lets you put multiple LLMs to work on a single prob...

187. [(PDF) Plasma-assisted pre-treatment of lignocellulosic biomass for ...](https://www.academia.edu/74874890/Plasma_assisted_pre_treatment_of_lignocellulosic_biomass_for_anaerobic_digestion) - DBD plasma treatment increased biogas production by 18% in batch AD with washed maize feedstock. Unw...

188. [Cold plasma pretreatment reinforces the lignocellulose-derived ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10273749/) - Acceleration of biodetoxification on dilute acid pretreated lignocellulose feedstock by aeration and...

189. [Cellular variability as a driver for bioprocess innovation and ...](https://www.sciencedirect.com/science/article/pii/S073497502500014X) - This review explores the different dimensions of cellular heterogeneity, focusing on its manifestati...

190. [Metabolic engineering of Corynebacterium glutamicum aimed at ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC3962153/) - Corynebacterium glutamicum is well known as the amino acid-producing workhorse of fermentation indus...

191. [Engineering Corynebacterium glutamicum cell factory for producing ...](https://www.sciencedirect.com/science/article/pii/S2693125725000093) - As an essential industrial microorganism, Corynebacterium glutamicum has been employed in amino acid...

192. [TreeQuest by Sakana AI: A Breakthrough Open-Source Algorithm for ...](https://www.linkedin.com/pulse/treequest-sakana-ai-breakthrough-open-source-algorithm-anshuman-jha-4a58c) - TreeQuest builds on Sakana AI's prior work in evolutionary algorithms and multi-model systems, repre...

193. [Sakana AI's TreeQuest: Deploy multi-model teams that outperform ...](https://venturebeat.com/ai/sakana-ais-treequest-deploy-multi-model-teams-that-outperform-individual-llms-by-30) - Sakana AI's new inference-time scaling technique uses Monte-Carlo Tree Search to orchestrate multipl...

194. [Build multi-agent systems with LangGraph and Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/build-multi-agent-systems-with-langgraph-and-amazon-bedrock/) - It explains how to use LangGraph and Amazon Bedrock to build powerful, interactive multi-agent appli...

195. [LangGraph Multi-Agent Orchestration: Complete Framework Guide ...](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-multi-agent-orchestration-complete-framework-guide-architecture-analysis-2025) - Explore a comprehensive guide on multi-agent orchestration with LangGraph, covering architecture, ch...

196. [LangGraph & MCP Are the Future of Multi-Agent AI Orchestration](https://healthark.ai/orchestrating-multi-agent-systems-with-lang-graph-mcp/) - Understand how LangGraph and MCP simplify multi-agent coordination with dynamic task graphs, context...

197. [LangGraph: Agent Orchestration Framework for Reliable AI Agents](https://www.langchain.com/langgraph) - LangGraph sets the foundation for how we can build and scale AI workloads — from conversational agen...

198. [Auxotrophy-based curation improves the consensus genome-scale metabolic model of yeast](https://pmc.ncbi.nlm.nih.gov/articles/PMC11704421/) - ## Abstract

*Saccharomyces cerevisiae*, a widely utilized model organism, has seen continuous updat...

199. [Yeast9: a consensus genome-scale metabolic model for S ... - PubMed](https://pubmed.ncbi.nlm.nih.gov/39134886/) - We generated 163 condition-specific GEMs constrained by single-cell transcriptomics from osmotic pre...

200. [The consensus genome-scale metabolic model of Saccharomyces ...](https://sysbiochalmers.github.io/yeast-GEM/) - This repository contains the continuously updated consensus genome-scale metabolic model of Saccharo...

201. [Yeast9: a consensus genome-scale metabolic model for S ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11450192/) - Genome-scale metabolic models (GEMs) can facilitate metabolism-focused multi-omics integrative analy...

202. [SysBioChalmers/yeast-GEM: The consensus GEM for ... - GitHub](https://github.com/sysbiochalmers/yeast-gem) - This repository contains the current consensus genome-scale metabolic model of Saccharomyces cerevis...

203. [SysBioChalmers/Yeast-ME-GEM - GitHub](https://github.com/SysBioChalmers/Yeast-ME-GEM) - This model can be used to interpret the yeast adaptive responses as well as to determine the optimal...

204. [MACE-OFF: Short Range Transferable Machine Learning Force ...](https://arxiv.org/html/2312.15211v5) - In this paper, we introduce MACE-OFF, a series of short range transferable force fields for organic ...

205. [MACE-OFF: Short-Range Transferable Machine Learning Force ...](https://pubs.acs.org/doi/10.1021/jacs.4c07099) - In this paper, we introduce MACE-OFF, a series of short-range transferable force fields for organic ...

206. [MACE-OFF: Short-Range Transferable Machine Learning Force ...](https://www.repository.cam.ac.uk/items/2969f1fd-9ec6-4ea2-9608-a88239b1e28e) - In this paper, we introduce MACE-OFF, a series of short-range transferable force fields for organic ...

207. [MACE-OFF: Short-Range Transferable Machine Learning Force ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12123624/) - In this paper, we introduce MACE-OFF, a series of short-range transferable force fields for organic ...

208. [MACE-OFF: Short-Range Transferable Machine Learning Force ...](https://pubs.acs.org/doi/abs/10.1021/jacs.4c07099) - In this paper, we introduce MACE-OFF, a series of short-range transferable force fields for organic ...

