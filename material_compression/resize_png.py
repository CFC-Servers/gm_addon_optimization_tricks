# Lowers png resolution to under the specified size, useful for animated textures that were exported as pngs.

import os
from PIL import Image

def clamp_pngs(folder, max_size):
    total_size = 0
    total_resized = 0
    total_resized_files = 0
    total_files = 0

    for path, subdirs, files in os.walk(folder):
        for name in files:
            filepath = os.path.join(path, name)
            filetype = name.split(".")[-1]
            if filetype == "png":
                total_files += 1
                original_size = os.path.getsize(filepath)
                total_size += original_size
                image = Image.open(filepath)
                w, h = image.size
                if w > max_size or h > max_size:
                    maxd = max(w, h)
                    scale = max_size / maxd
                    neww = int(w * scale)
                    newh = int(h * scale)
                    image = image.resize((neww, newh))
                    image.save(filepath, quality=95)
                    total_resized += os.path.getsize(filepath)
                    total_resized_files += 1
                    print(f"Resized {filepath} from {w}x{h} to {neww}x{newh}")
                else:
                    total_resized += original_size

    total_saved_mb = round((total_size - total_resized) / 1000000, 2)
    print("="*60)
    print(f"Resized {total_resized_files} files, {total_saved_mb} mb saved")
    print("="*60)
