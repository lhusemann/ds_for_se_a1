# Initial file created by Alexander Makejkin, code to be used inside the google colab for Week 3
# Task:
# scan the filtered .rsf dependency file from week 1 to construct a matrix
# where each entry is the number of packages each pair of files depend on.
# executing this cell produces 'struct_matrix_raw'

# ---------------- CODE BELOW ALREADY EXISTS IN PREVIOUS NOTEBOOK CELLS ---------------
# ---------------- AND USED ONLY TO DEBUG LOCALLY -------------------------------------

from pathlib import Path
import numpy as np

SOURCE_CODE_DIR = Path("content/lucene-9.0.0/lucene/codecs/src/java/org/apache/lucene/codecs")

files_names = [] # File names are unique
# .rglob() searches the root folder and all sub-folders automatically
for file_path in SOURCE_CODE_DIR.rglob('*.java'):
    if file_path.is_file() and "package-info.java" not in file_path.name:
        files_names.append(file_path.name)

# ---------------- CODE BELOW CAN BE USED INSIDE THE NOTEBOOK CELL --------------------

SUFFIX = ".java"
file_to_files = {} # Dict of Set

# Parse rsf file
with open("content/filtered.rsf", "r") as file:
    for line in file:
        parts = line.strip().split()
        if len(parts) != 3 or parts[0] != "depends":
            continue
        
        source, target = parts[1], parts[2]
        # Since files are needed but the rsf file lists per class, the syntax is mainclass$otherclass, so split and take first
        # Then remove package and only take the class/file name, and append file suffix
        source = source.split("$")[0].split(".")[-1] + SUFFIX
        target = target.split("$")[0].split(".")[-1] + SUFFIX

        # Self-referencing classes within a file should be ignored
        if source == target:
            continue

        if source not in file_to_files:
            file_to_files[source] = set()

        file_to_files[source].add(target)

file_to_depscount = {} # Dict of list of tuple(string <the other element>, int <count>)

for file, files in file_to_files.items():
    file_to_depscount[file] = []
    for file_2, files_2 in file_to_files.items():
        # Don't count self<->self since they are not necessarily equal across all files.
        # The next cell normalizes and THEN sets diagonal to 1, which would lead to incorrect numbers overall
        if file == file_2:
            continue

        count = len(files.intersection(files_2))

        # detect bidirectional dependencies
        if file_2 in files and file in files_2:
            count += 1

        if count == 0:
            continue

        file_to_depscount[file].append((file_2, count))

# There will be some files like org.apache.lucene.codecs.simpletext.SimpleTextUtil missing as they do not appear on the left side of the rsf
# As it has no references to other files within codecs (which is the package of interest)
# So the entries will be 0

# Use files_names to index the matrix, using data from file_to_files
size = len(files_names)
struct_matrix_raw = np.zeros((size, size))

for file, depscount in file_to_depscount.items():
    if file not in files_names:
        continue

    file_index = files_names.index(file)

    for (other, count) in depscount:
        if other not in files_names:
            continue
        
        other_index = files_names.index(other)
        # Matrix is symmetric by definition of the task
        struct_matrix_raw[file_index, other_index] = count
        struct_matrix_raw[other_index, file_index] = count

print(f"struct_matrix_raw Done ({size}x{size})")
