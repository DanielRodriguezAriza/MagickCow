# region Blender related Utility Functions

# Append the specified blender file to the current scene
def mcow_utility_append_blender_scene(path, link = False):
    # Select all of the data we want to extract from the blend file
    with bpy.data.libraries.load(path, link = link) as (data_from, data_to):
        data_to.objects = data_from.objects

    # Append it to the current scene
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

# endregion
