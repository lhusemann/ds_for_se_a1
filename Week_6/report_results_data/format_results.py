import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CLUSTER_SET_RSF = os.path.join(BASE_DIR, "..", "extra_results_data", "file-based-rsf", "wca_UEM.rsf")
INPUT_FOLDER_CLUSTER_DESCRIPTION = os.path.join(BASE_DIR, "..", "..", "Week_4", "generated_files", "wca_UEM", "chain-of-thought")
OUTPUT_CSV = os.path.join(BASE_DIR, "chain-of-thought.csv")

cluster_files = {}
with open(INPUT_CLUSTER_SET_RSF, "r") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0] == "contain":
            cluster_id = parts[1]
            file_name = parts[2]
            if cluster_id.endswith(".ss"):
                # this is the case for the acdc.rsf
                cluster_id = cluster_id[:-3]
            cluster_files.setdefault(cluster_id, []).append(file_name)

rows = []
for txt_file in sorted(os.listdir(INPUT_FOLDER_CLUSTER_DESCRIPTION), key=lambda f: int(f.removesuffix(".txt"))):
    if not txt_file.endswith(".txt"):
        continue

    cluster_id = txt_file.removesuffix(".txt")
    txt_path = os.path.join(INPUT_FOLDER_CLUSTER_DESCRIPTION, txt_file)

    with open(txt_path, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        non_empty_lines = [line for line in lines if line]

    if non_empty_lines and non_empty_lines[0].startswith("**Title:**"):
        title = non_empty_lines[0].removeprefix("**Title:**").strip()
        remaining = non_empty_lines[1:]
        if remaining and remaining[0].startswith("**Summary:**"):
            remaining[0] = remaining[0].removeprefix("**Summary:**").strip()
        description = " ".join(line for line in remaining if line)
    else:
        title = "unknown"
        description = " ".join(non_empty_lines)

    files = "; ".join(cluster_files.get(cluster_id, []))

    rows.append({
        "cluster_ID": cluster_id,
        "files": files,
        "title": title,
        "description": description,
    })

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["cluster_ID", "files", "title", "description"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done — wrote {len(rows)} rows to {OUTPUT_CSV}")