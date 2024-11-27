import questionary
import os

from utils.formatting import format_size
from unused_files.modelformats import unused_model_formats
from unused_files.content import unused_content
from material_compression.resize_and_compress import resize_and_compress
from material_compression.resize_png import clamp_pngs
from sound_compression.wav_to_mp3 import wav_to_mp3

FOLDER = ""

def main():
    global FOLDER

    if not FOLDER:
        FOLDER = questionary.text("Absolute path to folder:").ask()
    if not FOLDER:
        return

    action =  questionary.select( "What do you want to do?",
        choices=["Unused model formats", "Find unused content (WIP)", "Compress VTF files", "Use DXT for VTFs", "Clamp PNG files", ".wav to .mp3 (lowers filesize) (skips looped/cued files)","Exit"],
    ).ask()
    
    if not action:
        return
    
    if action == "Exit":
        return
    
    if not os.path.exists(FOLDER):
        print("Folder does not exist")
        main()
        return

    if action == "Unused model formats":
        remove = questionary.confirm("Do you want to remove the models?").ask()
        size, count = unused_model_formats(FOLDER, remove)

        formatted_size = format_size(size)
        if remove:
            print(f"Removed {count} unused model formats, saving {formatted_size}")
        else:
            print(f"Found {count} unused model formats, taking up {formatted_size}")
    
    if action == "Find unused content (WIP)":
        remove = questionary.confirm("Do you want to remove the found unused files? This isn't 100% and can remove used files!").ask()
        size, count = unused_content(FOLDER, remove)
        if remove:
            print(f"Removed {count} unused files, saving {format_size(size)}")
        else:
            print(f"Found {count} unused files, taking up {format_size(size)}")

    if action == "Compress VTF files":
        size = questionary.text("Clamp size:", validate=lambda text: True if text.isdigit() else "Please enter a valid number").ask()
        resize_and_compress(FOLDER, int(size))
    
    if action == "Use DXT for VTFs":
        resize_and_compress(FOLDER, 1000000)

    if action == "Clamp PNG files":
        size = questionary.text("Clamp size:", validate=lambda text: True if text.isdigit() else "Please enter a valid number").ask()
        clamp_pngs(FOLDER, int(size))

    if action == ".wav to .mp3 (lowers filesize) (skips looped/cued files)":
        wav_to_mp3(FOLDER)

    main()

if __name__ == "__main__":
    main()
