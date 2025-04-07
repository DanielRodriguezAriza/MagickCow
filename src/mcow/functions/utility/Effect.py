# region Material Utility Functions

# NOTE : Magicka / XNA "Effects" are linked to Blender Materials on this Blender addon.

# NOTE : Here I'm sort of experimenting with static classes with @staticmethod to simulate namespaces in python... we'll see how it goes...
# Also going back to my snake_case C roots, which is more in line with PEP8. I'm just kind of tired of C#'s / Microsoft PascalCase I suppose.

def class material_utility:
    
    # NOTE : The mesh param here is the same as obj, NOT obj.data!!!
    
    @staticmethod
    def get_material_name(mesh, material_index):
        material_name = mesh.materials[material_index].name if len(mesh.materials) > 0 else MaterialUtility.get_material_name_default(mesh.magickcow_mesh_type)
        return material_name

    @staticmethod
    def get_material_name_default(fallback_type = "GEOMETRY"):
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

    @staticmethod
    def get_material_data(material):
        ans = {}
        if material.mcow_effect_mode == "DOC":
            # Get material data from JSON
            ans = get_json_object(material.)
        else:
            # Get material data from material panel
            pass
        return ans

# endregion
