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

# Append the material group nodes stored within the specified blender file to the current one
def mcow_utility_append_blender_group_nodes(path, link = False):
    with bpy.data.libraries.load(path, link = link) as (data_from, data_to):
        data_to.node_groups = data_from.node_groups

# Append the material group nodes stored within the specified blender file to the current one with override (those whose name are shared will be overwritten with the new data)
def mcow_utility_append_blender_group_nodes(path, link = False):
    
    with bpy.data.libraries.load(path, link = link) as (data_from, data_to):

        node_groups_names_pairs = []

        for new_node_group in data_from.node_groups:
            old_node_group = bpy.data.node_groups.get(new_node_group.name)
            if node is not None:
                old_node_group.name = old_node_group.name + "_OLD"
                node_groups_names_pairs.append((old_node_group.name, new_node_group.name))

        data_to.node_groups = data_from.node_groups

        for node_group_name_pair in node_groups_names_pairs:
            old_name, new_name = node_group_name_pair
            old_node = bpy.data.node_groups[old_name]
            new_node = bpy.data.node_groups[new_name]
            old_node.user_remap(new_node)
            bpy.data.node_groups.remove(old_node)

# endregion
