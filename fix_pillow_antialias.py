# Fix for PIL.Image.ANTIALIAS deprecation in moviepy
import os
import sys

# Path to the moviepy resize.py file
resize_py_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'moviepy', 'video', 'fx', 'resize.py')

# Check if the file exists
if not os.path.exists(resize_py_path):
    print(f"Error: Could not find {resize_py_path}")
    sys.exit(1)

# Read the file content
with open(resize_py_path, 'r') as f:
    content = f.read()

# Check if the file contains the ANTIALIAS constant
if 'Image.ANTIALIAS' in content:
    print("Found PIL.Image.ANTIALIAS in resize.py, replacing with compatible code...")
    
    # Replace the ANTIALIAS with a version-compatible approach
    modified_content = content.replace(
        'resized_pil = pilim.resize(newsize[::-1], Image.ANTIALIAS)',
        'try:\n'
        '                # For Pillow >= 9.1.0 with Resampling enum\n'
        '                from PIL.Image import Resampling\n'
        '                resized_pil = pilim.resize(newsize[::-1], Resampling.LANCZOS)\n'
        '            except ImportError:\n'
        '                # For Pillow < 9.1.0\n'
        '                try:\n'
        '                    # For Pillow >= 7.0.0\n'
        '                    resized_pil = pilim.resize(newsize[::-1], Image.LANCZOS)\n'
        '                except AttributeError:\n'
        '                    # For Pillow < 7.0.0\n'
        '                    resized_pil = pilim.resize(newsize[::-1], Image.ANTIALIAS)'
    )
    
    # Write the modified content back to the file
    with open(resize_py_path, 'w') as f:
        f.write(modified_content)
    
    print("Successfully patched resize.py to work with all Pillow versions")
else:
    print("PIL.Image.ANTIALIAS not found in resize.py, no changes needed")