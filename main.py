import questionary
import os

from utils.formatting import format_size
from unused_files.modelformats import unused_model_formats
from unused_files.content import unused_content
from unused_files.remove_game_files import remove_game_files
from material_compression.resize_and_compress import resize_and_compress
from material_compression.resize_png import clamp_pngs
from material_compression.remove_mipmaps import remove_mipmaps
from sound_compression.wav_to_mp3 import wav_to_mp3
from sound_compression.wav_to_ogg import wav_to_ogg
from sound_compression.mp3_to_ogg import mp3_to_ogg
from sound_compression.trim_empty import trim_empty_audio
from mapping.find_map_content import find_map_content

FOLDER = ""

def handle_unused_model_formats():
    remove = questionary.confirm("Do you want to remove the models?").ask()
    size, count = unused_model_formats(FOLDER, remove)
    formatted_size = format_size(size)
    if remove:
        print(f"Removed {count} unused model formats, saving {formatted_size}")
    else:
        print(f"Found {count} unused model formats, taking up {formatted_size}")


def handle_unused_content():
    remove = questionary.confirm("Do you want to remove the found unused files? This isn't 100% and can remove used files!").ask()
    size, count = unused_content(FOLDER, remove)
    if remove:
        print(f"Removed {count} unused files, saving {format_size(size)}")
    else:
        print(f"Found {count} unused files, taking up {format_size(size)}")

def handle_remove_game_files():
    remove = questionary.confirm("Do you want to remove the found files?").ask()
    gamefolder = questionary.text("Absolute path to game folder (eg C:/Program Files(x86)/Steam/steamapps/common/GarrysMod)").ask()
    # check if gmod.exe exists in the folder
    if not gamefolder or not os.path.exists(os.path.join(gamefolder, "gmod.exe")):
        print("Invalid game folder")
        return

    remove_game_files(FOLDER, gamefolder, remove)


def handle_compress_vtf():
    size = questionary.text("Clamp size:", validate=lambda text: True if text.isdigit() else "Please enter a valid number").ask()
    if size:
        resize_and_compress(FOLDER, int(size))


def handle_use_dxt():
    resize_and_compress(FOLDER, 1000000)


def handle_remove_mipmaps():
    remove_mipmaps(FOLDER)


def handle_clamp_png():
    size = questionary.text("Clamp size:", validate=lambda text: True if text.isdigit() else "Please enter a valid number").ask()
    if size:
        clamp_pngs(FOLDER, int(size))

def handle_wav_to_mp3():
    wav_to_mp3(FOLDER)


def handle_wav_to_ogg():
    wav_to_ogg(FOLDER)


def handle_mp3_to_ogg():
    mp3_to_ogg(FOLDER)


def handle_trim_empty_audio():
    trim_empty_audio(FOLDER)

def handle_find_map_content():
    map_file = questionary.text("Absolute path to map file (.vmf):").ask()
    if not map_file or not os.path.exists(map_file) or not map_file.endswith(".vmf"):
        print("Invalid map file")
        return
    map_file = map_file.strip('"')

    new_content_folder = questionary.text("Folder to copy found content to (will be created if it doesn't exist):").ask()
    if not new_content_folder:
        print("Invalid destination folder")
        return
    os.makedirs(new_content_folder, exist_ok=True)

    find_map_content(FOLDER, new_content_folder, map_file)

def handle_resave_vtf():
    for root, dirs, files in os.walk(FOLDER):
        for filename in files:
            if filename.endswith(".vtf"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r+b") as f:
                    data = f.read()
                    f.seek(0)
                    f.write(data)
                    f.truncate()

def handle_select_folder():
    global FOLDER
    new_folder = questionary.text("Absolute path to folder:").ask()
    if new_folder:
        FOLDER = new_folder.strip('"')

def main():
    global FOLDER

    if not FOLDER:
        FOLDER = questionary.text("Absolute path to folder:").ask()
    if not FOLDER:
        return
    
    FOLDER = FOLDER.strip('"')

    actions = {
        "Unused model formats": handle_unused_model_formats,
        "Find unused content (WIP)": handle_unused_content,
        "Clamp VTF file sizes": handle_compress_vtf,
        "Use DXT for VTFs": handle_use_dxt,
        "Remove mipmaps (Useful for close-up textures, eg viewmodels)": handle_remove_mipmaps,
        "Clamp PNG file sizes": handle_clamp_png,
        ".wav to .ogg (lowers filesize) (skips looped/cued files) (better than mp3)": handle_wav_to_ogg,
        ".wav to .mp3 (lowers filesize) (skips looped/cued files)": handle_wav_to_mp3,
        ".mp3 to .ogg": handle_mp3_to_ogg,
        "Trim empty audio from end of sound files, not great. convert to ogg first as trimming might not do anything": handle_trim_empty_audio,
        "Resave VTF files to trigger autorefresh": handle_resave_vtf,
        "Remove files that are already in the game (eg HL2, CSS) good for map files": handle_remove_game_files,
        "Find and copy all content used by a map file (.vmf)": handle_find_map_content,
        "Select another folder": handle_select_folder,
    }

    action = questionary.select(
        "What do you want to do?",
        choices=list(actions.keys()) + ["Exit"]
    ).ask()
    
    if not action or action == "Exit":
        return
    
    if not os.path.exists(FOLDER):
        print("Folder does not exist")
        main()
        return

    # Execute the selected action
    if action in actions:
        actions[action]()

    main()

if __name__ == "__main__":
    main()
