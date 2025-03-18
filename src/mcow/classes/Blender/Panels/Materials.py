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
            material_type = material.mcow_effect_type
            layout.prop(material, "mcow_effect_type")

            if material_type == "EFFECT_DEFERRED":
                self.draw_effect_deferred(layout, material)
            elif material_type == "EFFECT_LIQUID_WATER":
                self.draw_effect_water(layout, material)
            elif material_type == "EFFECT_LIQUID_LAVA":
                self.draw_effect_lava(layout, material)
            elif material_type == "EFFECT_FORCE_FIELD":
                self.draw_effect_force_field(layout, material)
    
    # From here on out, we have custom draw methods for each type of material
    def draw_effect_deferred(self, layout, material):
        layout.prop(material, "mcow_effect_deferred_alpha")
        layout.prop(material, "mcow_effect_deferred_sharpness")
        layout.prop(material, "mcow_effect_deferred_vertex_color_enabled")
    
    def draw_effect_water(self, layout, material):
        pass
    
    def draw_effect_lava(self, layout, material):
        pass
    
    def draw_effect_force_field(self, layout, material):
        pass

# endregion

# region Register and Unregister Functions - Internal

def register_properties_material_generic(material):
    material.mcow_effect_type = bpy.props.EnumProperty(
        name = "Material Type",
        description = "Determines the type of this material",
        items = [
            ("EFFECT_DEFERRED", "Deferred", "Default geometry material"),
            ("EFFECT_LIQUID_WATER", "Water", "Water material"),
            ("EFFECT_LIQUID_LAVA", "Lava", "Lava material"),
            ("EFFECT_FORCE_FIELD", "Force Field", "Force Field material")
        ],
        default = "EFFECT_DEFERRED"
    )

def unregister_properties_material_generic(material):
    del material.mcow_effect_type

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

def unregister_properties_material_geometry(material):
    del material.mcow_effect_deferred_alpha
    del material.mcow_effect_deferred_sharpness
    del material.mcow_effect_deferred_vertex_color_enabled

def register_properties_material_water(material):
    pass

def unregister_properties_material_water(material):
    pass

def register_properties_material_lava(material):
    pass

def unregister_properties_material_lava(material):
    pass

def register_properties_material_force_field(material):
    pass

def unregister_properties_material_force_field(material):
    pass

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

    # Register the material properties panel
    register_properties_panel_class_material()

def unregister_custom_material_panel():
    # Get reference to Blender material type
    material = bpy.types.Material

    # Unregister the material properties
    unregister_properties_material_generic(material)
    unregister_properties_material_geometry(material)
    unregister_properties_material_water(material)
    unregister_properties_material_lava(material)
    unregister_properties_material_force_field(material)

    # Unregister the material properties panel
    unregister_properties_panel_class_material()

# endregion

# endregion
