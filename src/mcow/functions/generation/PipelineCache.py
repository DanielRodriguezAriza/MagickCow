# region Pipeline Cache Classes

# The classes within this region correspond to cache dicts and other cache objects that must be shared across different steps of the pipeline.

# TODO : Implement logic for adding and getting shared resources and effects
# TODO : Add the remaining functions LOL (eg: the ones used within the _create_default_values_effects() method)
class MCow_Data_Pipeline_Cache:
    
    # region Constructor
    
    def __init__(self):
        self._cache_shared_resources = {} # Cache Dictionary for Shared Resources generated
        self._cache_generated_effects = {} # Cache Dictionary for Material Effects generated

    # endregion

    # region Private Methods

    def _create_default_values(self):
        self._create_default_values_effects() # Initialize the values for the Material Effects cache with default values
    
    def _create_default_values_effects(self, effect_types = ["GEOMETRY", "WATER", "LAVA"]):
        # region Comment

        # Cached Effects Initialization
        # Setup all default material data beforehand (not required as the process would still work even if this was not done, but whatever... basically this works as a sort of precaching, but since it is
        # not compiletime because this is not C, there really is not much point ot it, altough maybe making the dict with self.dict_effects = {"base/whatever" : {blah blah blah...}, ...} could actually
        # be faster in future versions of Python, idk)

        # endregion
        for effect_type in effect_types:
            self._cache_generated_effects[self._create_default_effect_name(effect_type)] = self._create_default_effect_data(current_type)
    
    # endregion

    # region Public Methods - Shared Resources

    def add_shared_resource(self, resource_name, resource_content):
        if resource_name not in self._cache_shared_resources:
            num_resources = len(self._cache_shared_resources)
            resource_index = num_resources + 1 # Use the current count of resources as the index of each element (note that indices for shared resources in XNB files start at 1, not 0)
            self._cache_shared_resources[resource_name] = (resource_index, resource_content) # Store the resource index and its contents
            return resource_index
        else: # If the resource was already within the list, we don't add it again, we just return the index
            idx, content = self.dict_shared_resources[resource_name]
            return idx

    def get_shared_resource(self, resource_name):
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return (idx, content)
        return (0, None) # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    def get_shared_resource_index(self, resource_name):
        # NOTE : Same as the get function, but instead of returning the content, we only return the index.
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return idx
        return 0 # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    def make_shared_resources_list(self):
        ans = []
        for key, resource in self._cache_shared_resources.items():
            idx, content = resource
            ans.append(content)
        return ans
    
    # endregion

    # region Public Methods - Material Effects

    # region Comment - get_material_path
    # Returns the full path for a given material file. It does not check in the file system, all it does is append the selected path for material files to the given blender material name.
    # Automatically appends the ".json" extension if the material name does not end in ".json" to ensure that the correct file name is generated.
    # All validity checkign is performed later, when the actual contents of the file are retrieved, where the system checks for whether this file exists or not.
    # endregion
    def get_material_path(self, matname):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, matname)
        if ans.endswith(".json"):
            return ans
        return ans + ".json"

    # region Comment - get_material_name
    # Gets the full material name used on a mesh. This full name corresponds to the full path + filename of the JSON file that corresponds to the effect represented by the material's name.
    # If the mesh does not have a material assigned, it uses as material name the name "base/default"
    # endregion
    def get_material_name(self, obj, material_index = 0):
        # Get mesh
        mesh = obj.data
        
        # Get material name
        matname = mesh.materials[material_index].name if len(mesh.materials) > 0 else self.generate_default_effect_name(mesh.magickcow_mesh_type)
        matname = self.get_material_path(matname)
        
        return matname
    
    # region Generate Material / Effect Data Functions
    
    # These are literally bordering the edge between the "make" and "generate" stages, since it returns a JSON-like dict object...
    # They used to be part of the make stage, so all file reading was done there and data generation was uninterrupted, but the shared_object stuff is now done in the generate stage so we have to move this somewhere...
    
    # TODO : Implement something similar to what the following comment says...
    # The good thing about putting it in this stage is that at least it is easier to make this generation dependant on the default collision channel or something fancy like that, so it becomes easier to
    # quickly debug a map without having it all look like stone...

    def generate_default_effect_name(self, fallback_type = "GEOMETRY"):
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

    def generate_default_effect_data(self, fallback_type = "GEOMETRY"):
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
    
    def generate_effect_data(self, mat_file_name, fallback_type = "GEOMETRY"):
        ans = get_json_object(mat_file_name)
        if len(ans) > 0:
            return ans
        return self.generate_default_effect_data(fallback_type)

    # endregion

    # Creates material data.
    # If the material is created for the first time, it is loaded from the JSON file containing its data, and the result is cached for future uses.
    # If the material had already been created before, it uses the previously cached result to prevent having to load the file multiple times.
    # This way, multiple disk accesses are prevented when loading the same material / effect multiple times.
    def create_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name not in self.dict_effects:
            self.dict_effects[material_name] = self.generate_effect_data(material_name, fallback_type)

    # Gets the material from the materials dictionary. Used in the make stage.
    # If for some reason the material were to not have been created previously (could only happen if there were some bug in the code that would need to be fixed ASAP),
    # then it would just re-generate the default effect data based on the fallback type. That feature exists as a last measure and we should not rely on it to export working files!!! 
    def get_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name in self.dict_effects:
            return self.dict_effects[material_name]
        return self.generate_default_effect_data(fallback_type)

    # endregion


# endregion
