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

def mcow_file_append(write_file, filename):
    mcow_debug_log(f"Appending File : \"{filename}\"")
    with open(filename, "r") as read_file:
        contents = read_file.read()
        write_file.write(f"# {filename}\n")
        write_file.write(contents)
        write_file.write("\n") # I would write \r\n in Windows, but doing so leads to \r\r\n since \n is translated to \r\n automatically when working with "r" and "w" modes rather than "rb" and "wb". In short, python handles text mode operations for us already so we don't have anything to worry about.

def mcow_file_generate(out_filename, in_filenames):
    mcow_debug_log(f"Generating File : \"{out_filename}\"")
    try:
        size = 0
        with open(out_filename, "w") as file:
            for filename in in_filenames:
                mcow_file_append(file, filename)
            size = mcow_file_get_size(file)
        mcow_debug_log(f"{cli_ansi.color.fg.green}Data successfully generated!{cli_ansi.color.end}")
        mcow_debug_log(f"Generated File : ( name = \"{out_filename}\", size = {size} bytes )")
    except Exception as e:
        mcow_debug_log(f"{cli_ansi.color.fg.bright_red}There was an error generating the output file: {e}{cli_ansi.color.end}")

def main():
    cli_ansi.init()
    ofilename = "../../magickcow.py"
    ifilenames = [
        # Top
        "../mcow/License.py",
        "../mcow/Comments.py",
        "../mcow/BlenderInfo.py",
        "../mcow/Imports.py",

        # Classes - MagickCow
        "../mcow/classes/MagickCow/Exception.py",
        "../mcow/classes/MagickCow/Mesh.py",
        "../mcow/classes/MagickCow/Map/Scene.py",
        "../mcow/classes/MagickCow/PhysicsEntity/PhysicsEntity.py",

        # Classes - XNA
        "../mcow/classes/XNA/Matrix.py",
        "../mcow/classes/XNA/Model.py",

        # Classes - Blender
        "../mcow/classes/Blender/Data/Data.py",
        "../mcow/classes/Blender/Operators/Exporter.py",
        "../mcow/classes/Blender/Operators/Importer.py",
        "../mcow/classes/Blender/Panels/Materials.py",
        "../mcow/classes/Blender/Panels/Objects.py",
        "../mcow/classes/Blender/Panels/Scene.py",

        # Utility functions
        "../mcow/functions/utility/Utility.py", # TODO : Further subdivide this code maybe?
        "../mcow/functions/utility/Effect.py", # Effect / Material related utility functions

        # Export Data Generation (The 3 stages of data transformation pipeline for export in MagickCow: Blender Data -> Get Stage -> Generate Stage -> Make Stage -> Final JSON file)
        # TODO : Rename all of the Pipeline classes to use some "ExportPipeline" prefix or whatever...
        "../mcow/functions/generation/export/Get.py",
        "../mcow/functions/generation/export/Generate.py",
        "../mcow/functions/generation/export/Make.py",
        "../mcow/functions/generation/export/Pipeline.py",
        "../mcow/functions/generation/export/PipelineCache.py",
        
        # Import Data Generation
        # TODO : Rename all of the pipleine classes and files to use the "ImportPipeline" prefix or something like that...
        "../mcow/functions/generation/import/Pipeline.py", # ImportPipeline Base
        "../mcow/functions/generation/import/derived/Map.py", # LevelModel ImportPipeline
        "../mcow/functions/generation/import/derived/PhysicsEntity.py", # PhysicsEntity ImportPipeline

        # Main entry point
        "../mcow/Main.py",
    ]
    mcow_file_generate(ofilename, ifilenames)

if __name__ == "__main__":
    main()

# endregion
