import os

# Removes unused model formats from a directory, such as .dx80.vtx, .xbox.vtx, .sw.vtx
# These are effectively not used in gmod and can take up a lot of space

# Config
DIR = r"garrysmod\addons\addon_name"

total_size = 0

formats_to_remove = [
    ".dx80.vtx",
    ".xbox.vtx",
    ".sw.vtx",
]

for root, dirs, files in os.walk(DIR):
    for file in files:
        _, ext = os.path.splitext(file)
        relative_path = os.path.relpath(root, DIR)

        for format in formats_to_remove:
            if file.endswith(format):
                total_size += os.path.getsize(os.path.join(root, file))
                os.remove(os.path.join(root, file))
                print("Removed", os.path.join(root, file))


print("Total size of unused files: ",  round(total_size / 1000000, 2), "mb")
