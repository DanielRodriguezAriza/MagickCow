# region Material Utility Functions

# NOTE : Magicka / XNA "Effects" are linked to Blender Materials on this Blender addon.

# NOTE : Here I'm sort of experimenting with static classes with @staticmethod to simulate namespaces in python... we'll see how it goes...
# Also going back to my snake_case C roots, which is more in line with PEP8. I'm just kind of tired of C#'s / Microsoft PascalCase I suppose.

class material_utility:
    
    # NOTE : The mesh param here is the same as obj, NOT obj.data!!!
    
    # region Blender Material

    # If the material does not exist, then we return None (null). Otherwise, we return the reference to the blender material itself.
    @staticmethod
    def get_material(obj, material_index):
        num_materials = len(obj.materials)
        if num_materials > 0:
            min_idx = 0
            max_idx = num_materials - 1
            if num_materials >= min_idx and num_materials <= max_idx:
                return obj.materials[material_idx]
        return None

    # endregion

    # region Material Name

    @staticmethod
    def get_material_name(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_name = get_material_name_instance(material) if material is not None else get_material_name_default(obj.magickcow_mesh_type)

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
    def get_material_name_instance(material):
        return material.name

    # endregion

    # region Material Data

    @staticmethod
    def get_material_data(material, fallback_type = "GEOMETRY"):
        ans = {}
        material_mode = material.mcow_effect_mode
        if material_mode == "DOC":
            # Get material data from JSON file
            ans = material_utility.get_material_data_instance_json(material)
        elif material_mode == "MAT":
            # Get material data from material panel
            ans = material_utility.get_material_data_instance_blend(material)
        if len(ans) <= 0:
            ans = material_utility.get_material_data_default(fallback_type)
        return ans
    
    @staticmethod
    def get_material_data_default(fallback_type = "GEOMETRY"):
        pass
    
    @staticmethod
    def get_material_data_instance_json(material):
        ans = get_json_object(material_utility.get_material_path(material))
        return ans
    
    @staticmethod
    def get_material_data_instance_blend(material):
        # TODO : Implement for each of the material types! You'll basically just need to extract the values from the blender panel and then arrange them in a json-like python dict.
        ans = None
        return ans

    # endregion

    # region Material Path

    @staticmethod
    def get_material_path(material):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, material.mcow_effect_path)
        if not ans.endswith(".json")
            ans = ans + ".json"
        return ans

    # endregion

# endregion
