"""
This script extracts all unique source and target files from a filtered-without-innerclasses.rsf and saves them as a JSON list.
With this it is clear which java files are relevant for our group.
"""

import json

files = set()
with open("filtered-without-innerclasses.rsf", "r") as infile:
    for line in infile:
        parts = line.strip().split()
        if len(parts) != 3 or parts[0] != "depends":
            continue
        source, target = parts[1], parts[2]
        files.add(source)
        files.add(target)

with open("relevant-files.json", "w") as outfile:
    json.dump(list(files), outfile)

print("Done. Result can be found in relevant-files.json")