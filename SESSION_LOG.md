# Signal Shield - Session Log (Aug 6, 2026)

## 1. UI Updates (Landing Page)

Updated all landing page components to match Figma design screenshots.

### Files Modified:
- `frontend/src/components/landing/Problem.tsx` — light blue bg (#EEF2FF), green badge, blue stat values, updated labels
- `frontend/src/components/landing/Comparison.tsx` — "WHY SIGNALSHIELD" dark navy, updated table rows (Survives compression, Data privacy), blue checks
- `frontend/src/components/landing/Features.tsx` — card layout with shield icon, "AUDIO" category badge
- `frontend/src/components/landing/HowItWorks.tsx` — updated step descriptions, translucent white badge
- `frontend/src/components/landing/TryItFree.tsx` — Resemblyzer/ECAPA-TDNN/HuBERT encoders, green checkmarks, upload icon, light bg
- `frontend/src/components/landing/Pricing.tsx` — Creator card dark navy with "Most Popular", updated features, rounded-full dark CTA buttons
- `frontend/src/components/landing/LearnMore.tsx` — green "API" badge, JS/TS code example, 10,000 Hz
- `frontend/src/components/landing/Footer.tsx` — updated tagline, PRODUCT links only with Changelog added

### Figma MCP Server Added:
```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```
Restart Claude Code to use it. Share Figma URL for pixel-perfect implementation.

---

## 2. Vast.ai GPU Training Setup

### Instance Details
- **Instance ID:** 47002374
- **Machine:** RTX 3090 (2x), Czechia datacenter
- **Cost:** $0.27/hr
- **Disk:** 100GB allocated
- **SSH:** `ssh -p 12374 root@ssh4.vast.ai`
- **Vastai CLI path:** `/Users/raimasaha/Library/Python/3.13/bin/vastai`

### What Was Set Up on the Instance
1. Installed aria2, downloaded LibriSpeech train-clean-360 (~21GB)
2. Extracted to `/root/LibriSpeech/train-clean-360/`
3. Ran `prepare_data.py` — **921 speakers**, 93,546 train / 10,468 valid utterances
4. Converted JSON manifests to CSV with duration/start/stop columns (`make_csv.py`)
5. Filtered short clips (<3.5s) with `fix_csv.py` — resulted in 828 usable speakers
6. Installed SpeechBrain, cloned recipes to `/root/speechbrain/`
7. Upgraded PyTorch to 2.4.0 for SpeechBrain compatibility
8. Downloaded noise/RIR augmentation data

### File Locations on Instance
- LibriSpeech: `/root/LibriSpeech/train-clean-360/`
- Manifests: `/root/manifests/train.csv`, `/root/manifests/valid.csv`
- SpeechBrain: `/root/speechbrain/`
- Training scripts: `/root/training/`
  - `prepare_data.py`
  - `make_csv.py`
  - `fix_csv.py`
  - `setup.sh` (PyTorch upgrade)
  - `run_xvector.sh`
  - `run_ecapa.sh`
- X-Vector output: `/root/output/xvector/`
- ECAPA output (future): `/root/output/ecapa/`

### Training Scripts

#### run_xvector.sh (currently running)
```bash
cd /root/speechbrain/recipes/VoxCeleb/SpeakerRec
python train_speaker_embeddings.py \
  hparams/train_x_vectors.yaml \
  --data_folder /root/manifests \
  --train_annotation /root/manifests/train.csv \
  --valid_annotation /root/manifests/valid.csv \
  --out_n_neurons 921 \
  --output_folder /root/output/xvector \
  --batch_size 128 \
  --number_of_epochs 10 \
  --precision fp16 \
  --num_workers 2 \
  --dataloader_options '{"num_workers": 2}'
```

#### run_ecapa.sh (run after X-Vector finishes)
```bash
cd /root/speechbrain/recipes/VoxCeleb/SpeakerRec
python train_speaker_embeddings.py \
  hparams/train_ecapa_tdnn.yaml \
  --data_folder /root/manifests \
  --train_annotation /root/manifests/train.csv \
  --valid_annotation /root/manifests/valid.csv \
  --out_n_neurons 921 \
  --output_folder /root/output/ecapa \
  --batch_size 64 \
  --number_of_epochs 10 \
  --precision fp16 \
  --num_workers 2 \
  --dataloader_options '{"num_workers": 2}'
```

### Reconnecting to Training
```bash
ssh -p 12374 root@ssh4.vast.ai
tmux attach
```

### After Training is Complete

#### 1. Run ECAPA-TDNN (if X-Vector just finished)
```bash
bash /root/training/run_ecapa.sh
```

#### 2. Download trained models to local machine
```bash
scp -P 12374 -r root@ssh4.vast.ai:/root/output/xvector/save/CKPT+latest ~/workspace/signal-shield/backend/models/xvector
scp -P 12374 -r root@ssh4.vast.ai:/root/output/ecapa/save/CKPT+latest ~/workspace/signal-shield/backend/models/ecapa
```

#### 3. Configure backend to use custom models
```bash
export SS_XVECTOR_MODEL_PATH=/path/to/models/xvector
export SS_ECAPA_MODEL_PATH=/path/to/models/ecapa
```

#### 4. Destroy the Vast.ai instance (stop paying)
```bash
/Users/raimasaha/Library/Python/3.13/bin/vastai destroy instance 47002374
```

---

## 3. Issues Encountered & Solutions

| Issue | Solution |
|---|---|
| Disk full (16GB default) | Use CLI: `vastai create instance ... --disk 100` |
| `vastai` command not found | Use full path: `/Users/raimasaha/Library/Python/3.13/bin/vastai` |
| Multi-line paste breaks in SSH | Use `scp` to upload scripts instead of pasting |
| SpeechBrain expects CSV not JSON | Created `make_csv.py` to convert with duration columns |
| Short audio clips crash training | Created `fix_csv.py` to filter clips < 3.5s |
| `torch.amp.custom_fwd` missing | Upgraded PyTorch to 2.4.0 (`setup.sh`) |
| CUDA OOM at default batch size | Reduced batch_size to 128 with fp16 |
| DataLoader worker crash | Set `num_workers 0` initially, then 2 |

---

## 4. GPU Recommendations (for future reference)

For speaker encoder training (small models ~5M params):
- **Best value:** RTX 3090 ($0.20-0.40/hr) — 24GB VRAM, plenty for these models
- **Overkill:** A100 ($0.80-1.50/hr) — not needed for this workload
- **Too small:** RTX 3080 10GB — tight on VRAM
- **Key filters on Vast.ai:** 200GB+ disk, 95%+ reliability, on-demand (not interruptible)
- Always set disk allocation explicitly when renting
- Always use tmux for long training runs
- Use aria2c for fast dataset downloads
