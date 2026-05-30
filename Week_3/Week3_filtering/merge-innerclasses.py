"""
This script removes all innerclasses from the filtered.rsf files.
With this a comparison can be done on file-level which is used in arc clustering.
"""

SUFFIX = ".java"
seen = set()

with open("filtered.rsf", "r") as infile, open("filtered-without-innerclasses.rsf", "w") as outfile:
    for line in infile:
        parts = line.strip().split()
        if len(parts) != 3 or parts[0] != "depends":
            continue

        source, target = parts[1], parts[2]
        # Since files are needed but the rsf file lists per class, the syntax is mainclass$innerclass, so split and take first
        # Then remove package and only take the class/file name, and append file suffix
        source = source.split("$")[0].split(".")[-1] + SUFFIX
        target = target.split("$")[0].split(".")[-1] + SUFFIX

        # Self-referencing classes within a file should be ignored
        if source == target:
            continue

        entry = f'depends {source} {target}'
        if entry in seen:
            continue
        seen.add(entry)
        outfile.write(entry + '\n')
        
print("Done. Result can be found in filtered-without-innerclasses.rsf")