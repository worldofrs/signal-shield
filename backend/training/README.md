# Training Clean Speaker Encoders

Train x-vector and ECAPA-TDNN models from scratch on commercially clean data,
replacing the default VoxCeleb-pretrained weights.

## 1. Download Data

### LibriSpeech (required)

Download `train-clean-360` (or `train-clean-100` for a faster test run):

```bash
wget https://www.openslr.org/resources/12/train-clean-360.tar.gz
tar xzf train-clean-360.tar.gz
```

### Common Voice (optional, adds speaker diversity)

Download from https://commonvoice.mozilla.org/en/datasets — you need the
`validated.tsv` file and the `clips/` directory.

## 2. Prepare Data

Run the preparation script to generate SpeechBrain JSON manifests:

```bash
# LibriSpeech only
python prepare_data.py \
  --librispeech /path/to/LibriSpeech/train-clean-360 \
  --output /path/to/manifests

# LibriSpeech + Common Voice
python prepare_data.py \
  --librispeech /path/to/LibriSpeech/train-clean-360 \
  --commonvoice /path/to/cv-corpus-XX/en \
  --output /path/to/manifests
```

This outputs `train.json` and `valid.json`, and prints the total speaker count.
Note that number — you need it for `out_n_neurons` in step 3.

## 3. Train Models

Clone SpeechBrain and use its speaker verification recipes:

```bash
git clone https://github.com/speechbrain/speechbrain.git
cd speechbrain
pip install -e .
```

### X-Vector

```bash
cd recipes/VoxCeleb/SpeakerRec
python train_speaker_embeddings.py hparams/train_xvect.yaml \
  --data_folder /path/to/manifests \
  --train_annotation /path/to/manifests/train.json \
  --valid_annotation /path/to/manifests/valid.json \
  --out_n_neurons <SPEAKER_COUNT> \
  --output_folder /path/to/output/xvector
```

### ECAPA-TDNN

```bash
cd recipes/VoxCeleb/SpeakerRec
python train_speaker_embeddings.py hparams/train_ecapa_tdnn.yaml \
  --data_folder /path/to/manifests \
  --train_annotation /path/to/manifests/train.json \
  --valid_annotation /path/to/manifests/valid.json \
  --out_n_neurons <SPEAKER_COUNT> \
  --output_folder /path/to/output/ecapa
```

Replace `<SPEAKER_COUNT>` with the number printed by `prepare_data.py`.

## 4. Use Trained Models

Point the backend at your trained models via environment variables:

```bash
export SS_XVECTOR_MODEL_PATH=/path/to/output/xvector/save/CKPT+latest
export SS_ECAPA_MODEL_PATH=/path/to/output/ecapa/save/CKPT+latest
```

Then start the backend as usual. It will load your custom-trained models
instead of the default VoxCeleb-pretrained ones.

## Notes

- Split is by speaker (not utterance) to prevent data leakage in validation.
- Speaker IDs are prefixed with `ls-` / `cv-` to avoid collisions between datasets.
- Training from scratch requires a GPU. CPU training is possible but impractical.
- `train-clean-100` has ~250 speakers; `train-clean-360` has ~900. More speakers = better embeddings.
