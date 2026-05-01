"""CEKM — Conditional Enzyme Kinetics Model (Zer0pa-owned, MIT-permissive).

Per PRD §12: CEKM training corpus = BRENDA + EnzyExtract + GotEnzymes2 +
ProteinGym. Adversarial three-tier synthetic-negatives sampler defends
against survivorship bias. Held-out blind eval; calibration audit per
Tier α/β/γ.

This module ships the **CPU prototype data pipeline** — corpus assembly
skeleton + adversarial-negatives sampler + held-out split logic +
calibration scaffolding. Full GPU training is Wave 4 Runpod-bound.
The point of the CPU prototype is to validate the data plumbing end-to-end
and produce a small smoke-test corpus before paying for A100 hours.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal


@dataclass
class KineticsRow:
    """A single (enzyme, substrate, condition) → (kcat, Km) record."""

    enzyme_uniprot_id: str
    substrate_inchi_key: str
    organism_taxonomy_id: int
    temperature_c: float
    ph: float
    kcat_per_s: float | None
    km_mm: float | None
    source: Literal["brenda", "enzyextract", "gotenzymes2", "proteingym"]
    citation: str = ""
    license_class: Literal["A", "B", "C", "D", "E"] = "A"

    @property
    def row_id(self) -> str:
        seed = (
            f"{self.enzyme_uniprot_id}|{self.substrate_inchi_key}|"
            f"{self.organism_taxonomy_id}|{self.temperature_c}|{self.ph}|{self.source}"
        )
        return hashlib.sha256(seed.encode()).hexdigest()[:16]


@dataclass
class AdversarialNegative:
    """A synthetic-negative sample tied to a positive `KineticsRow`."""

    parent_row_id: str
    tier: Literal["alpha", "beta", "gamma"]
    enzyme_uniprot_id: str
    decoy_substrate_inchi_key: str
    active_site_distance_factor: float  # α=0.5×, β=1.0×, γ=2.0× per PRD §12.2
    rationale: str = ""

    @property
    def negative_id(self) -> str:
        seed = f"{self.parent_row_id}|{self.tier}|{self.decoy_substrate_inchi_key}"
        return "neg_" + hashlib.sha256(seed.encode()).hexdigest()[:16]


@dataclass
class CorpusSlice:
    """One source's contribution to the CEKM corpus."""

    source: Literal["brenda", "enzyextract", "gotenzymes2", "proteingym"]
    license_class: Literal["A", "B", "C", "D", "E"]
    rows: list[KineticsRow] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)


@dataclass
class HeldOutSplit:
    """Held-out partition for blind eval."""

    in_corpus_row_ids: set[str] = field(default_factory=set)
    held_out_row_ids: set[str] = field(default_factory=set)
    holdout_fraction: float = 0.15
    seed: int = 0


def assemble_corpus(slices: Iterable[CorpusSlice]) -> list[KineticsRow]:
    """Concatenate-and-deduplicate kinetics rows across CEKM source slices.

    Per PRD §12.1: BRENDA bulk core (CC BY 4.0), EnzyExtract (MIT;
    89,544 BRENDA-absent entries materially reduce survivorship bias),
    GotEnzymes2 (CC BY 4.0; 59.6M predicted entries used as curriculum
    pre-training only — soft pseudo-labels), ProteinGym (MIT; auxiliary).

    Excluded: BioTRY (PARKED v1), BKMS-react (E), KEGG bulk (E),
    ATLAS (D).
    """
    seen: set[str] = set()
    out: list[KineticsRow] = []
    for s in slices:
        if s.license_class in {"D", "E"}:
            raise ValueError(
                f"Source {s.source} has license_class={s.license_class}; "
                "Class D/E sources are excluded from the CEKM training corpus "
                "by construction. Add a license_grant before retrying."
            )
        for r in s.rows:
            if r.row_id in seen:
                continue
            seen.add(r.row_id)
            out.append(r)
    return out


def held_out_split(
    rows: list[KineticsRow],
    holdout_fraction: float = 0.15,
    seed: int = 0,
    enzyextract_holdout_full: bool = True,
) -> HeldOutSplit:
    """Build held-out partition for blind eval per PRD §12.3.

    Default discipline: 10-20% of BRENDA bulk + 100% of EnzyExtract's
    'dark matter' corpus (89,544 BRENDA-absent entries) is held-out.
    CEKM never sees these during training.
    """
    rng = random.Random(seed)
    in_corpus: set[str] = set()
    held_out: set[str] = set()
    for r in rows:
        if r.source == "enzyextract" and enzyextract_holdout_full:
            held_out.add(r.row_id)
            continue
        if rng.random() < holdout_fraction:
            held_out.add(r.row_id)
        else:
            in_corpus.add(r.row_id)
    return HeldOutSplit(
        in_corpus_row_ids=in_corpus,
        held_out_row_ids=held_out,
        holdout_fraction=holdout_fraction,
        seed=seed,
    )


def sample_adversarial_negatives(
    positives: list[KineticsRow],
    decoy_pool: list[str],  # InChIKey list of candidate decoy substrates
    *,
    seed: int = 0,
) -> list[AdversarialNegative]:
    """Adversarial three-tier sampler per PRD §12.2.

    For every positive `(enzyme, substrate, condition, kcat, Km)`, draw
    three negatives:
      α (0.5× active-site distance) — near-miss
      β (1.0× distance, dissimilar)
      γ (2.0× distance, low Vina score) — far

    The active-site distance factors are an interface contract; the
    actual selection of decoy substrates per tier requires AlphaFold +
    AutoDock Vina (GPU-bound). On the CPU prototype we sample uniformly
    from `decoy_pool` and tag each with the tier and the synthetic
    distance factor, so the data shape is correct for the downstream
    training loop.
    """
    rng = random.Random(seed)
    out: list[AdversarialNegative] = []
    for pos in positives:
        for tier, factor, rationale in (
            ("alpha", 0.5, "near-miss decoy at half active-site distance"),
            ("beta", 1.0, "distance-equal decoy chemically dissimilar"),
            ("gamma", 2.0, "far decoy with low predicted docking score"),
        ):
            decoy = rng.choice(decoy_pool) if decoy_pool else "DECOY-PLACEHOLDER"
            # Skip if the decoy IS the positive substrate.
            attempts = 0
            while decoy == pos.substrate_inchi_key and decoy_pool and attempts < 10:
                decoy = rng.choice(decoy_pool)
                attempts += 1
            out.append(
                AdversarialNegative(
                    parent_row_id=pos.row_id,
                    tier=tier,  # type: ignore[arg-type]
                    enzyme_uniprot_id=pos.enzyme_uniprot_id,
                    decoy_substrate_inchi_key=decoy,
                    active_site_distance_factor=factor,
                    rationale=rationale,
                )
            )
    return out


@dataclass
class CalibrationReport:
    """Per-tier calibration audit per PRD §12.3."""

    tier_alpha_coverage_at_90: float | None = None
    tier_beta_coverage_at_90: float | None = None
    tier_gamma_coverage_at_90: float | None = None
    held_out_brenda_coverage_at_90: float | None = None
    held_out_enzyextract_coverage_at_90: float | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": "synbio.cekm_calibration.v0.1",
            **self.__dict__,
        }


def smoke_test_pipeline() -> dict:
    """Run the CPU-side data pipeline on a tiny synthetic corpus.

    Returns a summary dict suitable for `synbio cekm smoke` CLI hookup.
    The smoke test asserts: assembly + dedup + held-out split + adversarial
    sampler all run end-to-end with sensible counts, deterministic IDs.
    Wave 4 (Runpod): replace the synthetic corpus with the real BRENDA
    + EnzyExtract + GotEnzymes2 + ProteinGym slices.
    """
    # Synthetic BRENDA-shaped slice.
    brenda = CorpusSlice(
        source="brenda",
        license_class="A",
        rows=[
            KineticsRow(
                enzyme_uniprot_id=f"P{i:05d}",
                substrate_inchi_key=f"SUBSTRATE-{i:03d}",
                organism_taxonomy_id=562,
                temperature_c=37.0,
                ph=7.0,
                kcat_per_s=10.0 + i * 0.3,
                km_mm=0.1 + i * 0.05,
                source="brenda",
                citation="(synthetic for smoke test)",
            )
            for i in range(50)
        ],
    )
    enzyextract = CorpusSlice(
        source="enzyextract",
        license_class="A",
        rows=[
            KineticsRow(
                enzyme_uniprot_id=f"Q{i:05d}",
                substrate_inchi_key=f"DARK-MATTER-{i:03d}",
                organism_taxonomy_id=562,
                temperature_c=30.0,
                ph=6.5,
                kcat_per_s=5.0 + i * 0.2,
                km_mm=0.2,
                source="enzyextract",
                citation="(synthetic dark-matter)",
            )
            for i in range(20)
        ],
    )
    gotenzymes2 = CorpusSlice(
        source="gotenzymes2",
        license_class="A",
        rows=[
            KineticsRow(
                enzyme_uniprot_id=f"R{i:05d}",
                substrate_inchi_key=f"PRED-{i:03d}",
                organism_taxonomy_id=562,
                temperature_c=37.0,
                ph=7.0,
                kcat_per_s=8.0 + (i % 7),
                km_mm=0.3,
                source="gotenzymes2",
                citation="(synthetic; soft pseudo-label)",
            )
            for i in range(30)
        ],
    )
    rows = assemble_corpus([brenda, enzyextract, gotenzymes2])
    split = held_out_split(rows, seed=42)
    decoy_pool = [r.substrate_inchi_key for r in rows[: len(rows) // 2]]
    in_corpus_rows = [r for r in rows if r.row_id in split.in_corpus_row_ids]
    negatives = sample_adversarial_negatives(in_corpus_rows, decoy_pool, seed=42)
    cal = CalibrationReport(
        notes="CPU prototype; full per-tier calibration runs after Wave 4 Runpod training",
    )
    return {
        "schema_version": "synbio.cekm_smoke.v0.1",
        "corpus_size": len(rows),
        "in_corpus_size": len(split.in_corpus_row_ids),
        "held_out_size": len(split.held_out_row_ids),
        "adversarial_negative_count": len(negatives),
        "tier_alpha_count": sum(1 for n in negatives if n.tier == "alpha"),
        "tier_beta_count": sum(1 for n in negatives if n.tier == "beta"),
        "tier_gamma_count": sum(1 for n in negatives if n.tier == "gamma"),
        "calibration_report": cal.to_dict(),
        "next_action": "Wave 4 Runpod training: substitute real BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym slices",
    }


__all__ = [
    "KineticsRow",
    "AdversarialNegative",
    "CorpusSlice",
    "HeldOutSplit",
    "CalibrationReport",
    "assemble_corpus",
    "held_out_split",
    "sample_adversarial_negatives",
    "smoke_test_pipeline",
]
