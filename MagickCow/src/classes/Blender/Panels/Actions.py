# region MagickCow Actions - Operators

# region Comment - Scene Templates

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

# endregion

class MagickCow_OT_Action_InstallTemplates(bpy.types.Operator):
    bl_idname = "magickcow.action_install_templates"
    bl_label = "Install Templates"
    def execute(self, context):
        try:
            mcow_action_install_templates()
            self.report({"INFO"}, "Successfully installed scene templates!")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, "Failed to install scene templates!")
            return {"CANCELLED"}

def mcow_action_install_templates():
    path_addon = os.path.dirname(__file__)
    path_local = bpy.utils.script_path_user()

    path_addon_startup = os.path.join(path_addon, "data", "startup")
    path_local_startup = os.path.join(path_local, "startup")

    # print(f"Path Addon: {path_addon_startup}")
    # print(f"Path Local: {path_local_startup}")

    shutil.copytree(path_addon_startup, path_local_startup, dirs_exist_ok=True)

class MagickCow_OT_Action_UninstallTemplates(bpy.types.Operator):
    bl_idname = "magickcow.action_uninstall_templates"
    bl_label = "Uninstall Templates"
    def execute(self, context):
        try:
            mcow_action_uninstall_templates()
            self.report({"INFO"}, "Successfully uninstalled scene templates!")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, "Failed to uninstall scene templates!")
            return {"CANCELLED"}

def mcow_action_uninstall_templates():
    path_to_remove = os.path.join(bpy.utils.script_path_user(), "startup", "bl_app_templates_user", "Magicka")
    # print(f"The path to remove is : {path_to_remove}")
    shutil.rmtree(path_to_remove)

class MagickCow_OT_Action_GenerateAssetLibrary(bpy.types.Operator):
    bl_idname = "magickcow.action_generate_asset_library"
    bl_label = "Generate Vanilla Assets"
    def execute(self, context):
        self.report({"ERROR"}, "This feature is not implemented yet!")
        return {"CANCELLED"}

def mcow_action_generate_asset_library():
    # TODO : Implement
    pass

# TODO : Add an operator for every single other type of scene model (Physics Entities, Character Models, etc...)
# Basically, just have this evolve as time goes on...
class MagickCow_OT_Action_AppendBlendFile_Example_LevelModel(bpy.types.Operator):
    bl_idname = "magickcow.action_generate_blend_file_example_level_model"
    bl_label = "Generate Level Model"
    def execute(self, context):
        return mcow_action_append_blend_file_example(self, "Level Model", "level_model.blend")

def mcow_action_append_blend_file_example_internal(file_name):
    # Compute the path where the blend file is located
    path_addon = os.path.dirname(__file__)
    path_file = os.path.join(path_addon, "data", "examples", file_name)

    # Append the scene data from the selected blend file to the current scene
    mcow_utility_append_blender_scene(path_file)

def mcow_action_append_blend_file_example(self, display_name, file_name):
    try:
        mcow_action_append_blend_file_example_internal(file_name)
        self.report({"INFO"}, f"Successfully loaded \"{display_name}\" example scene!")
        return {"FINISHED"}
    except Exception as e:
        self.report({"ERROR"}, f"Failed to load \"{display_name}\" example scene!")
        return {"CANCELLED"}

def register_actions_operators():
    bpy.utils.register_class(MagickCow_OT_Action_InstallTemplates)
    bpy.utils.register_class(MagickCow_OT_Action_UninstallTemplates)
    bpy.utils.register_class(MagickCow_OT_Action_GenerateAssetLibrary)
    bpy.utils.register_class(MagickCow_OT_Action_AppendBlendFile_Example_LevelModel)

def unregister_actions_operators():
    bpy.utils.unregister_class(MagickCow_OT_Action_InstallTemplates)
    bpy.utils.unregister_class(MagickCow_OT_Action_UninstallTemplates)
    bpy.utils.unregister_class(MagickCow_OT_Action_GenerateAssetLibrary)
    bpy.utils.unregister_class(MagickCow_OT_Action_AppendBlendFile_Example_LevelModel)

# endregion

# region MagickCow Actions - N-Key Panel

# This class is the one that controls the N-Key panel for MagickCow Actions.
class OBJECT_PT_MagickCowActionsPanel(bpy.types.Panel):

    bl_label = "MagickCow Actions"
    bl_idname = "OBJECT_PT_MagickCowActions_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MagickCow"

    def draw(self, context):
        layout = self.layout
        
        # layout.label(text = "No available actions yet!")

        # App templates handler menu ("scene prefabs / presets")
        boxA = layout.box()
        boxA.label(text="Scene Templates Generator")
        boxA.operator("magickcow.action_install_templates")
        boxA.operator("magickcow.action_uninstall_templates")

        # Create .blend files with example scenes
        boxA = layout.box()
        boxA.label(text="Example Scene Generator")
        boxA.operator("magickcow.action_generate_blend_file_example_level_model")

        # Asset library generator menu (create assets library from Magicka files, etc...)
        boxB = layout.box()
        boxB.label(text="Vanilla Assets Generator")
        boxB.operator("magickcow.action_generate_asset_library")

def register_actions_panel():
    bpy.utils.register_class(OBJECT_PT_MagickCowActionsPanel)

def unregister_actions_panel():
    bpy.utils.unregister_class(OBJECT_PT_MagickCowActionsPanel)

# endregion

# region MagickCowA Actions - Register Functions

# This region contains the top-level function to register and unregister all MagickCow Actions related classes, data and properties.
# Each sub-category implements its own pair of register and unregister functions.
# These top-level functions simply serves as an abstraction to call the ones from the sub-categories.

def register_actions():
    register_actions_operators()
    register_actions_panel()

def unregister_actions():
    unregister_actions_operators()
    unregister_actions_panel()

# endregion
