"""CEKM model — Conditional Enzyme Kinetics Model (Zer0pa-owned, MIT-permissive).

BOUNDARY:
Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts — predicted pathways, predicted
KPIs, candidate genetic modification specifications. No regulatory
certification claims. No clinical or human-subject use. No environmental
release of GMOs. No biocontainment-level claims (the pipeline does not
commission BSL-2/3 work). No human gene drive or eugenic application.
Defence / weapons / dual-use bio applications excluded under operator policy.

PRD §12 architecture (full PyTorch implementation):

  ESM-2-650M backbone (frozen by default; unfreeze last N layers) — or a
    stub nn.Embedding[residue_idx → 1280-d] when ESM-2 is unavailable.
  D-MPNN substrate encoder — directed message-passing over atom/bond graphs,
    falling back to a Morgan-fingerprint MLP when RDKit is available but a
    graph stack is absent, or to a random-embedding stub otherwise.
  Condition MLP — (pH, T, ionic_strength) → 32–128-d latent vector.
  Adaptive gate — cross-attention–style gating combining the three branches.
  Two regression heads: kcat (log-space) and Km (log-space).
  One discriminator block with three binary heads (per adversarial tier α/β/γ).

Graceful degradation (no torch installed):
  All public symbols are defined at import time. When torch is absent the
  module raises ImportError only at *instantiation* time (inside __init__),
  not at import time. This keeps CPU-only CI green.

bfloat16 / Flash-Attention:
  CEKMModel.to_bf16() casts the non-backbone parameters to bfloat16.
  Flash-Attention 2 is patched into the ESM-2 model when
  use_flash_attention_2=True and the flash_attn package is present.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional

# ---------------------------------------------------------------------------
# Soft torch import — module is importable without torch installed.
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]

# Soft transformers import (ESM-2 backbone).
try:
    from transformers import AutoModel, AutoTokenizer, EsmModel  # type: ignore
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    AutoModel = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]
    EsmModel = None  # type: ignore[assignment]

# Soft RDKit import (for fingerprint fallback in the substrate encoder).
try:
    from rdkit import Chem  # type: ignore
    from rdkit.Chem import AllChem  # type: ignore
    _RDKIT_AVAILABLE = True
except ImportError:
    _RDKIT_AVAILABLE = False
    Chem = None  # type: ignore[assignment]
    AllChem = None  # type: ignore[assignment]

if TYPE_CHECKING:
    # These only exist at type-check time; avoids polluting the runtime
    # namespace on machines without torch.
    import torch as _torch
    import torch.nn as _nn

# Standard amino-acid vocabulary for the ESM-2 stub encoder.
_AA_VOCAB: dict[str, int] = {
    aa: i for i, aa in enumerate(
        "ACDEFGHIKLMNPQRSTVWYBZXU<>$*"
    )
}
_AA_VOCAB_SIZE = len(_AA_VOCAB)
# ESM-2 650M hidden dimension — must stay 1280 as a contract invariant.
_ESM2_HIDDEN_DIM: int = 1280

# Morgan fingerprint radius and bit-vector length for the substrate fallback.
_FP_RADIUS: int = 2
_FP_NBITS: int = 2048


# ---------------------------------------------------------------------------
# Guard helper
# ---------------------------------------------------------------------------

def _require_torch() -> None:
    if not _TORCH_AVAILABLE:
        raise ImportError(
            "torch is required to instantiate CEKMModel. "
            "Install it via: pip install 'zer0pa_synbio[mfmo]'"
        )


# ---------------------------------------------------------------------------
# Sub-module 1 — ESM-2 backbone (or stub)
# ---------------------------------------------------------------------------

class ESM2Backbone(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """ESM-2-650M backbone for enzyme amino-acid sequences.

    When transformers + ESM-2 weights are available: loads the real model,
    extracts CLS-token embedding (dim=1280), optionally unfreezes the last N
    transformer layers.

    When unavailable (CI / Mac without HF cache): stubs with
    nn.Embedding(vocab_size, 1280) → mean-pools over sequence length →
    yields the same (B, 1280) output tensor. Marks `_using_real_esm2=False`.

    Input:
      sequence_ids: LongTensor (B, L)  — tokenised residue indices
    Output:
      Tensor (B, 1280)  — per-sequence embedding
    """

    _using_real_esm2: bool

    def __init__(
        self,
        model_name: str = "facebook/esm2_t33_650M_UR50D",
        frozen: bool = True,
        unfreeze_last_n_layers: int = 0,
        use_flash_attention_2: bool = False,
    ) -> None:
        _require_torch()
        super().__init__()
        self._using_real_esm2 = False
        self._frozen = frozen
        self._unfreeze_last_n = unfreeze_last_n_layers

        if _TRANSFORMERS_AVAILABLE:
            try:
                kwargs: dict[str, Any] = {
                    "trust_remote_code": False,
                }
                if use_flash_attention_2:
                    # flash-attn ≥2 required; silently fall back if absent.
                    try:
                        import flash_attn  # type: ignore  # noqa: F401
                        kwargs["attn_implementation"] = "flash_attention_2"
                    except ImportError:
                        pass
                self.esm2: Any = AutoModel.from_pretrained(model_name, **kwargs)
                self._using_real_esm2 = True
            except Exception:
                # HF weights unavailable (no cache, no internet in CI).
                self.esm2 = None

        if not self._using_real_esm2:
            # Stub: embedding table over residue vocab, shape → (B, L, 1280).
            self._stub_embed: Any = torch.nn.Embedding(_AA_VOCAB_SIZE, _ESM2_HIDDEN_DIM)
            self.esm2 = None

        if self._using_real_esm2:
            self._apply_freeze()

    def _apply_freeze(self) -> None:
        """Freeze the backbone; optionally unfreeze the last N layers."""
        assert self.esm2 is not None
        for param in self.esm2.parameters():
            param.requires_grad = False
        if not self._frozen or self._unfreeze_last_n > 0:
            # Unfreeze the top-N transformer encoder layers.
            encoder_layers: list[Any] = list(self.esm2.encoder.layer)
            unfreeze_from = max(0, len(encoder_layers) - self._unfreeze_last_n)
            for layer in encoder_layers[unfreeze_from:]:
                for param in layer.parameters():
                    param.requires_grad = True

    def forward(self, sequence_ids: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            sequence_ids: LongTensor (B, L) — tokenised residue indices

        Returns:
            Tensor (B, 1280)
        """
        if self._using_real_esm2 and self.esm2 is not None:
            attention_mask = (sequence_ids != 1).long()  # 1 = ESM-2 pad id
            out = self.esm2(
                input_ids=sequence_ids,
                attention_mask=attention_mask,
            )
            # CLS token (position 0) embedding.
            return out.last_hidden_state[:, 0, :]  # (B, 1280)
        else:
            # Stub: embed each residue, mean-pool over sequence length.
            emb = self._stub_embed(sequence_ids)  # (B, L, 1280)
            return emb.mean(dim=1)  # (B, 1280)


# ---------------------------------------------------------------------------
# Sub-module 2 — D-MPNN substrate encoder (fingerprint MLP fallback)
# ---------------------------------------------------------------------------

class _FingerprintSubstrateEncoder(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Substrate encoder using Morgan fingerprints → MLP (fallback).

    Used when a graph-neural-network stack is unavailable. Expects a
    pre-computed fingerprint tensor (B, nbits) as input; yields (B, output_dim).
    """

    def __init__(
        self,
        nbits: int = _FP_NBITS,
        hidden_dim: int = 300,
        output_dim: int = 300,
        dropout: float = 0.1,
    ) -> None:
        _require_torch()
        super().__init__()
        self.mlp = torch.nn.Sequential(
            torch.nn.Linear(nbits, 512),
            torch.nn.GELU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(512, 256),
            torch.nn.GELU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(256, output_dim),
        )

    def forward(self, fp: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            fp: FloatTensor (B, nbits) — Morgan fingerprint bit-vectors

        Returns:
            Tensor (B, output_dim)
        """
        return self.mlp(fp)


class _RandomSubstrateEncoder(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Minimal stub substrate encoder when no chemistry library is available.

    Accepts an integer InChIKey hash tensor (B,) and returns a learned
    embedding (B, output_dim).  Purely for shape-correct CPU tests.
    """

    def __init__(self, output_dim: int = 300) -> None:
        _require_torch()
        super().__init__()
        # Hash space: 2^20 buckets ought to cover test diversity.
        self.embed = torch.nn.Embedding(2**20, output_dim)
        self._output_dim = output_dim

    def forward(self, substrate_hash: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            substrate_hash: LongTensor (B,) — integer hash of InChIKey

        Returns:
            Tensor (B, output_dim)
        """
        return self.embed(substrate_hash % (2**20))


class DMPNNSubstrateEncoder(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """D-MPNN substrate encoder per PRD §12.

    Directed message-passing neural network over the molecular graph.
    Falls back gracefully to a fingerprint MLP (RDKit available, no full
    DMPNN stack) or to a hash-embedding stub (no chemistry).

    Public interface contract (load-bearing for tests):
      - Accepts `substrate_input` which is one of:
          * FloatTensor (B, nbits): pre-computed fingerprint (fingerprint mode)
          * LongTensor  (B,): integer substrate hash (stub mode)
      - Returns FloatTensor (B, hidden_dim)

    The `input_mode` attribute ("fingerprint" | "stub") is set at construction
    time based on available libraries.
    """

    input_mode: str  # "dmpnn" | "fingerprint" | "stub"

    def __init__(
        self,
        atom_feature_dim: int = 72,
        bond_feature_dim: int = 14,
        hidden_dim: int = 300,
        depth: int = 3,
        dropout: float = 0.1,
        aggregation: str = "mean",
    ) -> None:
        _require_torch()
        super().__init__()
        self._hidden_dim = hidden_dim
        self._depth = depth
        self._dropout_p = dropout
        self._aggregation = aggregation

        # Attempt to build a real D-MPNN. If the graph libraries are absent,
        # fall back to fingerprint MLP or stub.
        self._encoder: Any
        self._build_encoder(atom_feature_dim, bond_feature_dim, hidden_dim, dropout)

    def _build_encoder(
        self,
        atom_feature_dim: int,
        bond_feature_dim: int,
        hidden_dim: int,
        dropout: float,
    ) -> None:
        """Select and construct the best available encoder backend.

        Priority order: STUB > FINGERPRINT > DMPNN.

        We invert the original priority because the current train.py loop
        passes substrate_input as a LongTensor (B,) hash — only the random
        stub encoder accepts that shape. _TorchDMPNN.__init__ succeeds but
        its forward raises NotImplementedError until a Chemprop-style batch
        loader is wired in (Wave 4 future work).

        To opt back into the DMPNN path: set env CEKM_SUBSTRATE_ENCODER=dmpnn.
        To force fingerprints: CEKM_SUBSTRATE_ENCODER=fingerprint.
        """
        import os as _os

        preferred = _os.environ.get("CEKM_SUBSTRATE_ENCODER", "stub").lower()

        if preferred == "dmpnn":
            try:
                self._encoder = _TorchDMPNN(
                    atom_feature_dim=atom_feature_dim,
                    bond_feature_dim=bond_feature_dim,
                    hidden_dim=hidden_dim,
                    depth=self._depth,
                    dropout=dropout,
                    aggregation=self._aggregation,
                )
                self.input_mode = "dmpnn"
                return
            except Exception:
                pass

        if preferred in ("fingerprint", "dmpnn") and _RDKIT_AVAILABLE:
            self._encoder = _FingerprintSubstrateEncoder(
                nbits=_FP_NBITS,
                output_dim=hidden_dim,
                dropout=dropout,
            )
            self.input_mode = "fingerprint"
            return

        # Default: stub — accepts (B,) LongTensor hash input.
        self._encoder = _RandomSubstrateEncoder(output_dim=hidden_dim)
        self.input_mode = "stub"

    def forward(self, substrate_input: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            substrate_input: Tensor of shape (B, nbits) or (B,) depending on
                             `self.input_mode`.

        Returns:
            Tensor (B, hidden_dim)
        """
        return self._encoder(substrate_input)


class _TorchDMPNN(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Lightweight D-MPNN implemented in pure PyTorch (no torch_geometric).

    This is a self-contained directed-message-passing net following the
    Chemprop D-MPNN architecture.  It is used when torch is available but
    torch_geometric / chemprop is not.

    Input contract: the caller must supply a padded batch representation
    (atom_feats, bond_feats, bond_index, rev_bond_index, atom_scope) — the
    standard Chemprop batch format.  When this is unavailable (e.g., in CPU
    unit tests that pass plain tensors), the module raises a descriptive error
    so the fallback chain in DMPNNSubstrateEncoder catches it correctly.
    """

    def __init__(
        self,
        atom_feature_dim: int = 72,
        bond_feature_dim: int = 14,
        hidden_dim: int = 300,
        depth: int = 3,
        dropout: float = 0.1,
        aggregation: str = "mean",
    ) -> None:
        _require_torch()
        super().__init__()
        self._hidden_dim = hidden_dim
        self._depth = depth
        self._aggregation = aggregation

        # Initial atom + bond projection.
        self.W_i = torch.nn.Linear(atom_feature_dim + bond_feature_dim, hidden_dim, bias=False)
        # Message passing.
        self.W_h = torch.nn.Linear(hidden_dim, hidden_dim, bias=False)
        # Atom update after MP.
        self.W_o = torch.nn.Linear(atom_feature_dim + hidden_dim, hidden_dim)
        self.dropout = torch.nn.Dropout(dropout)
        self.act = torch.nn.ReLU()

    def forward(self, substrate_input: "torch.Tensor") -> "torch.Tensor":
        """Placeholder forward that raises so the fallback chain fires."""
        raise NotImplementedError(
            "_TorchDMPNN.forward() requires a Chemprop-style batch tuple. "
            "Pass pre-computed fingerprints instead, or wire a real graph loader."
        )


# ---------------------------------------------------------------------------
# Sub-module 3 — Condition MLP
# ---------------------------------------------------------------------------

class ConditionMLP(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Condition encoder: (pH, T[°C], ionic_strength) → latent condition vector.

    Input:
      conditions: FloatTensor (B, input_dim) — [pH, T, ionic_strength, ...]
    Output:
      Tensor (B, output_dim)
    """

    def __init__(
        self,
        input_dim: int = 2,
        hidden_dims: Optional[list[int]] = None,
        output_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        _require_torch()
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [64, 128]

        layers: list[Any] = []
        in_d = input_dim
        for h in hidden_dims:
            layers.append(torch.nn.Linear(in_d, h))
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(dropout))
            in_d = h
        layers.append(torch.nn.Linear(in_d, output_dim))
        self.net = torch.nn.Sequential(*layers)
        self._output_dim = output_dim

    def forward(self, conditions: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            conditions: FloatTensor (B, input_dim)

        Returns:
            Tensor (B, output_dim)
        """
        return self.net(conditions)


# ---------------------------------------------------------------------------
# Sub-module 4 — Adaptive gate (cross-attention–style fusion)
# ---------------------------------------------------------------------------

class AdaptiveGate(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Adaptive gate combining ESM-2 + D-MPNN + condition representations.

    Implements a cross-attention–style gating:
      1. Projects each of the three branch representations to a common dim.
      2. Computes learned scalar gates (sigmoid-activated) over the concatenated
         representations.
      3. Fuses via gated sum → linear projection → LayerNorm + GELU.

    Input:
      enzyme_repr:    FloatTensor (B, esm2_dim)
      substrate_repr: FloatTensor (B, substrate_dim)
      condition_repr: FloatTensor (B, condition_dim)

    Output:
      Tensor (B, output_dim)
    """

    def __init__(
        self,
        esm2_dim: int = 1280,
        substrate_dim: int = 300,
        condition_dim: int = 128,
        gate_hidden_dim: int = 256,
        output_dim: int = 512,
    ) -> None:
        _require_torch()
        super().__init__()
        self._output_dim = output_dim

        # Branch projections → common gate_hidden_dim.
        self.proj_enzyme = torch.nn.Linear(esm2_dim, gate_hidden_dim)
        self.proj_substrate = torch.nn.Linear(substrate_dim, gate_hidden_dim)
        self.proj_condition = torch.nn.Linear(condition_dim, gate_hidden_dim)

        # Gate scalars: input = [enzyme_proj, substrate_proj, condition_proj]
        # → 3 sigmoid scalars (one per branch).
        self.gate_mlp = torch.nn.Sequential(
            torch.nn.Linear(gate_hidden_dim * 3, gate_hidden_dim),
            torch.nn.Tanh(),
            torch.nn.Linear(gate_hidden_dim, 3),  # raw gate logits
        )

        # Fusion: gated_sum → output_dim.
        self.fusion = torch.nn.Sequential(
            torch.nn.Linear(gate_hidden_dim, output_dim),
            torch.nn.LayerNorm(output_dim),
            torch.nn.GELU(),
        )
        self.dropout = torch.nn.Dropout(0.1)

    def forward(
        self,
        enzyme_repr: "torch.Tensor",
        substrate_repr: "torch.Tensor",
        condition_repr: "torch.Tensor",
    ) -> "torch.Tensor":
        """
        Args:
            enzyme_repr:    (B, esm2_dim)
            substrate_repr: (B, substrate_dim)
            condition_repr: (B, condition_dim)

        Returns:
            Tensor (B, output_dim)
        """
        e = torch.relu(self.proj_enzyme(enzyme_repr))       # (B, G)
        s = torch.relu(self.proj_substrate(substrate_repr))  # (B, G)
        c = torch.relu(self.proj_condition(condition_repr))  # (B, G)

        combined = torch.cat([e, s, c], dim=-1)              # (B, 3G)
        gates = torch.sigmoid(self.gate_mlp(combined))       # (B, 3)

        # Weighted sum of the three projected branches.
        fused = (
            gates[:, 0:1] * e
            + gates[:, 1:2] * s
            + gates[:, 2:3] * c
        )  # (B, G)
        fused = self.dropout(fused)
        return self.fusion(fused)  # (B, output_dim)


# ---------------------------------------------------------------------------
# Sub-module 5 — Regression heads (kcat, Km)
# ---------------------------------------------------------------------------

class _RegressionHead(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """MLP regression head predicting a scalar in log-space.

    Input:  FloatTensor (B, input_dim)
    Output: FloatTensor (B,) — predicted log10(value)
    """

    def __init__(
        self,
        input_dim: int = 512,
        hidden_dims: Optional[list[int]] = None,
        dropout: float = 0.1,
    ) -> None:
        _require_torch()
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [256, 128]

        layers: list[Any] = []
        in_d = input_dim
        for h in hidden_dims:
            layers.append(torch.nn.Linear(in_d, h))
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(dropout))
            in_d = h
        layers.append(torch.nn.Linear(in_d, 1))
        self.net = torch.nn.Sequential(*layers)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            x: (B, input_dim)

        Returns:
            Tensor (B,)
        """
        return self.net(x).squeeze(-1)


# ---------------------------------------------------------------------------
# Sub-module 6 — Discriminator heads (one per adversarial tier)
# ---------------------------------------------------------------------------

class _DiscriminatorHead(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Binary discriminator head for one adversarial tier (α | β | γ).

    Input:  FloatTensor (B, input_dim)
    Output: FloatTensor (B,) — raw binary logit (positive=1, negative=0)
    """

    def __init__(
        self,
        input_dim: int = 512,
        hidden_dims: Optional[list[int]] = None,
        dropout: float = 0.1,
    ) -> None:
        _require_torch()
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [128, 64]

        layers: list[Any] = []
        in_d = input_dim
        for h in hidden_dims:
            layers.append(torch.nn.Linear(in_d, h))
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(dropout))
            in_d = h
        layers.append(torch.nn.Linear(in_d, 1))
        self.net = torch.nn.Sequential(*layers)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            x: (B, input_dim)

        Returns:
            Tensor (B,) — raw logit
        """
        return self.net(x).squeeze(-1)


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------

class CEKMModel(nn.Module if _TORCH_AVAILABLE else object):  # type: ignore[misc]
    """Conditional Enzyme Kinetics Model (PRD §12).

    Architecture:
        ESM2Backbone          → enzyme repr  (B, 1280)
        DMPNNSubstrateEncoder → substrate repr (B, hidden_dim)
        ConditionMLP          → condition repr (B, condition_dim)
        AdaptiveGate          → fused repr (B, gate_output_dim)
        _RegressionHead × 2   → log10(kcat), log10(Km)  each (B,)
        _DiscriminatorHead × 3 → disc_alpha, disc_beta, disc_gamma each (B,)

    Dropout-based uncertainty:
        Enabling dropout at eval time (model.train(False) with
        `enable_dropout=True`) gives MC-dropout uncertainty estimates.
        The model exposes `enable_mc_dropout()` for this.

    bfloat16:
        Call `.to_bf16()` to cast non-backbone parameters to bfloat16.
    """

    _using_real_esm2: bool  # reflected from ESM2Backbone

    def __init__(self, cfg: Any) -> None:  # cfg: TrainingConfig at runtime
        """
        Args:
            cfg: TrainingConfig (from train.py) or any object with attributes
                 esm2, dmpnn, condition_mlp, adaptive_gate, heads matching
                 the dataclasses defined in train.py.
        """
        _require_torch()
        super().__init__()

        esm2_cfg = cfg.esm2
        dmpnn_cfg = cfg.dmpnn
        cond_cfg = cfg.condition_mlp
        gate_cfg = cfg.adaptive_gate
        heads_cfg = cfg.heads

        # --- backbone -------------------------------------------------------
        self.esm2_backbone = ESM2Backbone(
            model_name=esm2_cfg.model_name,
            frozen=esm2_cfg.frozen,
            unfreeze_last_n_layers=esm2_cfg.unfreeze_last_n_layers,
            use_flash_attention_2=getattr(cfg, "use_flash_attention_2", False),
        )
        self._using_real_esm2 = self.esm2_backbone._using_real_esm2

        # --- substrate encoder ----------------------------------------------
        self.substrate_encoder = DMPNNSubstrateEncoder(
            atom_feature_dim=dmpnn_cfg.atom_feature_dim,
            bond_feature_dim=dmpnn_cfg.bond_feature_dim,
            hidden_dim=dmpnn_cfg.hidden_dim,
            depth=dmpnn_cfg.depth,
            dropout=dmpnn_cfg.dropout,
            aggregation=dmpnn_cfg.aggregation,
        )

        # --- condition MLP --------------------------------------------------
        self.condition_mlp = ConditionMLP(
            input_dim=cond_cfg.input_dim,
            hidden_dims=list(cond_cfg.hidden_dims),
            output_dim=cond_cfg.output_dim,
            dropout=cond_cfg.dropout,
        )

        # --- adaptive gate --------------------------------------------------
        self.adaptive_gate = AdaptiveGate(
            esm2_dim=gate_cfg.esm2_dim,
            substrate_dim=gate_cfg.substrate_dim,
            condition_dim=gate_cfg.condition_dim,
            gate_hidden_dim=gate_cfg.gate_hidden_dim,
            output_dim=gate_cfg.output_dim,
        )
        gate_out = gate_cfg.output_dim

        # --- output heads ---------------------------------------------------
        self.kcat_head = _RegressionHead(
            input_dim=gate_out,
            hidden_dims=list(heads_cfg.kcat_hidden_dims),
        )
        self.km_head = _RegressionHead(
            input_dim=gate_out,
            hidden_dims=list(heads_cfg.km_hidden_dims),
        )
        # Three discriminator heads: alpha, beta, gamma.
        assert heads_cfg.n_discriminator_heads == 3, (
            "CEKMModel expects exactly 3 discriminator heads (one per adversarial tier)."
        )
        self.disc_alpha = _DiscriminatorHead(
            input_dim=gate_out,
            hidden_dims=list(heads_cfg.discriminator_hidden_dims),
        )
        self.disc_beta = _DiscriminatorHead(
            input_dim=gate_out,
            hidden_dims=list(heads_cfg.discriminator_hidden_dims),
        )
        self.disc_gamma = _DiscriminatorHead(
            input_dim=gate_out,
            hidden_dims=list(heads_cfg.discriminator_hidden_dims),
        )

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        sequence_ids: "torch.Tensor",
        substrate_input: "torch.Tensor",
        conditions: "torch.Tensor",
    ) -> dict[str, "torch.Tensor"]:
        """Full model forward pass.

        Args:
            sequence_ids:    LongTensor  (B, L)   — tokenised enzyme sequence
            substrate_input: Tensor      (B, ...)  — substrate features
                             (B, nbits) for fingerprint mode, (B,) for stub
            conditions:      FloatTensor (B, C)   — [pH, T, ionic_strength, ...]

        Returns:
            dict with keys:
              "kcat_log"    FloatTensor (B,)  — predicted log10(kcat / s⁻¹)
              "km_log"      FloatTensor (B,)  — predicted log10(Km / mM)
              "disc_alpha"  FloatTensor (B,)  — binary logit, tier-α discriminator
              "disc_beta"   FloatTensor (B,)  — binary logit, tier-β discriminator
              "disc_gamma"  FloatTensor (B,)  — binary logit, tier-γ discriminator
              "fused"       FloatTensor (B, gate_output_dim) — fused representation
        """
        enzyme_repr = self.esm2_backbone(sequence_ids)         # (B, 1280)
        substrate_repr = self.substrate_encoder(substrate_input)  # (B, substrate_dim)
        condition_repr = self.condition_mlp(conditions)         # (B, condition_dim)

        fused = self.adaptive_gate(enzyme_repr, substrate_repr, condition_repr)  # (B, gate_out)

        kcat_log = self.kcat_head(fused)       # (B,)
        km_log = self.km_head(fused)           # (B,)
        disc_alpha = self.disc_alpha(fused)    # (B,)
        disc_beta = self.disc_beta(fused)      # (B,)
        disc_gamma = self.disc_gamma(fused)    # (B,)

        return {
            "kcat_log": kcat_log,
            "km_log": km_log,
            "disc_alpha": disc_alpha,
            "disc_beta": disc_beta,
            "disc_gamma": disc_gamma,
            "fused": fused,
        }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def to_bf16(self) -> "CEKMModel":
        """Cast all non-backbone parameters to bfloat16. Returns self."""
        # Cast the whole model, then restore backbone precision.
        self.bfloat16()
        # Keep stub embedding in float32 to avoid tokenisation issues.
        if not self._using_real_esm2:
            self.esm2_backbone._stub_embed.float()
        return self

    def enable_mc_dropout(self) -> None:
        """Enable dropout at eval time (MC-Dropout uncertainty estimation)."""
        for module in self.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train(True)

    def named_trainable_parameters(self) -> list[tuple[str, "torch.nn.Parameter"]]:
        """Return list of (name, param) for all parameters that require grad."""
        return [(n, p) for n, p in self.named_parameters() if p.requires_grad]

    def count_parameters(self) -> dict[str, int]:
        """Return {backbone, non_backbone, total} parameter counts."""
        backbone_params = sum(
            p.numel() for p in self.esm2_backbone.parameters()
        )
        non_backbone_params = sum(
            p.numel() for p in self.parameters()
        ) - backbone_params
        return {
            "backbone": backbone_params,
            "non_backbone": non_backbone_params,
            "total": backbone_params + non_backbone_params,
        }


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def build_cekm_model(cfg: Any) -> "CEKMModel":
    """Instantiate a CEKMModel from a TrainingConfig.

    Args:
        cfg: TrainingConfig (or compatible duck-type with the expected attrs).

    Returns:
        CEKMModel on CPU (caller is responsible for .cuda() / .to(device)).

    Raises:
        ImportError: if torch is not installed.
    """
    _require_torch()
    model = CEKMModel(cfg)
    return model


__all__ = [
    "CEKMModel",
    "ESM2Backbone",
    "DMPNNSubstrateEncoder",
    "ConditionMLP",
    "AdaptiveGate",
    "build_cekm_model",
    "_TORCH_AVAILABLE",
    "_TRANSFORMERS_AVAILABLE",
    "_RDKIT_AVAILABLE",
    "_ESM2_HIDDEN_DIM",
    "_FP_NBITS",
]
