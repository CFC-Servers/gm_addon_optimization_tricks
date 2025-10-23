import os


def unused_model_formats(folder, remove=True):
    total_size = 0
    count = 0

    formats_to_remove = [
        ".dx80.vtx",
        ".xbox.vtx",
        ".sw.vtx",
        ".360.vtx"
    ]

    for root, _, files in os.walk(folder):
        for file in files:
            for fmt in formats_to_remove:
                if file.endswith(fmt):
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    if remove:
                        os.remove(file_path)
                        print("Removed", file_path)
                    else:
                        print("Found unused file:", file_path)
                    count += 1


    return total_size, count
