import os
import humanize

# Config
DIR = r"garrysmod\addons\addon_name"

total_size = 0

formats_to_remove = [
    ".dx80.vtx",
    ".xbox.vtx",
    ".sw.vtx",
]

# Loop through all files in the directory and subdirectories and store the contents of all lua files / files to scan
for root, dirs, files in os.walk(DIR):
    for file in files:
        _, ext = os.path.splitext(file)
        relative_path = os.path.relpath(root, DIR)

        # check if file ends with .lua
        for format in formats_to_remove:
            if file.endswith(format):
                total_size += os.path.getsize(os.path.join(root, file))
                os.remove(os.path.join(root, file))
                print("Removed", os.path.join(root, file))


print("Total size of unused files: ",  humanize.naturalsize(total_size))
