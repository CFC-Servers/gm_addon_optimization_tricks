import os
from resizelib import resizeVTF

# Edit these variables
PATH_TO_DIR = r"garrysmod\addons\addon_name\materials"
CLAMP_SIZE = 1024
# End of variables

old_size = 0
new_size = 0
replace_count = 0

for path, subdirs, files in os.walk(PATH_TO_DIR):
    for name in files:
        if not name.endswith(".vtf"):
            continue

        old_size_temp = os.path.getsize(path)
        converted = resizeVTF(os.path.join(path, name), CLAMP_SIZE)
        if converted:
            replace_count += 1
            new_size += os.path.getsize(path)
            old_size += old_size_temp

print("Replaced", replace_count, "files.")
if replace_count == 0:
    print("No files were replaced.")
else:
    print("Clamped to", CLAMP_SIZE, "resolution.")
    print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
    print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
