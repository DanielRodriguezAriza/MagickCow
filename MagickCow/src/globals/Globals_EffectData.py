#region Globals - Effect Data

# Dictionary of all default material effect configs for the default shader types supported by Magicka.
# Custom shaders and dict based shaders must be implemented by hand by users by writing directly the JSON data.
# This data is just for default values.

# NOTE : No default fallback for additive effects exists in JSON mode, since geometry objects can have both deferred effects and additive effects, and for performance and logical reasons,
# level geometry (mcow type "GEOMETRY") meshes with non-specified or non-valid materials are assumed to use deferred effects as fallback by default

MCOW_EFFECTS = {
    "GEOMETRY" : {
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
    },
    "WATER" : {
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
    },
    "LAVA" : {
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
    },
    "FORCE_FIELD" : {
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
}

# endregion
