import os
import signal
import time
from material_compression.resizelib import resizeVTF

def resize_and_compress(folder, size):
    old_size = 0
    new_size = 0
    replace_count = 0
    startime = time.time()


    def signal_handler(sig, frame):
        if os.path.exists("crashfile.txt"):
            os.remove("crashfile.txt")

        print("Time taken:", round(time.time() - startime, 2), "seconds")
        print("Cancelled by user.")
        exit()


    signal.signal(signal.SIGINT, signal_handler)

    if os.path.exists("crashfile.txt"):
        with open("crashfile.txt", "r") as f:
            print("Crash/exit detected! Last file processed:", f.read())
            print("Try importing and exporting the VTF with VTFEdit to fix it.")

        os.remove("crashfile.txt")

    for path, subdirs, files in os.walk(folder):
        for name in files:
            if not name.endswith(".vtf"):
                continue

            with open("crashfile.txt", "w") as f:
                f.write(os.path.join(path, name))

            old_size_temp = os.path.getsize(os.path.join(path, name))
            converted = resizeVTF(os.path.join(path, name), size)
            if converted:
                replace_count += 1
                new_size += os.path.getsize(os.path.join(path, name))
                old_size += old_size_temp
            else:
                new_size += old_size_temp
                old_size += old_size_temp

    print("Replaced", replace_count, "files.")
    if replace_count == 0:
        print("No files were replaced.")
    else:
        print("Clamped to", size, "resolution.")
        print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
        print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
    print("Time taken:", round(time.time() - startime, 2), "seconds")
