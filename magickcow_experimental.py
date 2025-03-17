import bpy

bl_info = {
    "name" : "MagickCow Experimental Features Addon",
    "blender" : (3, 0, 0),
    "category" : "Export",
    "description" : "Adds some experimental stuff to MagickCow",
    "author" : "potatoes",
    "version" : (1, 0, 0)
}

def register_custom_material_properties():
    bpy.types.Material.custom_float = bpy.props.FloatProperty(
        name = "Custom Float",
        description = "A custom material property that is a float",
        default = 1.0,
        min = 0.0,
        max = 1.0
    )

def unregister_custom_material_properties():
    del bpy.types.Material.custom_float

class MATERIAL_PT_CustomPanel(bpy.types.Panel):
    bl_label = "Custom Material Property"
    bl_idname = "MATERIAL_PT_custom_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    bl_options = {"DEFAULT_CLOSED"} # The panel will be closed by default when the addon is installed
    bl_order = 0 # The panel will be added at the very top by default. The user can manually change this by dragging it down on their own, but this should make it easier to find the mcow material props.

    def draw(self, context):
        layout = self.layout
        material = context.material
        if material:
            layout.prop(material, "custom_float")

def register_custom_material_panel():
    bpy.utils.register_class(MATERIAL_PT_CustomPanel)

def unregister_custom_material_panel():
    bpy.utils.unregister_class(MATERIAL_PT_CustomPanel)

def register():
    register_custom_material_properties()
    register_custom_material_panel()

def unregister():
    unregister_custom_material_properties()
    unregister_custom_material_panel()

if __name__ == "__main__":
    register()
