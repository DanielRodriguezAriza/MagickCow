# region Blender Panel classes, register and unregister functions for MagickCow material properties handling

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

def register_properties_material():
    # Register the material properties
    bpy.types.Material.custom_float = bpy.props.FloatProperty(
        name = "Custom Float",
        description = "A custom material property that is a float",
        default = 1.0,
        min = 0.0,
        max = 1.0
    )

    # Register the material properties panel
    bpy.utils.register_class(MATERIAL_PT_MagickCowPanel)

def unregister_custom_material_panel():
    # Unregister the material properties
    del bpy.types.Material.custom_float

    # Unregister the material properties panel
    bpy.utils.unregister_class(MATERIAL_PT_MagickCowPanel)

# endregion
