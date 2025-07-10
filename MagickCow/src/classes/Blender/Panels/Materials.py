# region Blender Panel classes, register and unregister functions for MagickCow material properties handling

# NOTE : The Water / Lava distinction does not exist on the properties for geometry but it does exist for materials
# That is because within Magicka's code, both water and lava behave differently, but both instantiate geometry of type liquid, and the behaviour changes according to whether they use a water or lava effect (material).
# As for materials, there needs to be a distinction because the type of the class used for the material effect is different.
# Maybe in the future I could improve the behaviour so that less edge cases exist where users can input wrong data (eg: deffered effect / geometry material for a geometry marked as liquid, that would crash, but the UI allows it...)

# region Panel Class

class MATERIAL_PT_MagickCowPanel(bpy.types.Panel):
    bl_label = "MagickCow Material Properties"
    bl_idname = "MATERIAL_PT_custom_panel_mcow"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    bl_options = {"DEFAULT_CLOSED"} # The panel will be closed by default when the addon is installed
    bl_order = 0 # The panel will be added at the very top by default. The user can manually change this by dragging it down on their own, but this should make it easier to find the mcow material props.

    # The poll() method controls the drawing of the panel itself under the materials panel
    @classmethod
    def poll(cls, context):
        return context.material is not None # Only show the panel if the material exists. If no materials exist on a given mesh, then this check prevents the panel from being drawn (note that if it were to be drawn, it would be an empty panel with no props, as no material exists and the props themselves already take care of not drawing themselves if the material is null to prevent null dereferences)

    # The draw() method controls the drawing logic for individual properties
    def draw(self, context):
        layout = self.layout
        material = context.material
        if material:
            material_mode = material.mcow_effect_mode
            material_type = material.mcow_effect_type

            layout.prop(material, "mcow_effect_mode")

            if material_mode == "DOC_JSON":
                layout.prop(material, "mcow_effect_path")
            elif material_mode == "MAT_DICT":
                layout.prop(material, "mcow_effect_type")
                if material_type == "EFFECT_DEFERRED":
                    self.draw_effect_deferred(layout, material)
                elif material_type == "EFFECT_LIQUID_WATER":
                    self.draw_effect_water(layout, material)
                elif material_type == "EFFECT_LIQUID_LAVA":
                    self.draw_effect_lava(layout, material)
                elif material_type == "EFFECT_FORCE_FIELD":
                    self.draw_effect_force_field(layout, material)
                elif material_type == "EFFECT_ADDITIVE":
                    self.draw_effect_additive(layout, material)
            elif material_mode == "MAT_JSON":
                layout.prop(material, "mcow_effect_json")
    
    # From here on out, we have custom draw methods for each type of material
    def draw_effect_deferred(self, layout, material):
        layout.prop(material, "mcow_effect_deferred_alpha")
        layout.prop(material, "mcow_effect_deferred_sharpness")
        layout.prop(material, "mcow_effect_deferred_vertex_color_enabled")

        layout.prop(material, "mcow_effect_deferred_reflection_map_enabled")
        layout.prop(material, "mcow_effect_deferred_reflection_map")

        layout.prop(material, "mcow_effect_deferred_diffuse_texture_0_alpha_disabled")
        layout.prop(material, "mcow_effect_deferred_alpha_mask_0_enabled")
        layout.prop(material, "mcow_effect_deferred_diffuse_color_0")
        layout.prop(material, "mcow_effect_deferred_specular_amount_0")
        layout.prop(material, "mcow_effect_deferred_specular_power_0")
        layout.prop(material, "mcow_effect_deferred_emissive_amount_0")
        layout.prop(material, "mcow_effect_deferred_normal_power_0")
        layout.prop(material, "mcow_effect_deferred_reflection_intensity_0")
        layout.prop(material, "mcow_effect_deferred_diffuse_texture_0")
        layout.prop(material, "mcow_effect_deferred_material_texture_0")
        layout.prop(material, "mcow_effect_deferred_normal_texture_0")

        layout.prop(material, "mcow_effect_deferred_has_second_set")

        layout.prop(material, "mcow_effect_deferred_diffuse_texture_1_alpha_disabled")
        layout.prop(material, "mcow_effect_deferred_alpha_mask_1_enabled")
        layout.prop(material, "mcow_effect_deferred_diffuse_color_1")
        layout.prop(material, "mcow_effect_deferred_specular_amount_1")
        layout.prop(material, "mcow_effect_deferred_specular_power_1")
        layout.prop(material, "mcow_effect_deferred_emissive_amount_1")
        layout.prop(material, "mcow_effect_deferred_normal_power_1")
        layout.prop(material, "mcow_effect_deferred_reflection_intensity_1")
        layout.prop(material, "mcow_effect_deferred_diffuse_texture_1")
        layout.prop(material, "mcow_effect_deferred_material_texture_1")
        layout.prop(material, "mcow_effect_deferred_normal_texture_1")
    
    def draw_effect_water(self, layout, material):
        pass
    
    def draw_effect_lava(self, layout, material):
        pass
    
    def draw_effect_force_field(self, layout, material):
        layout.prop(material, "mcow_effect_force_field_color")
        layout.prop(material, "mcow_effect_force_field_width")
        layout.prop(material, "mcow_effect_force_field_alpha_power")
        layout.prop(material, "mcow_effect_force_field_alpha_fallof_power")
        layout.prop(material, "mcow_effect_force_field_max_radius")
        layout.prop(material, "mcow_effect_force_field_ripple_distortion")
        layout.prop(material, "mcow_effect_force_field_map_distortion")
        layout.prop(material, "mcow_effect_force_field_vertex_color_enabled")
        layout.prop(material, "mcow_effect_force_field_displacement_map")
        layout.prop(material, "mcow_effect_force_field_ttl")
    
    def draw_effect_additive(self, layout, material):
        layout.prop(material, "mcow_effect_additive_color_tint")
        layout.prop(material, "mcow_effect_additive_vertex_color_enabled")
        layout.prop(material, "mcow_effect_additive_texture_enabled")
        layout.prop(material, "mcow_effect_additive_texture")

# endregion

# region Register and Unregister Functions - Internal

def register_properties_material_text(material):
    pass

def unregister_properties_material_text(material):
    pass

def register_properties_material_generic(material):
    material.mcow_effect_type = bpy.props.EnumProperty(
        name = "Material Type",
        description = "Determines the type of this material",
        items = [
            ("EFFECT_DEFERRED", "Deferred", "Deferred material. Used for opaque objects. This is the default configuration for level geometry materials."),
            ("EFFECT_ADDITIVE", "Additive", "Additive material. Used for objects with transparency."), # NOTE : Be mindful of the performance impact of using additive (transparent) materials. Magicka suffers of overdraw issues with transparent materials, just like any other game engine.
            ("EFFECT_LIQUID_WATER", "Water", "Water material. Used for surfaces of type water."),
            ("EFFECT_LIQUID_LAVA", "Lava", "Lava material. Used for surfaces of type lava."),
            ("EFFECT_FORCE_FIELD", "Force Field", "Force Field material. Used for surfaces of type force field.")
        ],
        default = "EFFECT_DEFERRED" # This is the best default option for obvious reasons. First because of performance reasons. Second because most objects an user will add will be opaque level geometry, so this is the best default setting.
    )

    material.mcow_effect_mode = bpy.props.EnumProperty(
        name = "Origin Type",
        description = "Determines the type of origin for the configuration for this material",
        items = [
            ("DOC_JSON", "JSON Document", "The configuration for this material will be obtained from the selected JSON file."), # Origin : Json Document data.
            ("MAT_DICT", "Blender Material (Dictionary)", "The configuration for this material will be obtained from the material configuration as laid out on the Blender panel."), # Origin : Blender panel data. This is a sort of "inline dict" mode
            ("MAT_JSON", "Blender Material (inline JSON)", "The configuration for this material will be obtained from the material configuration as laid out on the inline JSON.") # Origin : Blender panel, inline JSON.
        ],
        default = "MAT_DICT"
    )

    material.mcow_effect_path = bpy.props.StringProperty(
        name = "Json Path",
        description = "Determines the path where the JSON file is located",
        default = ""
    )

    # NOTE : If this field could be made to be multiline in Blender, this would be the superior choice out of them all... but alas, the Blender Foundation has yet to figure out how to make fucking multiline
    # input text fields. This has literally been a topic of debate since 2014. How the fuck can we be living in the year 2025 and still not have official support for these on Blender, what the fuck.
    material.mcow_effect_json = bpy.props.StringProperty(
        name = "Json Data",
        description = "Determines the inline data for the material JSON",
        default = "",
    )

def unregister_properties_material_generic(material):
    del material.mcow_effect_type
    del material.mcow_effect_mode
    del material.mcow_effect_path

def register_properties_material_geometry(material): # NOTE : Maybe this should be renamed to deferred or something? we could also add transparent mats in the future I suppose.
    material.mcow_effect_deferred_alpha = bpy.props.FloatProperty(
        name = "Alpha",
        default = 0.4
    )

    material.mcow_effect_deferred_sharpness = bpy.props.FloatProperty(
        name = "Sharpness",
        default = 1.0
    )

    material.mcow_effect_deferred_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        default = False
    )

    material.mcow_effect_deferred_reflection_map_enabled = bpy.props.BoolProperty(
        name = "Reflection Map Enabled",
        default = False
    )

    material.mcow_effect_deferred_reflection_map = bpy.props.StringProperty(
        name = "Reflection Map",
        default = ""
    )

    material.mcow_effect_deferred_diffuse_texture_0_alpha_disabled = bpy.props.BoolProperty(
        name = "Diffuse Texture 0 Alpha Disabled",
        default = True
    )

    material.mcow_effect_deferred_alpha_mask_0_enabled = bpy.props.BoolProperty(
        name = "Alpha Mask 0 Enabled",
        default = False
    )

    material.mcow_effect_deferred_diffuse_color_0 = bpy.props.FloatVectorProperty(
        name = "Diffuse Color 0",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_deferred_specular_amount_0 = bpy.props.FloatProperty(
        name = "Specular Amount 0",
        default = 0
    )

    material.mcow_effect_deferred_specular_power_0 = bpy.props.FloatProperty(
        name = "Specular Power 0",
        default = 20
    )

    material.mcow_effect_deferred_emissive_amount_0 = bpy.props.FloatProperty(
        name = "Emissive Amount 0",
        default = 0
    )

    material.mcow_effect_deferred_normal_power_0 = bpy.props.FloatProperty(
        name = "Normal Power 0",
        default = 1
    )

    material.mcow_effect_deferred_reflection_intensity_0 = bpy.props.FloatProperty(
        name = "Reflection Intensity 0",
        default = 0
    )

    material.mcow_effect_deferred_diffuse_texture_0 = bpy.props.StringProperty(
        name = "Diffuse Texture 0",
        default = "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0"
    )

    material.mcow_effect_deferred_material_texture_0 = bpy.props.StringProperty(
        name = "Material Texture 0",
        default = ""
    )

    material.mcow_effect_deferred_normal_texture_0 = bpy.props.StringProperty(
        name = "Normal Texture 0",
        default = ""
    )

    material.mcow_effect_deferred_has_second_set = bpy.props.BoolProperty(
        name = "Has Second Set",
        default = False
    )

    material.mcow_effect_deferred_diffuse_texture_1_alpha_disabled = bpy.props.BoolProperty(
        name = "Diffuse Texture 1 Alpha Disabled",
        default = True
    )

    material.mcow_effect_deferred_alpha_mask_1_enabled = bpy.props.BoolProperty(
        name = "Alpha Mask 1 Enabled",
        default = False
    )

    material.mcow_effect_deferred_diffuse_color_1 = bpy.props.FloatVectorProperty(
        name = "Diffuse Color 1",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_deferred_specular_amount_1 = bpy.props.FloatProperty(
        name = "Specular Amount 1",
        default = 0.0
    )

    material.mcow_effect_deferred_specular_power_1 = bpy.props.FloatProperty(
        name = "Specular Power 1",
        default = 0.0
    )

    material.mcow_effect_deferred_emissive_amount_1 = bpy.props.FloatProperty(
        name = "Emissive Amount 1",
        default = 0.0
    )

    material.mcow_effect_deferred_normal_power_1 = bpy.props.FloatProperty(
        name = "Normal Power 1",
        default = 0.0
    )

    material.mcow_effect_deferred_reflection_intensity_1 = bpy.props.FloatProperty(
        name = "Reflection Intensity 1",
        default = 0.0
    )

    material.mcow_effect_deferred_diffuse_texture_1 = bpy.props.StringProperty(
        name = "Diffuse Texture 1",
        default = ""
    )

    material.mcow_effect_deferred_material_texture_1 = bpy.props.StringProperty(
        name = "Material Texture 1",
        default = ""
    )

    material.mcow_effect_deferred_normal_texture_1 = bpy.props.StringProperty(
        name = "Normal Texture 1",
        default = ""
    )

    # NOTE : On the GUI side, maybe expose these properties under the labels "texture set 0" and "texture set 1" or whatever the fuck so that we can have some better organization,
    # maybe even make the window expandable or whatever, or add an enabled / disabled option for the second texture / material info set. Something like "bool secondMaterialSetEnabled"...

def unregister_properties_material_geometry(material):
    del material.mcow_effect_deferred_alpha
    del material.mcow_effect_deferred_sharpness
    del material.mcow_effect_deferred_vertex_color_enabled

    del material.mcow_effect_deferred_reflection_map_enabled
    del material.mcow_effect_deferred_reflection_map

    del material.mcow_effect_deferred_diffuse_texture_0_alpha_disabled
    del material.mcow_effect_deferred_alpha_mask_0_enabled
    del material.mcow_effect_deferred_diffuse_color_0
    del material.mcow_effect_deferred_specular_amount_0
    del material.mcow_effect_deferred_specular_power_0
    del material.mcow_effect_deferred_emissive_amount_0
    del material.mcow_effect_deferred_normal_power_0
    del material.mcow_effect_deferred_reflection_intensity_0
    del material.mcow_effect_deferred_diffuse_texture_0
    del material.mcow_effect_deferred_material_texture_0
    del material.mcow_effect_deferred_normal_texture_0

    del material.mcow_effect_deferred_has_second_set

    del material.mcow_effect_deferred_diffuse_texture_1_alpha_disabled
    del material.mcow_effect_deferred_alpha_mask_1_enabled
    del material.mcow_effect_deferred_diffuse_color_1
    del material.mcow_effect_deferred_specular_amount_1
    del material.mcow_effect_deferred_specular_power_1
    del material.mcow_effect_deferred_emissive_amount_1
    del material.mcow_effect_deferred_normal_power_1
    del material.mcow_effect_deferred_reflection_intensity_1
    del material.mcow_effect_deferred_diffuse_texture_1
    del material.mcow_effect_deferred_material_texture_1
    del material.mcow_effect_deferred_normal_texture_1

def register_properties_material_water(material):
    pass

def unregister_properties_material_water(material):
    pass

def register_properties_material_lava(material):
    pass

def unregister_properties_material_lava(material):
    pass

def register_properties_material_force_field(material):
    material.mcow_effect_force_field_color = bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_force_field_width = bpy.props.FloatProperty(
        name = "Width",
        default = 0.5
    )

    material.mcow_effect_force_field_alpha_power = bpy.props.FloatProperty(
        name = "Alpha Power",
        default = 4
    )

    material.mcow_effect_force_field_alpha_fallof_power = bpy.props.FloatProperty(
        name = "Alpha Falloff Power",
        default = 2
    )

    material.mcow_effect_force_field_max_radius = bpy.props.FloatProperty(
        name = "Max Radius",
        default = 4
    )

    material.mcow_effect_force_field_ripple_distortion = bpy.props.FloatProperty(
        name = "Ripple Distortion",
        default = 2
    )

    material.mcow_effect_force_field_map_distortion = bpy.props.FloatProperty(
        name = "Map Distortion",
        default = 0.53103447
    )

    material.mcow_effect_force_field_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        default = True
    )

    material.mcow_effect_force_field_displacement_map = bpy.props.StringProperty(
        name = "Displacement Map",
        default = "..\\..\\Textures\\Liquids\\WaterNormals_0"
    )

    material.mcow_effect_force_field_ttl = bpy.props.FloatProperty(
        name = "Time",
        default = 1
    )

def unregister_properties_material_force_field(material):
    del material.mcow_effect_force_field_color
    del material.mcow_effect_force_field_width
    del material.mcow_effect_force_field_alpha_power
    del material.mcow_effect_force_field_alpha_fallof_power
    del material.mcow_effect_force_field_max_radius
    del material.mcow_effect_force_field_ripple_distortion
    del material.mcow_effect_force_field_map_distortion
    del material.mcow_effect_force_field_vertex_color_enabled
    del material.mcow_effect_force_field_displacement_map
    del material.mcow_effect_force_field_ttl

def register_properties_material_additive(material):
    material.mcow_effect_additive_color_tint = bpy.props.FloatVectorProperty(
        name = "Color Tint",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    # NOTE : Maybe in the future, this property should be automatically determined for ALL of the material effect types, based on whether the object has a vertex color layer or not? idk...
    # Also, these properties that are common across different types of material effects should maybe be modified to be added in the generic props rather than having them duplicated.
    # For now, this is ok, but this should probably be reworked in the future.
    material.mcow_effect_additive_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        default = False
    )

    material.mcow_effect_additive_texture_enabled = bpy.props.BoolProperty(
        name = "Texture Enabled",
        default = True
    )

    material.mcow_effect_additive_texture = bpy.props.StringProperty(
        name = "Texture",
        default = "..\\Textures\\Surface\\Nature\\Atmosphere\\light_ray00_0" # NOTE : Maybe find a better default for this, like a grass texture or whatever?
    )

def unregister_properties_material_additive(material):
    del material.mcow_effect_additive_color_tint
    del material.mcow_effect_additive_vertex_color_enabled
    del material.mcow_effect_additive_texture_enabled
    del material.mcow_effect_additive_texture

def register_properties_panel_class_material():
    bpy.utils.register_class(MATERIAL_PT_MagickCowPanel)

def unregister_properties_panel_class_material():
    bpy.utils.unregister_class(MATERIAL_PT_MagickCowPanel)

# endregion

# region Register and Unregister Functions - Main

def register_properties_material():
    # Get reference to Blender material type
    material = bpy.types.Material

    # Register the material properties
    register_properties_material_generic(material)
    register_properties_material_geometry(material)
    register_properties_material_water(material)
    register_properties_material_lava(material)
    register_properties_material_force_field(material)
    register_properties_material_additive(material)

    # Register the material text data block style props
    register_properties_material_text(material)

    # Register the material properties panel
    register_properties_panel_class_material()

def unregister_properties_material():
    # Get reference to Blender material type
    material = bpy.types.Material

    # Unregister the material properties
    unregister_properties_material_generic(material)
    unregister_properties_material_geometry(material)
    unregister_properties_material_water(material)
    unregister_properties_material_lava(material)
    unregister_properties_material_force_field(material)
    unregister_properties_material_additive(material)

    # Unregister the material text data block style props
    unregister_properties_material_text(material)

    # Unregister the material properties panel
    unregister_properties_panel_class_material()

# endregion

# endregion
