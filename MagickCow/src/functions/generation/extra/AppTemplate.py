# region startup template

# NOTE : The "register" and "unregister" notation here is kinda weird since
# we're doing some non standard file IO to add and remove the startup files
# when installing and uninstalling mcow.

# NOTE : In the future, if I add more startup scenes for different types of objects
# (eg: Magicka LevelModel, Magicka CharacterModel, Magicka PhysicsEntity, etc...),
# then I will need to delete all of the subdirectories by name, one by one, as each template requires its own dir.
# This maybe could benefit from some generalization in the implementation of the registration and unregistration logic.
# But this is OK for now.

def register_startup_app_templates():
    path_addon = os.path.dirname(__file__)
    path_local = bpy.utils.script_path_user()

    path_addon_startup = os.path.join(path_addon, "data", "startup")
    path_local_startup = os.path.join(path_local, "startup")

    # print(f"Path Addon: {path_addon_startup}")
    # print(f"Path Local: {path_local_startup}")

    shutil.copytree(path_addon_startup, path_local_startup, dirs_exist_ok=True)

def unregister_startup_app_templates():
    path_to_remove = os.path.join(bpy.utils.script_path_user(), "startup", "bl_app_templates_user", "Magicka")

    # print(f"The path to remove is : {path_to_remove}")

    shutil.rmtree(path_to_remove)

# endregion
