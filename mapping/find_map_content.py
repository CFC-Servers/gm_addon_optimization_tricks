import srctools
import os
import shutil
import re
from typing import Set, Dict, List

def extract_content_paths(vmf: srctools.VMF, vmf_folder: str = '', processed_instances: Set[str] = None) -> Dict[str, Set[str]]:
    """
    Extract all content paths from a VMF file, including content from instances.
    
    Args:
        vmf: Parsed VMF object
        vmf_folder: Folder containing the VMF file (for resolving relative instance paths)
        processed_instances: Set of already processed instance files to avoid infinite recursion
        
    Returns:
        Dictionary with content types as keys and sets of file paths as values
    """
    if processed_instances is None:
        processed_instances = set()
    
    content = {
        'materials': set(),
        'models': set(),
        'sounds': set(),
        'scripts': set(),
        'particles': set()
    }
    
    # Common VMF keys that reference materials
    material_keys = {
        'material', 'texture', 'material0', 'material1', 'material2', 'material3',
        'basetexture', 'normalmap', 'bumpmap', 'detailtexture', 'envmap',
        'uaxis', 'vaxis'  # These contain material info in brush faces
    }
    
    # Common VMF keys that reference models
    model_keys = {
        'model', 'modelname', 'body', 'skin'
    }
    
    # Common VMF keys that reference sounds
    sound_keys = {
        'message', 'noise', 'soundname', 'loopsound', 'startsound', 'stopsound',
        'breakablesound', 'impactsound', 'noisewalkingtime', 'noisestill',
        'noiserunning', 'noisejump', 'noiselanding'
    }
    
    # Keys that might reference scripts or particles
    script_keys = {
        'script', 'vscript', 'script_file'
    }
    
    particle_keys = {
        'effect_name', 'particle_system', 'attachment_name'
    }
    
    print("Scanning VMF entities for content references...")
    entity_count = 0
    instance_count = 0
    
    # Iterate through all entities in the VMF
    for entity in vmf.iter_ents():
        entity_count += 1
        classname = entity.get('classname', '')
        
        # Handle func_instance entities - these reference other VMF files
        if classname == 'func_instance':
            instance_file = entity.get('file', '')
            if instance_file:
                instance_count += 1
                # Instance paths are relative to the maps folder
                # Normalize the instance file path
                instance_file_normalized = instance_file.replace('/', os.sep).replace('\\', os.sep)
                
                if vmf_folder:
                    # Try to find 'maps' folder in the path
                    vmf_folder_normalized = os.path.normpath(vmf_folder)
                    parts = vmf_folder_normalized.split(os.sep)
                    
                    # Find the last occurrence of 'maps' in the path
                    maps_index = -1
                    for i in range(len(parts) - 1, -1, -1):
                        if parts[i].lower() == 'maps':
                            maps_index = i
                            break
                    
                    if maps_index >= 0:
                        # Reconstruct path up to and including the maps folder
                        maps_folder = os.sep.join(parts[:maps_index + 1])
                        # Instance paths are always relative to the maps folder
                        instance_path = os.path.normpath(os.path.join(maps_folder, instance_file_normalized))
                    else:
                        # Fallback: assume instance is relative to VMF location
                        instance_path = os.path.normpath(os.path.join(vmf_folder, instance_file_normalized))
                else:
                    instance_path = os.path.normpath(instance_file_normalized)
                
                # Check if we've already processed this instance to avoid infinite recursion
                if instance_path not in processed_instances:
                    processed_instances.add(instance_path)
                    print(f"  Found instance: {instance_file}")
                    
                    # Try to load and parse the instance VMF
                    if os.path.exists(instance_path):
                        try:
                            print(f"    Parsing instance: {instance_path}")
                            with open(instance_path, 'r', encoding='utf-8', errors='ignore') as f:
                                instance_content = f.read()
                            
                            instance_kv = srctools.Keyvalues.parse(instance_content)
                            instance_vmf = srctools.VMF.parse(instance_kv)
                            
                            # Recursively extract content from the instance
                            instance_folder = os.path.dirname(instance_path)
                            instance_content_dict = extract_content_paths(instance_vmf, instance_folder, processed_instances)
                            
                            # Merge the instance content with our content
                            for content_type, paths in instance_content_dict.items():
                                content[content_type].update(paths)
                            
                            print(f"    Instance content: {sum(len(paths) for paths in instance_content_dict.values())} files")
                        except Exception as e:
                            print(f"    Warning: Failed to parse instance {instance_path}: {e}")
                    else:
                        print(f"    Warning: Instance file not found: {instance_path}")
        
        # Check all entity properties
        for key, value in entity.items():
            key_lower = key.lower()
            value_str = str(value).strip()
            
            if not value_str:
                continue
                
            # Extract materials
            if any(mat_key in key_lower for mat_key in material_keys):
                # Handle texture axis format (contains material path)
                if key_lower in ['uaxis', 'vaxis']:
                    # Format: "[1 0 0 0] 0.25" where material might be embedded
                    # Skip these for now as they're complex
                    continue
                    
                # Clean up material path
                material_path = value_str.replace('\\', '/').lower()
                if material_path and not material_path.startswith('['):
                    # Remove any file extensions and add .vmt
                    material_path = re.sub(r'\.(vmt|vtf)$', '', material_path)
                    content['materials'].add(material_path)
            
            # Extract models
            elif any(model_key in key_lower for model_key in model_keys):
                model_path = value_str.replace('\\', '/').lower()
                if model_path.endswith('.mdl'):
                    content['models'].add(model_path)
            
            # Extract sounds
            elif any(sound_key in key_lower for sound_key in sound_keys):
                sound_path = value_str.replace('\\', '/').lower()
                # Sounds can be .wav, .mp3, .ogg
                if any(sound_path.endswith(ext) for ext in ['.wav', '.mp3', '.ogg']):
                    content['sounds'].add(sound_path)
                elif classname.startswith('ambient_'):
                    # Ambient sounds might not have extensions
                    content['sounds'].add(sound_path)
            
            # Extract scripts
            elif any(script_key in key_lower for script_key in script_keys):
                script_path = value_str.replace('\\', '/').lower()
                if script_path.endswith('.nut') or script_path.endswith('.lua'):
                    content['scripts'].add(script_path)
            
            # Extract particles
            elif any(particle_key in key_lower for particle_key in particle_keys):
                content['particles'].add(value_str)
    
    # Also scan brush faces for materials
    print("Scanning brush faces for materials...")
    brush_count = 0
    face_count = 0
    
    for brush in vmf.iter_wbrushes():
        brush_count += 1
        for face in brush.sides:
            face_count += 1
            material = face.mat.casefold()
            if material and material != 'tools/toolsnodraw':
                content['materials'].add(material)
    
    print(f"Processed {entity_count} entities ({instance_count} instances), {brush_count} brushes, {face_count} faces")
    
    return content

def parse_vmt_textures(vmt_path: str) -> Set[str]:
    """
    Parse a VMT file and extract all texture references.
    
    Args:
        vmt_path: Path to the VMT file
        
    Returns:
        Set of texture paths referenced in the VMT
    """
    textures = set()
    
    try:
        with open(vmt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse the VMT as keyvalues
        kv = srctools.Keyvalues.parse(content)
        
        # Common texture keys in VMT files
        texture_keys = {
            '$basetexture', '$basetexture2', '$basetexture3', '$basetexture4',
            '$normalmap', '$bumpmap', '$heightmap', '$parallaxmap',
            '$detail', '$detailtexture', '$detailblendfactor',
            '$envmap', '$envmapmask', '$envmaptint',
            '$lightwarptexture', '$phongwarptexture',
            '$blendmodulatetexture', '$maskbasetexture',
            '$texture2', '$iris', '$corneatexture',
            '$ambientoccltexture', '$diffusewarp', '$phongwarp',
            '$selfillumtexture', '$selfillummask',
            '$reflecttexture', '$refracttexture'
        }
        
        def extract_textures_recursive(kv_node):
            """Recursively extract textures from keyvalues"""
            # Handle srctools Keyvalues structure
            if hasattr(kv_node, '__iter__'):
                try:
                    for item in kv_node:
                        # Each item has .name and .value attributes
                        key = item.name.lower()
                        value = item.value
                        
                        # Check if this key references a texture
                        if key in texture_keys:
                            if isinstance(value, str):
                                # Handle the raw string value - srctools may interpret some escape sequences
                                texture_path = str(value).strip()
                                
                                # Fix common escape sequence issues from srctools parsing
                                # \a (bell) -> \a, \b (backspace) -> \b, etc.
                                texture_path = texture_path.replace('\x07', '\\a')  # Bell char back to \a
                                texture_path = texture_path.replace('\x08', '\\b')  # Backspace back to \b  
                                texture_path = texture_path.replace('\x0c', '\\f')  # Form feed back to \f
                                texture_path = texture_path.replace('\x0a', '\\n')  # Newline back to \n
                                texture_path = texture_path.replace('\x0d', '\\r')  # Carriage return back to \r
                                texture_path = texture_path.replace('\x09', '\\t')  # Tab back to \t
                                texture_path = texture_path.replace('\x0b', '\\v')  # Vertical tab back to \v
                                
                                # Now normalize path separators
                                texture_path = texture_path.replace('\\', '/').lower()
                                if texture_path and not texture_path.startswith('['):
                                    # Remove any file extension
                                    texture_path = re.sub(r'\.(vtf|vmt)$', '', texture_path)
                                    textures.add(texture_path)
                        
                        # Recursively check nested values (for complex VMTs)
                        if hasattr(value, '__iter__') and not isinstance(value, str):
                            extract_textures_recursive(item)
                            
                except Exception:
                    # Fallback for different srctools versions
                    pass
        
        # Extract textures from all shader sections
        for shader_block in kv:
            extract_textures_recursive(shader_block)
        
    except Exception as e:
        print(f"  Warning: Failed to parse VMT {vmt_path}: {e}")
    
    return textures

def copy_content_files(content: Dict[str, Set[str]], source_folder: str, dest_folder: str) -> Dict[str, int]:
    """
    Copy found content files from source to destination folder.
    
    Args:
        content: Dictionary of content paths from extract_content_paths
        source_folder: Source folder to copy from
        dest_folder: Destination folder to copy to
        
    Returns:
        Dictionary with copy statistics
    """
    stats = {
        'materials_copied': 0,
        'models_copied': 0,
        'sounds_copied': 0,
        'scripts_copied': 0,
        'materials_missing': 0,
        'models_missing': 0,
        'sounds_missing': 0,
        'scripts_missing': 0
    }
    
    # Keep track of all textures we need to copy (including VMT references)
    all_textures = set(content['materials'])
    
    # First pass: Copy VMT files and parse them for texture references
    print("Copying materials and parsing VMT files for texture references...")
    vmt_textures_found = set()
    
    for material_path in content['materials']:
        # Try to find .vmt file
        vmt_source = os.path.join(source_folder, 'materials', material_path + '.vmt')
        vmt_dest = os.path.join(dest_folder, 'materials', material_path + '.vmt')
        
        if os.path.exists(vmt_source):
            os.makedirs(os.path.dirname(vmt_dest), exist_ok=True)
            shutil.copy2(vmt_source, vmt_dest)
            stats['materials_copied'] += 1
            print(f"  Copied: materials/{material_path}.vmt")
            
            # Parse the VMT file to find texture references
            referenced_textures = parse_vmt_textures(vmt_source)
            vmt_textures_found.update(referenced_textures)
            
            if referenced_textures:
                print(f"    Found {len(referenced_textures)} texture references in VMT")
                for tex in referenced_textures:
                    print(f"      -> {tex}")
        else:
            stats['materials_missing'] += 1
            print(f"  Missing: materials/{material_path}.vmt")
    
    # Add the VMT-referenced textures to our list
    all_textures.update(vmt_textures_found)
    
    # Second pass: Copy all VTF files (original materials + VMT references)
    print(f"Copying VTF textures ({len(all_textures)} total)...")
    for texture_path in sorted(all_textures):
        vtf_source = os.path.join(source_folder, 'materials', texture_path + '.vtf')
        vtf_dest = os.path.join(dest_folder, 'materials', texture_path + '.vtf')
        
        if os.path.exists(vtf_source):
            os.makedirs(os.path.dirname(vtf_dest), exist_ok=True)
            shutil.copy2(vtf_source, vtf_dest)
            print(f"  Copied: materials/{texture_path}.vtf")
        else:
            # Only count as missing if this was an original material (not a VMT reference)
            if texture_path in content['materials']:
                print(f"  Missing: materials/{texture_path}.vtf")
            else:
                print(f"  Missing VMT reference: materials/{texture_path}.vtf")
    
    # Model files (.mdl and associated files)
    print("Copying models...")
    for model_path in content['models']:
        model_base = model_path.replace('.mdl', '')
        model_extensions = ['.mdl', '.vvd', '.vtx', '.phy']
        
        copied_any = False
        for ext in model_extensions:
            source_file = os.path.join(source_folder, model_base + ext)
            dest_file = os.path.join(dest_folder, model_base + ext)
            
            if os.path.exists(source_file):
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(source_file, dest_file)
                if ext == '.mdl':
                    copied_any = True
                print(f"  Copied: {model_base}{ext}")
        
        if copied_any:
            stats['models_copied'] += 1
        else:
            stats['models_missing'] += 1
            print(f"  Missing: {model_path}")
    
    # Sound files
    print("Copying sounds...")
    for sound_path in content['sounds']:
        source_file = os.path.join(source_folder, 'sound', sound_path)
        dest_file = os.path.join(dest_folder, 'sound', sound_path)
        
        if os.path.exists(source_file):
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(source_file, dest_file)
            stats['sounds_copied'] += 1
            print(f"  Copied: sound/{sound_path}")
        else:
            stats['sounds_missing'] += 1
            print(f"  Missing: sound/{sound_path}")
    
    # Script files
    print("Copying scripts...")
    for script_path in content['scripts']:
        source_file = os.path.join(source_folder, 'scripts', script_path)
        dest_file = os.path.join(dest_folder, 'scripts', script_path)
        
        if os.path.exists(source_file):
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(source_file, dest_file)
            stats['scripts_copied'] += 1
            print(f"  Copied: scripts/{script_path}")
        else:
            stats['scripts_missing'] += 1
            print(f"  Missing: scripts/{script_path}")
    
    return stats

def find_map_content(all_content_folder: str, new_content_folder: str, map_file: str):
    """
    Find and copy all content used by a Source engine map file.
    
    Args:
        all_content_folder: Path to folder containing all content (materials, models, sounds, etc.)
        new_content_folder: Path to folder where found content should be copied
        map_file: Path to the .vmf map file to analyze
    """
    print(f"Finding content for map: {map_file}")
    print("="*60)
    
    if not os.path.exists(map_file):
        print(f"Error: Map file does not exist: {map_file}")
        return
    
    if not map_file.lower().endswith('.vmf'):
        print(f"Error: File is not a VMF file: {map_file}")
        return
    
    if not os.path.exists(all_content_folder):
        print(f"Error: Source content folder does not exist: {all_content_folder}")
        return
    
    try:
        # Read and parse the VMF file
        print("Loading VMF file...")
        with open(map_file, 'r', encoding='utf-8', errors='ignore') as f:
            vmf_content = f.read()
        
        # Parse keyvalues
        print("Parsing keyvalues...")
        kv_tree = srctools.Keyvalues.parse(vmf_content)
        
        # Parse VMF structure
        print("Parsing VMF structure...")
        vmf = srctools.VMF.parse(kv_tree)
        
        # Get the folder containing the VMF file for resolving relative instance paths
        vmf_folder = os.path.dirname(os.path.abspath(map_file))
        
        # Extract content paths
        content = extract_content_paths(vmf, vmf_folder)
        
        # Print summary
        print("\nContent found:")
        for content_type, paths in content.items():
            print(f"  {content_type}: {len(paths)} files")
        
        print(f"\nTotal unique files found: {sum(len(paths) for paths in content.values())}")
        
        # Create destination folder if it doesn't exist
        if new_content_folder:
            os.makedirs(new_content_folder, exist_ok=True)
            
            # Copy files
            print(f"\nCopying content to: {new_content_folder}")
            print("="*60)
            stats = copy_content_files(content, all_content_folder, new_content_folder)
            
            # Print copy statistics
            print("\n" + "="*60)
            print("Copy Summary:")
            print(f"  Materials: {stats['materials_copied']} copied, {stats['materials_missing']} missing")
            print(f"  Models: {stats['models_copied']} copied, {stats['models_missing']} missing")
            print(f"  Sounds: {stats['sounds_copied']} copied, {stats['sounds_missing']} missing")
            print(f"  Scripts: {stats['scripts_copied']} copied, {stats['scripts_missing']} missing")
            
            total_copied = (stats['materials_copied'] + stats['models_copied'] + 
                          stats['sounds_copied'] + stats['scripts_copied'])
            total_missing = (stats['materials_missing'] + stats['models_missing'] + 
                           stats['sounds_missing'] + stats['scripts_missing'])
            
            print(f"  Total: {total_copied} copied, {total_missing} missing")
            print("="*60)
        
    except Exception as e:
        print(f"Error processing VMF file: {e}")
        import traceback
        traceback.print_exc()