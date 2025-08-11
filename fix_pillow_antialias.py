# # Fix for PIL.Image.ANTIALIAS deprecation in moviepy
# import os
# import sys
# import glob
# from PIL import Image
# import moviepy

# def fix_antialias_in_file(file_path):
#     """Fix ANTIALIAS references in a single file."""
#     try:
#         with open(file_path, 'r') as f:
#             content = f.read()
        
#         if 'Image.ANTIALIAS' in content:
#             print(f"Found PIL.Image.ANTIALIAS in {file_path}, replacing with Image.Resampling.LANCZOS...")
            
#             # Replace the ANTIALIAS with Image.Resampling.LANCZOS for Pillow >= 10.0.0
#             modified_content = content.replace(
#                 'resized_pil = pilim.resize(newsize[::-1], Image.ANTIALIAS)',
#                 'try:\n'
#                 '                # For Pillow >= 10.0.0\n'
#                 '                from PIL import Image\n'
#                 '                resized_pil = pilim.resize(newsize[::-1], Image.Resampling.LANCZOS)\n'
#                 '            except AttributeError:\n'
#                 '                # Fallback for older Pillow versions\n'
#                 '                resized_pil = pilim.resize(newsize[::-1], Image.LANCZOS)'
#             )
            
#             # Also replace any other instances of Image.ANTIALIAS
#             modified_content = modified_content.replace(
#                 '                    resized_pil = pilim.resize(newsize[::-1], Image.ANTIALIAS)',
#                 '                    try:\n'
#                 '                        from PIL import Image\n'
#                 '                        resized_pil = pilim.resize(newsize[::-1], Image.Resampling.LANCZOS)\n'
#                 '                    except AttributeError:\n'
#                 '                        resized_pil = pilim.resize(newsize[::-1], Image.LANCZOS)'
#             )
            
#             # Write the modified content back to the file
#             with open(file_path, 'w') as f:
#                 f.write(modified_content)
            
#             print(f"Successfully patched {file_path} to use Image.Resampling.LANCZOS")
#             return True
#         else:
#             print(f"No PIL.Image.ANTIALIAS found in {file_path}")
#             return False
            
#     except Exception as e:
#         print(f"Error processing {file_path}: {e}")
#         return False

# def main():
#     """Main function to fix ANTIALIAS references in MoviePy files."""
#     # Find the site-packages directory
#     try:
#         import moviepy
#         moviepy_path = os.path.dirname(moviepy.__file__)
#     except ImportError:
#         site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
#         moviepy_path = os.path.join(site_packages, 'moviepy')
    
#     if not os.path.exists(moviepy_path):
#         print(f"Error: Could not find MoviePy at {moviepy_path}")
#         sys.exit(1)
    
#     # Find all Python files in MoviePy that might contain ANTIALIAS
#     moviepy_files = []
#     for root, dirs, files in os.walk(moviepy_path):
#         for file in files:
#             if file.endswith('.py'):
#                 file_path = os.path.join(root, file)
#                 try:
#                     with open(file_path, 'r') as f:
#                         content = f.read()
#                         if 'Image.ANTIALIAS' in content:
#                             moviepy_files.append(file_path)
#                 except:
#                     continue
    
#     if not moviepy_files:
#         print("No files with Image.ANTIALIAS found in MoviePy")
#         return
    
#     print(f"Found {len(moviepy_files)} files with Image.ANTIALIAS references:")
#     for file_path in moviepy_files:
#         print(f"  - {os.path.relpath(file_path, moviepy_path)}")
    
#     # Fix each file
#     fixed_count = 0
#     for file_path in moviepy_files:
#         if fix_antialias_in_file(file_path):
#             fixed_count += 1
    
#     print(f"\nFixed {fixed_count} out of {len(moviepy_files)} files")

# if __name__ == "__main__":
#     main()