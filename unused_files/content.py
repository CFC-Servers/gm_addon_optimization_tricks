import os
from utils.formatting import format_size

def unused_content(path, remove):
    lua_contents = ""

    file_names = []
    files_to_check = {}

    # Loop through all files in the directory and subdirectories and store the contents of all lua files / files to scan
    for root, dirs, files in os.walk(path):
        for file in files:
            _, ext = os.path.splitext(file)
            relative_path = os.path.relpath(root, path)

            if ext == ".lua":
                file_names.append(file)
                lua_contents += file + "\n"
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    lua_contents += f.read()

            if ext == ".wav" or ext == ".mp3" or ext == ".pcf" or ext == ".png" or ext == ".mdl":
                files_to_check[file] = os.path.join(root, file)

    # Loop through all files in the directory and subdirectories and store the sizes of all unused files
    combined_sizes = 0
    found_files = 0
    for file, fullpath in files_to_check.items():
        filename = os.path.splitext(file)[0]
        lua_contents = lua_contents.lower()
        if filename not in lua_contents:
            filesize = os.path.getsize(fullpath)
            combined_sizes += filesize
            found_files += 1

            if remove:
                os.remove(fullpath)
                print("Removed", fullpath + ":", format_size(filesize))
            else:
                print("Found unused file:", fullpath + ":", format_size(filesize))


    return combined_sizes, found_files
