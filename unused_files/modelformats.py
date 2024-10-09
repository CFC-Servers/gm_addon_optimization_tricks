import os

# Removes unused model formats from a directory, such as .dx80.vtx, .xbox.vtx, .sw.vtx
# These are effectively not used in gmod and can take up a lot of space

def unused_model_formats(folder, remove=True):
    total_size = 0
    count = 0

    formats_to_remove = [
        ".dx80.vtx",
        ".xbox.vtx",
        ".sw.vtx",
        ".360.vtx"
    ]

    for root, dirs, files in os.walk(folder):
        for file in files:
            _, ext = os.path.splitext(file)
            relative_path = os.path.relpath(root, folder)

            for format in formats_to_remove:
                if file.endswith(format):
                    total_size += os.path.getsize(os.path.join(root, file))
                    if remove:
                        os.remove(os.path.join(root, file))
                        print("Removed", os.path.join(root, file))
                    else:
                        print("Found unused file:", os.path.join(root, file))
                    
                    count += 1


    return total_size, count
