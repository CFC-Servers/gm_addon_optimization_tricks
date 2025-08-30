import os
import signal
import time
from pydub import AudioSegment, silence

def trim_single_audio_file(input_file, silence_thresh=-55, min_silence_len=50):
    """
    Trim silence from the end only of a single wav file.

    Args:
        input_file (str): Path to input WAV file.
        silence_thresh (int): Silence threshold in dBFS. Default -55 dB.
        min_silence_len (int): Minimum length of silence (ms) to trim. Default 50 ms.
    
    Returns:
        tuple: (success, message, bytes_saved)
    """
    try:
        # Get original file size
        original_size = os.path.getsize(input_file)
        
        # Load audio file
        audio = AudioSegment.from_wav(input_file)
        original_duration = len(audio)

        # Detect non-silent chunks
        non_silence_ranges = silence.detect_nonsilent(audio, 
                                                      min_silence_len=min_silence_len, 
                                                      silence_thresh=silence_thresh)

        if non_silence_ranges:
            # Get the last non-silent segment (only trim from end)
            end_trim = non_silence_ranges[-1][1]
            
            # Check if any trimming is needed from the end
            end_silence = original_duration - end_trim
            if end_silence <= min_silence_len:
                return False, f"No significant silence to trim from end ({end_silence}ms)", 0
            
            # Only trim from the end, keep the start intact
            trimmed_audio = audio[0:end_trim]
            new_duration = len(trimmed_audio)
            
            # Export result (overwrite original)
            trimmed_audio.export(input_file, format="wav")
            
            # Calculate savings
            new_size = os.path.getsize(input_file)
            bytes_saved = original_size - new_size
            time_saved = original_duration - new_duration
            
            return True, f"Trimmed {time_saved/1000:.1f}s of silence from end", bytes_saved
        else:
            return False, "No non-silent audio detected", 0
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}", 0

def trim_empty_audio(folder, silence_thresh=-55, min_silence_len=50):
    """
    Trim silence from the end only of all WAV files in the specified folder.
    
    Args:
        folder (str): Path to folder containing WAV files.
        silence_thresh (int): Silence threshold in dBFS. Default -55 dB.
        min_silence_len (int): Minimum length of silence (ms) to trim. Default 50 ms.
    """
    old_size = 0
    new_size = 0
    processed_count = 0
    success_count = 0
    start_time = time.time()
    
    def signal_handler(sig, frame):
        if os.path.exists("trim_crashfile.txt"):
            os.remove("trim_crashfile.txt")
        print(f"\nTime taken: {round(time.time() - start_time, 2)} seconds")
        print("Cancelled by user.")
        exit()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Handle crash recovery
    invalid_files = set()
    if os.path.exists("trim_crashfile.txt"):
        with open("trim_crashfile.txt", "r") as f:
            crash_file = f.read().strip()
            with open("trim_blacklist.txt", "a") as file:
                file.write(crash_file + "\n")
            print(f"Crash detected! Last file processed: {crash_file}")
            print("File has been blacklisted. Try manually fixing it.")
        os.remove("trim_crashfile.txt")
    
    # Load blacklist
    if os.path.exists("trim_blacklist.txt"):
        with open("trim_blacklist.txt", "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    invalid_files.add(line)
                    print(f"Blacklisted file: {line}")
    
    print(f"Scanning for WAV files in: {folder}")
    print("Trimming silence from end of WAV files...")
    
    # Process all WAV files
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if not filename.lower().endswith(".wav"):
                continue
                
            file_path = os.path.join(root, filename)
            
            # Skip blacklisted files
            if file_path in invalid_files:
                print(f"Skipping blacklisted file: {file_path}")
                continue
            
            # Create crash file for recovery
            with open("trim_crashfile.txt", "w") as f:
                f.write(file_path)
            
            try:
                # Get original file size
                old_file_size = os.path.getsize(file_path)
                old_size += old_file_size
                
                # Process the file
                success, message, bytes_saved = trim_single_audio_file(file_path, silence_thresh, min_silence_len)
                processed_count += 1
                
                if success:
                    success_count += 1
                    new_file_size = os.path.getsize(file_path)
                    new_size += new_file_size
                    saved_mb = bytes_saved / (1024 * 1024)
                    print(f"✓ {file_path} - {message} (saved {saved_mb:.2f} MB)")
                else:
                    new_size += old_file_size  # No change in size
                    print(f"⚠ {file_path} - {message}")
                
            except Exception as e:
                print(f"✗ {file_path} - Error: {str(e)}")
                new_size += old_file_size  # No change in size
    
    # Clean up crash file
    if os.path.exists("trim_crashfile.txt"):
        os.remove("trim_crashfile.txt")
    
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
        trim_empty_audio(sys.argv[1])
    else:
        print("Usage: python trim_empty.py <folder_path>")
