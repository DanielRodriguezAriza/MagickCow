import bpy

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
    # TODO : Implement
    pass

def unregister_custom_startup_file():
    # TODO : Implement
    pass

def register():
    register_custom_startup_file()

def unregister():
    unregister_custom_startup_file()

if __name__ == "__main__":
    register()
