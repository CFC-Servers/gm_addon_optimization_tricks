import os
import time
from PIL import Image
import material_compression.VTFLibWrapper.VTFLib as VTFLib
import material_compression.VTFLibWrapper.VTFLibEnums as VTFLibEnums
from material_compression.VTFLibWrapper.VTFLibEnums import ImageFormat

def strip_mipmaps_from_vtf(vtf_lib, path):
    """Strip mipmaps from a single VTF file while preserving all other properties"""
    try:
        # Load the VTF file
        vtf_lib.image_load(path, False)
        
        # Get current properties
        w = vtf_lib.width()
        h = vtf_lib.height()
        current_format = vtf_lib.image_format()
        current_flags = vtf_lib.get_image_flags()
        mipmap_count = vtf_lib.mipmap_count()
        
        # Skip if already has no mipmaps
        if mipmap_count <= 1:
            return False, f"Already has no mipmaps ({mipmap_count})"
        
        # Get the main image data (mipmap level 0)
        image_data = vtf_lib.get_rgba8888()
        image_data = bytes(image_data.contents)
        
        # Create new VTF with same properties but no mipmaps
        def_options = vtf_lib.create_default_params_structure()
        def_options.ImageFormat = current_format
        def_options.Flags = current_flags.value if hasattr(current_flags, 'value') else current_flags
        def_options.Mipmaps = 0  # Remove mipmaps
        def_options.Resize = 0
        
        # Create the new VTF
        if vtf_lib.image_create_single(w, h, image_data, def_options):
            vtf_lib.image_save(path)
            return True, f"Stripped {mipmap_count} mipmaps"
        else:
            return False, f"Failed to create new VTF: {vtf_lib.get_last_error()}"
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def remove_mipmaps(folder):
    """Remove mipmaps from all VTF files in the specified folder"""
    old_size = 0
    new_size = 0
    processed_count = 0
    success_count = 0
    start_time = time.time()
    
    # Handle crash recovery
    invalid_files = set()
    if os.path.exists("mipmap_crashfile.txt"):
        with open("mipmap_crashfile.txt", "r") as f:
            crash_file = f.read().strip()
            with open("mipmap_blacklist.txt", "a") as file:
                file.write(crash_file + "\n")
            print(f"Crash detected! Last file processed: {crash_file}")
            print("File has been blacklisted. Try manually fixing it with VTFEdit.")
        os.remove("mipmap_crashfile.txt")
    
    # Load blacklist
    if os.path.exists("mipmap_blacklist.txt"):
        with open("mipmap_blacklist.txt", "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    invalid_files.add(line)
                    print(f"Blacklisted file: {line}")
    
    print(f"Scanning for VTF files in: {folder}")
    print("Removing mipmaps from VTF files...")
    
    # Process all VTF files
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if not filename.endswith(".vtf"):
                continue
                
            file_path = os.path.join(root, filename)
            
            # Skip blacklisted files
            if file_path in invalid_files:
                print(f"Skipping blacklisted file: {file_path}")
                continue
            
            # Create crash file for recovery
            with open("mipmap_crashfile.txt", "w") as f:
                f.write(file_path)
            
            try:
                # Get original file size
                old_file_size = os.path.getsize(file_path)
                old_size += old_file_size
                
                # Create VTFLib instance for this file
                vtf_lib = VTFLib.VTFLib()
                
                # Process the file
                success, message = strip_mipmaps_from_vtf(vtf_lib, file_path)
                processed_count += 1
                
                if success:
                    success_count += 1
                    new_file_size = os.path.getsize(file_path)
                    new_size += new_file_size
                    saved_bytes = old_file_size - new_file_size
                    saved_mb = saved_bytes / (1024 * 1024)
                    print(f"✓ {file_path} - {message} (saved {saved_mb:.2f} MB)")
                else:
                    new_size += old_file_size  # No change in size
                    print(f"⚠ {file_path} - {message}")
                
                # Clean up VTFLib instance
                vtf_lib.shutdown()
                
            except Exception as e:
                print(f"✗ {file_path} - Error: {str(e)}")
                new_size += old_file_size  # No change in size
    
    # Clean up crash file
    if os.path.exists("mipmap_crashfile.txt"):
        os.remove("mipmap_crashfile.txt")
    
    # Print summary
    print("="*60)
    print(f"Files processed: {processed_count}")
    print(f"Files modified: {success_count}")
    print(f"Files skipped: {processed_count - success_count}")
    
    if success_count > 0:
        total_saved = old_size - new_size
        percent_saved = (total_saved / old_size) * 100 if old_size > 0 else 0
        mb_saved = total_saved / (1024 * 1024)
        
        print(f"Total size reduction: {mb_saved:.2f} MB ({percent_saved:.1f}%)")
        print(f"Average reduction per file: {mb_saved/success_count:.2f} MB")
    else:
        print("No files were modified.")
    
    print(f"Time taken: {round(time.time() - start_time, 2)} seconds")
    print("="*60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        remove_mipmaps(sys.argv[1])
    else:
        print("Usage: python remove_mipmaps.py <folder_path>")
