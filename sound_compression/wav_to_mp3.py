import pydub
import os

# Requires ffmpeg to be installed and added to PATH
# https://github.com/jiaaro/pydub?tab=readme-ov-file#getting-ffmpeg-set-up

def wav_to_mp3(folder):
    replaced_files = {}
    old_size = 0
    new_size = 0
    replace_count = 0

    for path, subdirs, files in os.walk(folder):
        for name in files:
            filepath = os.path.join(path, name)
            filetype = name.split(".")[-1]
            if filetype == "wav":
                old_size += os.path.getsize(filepath)
                sound = pydub.AudioSegment.from_wav(filepath)
                sound.export(filepath, format="mp3")
                new_size += os.path.getsize(filepath)

                file_name = os.path.basename(filepath)
                replace_count += 1
                replaced_files[file_name] = file_name.replace(".wav", ".mp3")

                print("Converted", filepath, "to mp3 successfully.")

    for path, subdirs, files in os.walk(folder):
        for name in files:
            filepath = os.path.join(path, name)
            filetype = name.split(".")[-1]
            if filetype == "lua":
                with open(filepath, "r", encoding="utf-8") as f:
                    contents = f.read()
                for old, new in replaced_files.items():
                    contents = contents.replace(old, new)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(contents)
                print("Replaced", filepath, "successfully.")

    print("Done.")
    print("Replaced", replace_count, "files.")
    if replace_count == 0:
        print("No files were replaced.")
    else:
        print("Reduced size by ", round((1 - new_size / old_size) * 100, 2), "%")
        print("Reduced size by ", round((old_size - new_size) / 1000000, 2), "mbs")
