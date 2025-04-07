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
        # Default effect (for now it is the same as the one found within the "GEOMETRY" case)
        ans = {
            "$type": "effect_deferred",
            "Alpha": 0.400000006,
            "Sharpness": 1,
            "VertexColorEnabled": False,
            "UseMaterialTextureForReflectiveness": False,
            "ReflectionMap": "",
            "DiffuseTexture0AlphaDisabled": True,
            "AlphaMask0Enabled": False,
            "DiffuseColor0": {
                "x": 1,
                "y": 1,
                "z": 1
            },
            "SpecAmount0": 0,
            "SpecPower0": 20,
            "EmissiveAmount0": 0,
            "NormalPower0": 1,
            "Reflectiveness0": 0,
            "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
            "MaterialTexture0": "",
            "NormalTexture0": "",
            "HasSecondSet": False,
            "DiffuseTexture1AlphaDisabled": False,
            "AlphaMask1Enabled": False,
            "DiffuseColor1": None,
            "SpecAmount1": 0,
            "SpecPower1": 0,
            "EmissiveAmount1": 0,
            "NormalPower1": 0,
            "Reflectiveness1": 0,
            "DiffuseTexture1": None,
            "MaterialTexture1": None,
            "NormalTexture1": None
        }
        if fallback_type == "GEOMETRY":
            ans = {
                "$type": "effect_deferred",
                "Alpha": 0.400000006,
                "Sharpness": 1,
                "VertexColorEnabled": False,
                "UseMaterialTextureForReflectiveness": False,
                "ReflectionMap": "",
                "DiffuseTexture0AlphaDisabled": True,
                "AlphaMask0Enabled": False,
                "DiffuseColor0": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "SpecAmount0": 0,
                "SpecPower0": 20,
                "EmissiveAmount0": 0,
                "NormalPower0": 1,
                "Reflectiveness0": 0,
                "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
                "MaterialTexture0": "",
                "NormalTexture0": "",
                "HasSecondSet": False,
                "DiffuseTexture1AlphaDisabled": False,
                "AlphaMask1Enabled": False,
                "DiffuseColor1": None,
                "SpecAmount1": 0,
                "SpecPower1": 0,
                "EmissiveAmount1": 0,
                "NormalPower1": 0,
                "Reflectiveness1": 0,
                "DiffuseTexture1": None,
                "MaterialTexture1": None,
                "NormalTexture1": None
            }
        elif fallback_type == "WATER":
            ans = {
                "$type": "effect_deferred_liquid",
                "ReflectionMap": "",
                "WaveHeight": 1,
                "WaveSpeed0": {
                    "x": 0.00930232555,
                    "y": 0.0900000036
                },
                "WaveSpeed1": {
                    "x": -0.0046511637,
                    "y": 0.0883720964
                },
                "WaterReflectiveness": 0.216049388,
                "BottomColor": {
                    "x": 0.400000006,
                    "y": 0.400000006,
                    "z": 0.600000024
                },
                "DeepBottomColor": {
                    "x": 0.300000012,
                    "y": 0.400000006,
                    "z": 0.5
                },
                "WaterEmissiveAmount": 0.806896567,
                "WaterSpecAmount": 0.300000012,
                "WaterSpecPower": 24,
                "BottomTexture": "..\\Textures\\Surface\\Nature\\Ground\\rock_0",
                "WaterNormalMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "IceReflectiveness": 0,
                "IceColor": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "IceEmissiveAmount": 0,
                "IceSpecAmount": 1,
                "IceSpecPower": 20,
                "IceDiffuseMap": "..\\Textures\\Surface\\Nature\\Ground\\ice02_0",
                "IceNormalMap": "..\\Textures\\Liquids\\IceNrm_0"
            }
        elif fallback_type == "LAVA":
            ans = {
                "$type" : "effect_lava",
                "MaskDistortion" : 0.2,
                "Speed0" : {
                    "x" : 0.5,
                    "y" : 0.5
                },
                "Speed1" : {
                    "x" : 0.03,
                    "y" : 0.03
                },
                "LavaHotEmissiveAmount" : 3.0,
                "LavaColdEmissiveAmount" : 0.0,
                "LavaSpecAmount" : 0.0,
                "LavaSpecPower" : 20.0,
                "TempFrequency" : 0.5586,
                "ToneMap" : "..\\Textures\\Liquids\\LavaToneMap_0",
                "TempMap" : "..\\Textures\\Liquids\\LavaBump_0",
                "MaskMap" : "..\\Textures\\Liquids\\lavaMask_0",
                "RockColor" : {
                    "x" : 1,
                    "y" : 1,
                    "z" : 1
                },
                "RockEmissiveAmount" : 0.0,
                "RockSpecAmount" : 0.0,
                "RockSpecPower" : 20.0,
                "RockNormalPower" : 1.0,
                "RockTexture" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_0",
                "RockNormalMap" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_NRM_0"
            }
        elif fallback_type == "FORCE_FIELD":
            ans = {
                "color" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "width" : 0.5,
                "alphaPower": 4,
                "alphaFalloffPower" : 2,
                "maxRadius" : 4,
                "rippleDistortion" : 2,
                "mapDistortion" : 0.53103447,
                "vertexColorEnabled": False,
                "displacementMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "ttl": 1
            }
        return ans

    @staticmethod
    def get_material_data_instance(material):
        if material.mcow_effect_mode == "DOC":
            return material_utility.get_material_data_instance_json(material)
        else:
            return material_utility.get_material_data_instance_blend(material)

    @staticmethod
    def get_material_data_instance_json(material):
        ans = get_json_object(material_utility.get_material_path(material))
        return ans
    
    @staticmethod
    def get_material_data_instance_blend(material):
        # TODO : Implement for each of the material types! You'll basically just need to extract the values from the blender panel and then arrange them in a json-like python dict.
        ans = {}
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
