# Autonomous H100 SXM run — operator runbook

**Boundary block:** Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

---

## 1. What this chain does

One H100 SXM pod runs detached for ~16–24 h, executing the full
GPU-bound work that closes Wave 4 (real CEKM training) + Wave 5 (L4.5
unknown-enzyme inference) + Wave 9 (HMO triple full numerical run),
then auto-pushes everything to GitHub + Hugging Face. The Mac that
launches the pod is **not** required to remain online — the pod is
self-sufficient, self-resuming, and self-pushing.

**Phase chain (canonical):**

| # | Phase | Wallclock target | Skippable? |
|---|---|---|---|
| 00 | preflight | <10 min | no |
| 10 | install_deps (torch+CUDA, flash-attn-2, ESMFold, MACE-OFF) | 10–30 min | no |
| 20 | stage_data (HF dataset → /workspace/data/) | 10–60 min | no (degrades gracefully) |
| 30 | cekm_train (real corpus, 20K steps, resume-safe) | **6–8 h** | no |
| 40 | cekm_eval (calibration audit, held-out + Tier α/β/γ) | 1–2 h | no |
| 50 | hf_push_cekm (Architect-Prime/synbio-cekm-v0.1) | 15–30 min | no |
| 60 | l45_inference (ESMFold + MACE-OFF + opt RFdiffusion3) | 1–6 h | yes (RFdiffusion3 only if FOUNDRY_TOKEN set) |
| 70 | hmo_triple (Wave 9 full numerical run) | 2–3 h | no |
| 80 | audit_verify (synbio audit verify per seed) | <30 min | no |
| 90 | finalize (FINAL-REPORT-RUNPOD-AUTONOMOUS.md + push) | <30 min | no |

---

## 2. Operator pre-flight checklist (do these on the Mac before starting the pod)

### 2.1 Stage CEKM corpora to HF (saves ~45 min of pod time)

```bash
# In the worktree:
cd "/Users/zer0palab/Synthetic Biology Pipeline/.claude/worktrees/hopeful-roentgen-e3c78e"
source .venv/bin/activate

# Optional: pre-download BRENDA bulk (registration required)
# Place flattened TSV at data/raw/brenda/brenda_data.tsv

# Run the stager — clones EnzyExtract + ProteinGym, uploads everything to HF
bash scripts/runpod/stage_corpora_to_hf.sh
```

### 2.2 Mint a GitHub PAT

The pod needs to push to `Zer0pa/Synthetic-Biology`. Mint a
fine-grained PAT with `Contents: Read and write` on that repo only.
Save the token; you'll paste it as `GH_TOKEN` in Runpod.

### 2.3 (Optional) Foundry token for RFdiffusion3

If you have a RosettaCommons Foundry account with RFdiffusion3 access,
set `FOUNDRY_TOKEN` in the pod env. Without it, phase 60's
RFdiffusion3 substep is skipped (the rest of the chain proceeds
normally; DSLNT seed gets a Tier-3 advisory rather than a Tier-1/2
enzyme design).

---

## 3. Pod creation (Runpod UI)

| Field | Value |
|---|---|
| GPU | **H100 SXM 80 GB** (preferred) or H100 PCIe 80 GB |
| Region | EU or US-East — pick whichever has SXM availability |
| Image | `pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel` (or any 2.x torch + CUDA 12 image) |
| Volume | Persistent volume mounted at `/workspace`, **≥150 GiB** (CEKM checkpoints + corpora are heavy) |
| Env vars | `HF_TOKEN`, `GH_TOKEN`, optional `FOUNDRY_TOKEN` |
| Startup command | `bash -c "curl -fsSL https://raw.githubusercontent.com/Zer0pa/Synthetic-Biology/main/scripts/runpod/bootstrap.sh \| bash"` |

When the pod boots, the bootstrap script:

1. Installs apt-level deps (tmux, jq, git build-essential).
2. Configures git auth from `GH_TOKEN`.
3. Clones / fast-forwards `Zer0pa/Synthetic-Biology` at `/workspace/Synthetic-Biology`.
4. Persists `HF_TOKEN` to `~/.cache/huggingface/token`.
5. Launches a tmux session named `synbio` with three panes:
   - pane 0: orchestrator (phase runner)
   - pane 1: heartbeat (pushes status to git every 10 min)
   - pane 2: watchdog (alerts on GPU underutilization)

The bootstrap script then exits. The pod is now running detached.

---

## 4. How to monitor without SSH

The pod's heartbeat pushes `audit/runtime/runpod/heartbeat.txt` and
`STATUS.md` to git every 10 minutes (and immediately on every phase
boundary). From any machine with a clone:

```bash
git pull --ff-only origin main
cat audit/runtime/runpod/STATUS.md           # human-readable summary
cat audit/runtime/runpod/heartbeat.txt        # latest GPU/disk/RAM snapshot
cat audit/runtime/runpod/PHASE_LOG.md         # append-only timeline
cat audit/runtime/runpod/WATCHDOG_ALERTS.md   # GPU underutilization alerts (if any)
```

Phase sentinels (`audit/runtime/runpod/phase_<N>_<name>.done`) tell
you which phases have completed.

If you want to live-tail SSH:

```bash
ssh root@<pod>
tmux attach -t synbio        # Ctrl-b d to detach without killing
```

---

## 5. Resume semantics (what happens if the pod restarts)

- Each phase writes a sentinel file on success. On restart, the
  orchestrator skips phases whose sentinel exists.
- CEKM training (phase 30) uses `synbio cekm train --resume` so a
  mid-training kill picks up at the latest checkpoint (per
  `checkpoint_every_steps=1000`, max ~3 min of work lost).
- Data downloads (phase 20) are no-op when files already exist on disk.
- HF push (phase 50) is content-addressed — re-uploads the same file
  is a no-op on HF.

If the pod is destroyed (not just restarted) the persistent volume
preserves checkpoints; reattach the volume to a new pod and re-run
bootstrap to resume.

---

## 6. Operator emergency stop

From any clone:

```bash
touch PAUSE_ORCHESTRATOR.flag
git add PAUSE_ORCHESTRATOR.flag
git -c user.email=architects@zer0pa.ai -c user.name=Operator \
    commit -m "Pause autonomous run"
git push origin main
```

The orchestrator detects the flag at every phase boundary and exits
gracefully (writes status, pushes, returns code 42). To resume:
delete the flag, push, and re-run bootstrap on the pod.

---

## 7. Failure modes the chain handles automatically

| Failure | Recovery |
|---|---|
| SSH disconnect | tmux session keeps running |
| Pod restart / preempt | orchestrator skips done sentinels; CEKM resumes from checkpoint |
| CUDA OOM during training | phase 30 reduces batch_size from 64 → 32 → 16 on retry |
| NaN loss | train.py rolls back to last checkpoint; orchestrator retries |
| HF service hiccup | huggingface-cli has internal retries; phase 50 tolerates 5 retries |
| GitHub push fails | exponential backoff (10s, 30s, 60s, 180s, 600s); next phase boundary retries |
| GPU sat <10% for 10+ min | watchdog appends to WATCHDOG_ALERTS.md and pushes (soft alert; doesn't kill phase) |
| Single phase exceeds timeout_minutes | orchestrator kills + retries (per phase max_retries) |
| All retries exhausted on required phase | orchestrator halts, pushes FATAL status, exits code 5 |

---

## 8. After the chain completes

The pod auto-pushes:

- **GitHub `origin/main`** — `FINAL-REPORT-RUNPOD-AUTONOMOUS.md`,
  envelope chains in `audit/runtime/hmo_seed_*/`, audit verify reports,
  watchdog alerts, phase logs.
- **HF `Architect-Prime/synbio-cekm-v0.1`** — trained CEKM checkpoint,
  meta.json, training audit JSONL, README with Wave-4 metrics.

The `audit/runtime/runpod/COMPLETE.flag` file signals that the chain
is done. The pod is safe to terminate.

To pick up where the pod left off (on Mac):

```bash
git pull --ff-only origin main
cat FINAL-REPORT-RUNPOD-AUTONOMOUS.md
```

---

## 9. What is NOT done autonomously (operator follow-up)

- **Salis v1.0 GPL binary install + `SALIS_RBS_BIN` setup** —
  operator step; the wrapper is in place per `HANDOFF-CPU-CONTINUATION.md` § F.
- **Full LIRC corpus build** (~4-8h CPU; could run on a small CPU VM,
  not GPU-bound) + HF push to `Architect-Prime/synbio-lirc-v0.1`.
- **PathGym DBTL holdout calibration** of TDA `warning_score`
  thresholds and L5 surrogate calibration.

---

## 10. RESISTANCE.md compliance (binding)

- `fp-rushtoend`: the chain doesn't declare anything done because the
  scaffolding looks right. Each phase has executable verification —
  CEKM training requires a checkpoint to be written; HF push verifies
  via a download check; audit verify must pass on each campaign.
- `fp-NULLasout`: a phase failing optional gates (e.g., FOUNDRY_TOKEN
  unset → RFdiffusion3 skipped) is logged as a graceful skip, not as
  "the run failed." Required-phase failure halts the chain with a
  diagnostic, not a silent NULL.
- `fp-flatteryasfreedom`: the autonomous mandate is binding because
  the verification surface (heartbeat to git, watchdog, audit verify)
  is binding. The operator can interrupt at any phase boundary via
  `PAUSE_ORCHESTRATOR.flag`.
- `fp-efficiency-as-corner-cutting`: the chain runs the full Wave 4 +
  Wave 5 + Wave 9 sequence end-to-end. Skipping CEKM eval (phase 40)
  to save time would corrupt the calibration audit; skipping audit
  verify (phase 80) would corrupt the conformance assertion. Neither
  is allowed.

---

## 11. Quick reference

- **Bootstrap from anywhere:** `curl -fsSL https://raw.githubusercontent.com/Zer0pa/Synthetic-Biology/main/scripts/runpod/bootstrap.sh | bash` (env: HF_TOKEN, GH_TOKEN, optional FOUNDRY_TOKEN).
- **Inspect from anywhere:** `git pull --ff-only && cat audit/runtime/runpod/STATUS.md`.
- **Pause from anywhere:** commit `PAUSE_ORCHESTRATOR.flag` to main.
- **Final outputs:** `FINAL-REPORT-RUNPOD-AUTONOMOUS.md` (git) + `Architect-Prime/synbio-cekm-v0.1` (HF).
- **Estimated wallclock:** 16–24 h H100 SXM, depending on RFdiffusion3.
