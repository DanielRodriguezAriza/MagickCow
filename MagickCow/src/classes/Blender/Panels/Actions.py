# region Blender Panel: N-Key Panel: MagickCow Actions

# This class is the one that controls the N-Key panel for MagickCow Actions.
class OBJECT_PT_MagickCowActionsPanel(bpy.types.Panel):

    bl_label = "MagickCow Actions"
    bl_idname = "OBJECT_PT_MagickCowActions_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MagickCow"

    def draw(self, context):
        layout = self.layout
        
        layout.label(text = "No available actions yet!")

def register_actions_panel():
    bpy.utils.register_class(OBJECT_PT_MagickCowActionsPanel)

def unregister_actions_panel():
    bpy.utils.unregister_class(OBJECT_PT_MagickCowActionsPanel)

# endregion
