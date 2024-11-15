import os
from srctools.mdl import Model
from srctools.vmt import Material
from srctools.filesys import RawFileSystem

model_formats = [
    ".mdl",
    ".vvd",
    ".phy",
    ".vtx",
    ".ani",
    ".sw.vtx",
    ".dx80.vtx",
    ".dx90.vtx",
    ".xbox.vtx",
]

def unused_content(path, remove=False):
    unused_sizes = 0
    unused_count = 0
    fs = RawFileSystem(path)

    # Find all the models in the filesystem
    all_models = []
    all_model_vmts = {}
    vmt_used_count = {}
    vmf_used_count = {}
    for file in fs.walk_folder(''):
        if file.path.endswith('.mdl'):
            all_models.append(file.path)

            all_model_vmts[file.path] = all_model_vmts.get(file.path, [])
            model = Model(fs, fs[file.path])
            for tex in model.iter_textures():
                # append path relative to the input path
                all_model_vmts[file.path].append(tex)
                vmt_used_count[tex] = vmt_used_count.get(tex, 0) + 1

    # Find all the vtfs of the all_model_vmts vmts
    all_model_vtfs = {}
    all_vtfs = []
    for model, vmts in all_model_vmts.items():
        for vmt_path in vmts:
            with open( os.path.join(path, vmt_path), "r", encoding="utf-8") as f:
                vmt = Material.parse(f, filename=vmt_path)
            for vmtfield in vmt.items():
                if vmtfield[0].startswith("$basetexture"):
                    vtf = os.path.normpath(vmtfield[1])
                    all_model_vtfs[model] = all_model_vtfs.get(model, [])
                    all_model_vtfs[model].append(vtf)
                    all_vtfs.append(vtf)
                    vmf_used_count[vtf] = vmf_used_count.get(vtf, 0) + 1

    # Find all the models used in lua files
    all_lua_used_models = []
    for file in fs.walk_folder('lua'):
        if file.path.endswith('.lua'):
            with open( os.path.join(path, file.path), "r", encoding="utf-8") as f:
                lua_contents = f.read()
                lua_contents = lua_contents.lower()
                for model in all_models:
                    if model in lua_contents:
                        all_lua_used_models.append(model)

    # print not used models
    print("Unused models:")
    unused_models = []
    for model in all_models:
        if model not in all_lua_used_models:
            no_ext_model = os.path.splitext(model)[0]
            for ext in model_formats:
                format_path = os.path.join(path, no_ext_model + ext)
                if os.path.exists(format_path):
                    if ext == ".mdl":
                        unused_models.append(model)

                        for vmt in all_model_vmts[model]:
                            vmt_used_count[vmt] -= 1

                        for vtf in all_model_vtfs.get(model, []):
                            vmf_used_count[vtf] -= 1

                    print("Found unused file:", format_path)
                    unused_sizes += os.path.getsize(format_path)
                    unused_count += 1
                    if remove:
                        os.remove(format_path)
                        print("Removed", format_path)

    # Find all the vmts that no longer get used
    unused_vmts = []
    for vmt_used in vmt_used_count:
        if vmt_used_count[vmt_used] == 0:
            unused_vmts.append(vmt_used)
            unused_sizes += os.path.getsize(os.path.join(path, vmt_used))
            unused_count += 1
            print("Found unused file:", os.path.join(path, vmt_used))
            if remove:
                os.remove(os.path.join(path, vmt_used))
                print("Removed", vmt_used)
    
    unused_vtfs = []
    for vtf_used in vmf_used_count:
        if vmf_used_count[vtf_used] == 0:
            vtf_used = "materials/" + vtf_used + ".vtf"
            if os.path.exists(os.path.join(path, vtf_used)):
                unused_vtfs.append(vtf_used)
                unused_sizes += os.path.getsize(os.path.join(path, vtf_used))
                unused_count += 1
                print("Found unused file:", os.path.join(path, vtf_used))
                if remove:
                    os.remove(os.path.join(path, vtf_used))
                    print("Removed", vtf_used)
            
    return unused_sizes, unused_count
