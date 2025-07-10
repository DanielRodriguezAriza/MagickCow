# region Window Utility

# Window management utility functions

# Utility functions to open / create new in-app (Blender-specific) windows.
# Stuff like opening a pop-up text editor for quick shader editing and stuff like that...
# Windows for property editing, etc... basically a QoL type of thing.

def mcow_window_open(window_name):
    bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
    area = bpy.context.window_manager.windows[-1].screen.areas[0]
    area.type = window_name
    return area

def mcow_window_open_text_editor(text_to_select):
    area = mcow_window_open("TEXT_EDITOR")
    area.spaces.active.text = bpy.data.texts.get(text_to_select)

# endregion
