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
def mcow_utility_append_blender_group_nodes_with_override(path, link = False):
    # List with pairs of node group names. Used to associate the old group node name to the new group node name when swapping them out for the overriding
    node_groups_names_pairs = []

    # Open the library file and start reading the data streams
    with bpy.data.libraries.load(path, link = link) as (data_from, data_to):
        # For each group node that we want to import, rename the old group node to avoid collisions and preserving the old name
        # And then store all the (old data block, new data block) pairs by name to the list of group nodes that we want to override
        for new_node_group in data_from.node_groups:
            old_node_group = bpy.data.node_groups.get(new_node_group)
            if old_node_group is not None:
                old_node_group.name = old_node_group.name + "_OLD" # Basically just ensure that there are no name collisions
                node_groups_names_pairs.append((old_node_group.name, new_node_group))

        # Add all of the new imported data to the scene.
        # No data block renaming takes place because we already ensured that there are no name collisions before importing any data at all.
        data_to.node_groups = data_from.node_groups

    # Delete the old data blocks and remap the users of the old data blocks to the new data blocks we've just imported.
    # NOTE : This is done outside of the "with" block because ONLY after going out of that block's scope are the data blocks actually appended to the scene.
    for node_group_name_pair in node_groups_names_pairs:
        old_name, new_name = node_group_name_pair
        old_node = bpy.data.node_groups[old_name]
        new_node = bpy.data.node_groups[new_name]
        old_node.user_remap(new_node)
        bpy.data.node_groups.remove(old_node)

# endregion
