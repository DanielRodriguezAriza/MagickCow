# region Material Utility Functions

# NOTE : Magicka / XNA "Effects" are linked to Blender Materials on this Blender addon.

# NOTE : Here I'm sort of experimenting with static classes with @staticmethod to simulate namespaces in python... we'll see how it goes...
# Also going back to my snake_case C roots, which is more in line with PEP8. I'm just kind of tired of C#'s / Microsoft PascalCase I suppose.

class material_utility:
    
    # NOTE : The obj param is the blender Object param.
    # NOTE : The mesh param is the mesh data, aka, obj.data.
    # Basically, the nomenclature used here is the same as everywhere else. At some point in history it was not, but do not get confused, because now it is! Just keep that in mind or things will go south real fast...
    
    # region Blender Material

    # If the material does not exist, then we return None (null). Otherwise, we return the reference to the blender material instance itself.
    @staticmethod
    def get_material(obj, material_index):
        num_materials = len(obj.data.materials)
        if num_materials > 0:
            min_idx = 0
            max_idx = num_materials - 1
            if material_index >= min_idx and material_index <= max_idx:
                return obj.data.materials[material_index]
        return None

    # endregion

    # region Material Info / All Material Data (basically, get both the name and the data generated in one go with these functions)

    # NOTE : Basically, these are the top-level functions that you should try to use most of the time.

    @staticmethod
    def get_material_effect_info(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_name = material_utility.get_material_name(material, obj.data.magickcow_mesh_type)
        material_data = material_utility.get_material_data(material, obj.data.magickcow_mesh_type)
        return (material_name, material_data)

    @staticmethod
    def get_material_name_from_mesh(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_name = material_utility.get_material_name(material, obj.data.magickcow_mesh_type)
        return material_name
    
    @staticmethod
    def get_material_data_from_mesh(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_data = material_utility.get_material_data(material, obj.data.magickcow_mesh_type)
        return material_data

    # endregion

    # region Material Name

    @staticmethod
    def get_material_name(material, fallback_type = "GEOMETRY"):
        if material is not None:
            return material_utility.get_material_name_instance(material)
        else:
            return material_utility.get_material_name_default(fallback_type)

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
        if material is not None:
            return material_utility.get_material_data_instance(material)
        else:
            return material_utility.get_material_data_default(fallback_type)
    
    @staticmethod
    def get_material_data_default(fallback_type = "GEOMETRY"):
        ans = MCOW_EFFECTS[fallback_type]
        return ans

    @staticmethod
    def get_material_data_instance(material):
        mode = material.mcow_effect_mode
        if mode == "DOC_JSON":
            return material_utility.get_material_data_instance_doc_json(material)
        elif mode == "MAT_DICT":
            return material_utility.get_material_data_instance_mat_dict(material)
        elif mode == "MAT_JSON":
            return material_utility.get_material_data_instance_mat_json(material)

    @staticmethod
    def get_material_data_instance_doc_json(material):
        ans = get_json_object(material_utility.get_material_path(material))
        return ans
    
    @staticmethod
    def get_material_data_instance_mat_dict(material):
        # TODO : Implement for each of the material types! You'll basically just need to extract the values from the blender panel and then arrange them in a json-like python dict.
        ans = {}
        return ans
    
    @staticmethod
    def get_material_data_instance_mat_json(material):
        # NOTE : This is literally the most easy to implement out of them all. Just return the inline JSON and call it a day.
        ans = material.mcow_effect_json
        return ans

    # endregion

    # region Material Path

    @staticmethod
    def get_material_path(material):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, material.mcow_effect_path)
        if not ans.endswith(".json"):
            ans = ans + ".json"
        return ans

    # endregion

# endregion
