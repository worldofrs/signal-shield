#!/bin/bash
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
