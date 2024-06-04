from PIL import Image
import os
import VTFLibWrapper.VTFLib as VTFLib
import VTFLibWrapper.VTFLibEnums as VTFLibEnums
import numpy as np
from ctypes import create_string_buffer

from VTFLibWrapper.VTFLibEnums import ImageFormat

# Source for the original: https://github.com/HaodongMo/ARC-9-Standard-Weapons/tree/main/tools
# Edit these variables
PATH_TO_FILE = r"garrysmod\addons\addon_name\materials\material_name.vtf"
CLAMP_SIZE = 4

vtf_lib = VTFLib.VTFLib()
old_size = 0
new_size = 0
replace_count = 0

if not os.path.exists(PATH_TO_FILE):
    print("File does not exist:", PATH_TO_FILE)
    exit()

name = os.path.basename(PATH_TO_FILE)

filetype = name.split(".")[-1]
if filetype == "vtf":
    image_header = vtf_lib.image_load(PATH_TO_FILE, True)

    w = vtf_lib.width()
    h = vtf_lib.height()
    neww = w
    newh = h
    format = vtf_lib.image_format()

    scale = 1
    if w > CLAMP_SIZE or h > CLAMP_SIZE:
        maxd = max(w, h)
        scale = CLAMP_SIZE / maxd
        neww *= scale
        newh *= scale

    # print(format.name)

    if scale != 1 or format != ImageFormat.ImageFormatDXT1:
        image_full = vtf_lib.image_load(PATH_TO_FILE, False)
        def_options = vtf_lib.create_default_params_structure()
        image_data = vtf_lib.get_rgba8888()
        image_data = bytes(image_data.contents)

        image = Image.frombytes("RGBA", (w, h), image_data)
        r, g, b, a = image.split()

        method = ImageFormat.ImageFormatDXT5
        if a.getextrema()[1] == 255 and a.getextrema()[0] == 255:
            method = ImageFormat.ImageFormatDXT1

        if scale != 1:
            image = image.convert("RGB")
            image_scaled = image.resize((int(neww), int(newh)))
            image_a_scaled = a.resize((int(neww), int(newh)))
            r, g, b = image_scaled.split()
            colorImage = (r, g, b, image_a_scaled)
            image = Image.merge('RGBA', colorImage)

        image_data = (np.asarray(image)*-1) * 255
        image_data = image_data.astype(np.uint8, copy=False)
        image_data = create_string_buffer(image_data.tobytes())

        def_options.ImageFormat = method
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        def_options.Resize = 1

        vtf_lib.image_create_single(int(neww), int(newh), image_data, def_options)

        old_size += os.path.getsize(PATH_TO_FILE)
        vtf_lib.image_save(PATH_TO_FILE)
        new_size += os.path.getsize(PATH_TO_FILE)
        replace_count += 1
        print("Converted", PATH_TO_FILE, "successfully:", w, "x", h, "->", int(neww), "x", int(newh))

print("Done.")
print("Clamped to", CLAMP_SIZE, "pixels.")
if replace_count == 0:
    print("No files were replaced.")
else:
    print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
    print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
