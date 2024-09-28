# Lowers png resolution to under the specified size, useful for animated textures that were exported as pngs.

import os
from PIL import Image

def clamp_pngs(folder, max_size):
    new_file_path = folder + "/resized"
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)

    total_size = 0
    total_resized = 0
    total_files = 0

    for path, subdirs, files in os.walk(folder):
        for name in files:
            filepath = os.path.join(path, name)
            filetype = name.split(".")[-1]
            if filetype == "png":
                total_files += 1
                total_size += os.path.getsize(filepath)
                image = Image.open(filepath)
                w, h = image.size
                if w > max_size or h > max_size:
                    maxd = max(w, h)
                    scale = max_size / maxd
                    neww = int(w * scale)
                    newh = int(h * scale)
                    image = image.resize((neww, newh))
                    image.save(new_file_path + "/" + name)
                    total_resized += os.path.getsize(filepath)
                    print(f"Resized {filepath} from {w}x{h} to {neww}x{newh}")

    total_resized_mb = round(total_resized / 1000000, 2)
    total_saved_mb = round((total_size - total_resized) / 1000000, 2)
    print(f"Resized {total_files} files, saved {total_resized_mb} mb, {total_saved_mb} mb saved")
