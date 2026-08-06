import argparse
import csv
import json
import random
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Prepare SpeechBrain JSON manifests from LibriSpeech and Common Voice."
    )
    parser.add_argument("--librispeech", required=True, help="Path to LibriSpeech root")
    parser.add_argument("--commonvoice", default=None, help="Path to Common Voice directory contain validated.tsv and clips/")
    parser.add_argument("--output", required=True, help="Output directory for train.json and valid.json")
    args = parser.parse_args()

    # collect utterances
    entries = collect_librispeech(args.librispeech)
    if args.commonvoice:
        entries.update(collect_commonvoice(args.commonvoice))

    # split, train, write
    train, valid = split_by_speaker(entries)

    Path(args.output).mkdir(parents=True, exist_ok=True)
    with open (Path(args.output) / "train.json", "w") as f:
        json.dump(train, f, indent = 2)
    with open (Path(args.output) / "valid.json", "w") as f:
            json.dump(valid, f, indent = 2)

    # print stats
    all_spks = {info["spk_id"] for info in entries.values()}
    print(f"Total speakers: {len(all_spks)} (set out_n_neurons to this value)")
    print(f"Train: {len(train)} utterances, Valid: {len(valid)} utterances")

def collect_librispeech(root):
    entries = {}
    for flac in Path(root).rglob("*.flac"):
        spk_id = f"ls-{flac.parent.parent.name}"
        utt_id = f"ls-{flac.stem}"
        entries[utt_id] = {"wav": str(flac.resolve()), "spk_id": spk_id}
    return entries

def collect_commonvoice(root):
    entries = {}
    tsv = Path(root) / "validated.tsv"
    with open(tsv) as f:
        reader = csv.DictReader(f, delimiter="\t") 
        for row in reader:
            clip = Path(root) / "clips" / row["path"]
            spk_id = f"cv-{row['client_id']}"
            utt_id = f"cv-{clip.stem}"
            entries[utt_id] = {"wav": str(clip.resolve()), "spk_id": spk_id}
    return entries

def split_by_speaker(entries, train_ratio=0.9):
    speakers = {}
    for utt_id, info in entries.items():
        speakers.setdefault(info["spk_id"], []).append(utt_id)

    spk_list = sorted(speakers.keys())
    random.shuffle(spk_list)
    cut = int(len(spk_list) * train_ratio)

    train, valid = {}, {}
    for spk in spk_list[:cut]:
        for utt_id in speakers[spk]:
            train[utt_id] = entries[utt_id]
    for spk in spk_list[cut:]:
        for utt_id in speakers[spk]:
            valid[utt_id] = entries[utt_id]
    return train, valid

if __name__ == "__main__":
    main()