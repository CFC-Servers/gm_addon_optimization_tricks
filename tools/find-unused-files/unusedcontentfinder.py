import os
import humanize

# Config
DIR = r"C:\path\to\folder"

# Variables
lua_contents = ""

file_names = []
files_to_check = {}
pngs = []

# Loop through all files in the directory and subdirectories and store the contents of all lua files / files to scan
for root, dirs, files in os.walk(DIR):
    for file in files:
        _, ext = os.path.splitext(file)
        relative_path = os.path.relpath(root, DIR)

        if ext == ".lua":
            file_names.append(file)
            lua_contents += file + "\n"
            with open(os.path.join(root, file), "r") as f:
                lua_contents += f.read()

        if ext == ".wav" or ext == ".mp3" or ext == ".pcf" or ext == ".png" or ext == ".mndl":
            files_to_check[file] = os.path.join(root, file)

# Loop through all files in the directory and subdirectories and store the sizes of all unused files
combined_sizes = 0
for file, fullpath in files_to_check.items():
    filename = os.path.splitext(file)[0]
    if filename not in lua_contents:
        combined_sizes += os.path.getsize(fullpath)
        print("Found unused file: ", fullpath)
        # os.remove(fullpath) # Uncomment to remove files

print("Total size of unused files: ",  humanize.naturalsize(combined_sizes))
