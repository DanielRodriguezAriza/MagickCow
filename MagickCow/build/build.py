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

# region Extra

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

# region Generator

def mcow_file_get_size(file):
    current = file.tell()
    file.seek(0, 2)
    size = file.tell()
    file.seek(current, 0)
    return size

def mcow_debug_log(message):
    print(f"[Generator] : {message}")

def mcow_debug_log_error(message):
    print(f"[Generator] : {cli_ansi.color.fg.bright_red}ERROR! {message}{cli_ansi.color.end}")

def mcow_debug_log_success(message):
    print(f"[Generator] : {cli_ansi.color.fg.green}SUCCESS! {message}{cli_ansi.color.end}")

def mcow_file_append(write_file, filename):
    mcow_debug_log(f"Appending File : \"{filename}\"")
    with open(filename, "r") as read_file:
        contents = read_file.read()
        write_file.write(f"# {filename}\n")
        write_file.write(contents)
        write_file.write("\n") # I would write \r\n in Windows, but doing so leads to \r\r\n since \n is translated to \r\n automatically when working with "r" and "w" modes rather than "rb" and "wb". In short, python handles text mode operations for us already so we don't have anything to worry about.

def mcow_file_generate(out_filename, in_filenames):
    mcow_debug_log(f"Generating Python File : \"{out_filename}\"")
    try:
        size = 0
        with open(out_filename, "w") as file:
            for filename in in_filenames:
                mcow_file_append(file, filename)
            size = mcow_file_get_size(file)
        mcow_debug_log_success("Data successfully generated!")
        mcow_debug_log(f"Generated Python File : ( name = \"{out_filename}\", size = {size} bytes )")
    except Exception as e:
        mcow_debug_log_error(f"There was an error generating the output file: {e}")

def mcow_directory_create(dir_name):
    mcow_debug_log(f"Generating Directory : \"{dir_name}\"")
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except Exception as e:
        mcow_debug_log_error(f"There was an error generating the directory: {e}")

def mcow_directory_copy(dst, src):
    mcow_debug_log(f"Generating Data : \"{src}\"")
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except Exception as e:
        mcow_debug_log_error(f"There was an error generating the data : {e}")

def mcow_directory_delete(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def mcow_archive_create(dst, src):
    mcow_debug_log(f"Generating Archive : \"{dst}\"")
    try:
        shutil.make_archive(dst, "zip", src)
    except Exception as e:
        mcow_debug_log_error(f"There was an error generating the archive : {e}")

def mcow_build():
    # Define file names
    ofilename = "./magickcow/magickcow/__init__.py"
    ifilenames = [
        # Top
        "../src/License.py",
        "../src/Comments.py",
        "../src/BlenderInfo.py",
        "../src/Imports.py",

        # Globals
        "../src/globals/Globals.py", # Global constants and other global values

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

        # App Templates
        # NOTE : These are the startup app template files that blender uses when creating a new scene.
        "../src/functions/generation/extra/AppTemplate.py",

        # Main entry point
        "../src/Main.py",
    ]

    # Delete old contents of the output directory if it exists
    mcow_directory_delete("./magickcow")

    # Ensure directories exist
    mcow_directory_create("./magickcow")
    mcow_directory_create("./magickcow/magickcow")
    mcow_directory_create("./magickcow/magickcow/data")
    
    # Create the __init__.py file
    mcow_file_generate(ofilename, ifilenames)

    # Copy data directory
    mcow_directory_copy("./magickcow/magickcow/data", "../data")

    # Put everything into a ZIP archive
    mcow_archive_create("./magickcow", "./magickcow")

def main():
    # Ensure ANSI escape sequence support is enabled for colored text to work
    cli_ansi.init()

    # Invoke the build process
    try:
        mcow_build()
    except:
        mcow_debug_log("Aborting mcow_build()")

if __name__ == "__main__":
    main()

# endregion
