# region Globals

# NOTE : This file contains all of the global constants that mcow relies on.
# It's a latter addition to the mcow implementation, so plenty of constants are still hardcoded in-place and need to be modified to use this instead.

# List of all supported image format file extensions.
# This list contains all of the officially supported image file formats found within Blender's documentation (https://docs.blender.org/manual/en/latest/files/media/image_formats.html)
# Last updated 31/05/2025@19:58
MCOW_IMAGE_EXTENSIONS = [
    "bmp",
    "sgi", "rgb", "bw",
    "png",
    "jpg", "jpeg",
    "jp2", "j2c",
    "tga",
    "cin",
    "dpx",
    "exr",
    "hdr",
    "tif", "tiff",
    "webp"
]

# endregion
