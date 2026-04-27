TARGET_PACKAGES = [
    "org.apache.lucene.codecs.simpletext",
    "org.apache.lucene.codecs.blockterms",
    "org.apache.lucene.codecs.bloom",
    "org.apache.lucene.codecs.memory",
    "org.apache.lucene.codecs.blocktreeords",
]

def is_relevant(package):
    return any(package.startswith(p) for p in TARGET_PACKAGES)

with open("output.rsf", "r") as infile, open("filtered.rsf", "w") as outfile:
    for line in infile:
        parts = line.strip().split()
        if len(parts) == 3 and parts[0] == "depends":
            source, target = parts[1], parts[2]
            if is_relevant(source) or is_relevant(target):
                outfile.write(line)

print("Done. Filtered dependencies written to filtered.rsf")