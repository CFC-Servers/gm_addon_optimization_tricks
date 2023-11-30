from PIL import Image
import os
import VTFLibWrapper.VTFLib as VTFLib
import numpy as np
from ctypes import create_string_buffer

from VTFLibWrapper.VTFLibEnums import ImageFormat

# Source for the original: https://github.com/HaodongMo/ARC-9-Standard-Weapons/tree/main/tools
# Edit these variables
PATH_TO_DIR = r"garrysmod\addons\addon_name"

vtf_lib = VTFLib.VTFLib()
old_size = 0
new_size = 0
replace_count = 0


def has_transparency(img):
    if image.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


for path, subdirs, files in os.walk(PATH_TO_DIR):
    for name in files:
        filepath = os.path.join(path, name)
        filetype = name.split(".")[-1]
        if filetype == "vtf":
            image_header = vtf_lib.image_load(filepath, True)

            w = vtf_lib.width()
            h = vtf_lib.height()
            format = vtf_lib.image_format()

            if format != ImageFormat.ImageFormatDXT1:
                image_full = vtf_lib.image_load(filepath, False)
                def_options = vtf_lib.create_default_params_structure()
                image_data = vtf_lib.get_rgba8888()
                image_data = bytes(image_data.contents)
                image = Image.frombytes("RGBA", (w, h), image_data)

                should_dxt1 = not has_transparency(image)

                if should_dxt1:
                    def_options.ImageFormat = ImageFormat.ImageFormatDXT1
                    def_options.Resize = 1

                    image_data = (np.asarray(image)*-1) * 255
                    image_data = image_data.astype(np.uint8, copy=False)
                    image_data = create_string_buffer(image_data.tobytes())

                    vtf_lib.image_create_single(w, h, image_data, def_options)

                    old_size += os.path.getsize(filepath)
                    vtf_lib.image_save(filepath)
                    new_size += os.path.getsize(filepath)
                    replace_count += 1
                    print("DXT1-ified", filepath, "successfully.")

print("Done.")
print("Replaced", replace_count, "files.")
if replace_count == 0:
    print("No files were replaced.")
else:
    print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
    print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
