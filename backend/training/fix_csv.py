import csv

MIN_DURATION = 3.5  # seconds, must be longer than the training segment length

for s in ["train", "valid"]:
    inpath = f"/root/manifests/{s}.csv"
    outpath = f"/root/manifests/{s}_fixed.csv"
    total = 0
    kept = 0
    with open(inpath, newline="") as fin, open(outpath, "w", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            total += 1
            if float(row["duration"]) >= MIN_DURATION:
                writer.writerow(row)
                kept += 1
    print(f"{s}: kept {kept}/{total} (removed {total - kept} short clips)")

    # overwrite original
    import shutil
    shutil.move(outpath, inpath)
    print(f"  -> saved to {inpath}")
