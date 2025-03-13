# region Comment

# This is a simple script to generate the final single file magickcow.py blender addon.
# It simply joins together all of the files that have been separated into segments of their own.
# The reason this is done like this is because a large enough multi-file python program can actually take multiple seconds to start up, and for mcow
# that has proven to actually have a visible performance impact...
# This is commonly known as the "python import time problem"... This comment is here for those who want to criticise my code, so that they know why is it that I did things the way that I did.
# You are free to ignore this, fork my project and make your own thing where you actually use imports if it ever bothers you that much to package all of the code into a final single file addon.

# endregion

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
        mcow_debug_log("Data successfully generated!")
        mcow_debug_log(f"Generated File : ( name = \"{out_filename}\", size = {size} bytes )")
    except Exception as e:
        mcow_debug_log(f"There was an error generating the output file: {e}")

def main():
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
        "../mcow/classes/Blender/Operators/Objects.py",
        "../mcow/classes/Blender/Operators/Scene.py",

        # Utility functions
        "../mcow/functions/utility/Utility.py", # TODO : Further subdivide this code maybe?

        # Export Data Generation (The 3 stages of data transformation pipeline for export in MagickCow: Blender Data -> Get Stage -> Generate Stage -> Make Stage -> Final JSON file)
        # TODO : Rename all of the Pipeline classes to use some "ExportPipeline" prefix or whatever...
        "../mcow/functions/generation/export/Get.py",
        "../mcow/functions/generation/export/Generate.py",
        "../mcow/functions/generation/export/Make.py",
        "../mcow/functions/generation/export/Pipeline.py",
        "../mcow/functions/generation/export/PipelineCache.py",
        
        # Import Data Generation
        "../mcow/functions/generation/import/Pipeline.py"

        # Main entry point
        "../mcow/Main.py",
    ]
    mcow_file_generate(ofilename, ifilenames)

if __name__ == "__main__":
    main()
