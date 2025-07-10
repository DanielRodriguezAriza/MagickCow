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

    # This is the top level function for getting material data.
    # All other functions are "internal" methods that should be called by this one.
    # Users call this function, and whatever internal processing is required will be performed automatically by its internal logic and call stack.
    # TODO : Clean up this messy implementation in the future... this is pretty shit ngl.
    @staticmethod
    def get_material_data(material, fallback_type = "GEOMETRY"):
        try: # This try is here just in case we have an exception when loading the JSON data. That way, we can silently fail by just skipping to using the default generated data instead.
        
            # If the material is valid, then generate data from the material instance
            if material is not None:
                ans = material_utility.get_material_data_instance(material)
            
            # If the length of the generated dict is 0, then that means that we did not generate a proper dict
            if len(ans) <= 0:
                raise Exception("")

            # If the generated dict is not empty, then that means we successfully found data within this object, so we use this
            return ans

        except Exception as e:

            # Otherwise, that means that the data within those files was not found or was not a proper json structure, so we discard it and generate a default material instead.
            # NOTE : This means that we "silently fail" in the sense that non-valid material effects will be converted to valid ones, but not necessarily the one we wanted.
            # TODO : In the future, maybe add a warning or something like that?
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
        # NOTE : "Classic" mode. This is the first one that was ever implemented.
        # Loads the data from a file on disk.
        ans = get_json_object(material_utility.get_material_path(material))
        return ans
    
    @staticmethod
    def get_material_data_instance_mat_dict(material):
        # TODO : Implement for each of the material types! You'll basically just need to extract the values from the blender panel and then arrange them in a json-like python dict.
        ans = {}
        return ans
    
    @staticmethod
    def get_material_data_instance_mat_json(material):
        # NOTE : This is literally the most easy to implement out of them all, as well as the most generic with support for any new type of custom dict-based, user-defined materials in the future.
        # Just return the Json stored within the text data block as a dict and call it a day.
        ans = get_material_text(material)
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

    # region Material Text Data Block

    @staticmethod
    def get_material_text(material):
        text_data_block = material.mcow_effect_text
        ans_str = "{}"
        if text_data_block is not None:
            ans_str = text_data_block.to_string()
        ans_dict = json.loads(ans_str)
        return ans_dict
    
    # endregion

# endregion
