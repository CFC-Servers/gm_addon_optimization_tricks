# Lowers png resolution to under the specified size, useful for animated textures that were exported as pngs.

import os
from PIL import Image

MAX_SIZE = 128
PATH_TO_DIR = r"C:\foldername"

new_file_path = PATH_TO_DIR + "/resized"
if not os.path.exists(new_file_path):
    os.makedirs(new_file_path)

total_size = 0
total_resized = 0
total_files = 0

for path, subdirs, files in os.walk(PATH_TO_DIR):
    for name in files:
        filepath = os.path.join(path, name)
        filetype = name.split(".")[-1]
        if filetype == "png":
            total_files += 1
            total_size += os.path.getsize(filepath)
            image = Image.open(filepath)
            w, h = image.size
            if w > MAX_SIZE or h > MAX_SIZE:
                maxd = max(w, h)
                scale = MAX_SIZE / maxd
                neww = int(w * scale)
                newh = int(h * scale)
                image = image.resize((neww, newh))
                image.save(new_file_path + "/" + name)
                total_resized += os.path.getsize(filepath)
                print(f"Resized {filepath} from {w}x{h} to {neww}x{newh}")

print(f"Resized {total_files} files, saved {total_resized} bytes, {total_size - total_resized} bytes saved")
