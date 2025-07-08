#region Base Path Operations

# Function to get the base path.
# Only useful when creating a new Magicka-type scene with the custom made app template scenes, since in every single other instance, relative paths should be used automatically.
# This function internally checks if the scene path override is enabled. That way, you can have both a global base path and a scene specific base path.

# TODO : Figure out how to properly implement this whole logic, or if it even makes sense in the first place...

def mcow_base_path_get():
    if bpy.context.scene.mcow_scene_base_path_override_enabled:
        return bpy.context.scene.mcow_scene_base_path
    return bpy.context.scene.mcow_scene_base_path

# endregion
