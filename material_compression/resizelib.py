from PIL import Image
import material_compression.VTFLibWrapper.VTFLib as VTFLib
import material_compression.VTFLibWrapper.VTFLibEnums as VTFLibEnums
from ctypes import create_string_buffer

from material_compression.VTFLibWrapper.VTFLibEnums import ImageFormat

def resizeVTFImage(vtf_lib, path, max_size):
    w = vtf_lib.width()
    h = vtf_lib.height()
    neww = w
    newh = h
    format = vtf_lib.image_format()

    scale = 1
    if w > max_size or h > max_size:
        maxd = max(w, h)
        scale = max_size / maxd
        neww *= scale
        newh *= scale

    if scale != 1 or format != ImageFormat.ImageFormatDXT1:
        vtf_lib.image_load(path, False)
        def_options = vtf_lib.create_default_params_structure()
        image_data = vtf_lib.get_rgba8888()
        image_data = bytes(image_data.contents) # Why would you crash here with no exception. I am sad >:(

        image = Image.frombytes("RGBA", (w, h), image_data)
        r, g, b, a = image.split()

        method = ImageFormat.ImageFormatDXT5
        if a.getextrema()[1] == 255 and a.getextrema()[0] == 255:
            method = ImageFormat.ImageFormatDXT1

        if scale == 1 and format == method:
            return False

        if scale != 1:
            image = image.convert("RGB")
            image_scaled = image.resize((int(neww), int(newh)))
            image_a_scaled = a.resize((int(neww), int(newh)))
            r, g, b = image_scaled.split()
            colorImage = (r, g, b, image_a_scaled)
            image = Image.merge('RGBA', colorImage)

        new_image_data = image.tobytes()

        def_options.ImageFormat = method
        def_options.Flags |= VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha
        def_options.Resize = 1

        vtf_lib.image_create_single(int(neww), int(newh), new_image_data, def_options)

        vtf_lib.image_save(path)

        print(scale != 1 and "Resized" or "Converted", path, "successfully:", w, "x", h, "->", int(neww), "x", int(newh))
        return True
    return False


def resizeVTF(path, max_size) -> bool:
    if not path.endswith(".vtf"):
        return False
    
    vtf_lib = VTFLib.VTFLib() # Give each run it's own vtflib instance so we can possibly run them in parallel later on.
    vtf_lib.image_load(path, True)

    if vtf_lib.frame_count() == 1:
        return resizeVTFImage(vtf_lib, path, max_size)
    else:
        print("Skipping", path, "because it has multiple frames.")
        return False