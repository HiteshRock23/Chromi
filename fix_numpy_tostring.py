# Fix for numpy.ndarray.tostring deprecation in moviepy
import os
import sys
import re

def patch_file(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return False

    # Read the file content with error handling for different encodings
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

    # Check if the file contains the tostring method
    if '.tostring(' in content:
        print(f"Found .tostring() in {file_path}, replacing with compatible code...")
        
        # Replace tostring with a version-compatible approach
        modified_content = re.sub(
            r'([a-zA-Z0-9_]+)\.tostring\(([^)]*)\)',
            r'\1.tobytes(\2) if hasattr(\1, "tobytes") else \1.tostring(\2)',
            content
        )
        
        # Write the modified content back to the file with the same encoding
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return False
        
        print(f"Successfully patched {file_path} to work with all NumPy versions")
        return True
    else:
        print(f".tostring() not found in {file_path}, no changes needed")
        return False

def find_and_patch_files():
    # Path to the moviepy package
    moviepy_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'moviepy')
    
    if not os.path.exists(moviepy_path):
        print(f"Error: Could not find MoviePy package at {moviepy_path}")
        return
    
    patched_files = 0
    
    # Walk through all files in the moviepy directory
    for root, dirs, files in os.walk(moviepy_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if patch_file(file_path):
                    patched_files += 1
    
    # Also check imageio package which is used by MoviePy
    imageio_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'imageio')
    if os.path.exists(imageio_path):
        for root, dirs, files in os.walk(imageio_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if patch_file(file_path):
                        patched_files += 1
    
    if patched_files > 0:
        print(f"Successfully patched {patched_files} files to fix numpy.ndarray.tostring deprecation")
    else:
        print("No files needed patching for numpy.ndarray.tostring deprecation")

if __name__ == "__main__":
    print("Fixing numpy.ndarray.tostring deprecation in MoviePy and related packages...")
    find_and_patch_files()
    print("Done!")