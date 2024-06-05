import os
import signal
from resizelib import resizeVTF

# Edit these variables
PATH_TO_DIR = r"garrysmod\addons\addon_name\materials"
CLAMP_SIZE = 512  # This can be set to a absurdly high number to only use DXT1 compression, or a lower number to clamp the resolution to that size.
# End of variables

old_size = 0
new_size = 0
replace_count = 0


def signal_handler(sig, frame):
    if os.path.exists("crashfile.txt"):
        os.remove("crashfile.txt")

    print("Cancelled by user.")
    exit()


signal.signal(signal.SIGINT, signal_handler)

if os.path.exists("crashfile.txt"):
    with open("crashfile.txt", "r") as f:
        print("Crash/exit detected! Last file processed:", f.read())
        print("Try importing and exporting the VTF with VTFEdit to fix it.")

    os.remove("crashfile.txt")

for path, subdirs, files in os.walk(PATH_TO_DIR):
    for name in files:
        if not name.endswith(".vtf"):
            continue

        with open("crashfile.txt", "w") as f:
            f.write(os.path.join(path, name))

        old_size_temp = os.path.getsize(os.path.join(path, name))
        converted = resizeVTF(os.path.join(path, name), CLAMP_SIZE)
        if converted:
            replace_count += 1
            new_size += os.path.getsize(os.path.join(path, name))
            old_size += old_size_temp
        else:
            new_size += old_size_temp
            old_size += old_size_temp

os.remove("crashfile.txt")
print("Replaced", replace_count, "files.")
if replace_count == 0:
    print("No files were replaced.")
else:
    print("Clamped to", CLAMP_SIZE, "resolution.")
    print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
    print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
