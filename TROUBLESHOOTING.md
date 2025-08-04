# Troubleshooting Guide

## numpy.ndarray.tostring Error

### Issue

If you encounter the following error when trying to convert videos to GIFs:

```
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
```

This is due to a compatibility issue between MoviePy and newer versions of the NumPy library. The `tostring` method was deprecated in NumPy 1.19.0 and replaced with `tobytes`, but some parts of MoviePy or its dependencies might still be using the old method.

### Solution

This project includes a utility script that patches the MoviePy and related libraries to work with newer versions of NumPy. To apply the fix:

1. Run the included patch script:

```
python fix_numpy_tostring.py
```

2. The script will automatically locate and modify any files that use the deprecated `tostring` method to make them compatible with newer NumPy versions.

3. Restart your Django server after applying the patch.

### How the Fix Works

The patch script replaces calls to the deprecated `tostring()` method with a version-compatible approach that tries to use:

1. `tobytes()` if the object has this method (for newer NumPy versions)
2. Falls back to `tostring()` for older NumPy versions

This ensures compatibility across all NumPy versions while maintaining the same functionality.

## PIL.Image.ANTIALIAS Error

### Issue

If you encounter the following error when trying to convert videos:

```
AttributeError: module 'PIL.Image' has no attribute 'ANTIALIAS'
```

This is due to a compatibility issue between MoviePy and newer versions of the Pillow library (version 10.0.0 and above). The `ANTIALIAS` constant was deprecated and removed in Pillow 10.0.0, but MoviePy still uses it in its resize functionality.

### Solution

This project includes a utility script that patches the MoviePy library to work with newer versions of Pillow. To apply the fix:

1. Run the included patch script:

```
python fix_pillow_antialias.py
```

2. The script will automatically locate and modify the MoviePy resize.py file to use the appropriate resampling filter based on your Pillow version.

3. Restart your Django server after applying the patch.

### How the Fix Works

The patch script replaces the deprecated `Image.ANTIALIAS` with a version-compatible approach that tries to use:

1. `PIL.Image.Resampling.LANCZOS` for Pillow >= 9.1.0
2. `PIL.Image.LANCZOS` for Pillow >= 7.0.0 but < 9.1.0
3. Falls back to `PIL.Image.ANTIALIAS` for older Pillow versions

This ensures compatibility across all Pillow versions while maintaining the same high-quality image resizing functionality.

## Other Common Issues

### Video Upload Size Limit

If you're unable to upload large video files, check the following:

1. The default upload size limit is set to 100MB in the Django settings
2. Your web server configuration might have its own upload size limits

### GIF Processing Takes Too Long

GIF processing time depends on several factors:

1. The size and length of the original video
2. The quality settings used for conversion
3. Your server's processing power

The current settings are optimized for Chrome background GIFs (see CONVERSION_SETTINGS.md for details). GIF conversion can be more time-consuming than video conversion due to the optimization process.

### GIF Resolution Issues

The application now enforces a 1280×720 (HD) resolution for all output GIFs. If you need a different resolution:

1. Modify the `trimmed_video = trimmed_video.resize(width=1280, height=720)` line in `views.py`
2. Be aware that larger resolutions will significantly increase GIF file size

### Fixed 6-Second Duration

The application now enforces a fixed 6-second duration for all output GIFs to meet Chrome's requirements. If you need a different duration:

1. Modify the `duration = 6` line in `views.py`
2. Update the duration validation if needed
3. Be aware that longer durations will significantly increase GIF file size