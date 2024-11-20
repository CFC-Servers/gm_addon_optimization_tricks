import pydub
import os
from wavinfo import WavInfoReader

# Requires ffmpeg to be installed and added to PATH
# https://github.com/jiaaro/pydub?tab=readme-ov-file#getting-ffmpeg-set-up

def has_loop(file_path):
    """Checks if a WAV file contains loop metadata in the smpl chunk."""
    try:
        with open(file_path, "rb") as f:
            # Verify RIFF/WAVE file
            riff_header = f.read(12)
            if riff_header[:4] != b'RIFF' or riff_header[8:12] != b'WAVE':
                return False
            
            # Parse chunks
            while True:
                chunk_header = f.read(8)
                if len(chunk_header) < 8:
                    break  # End of file
                
                chunk_id = chunk_header[:4].decode('ascii')
                chunk_size = int.from_bytes(chunk_header[4:], byteorder='little')
                
                if chunk_id == "smpl":
                    # Check for loop data in the smpl chunk
                    smpl_data = f.read(chunk_size)
                    num_loops = int.from_bytes(smpl_data[28:32], byteorder='little')
                    if num_loops > 0:
                        return True
                else:
                    f.seek(chunk_size, 1)  # Skip to the next chunk
            
            return False
    except Exception as e:
        return False

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
                wav_info = WavInfoReader(filepath)
                if len(wav_info.cues.cues) > 0:
                    print("File", filepath, "contains cues skipping.")
                    continue

                if has_loop(filepath):
                    print("File", filepath, "contains loops skipping.")
                    continue

                old_size += os.path.getsize(filepath)
                sound = pydub.AudioSegment.from_wav(filepath)

                new_filepath = filepath.replace(".wav", ".mp3")
                sound.export(new_filepath, format="mp3")
                new_size += os.path.getsize(new_filepath)

                file_name = os.path.basename(filepath)
                replace_count += 1
                replaced_files[file_name] = file_name.replace(".wav", ".mp3")
                os.remove(filepath)

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
