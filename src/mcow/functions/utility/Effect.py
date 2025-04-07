# region Material Utility Functions

# NOTE : Magicka / XNA "Effects" are linked to Blender Materials on this Blender addon.

def utility_get_effect_name(mesh, material_index):
    material_name = mesh.materials[material_index].name if len(mesh.materials) > 0 else utility_get_effect_name_default(mesh.magickcow_mesh_type)
    return material_name

def utility_get_effect_name_default(fallback_type = "GEOMETRY"):
    ans = "base/default"

    if fallback_type == "GEOMETRY":
        ans = "base/default_geometry"
    elif fallback_type == "WATER":
        ans = "base/default_water"
    elif fallback_type == "LAVA":
        ans = "base/default_lava"
    elif fallback_type == "FORCE_FIELD":
        ans = "base/ff/default_force_field"

    return ans

# TODO : Implement
def utility_get_effect_data(material):
    ans = {}
    if material.mcow_effect_mode == "DOC":
        # Get material data from JSON
        ans = get_json_object(material.)
    else:
        # Get material data from material panel
        pass
    return ans

# endregion
