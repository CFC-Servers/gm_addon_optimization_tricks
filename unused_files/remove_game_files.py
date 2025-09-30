import sourcepp
import os
import glob
from typing import List, Set

def get_vpk_files(gamefolder: str) -> Set[str]:
    """
    Get all file paths from VPK files in the game folder.
    
    Args:
        gamefolder: Path to the game folder containing VPK files
        
    Returns:
        Set of file paths found in all VPK files
    """
    print("Getting files from VPK archives...")
    
    vpk_files = set()
    vpk_count = 0
    
    # Find all VPK files in the game folder
    vpk_patterns = [
        os.path.join(gamefolder, "**", "*.vpk"),
        os.path.join(gamefolder, "*.vpk")
    ]
    
    found_vpks = []
    for pattern in vpk_patterns:
        found_vpks.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates and sort
    found_vpks = sorted(list(set(found_vpks)))
    
    if not found_vpks:
        print("No VPK files found in", gamefolder)
        return vpk_files
    
    print(f"Found {len(found_vpks)} VPK file(s) to process:")
    
    # Process each VPK file
    for vpk_path in found_vpks:
        try:
            # Counter for this VPK
            file_count = 0
            
            # Callback function to collect file paths
            def collect_files(path: str, entry) -> None:
                nonlocal file_count
                vpk_files.add(path.replace('\\', '/'))  # Normalize path separators
                file_count += 1
            
            # Open the VPK and iterate through all files
            vpk = sourcepp.vpkpp.VPK.open(vpk_path, collect_files)
            
            vpk_count += 1
            print(f"  Found {file_count} files in {os.path.basename(vpk_path)}")
            
        except Exception as e:
            print(f"  Error processing {os.path.basename(vpk_path)}: {e}")
            continue
    
    print("="*60)
    print(f"Processed {vpk_count} VPK file(s) successfully.")
    print(f"Total files found: {len(vpk_files)}")
    print("="*60)
    
    return vpk_files

def remove_game_files(folder, gamefolder, remove=True):
    """
    Remove files that exist in the game's VPK files from the addon folder.
    
    Args:
        folder: Path to the addon folder to clean
        gamefolder: Path to the game folder containing VPK files
        remove: If True, actually remove files. If False, just report what would be removed.
    """
    print("Removing game files...")
    
    # Get all files from VPK archives
    vpk_files = get_vpk_files(gamefolder)
    
    if not vpk_files:
        print("No files found in VPK archives. Nothing to remove.")
        return
    
    # Find files in the addon folder that match VPK files
    removed_count = 0
    removed_size = 0
    
    print(f"Scanning addon folder: {folder}")
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Get relative path from the addon folder
            rel_path = os.path.relpath(file_path, folder).replace('\\', '/')
            
            # Check if this file exists in any VPK
            if rel_path in vpk_files:
                file_size = os.path.getsize(file_path)
                removed_size += file_size
                removed_count += 1
                
                if remove:
                    try:
                        os.remove(file_path)
                        print(f"Removed: {rel_path}")
                    except Exception as e:
                        print(f"Failed to remove {rel_path}: {e}")
                else:
                    print(f"Would remove: {rel_path}")
    
    print("="*60)
    if remove:
        print(f"Removed {removed_count} game files.")
    else:
        print(f"Would remove {removed_count} game files.")
    
    if removed_count == 0:
        print("No game files were found in the addon folder.")
    else:
        print(f"Freed up {round(removed_size / 1000000, 2)} MB of space")
    print("="*60)
