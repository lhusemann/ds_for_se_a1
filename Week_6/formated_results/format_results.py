import csv
import os

INPUT_CLUSTER_SET_RSF = "file-based-rsf/arc.rsf"
INPUT_FOLDER_CLUSTER_DESCRIPTION = "folder/arc"
OUTPUT_CSV = "arc.csv"

cluster_files = {}
with open(INPUT_CLUSTER_SET_RSF, "r") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0] == "contain":
            cluster_id = parts[1]
            file_name = parts[2]
            cluster_files.setdefault(cluster_id, []).append(file_name)


rows = []
for txt_file in sorted(os.listdir(INPUT_FOLDER_CLUSTER_DESCRIPTION)):
    if not txt_file.endswith(".txt"):
        continue

    cluster_id = txt_file.removesuffix(".txt")
    txt_path = os.path.join(INPUT_FOLDER_CLUSTER_DESCRIPTION, txt_file)

    with open(txt_path, "r") as f:
        lines = f.readlines()

    title = lines[0].strip() if lines else ""
    description = "".join(lines[1:]).strip() if len(lines) > 1 else ""
    files = "; ".join(cluster_files.get(cluster_id, []))

    rows.append({
        "cluster_ID": cluster_id,
        "files": files,
        "title": title,
        "description": description,
    })

# Write everything to a CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["cluster_ID", "files", "title", "description"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done — wrote {len(rows)} rows to {OUTPUT_CSV}")