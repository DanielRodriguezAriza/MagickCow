# region startup template

# NOTE : The "register" and "unregister" notation here is kinda weird since
# we're doing some non standard file IO to add and remove the startup files
# when installing and uninstalling mcow.

# NOTE : In the future, if I add more startup scenes for different types of objects
# (eg: Magicka LevelModel, Magicka CharacterModel, Magicka PhysicsEntity, etc...),
# then I will need to delete all of the subdirectories by name, one by one, as each template requires its own dir.
# This maybe could benefit from some generalization in the implementation of the registration and unregistration logic.
# But this is OK for now.

# NOTE : Originally, the addon was going to be fully in charge of automatically generating and deleting stuff such as
# scene template files.
# The template files would be created on install, when register() was called, and then they would be removed on uninstall, when unregister() was called.
# Obviously this has an issue, which is that Blender calls unregister() on multiple points.
#
# First, unregister() is called when the addon is uninstalled. It is also called when the addon is disabled. But, the issue comes into play when you realize
# that unregister() is also called when the scene is reloaded, aka, whenever you create a new empty scene or load another scene file.
# This means that when using the custom template files with this automatic clean up logic, we'd run into a race condition, where sometimes Blender loads
# the files faster than they are deleted, so no issue, and sometimes the files would be deleted first, so Blender would always report that the template file
# is missing. When you check the files with a file explorer, it all appears to be just fine, and the files are there, because register() is called again
# afterward, so the template files are deleted and then re-generated, which is what leads to this race condition...
#
# This could be fixed if Blender offered a way to know what the origin of the unregister() call is. Since that does not exist, then we need to offer a manual
# interface for users to create and delete the template files.
# This is the same idea for the whole asset generation button which would be in charge of generating an asset library with meshes extracted from decompiled
# vanilla Magicka game maps. Doing this process automatically would be way heavier, and it makes no sense to do it on every single register call.
#
# Since register and unregister are called many times, this type of heavy operations are best left to user input in Blender, tho it would be really nice to
# have them be automatic...

def register_startup_app_templates():
    path_addon = os.path.dirname(__file__)
    path_local = bpy.utils.script_path_user()

    path_addon_startup = os.path.join(path_addon, "data", "startup")
    path_local_startup = os.path.join(path_local, "startup")

    # print(f"Path Addon: {path_addon_startup}")
    # print(f"Path Local: {path_local_startup}")

    shutil.copytree(path_addon_startup, path_local_startup, dirs_exist_ok=True)

def unregister_startup_app_templates():

    # Get the name of this addon's directory (this is the internal key used by Blender to refer to this addon)
    addon_name = os.path.basename(os.path.dirname(__file__))
    
    # If the addon is not within the list, then we unregistered the addon through an uninstall.
    # Otherwise, the addon was disabled (either by the user or by loading into a new scene, since Blender calls unregister() and
    # then register() again to reset the python environment when entering a new scene)
    if addon_name not in bpy.context.preferences.addons:
        path_to_remove = os.path.join(bpy.utils.script_path_user(), "startup", "bl_app_templates_user", "Magicka")
        # print(f"The path to remove is : {path_to_remove}")
        shutil.rmtree(path_to_remove)    
    
    # If we just disabled the addon but we didn't delete it, then we don't do anything harsh (no file deletion for scene app templates).
    # This is done to ensure that we don't try to delete the files during the the loading process.
    # If we deleted the generated scene files always, then we'd have a race condition where sometimes it would load just fine, and sometimes,
    # the unload call performed by Blender would cause the file to get deleted before we could put a lock on it and load it, causing the addon
    # to delete the scene before we could ever load it, which would simply get us to always see a warning report saying that the specified
    # template does not exist.

# endregion
