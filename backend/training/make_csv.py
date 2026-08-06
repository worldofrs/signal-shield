import json
import csv
import soundfile as sf

for s in ["train", "valid"]:
    d = json.load(open(f"/root/manifests/{s}.json"))
    f = open(f"/root/manifests/{s}.csv", "w", newline="")
    w = csv.writer(f)
    w.writerow(["ID", "duration", "wav", "start", "stop", "spk_id"])
    count = 0
    for u, i in d.items():
        info = sf.info(i["wav"])
        dur = info.duration
        w.writerow([u, dur, i["wav"], 0, dur, i["spk_id"]])
        count += 1
        if count % 5000 == 0:
            print(f"{s}: {count} done")
    f.close()
    print(f"{s}.csv: {count} rows")
