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
            layout.prop(material, "custom_float")

# endregion

# region Register and Unregister Functions - Internal

def register_properties_material_generic():
    pass

def unregister_properties_material_generic():
    pass

def register_properties_material_geometry(): # NOTE : Maybe this should be renamed to deferred or something? we could also add transparent mats in the future I suppose.
    pass

def unregister_properties_material_geometry():
    pass

def register_properties_material_water():
    pass

def unregister_properties_material_water():
    pass

def register_properties_material_lava():
    pass

def unregister_properties_material_lava():
    pass

def register_properties_material_force_field():
    pass

def unregister_properties_material_force_field():
    pass

def register_properties_panel_class_material():
    bpy.utils.register_class(MATERIAL_PT_MagickCowPanel)

def unregister_properties_panel_class_material():
    bpy.utils.unregister_class(MATERIAL_PT_MagickCowPanel)

# endregion

# region Register and Unregister Functions - Main

def register_properties_material():
    # Register the material properties
    register_properties_material_generic()
    register_properties_material_geometry()
    register_properties_material_water()
    register_properties_material_lava()
    register_properties_material_force_field()

    # Register the material properties panel
    register_properties_panel_class_material()

def unregister_custom_material_panel():
    # Unregister the material properties
    unregister_properties_material_generic()
    unregister_properties_material_geometry()
    unregister_properties_material_water()
    unregister_properties_material_lava()
    unregister_properties_material_force_field()

    # Unregister the material properties panel
    unregister_properties_panel_class_material()

# endregion

# endregion
