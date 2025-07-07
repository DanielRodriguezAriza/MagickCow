import bpy
import os
import shutil

bl_info = {
    "name" : "MagickCow Experimental Features Addon - Startup Scene",
    "blender" : (3, 0, 0),
    "category" : "Export",
    "description" : "Adds some experimental stuff to MagickCow",
    "author" : "potatoes",
    "version" : (1, 0, 0)
}

# NOTE : The "register" and "unregister" notation here is kinda weird since
# we're doing some non standard file IO to add and remove the startup files
# when installing and uninstalling mcow.

def register_custom_startup_file():
    path_addon = os.path.dirname(__file__)
    path_local = bpy.utils.script_path_user()

    path_addon_startup = os.path.join(path_addon, "startup")
    path_local_startup = os.path.join(path_addon, "startup")

    shutil.copytree(path_addon_startup, path_local_startup)

def unregister_custom_startup_file():
    path_to_remove = os.path.join(bpy.utils.script_path_user(), "startup", "bl_app_templates_user", "Magicka")
    shutil.rmtree(path_to_remove)

def register():
    register_custom_startup_file()

def unregister():
    unregister_custom_startup_file()

if __name__ == "__main__":
    register()
