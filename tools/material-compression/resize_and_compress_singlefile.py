import os
from resizelib import resizeVTF

# Edit these variables
PATH_TO_FILE = r"garrysmod\addons\addon_name\materials\material_name.vtf"
CLAMP_SIZE = 512
# End of variables

old_size = 0
new_size = 0
replace_count = 0

if not os.path.exists(PATH_TO_FILE):
    print("File does not exist:", PATH_TO_FILE)
    exit()

name = os.path.basename(PATH_TO_FILE)

filetype = name.split(".")[-1]
if filetype == "vtf":
    old_size = os.path.getsize(PATH_TO_FILE)
    resizeVTF(PATH_TO_FILE, CLAMP_SIZE)
    new_size = os.path.getsize(PATH_TO_FILE)

print("Clamped to", CLAMP_SIZE, "pixels.")
if replace_count == 0:
    print("No files were replaced.")
else:
    print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
    print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
