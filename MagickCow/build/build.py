# region Comment

# This is a simple script to generate the final single file magickcow.py blender addon.
# It simply joins together all of the files that have been separated into segments of their own.
# The reason this is done like this is because a large enough multi-file python program can actually take multiple seconds to start up, and for mcow
# that has proven to actually have a visible performance impact...
# This is commonly known as the "python import time problem"... This comment is here for those who want to criticise my code, so that they know why is it that I did things the way that I did.
# You are free to ignore this, fork my project and make your own thing where you actually use imports if it ever bothers you that much to package all of the code into a final single file addon.

# endregion

# region Imports

import os
import shutil

# endregion

# region Utility - ANSI

class cli_ansi:
    class color:
    
        end = "\033[0m"

        class fg:
            # Base colors
            black          = "\033[30m"
            red            = "\033[31m"
            green          = "\033[32m"
            yellow         = "\033[33m"
            blue           = "\033[34m"
            magenta        = "\033[35m"
            cyan           = "\033[36m"
            white          = "\033[37m"

            # Bright colors
            bright_black   = "\033[90m"
            bright_red     = "\033[91m"
            bright_green   = "\033[92m"
            bright_yellow  = "\033[93m"
            bright_blue    = "\033[94m"
            bright_magenta = "\033[95m"
            bright_cyan    = "\033[96m"
            bright_white   = "\033[97m"
    
        class bg:
            # Base colors
            black          = "\033[40m"
            red            = "\033[41m"
            green          = "\033[42m"
            yellow         = "\033[43m"
            blue           = "\033[44m"
            magenta        = "\033[45m"
            cyan           = "\033[46m"
            white          = "\033[47m"

            # Bright colors
            bright_black   = "\033[100m"
            bright_red     = "\033[101m"
            bright_green   = "\033[102m"
            bright_yellow  = "\033[103m"
            bright_blue    = "\033[104m"
            bright_magenta = "\033[105m"
            bright_cyan    = "\033[106m"
            bright_white   = "\033[107m"

    @staticmethod
    def init():
        if os.name == "nt":
            os.system("chcp 65001 > nul")

# endregion

# region Utility - Logging

def mcow_debug_log(message):
    print(f"[Generator] : {message}")

def mcow_debug_log_error(message):
    print(f"[Generator] : {cli_ansi.color.fg.bright_red}ERROR! {message}{cli_ansi.color.end}")

def mcow_debug_log_success(message):
    print(f"[Generator] : {cli_ansi.color.fg.green}SUCCESS! {message}{cli_ansi.color.end}")

# endregion

# region Utility - File System Ops

def mcow_file_get_size(file):
    current = file.tell()
    file.seek(0, 2)
    size = file.tell()
    file.seek(current, 0)
    return size

def mcow_directory_create(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def mcow_directory_copy(dst, src):
    shutil.copytree(src, dst, dirs_exist_ok=True)

def mcow_directory_delete(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def mcow_archive_create(dst, src):
    shutil.make_archive(dst, "zip", src)

# endregion

# region Generator

def mcow_file_append(write_file, filename):
    mcow_debug_log(f"    Appending File : \"{filename}\"")
    with open(filename, "r") as read_file:
        contents = read_file.read()
        write_file.write(f"# {filename}\n")
        write_file.write(contents)
        write_file.write("\n") # I would write \r\n in Windows, but doing so leads to \r\r\n since \n is translated to \r\n automatically when working with "r" and "w" modes rather than "rb" and "wb". In short, python handles text mode operations for us already so we don't have anything to worry about.

def mcow_file_generate(out_filename, in_filenames):
    size = 0
    with open(out_filename, "w") as file:
        for filename in in_filenames:
            mcow_file_append(file, filename)
        size = mcow_file_get_size(file)

def mcow_build_cleanup():
    # Delete old contents of the output directory if it exists
    # NOTE : This may be a little bit too destructive. Hopefully no users will have an already existing "magickcow" subdirectory sitting here with important data...
    mcow_debug_log("Cleaning up old data...")
    mcow_directory_delete("./magickcow")

def mcow_build_generate_dir(path):
    # mcow_debug_log(f"    Generating directory : \"{path}\"")
    mcow_directory_create(path)

def mcow_build_generate_dirs():
    # Ensure directories exist
    mcow_debug_log("Generating directories...")
    mcow_build_generate_dir("./magickcow")
    mcow_build_generate_dir("./magickcow/magickcow")
    mcow_build_generate_dir("./magickcow/magickcow/data")

def mcow_build_generate_file():

    # Output file name and input files for the build
    ofilename = "./magickcow/magickcow/__init__.py"
    ifilenames = [
        # Top
        "../src/License.py",
        "../src/Comments.py",
        "../src/BlenderInfo.py",
        "../src/Imports.py",

        # Globals (global constants and other global values of the program)
        "../src/globals/Globals_ImageData.py",
        "../src/globals/Globals_EffectData.py",

        # Classes - MagickCow
        "../src/classes/MagickCow/Exception.py",
        "../src/classes/MagickCow/Mesh.py",
        "../src/classes/MagickCow/Map/Scene.py",
        "../src/classes/MagickCow/PhysicsEntity/PhysicsEntity.py",

        # Classes - XNA
        "../src/classes/XNA/Matrix.py",
        "../src/classes/XNA/Model.py",

        # Classes - Blender
        "../src/classes/Blender/Data/Data.py",
        "../src/classes/Blender/Operators/Exporter.py",
        "../src/classes/Blender/Operators/Importer.py",
        "../src/classes/Blender/Panels/Materials.py",
        "../src/classes/Blender/Panels/Objects.py",
        "../src/classes/Blender/Panels/Scene.py",
        "../src/classes/Blender/Panels/Actions.py",

        # Utility functions
        "../src/functions/utility/Utility.py", # TODO : Further subdivide this code maybe?
        "../src/functions/utility/Effect.py", # Material-Effect related utility functions
        "../src/functions/utility/Path.py", # Path related utility functions
        "../src/functions/utility/Texture.py", # Texture related utility functions

        # Export Data Generation (The 3 stages of data transformation pipeline for export in MagickCow: Blender Data -> Get Stage -> Generate Stage -> Make Stage -> Final JSON file)
        # TODO : Rename all of the Pipeline classes to use some "ExportPipeline" prefix or whatever...
        "../src/functions/generation/export/Get.py",
        "../src/functions/generation/export/Generate.py",
        "../src/functions/generation/export/Make.py",
        "../src/functions/generation/export/Pipeline.py",
        "../src/functions/generation/export/PipelineCache.py",
        
        # Import Data Generation
        # TODO : Rename all of the pipleine classes and files to use the "ImportPipeline" prefix or something like that...
        "../src/functions/generation/import/Pipeline.py", # ImportPipeline Base
        "../src/functions/generation/import/ContentImporter.py", # Generic Content Importer # TODO : Figure out if this is good enough and should stay or if we're going to remove this and go back to the old way of doing things...
        "../src/functions/generation/import/derived/BufferMesh.py", # Importer for meshes made from vertex buffers and index buffers.
        "../src/functions/generation/import/derived/Map.py", # LevelModel ImportPipeline
        "../src/functions/generation/import/derived/PhysicsEntity.py", # PhysicsEntity ImportPipeline
        "../src/functions/generation/import/derived/XnaModel.py", # XnaModel ImportPipeline

        # Main entry point
        "../src/Main.py",
    ]

    # Create the __init__.py file
    mcow_debug_log("Generating addon Python script...")
    mcow_file_generate(ofilename, ifilenames)

def mcow_build_generate_data():
    # Copy data directory
    mcow_debug_log("Generating addon data...")
    mcow_directory_copy("./magickcow/magickcow/data", "../data")

def mcow_build_generate_archive():
    # Put everything into a ZIP archive
    mcow_archive_create("./magickcow", "./magickcow")

def mcow_build():
    mcow_build_cleanup() # Initial cleanup, deletes the dirs with the generated data so that we don't have any leftovers from before just in case they were not properly cleaned up during the previous build, or in case users add files that do not belong there. This way, no trash can appear within the final archive.
    mcow_build_generate_dirs()
    mcow_build_generate_file()
    mcow_build_generate_data()
    mcow_build_generate_archive()
    mcow_build_cleanup() # Final cleanup, deletes the dirs with the generated data and only leaves behind the final archive (zip file), which is what we care about. This maybe could be configured in the future with some preserve_directory flag or whatever, just in case users do want to preserve the generated dirs.

# endregion

# region Main

def main():
    # Ensure ANSI escape sequence support is enabled for colored text to work
    cli_ansi.init()

    # Invoke the build process
    try:
        mcow_build()
        mcow_debug_log_success("Data successfully generated!")
        mcow_debug_log("Generated archive : \"magickcow.zip\"")
    except:
        mcow_debug_log_error(f"There was an error building MagickCow : {e}")
        mcow_debug_log("Aborting mcow_build()")
        mcow_build_cleanup() # Clean up just in case the process was aborted half way through. This may come to bite us in the ass in the future tho! Because MAYBE it would be good to leave behind the generated build files for debugging purposes... but I don't want to clutter the user's machine with shit, so yeah.

if __name__ == "__main__":
    main()

# endregion
