# region Blender Operator classes for JSON Importer.

# This is the Blender Operator class for importing MagickaPUP JSON files into the scene.
# This operator allows Blender to transform the contents of a JSON file into a set of objects laid out on the scene in a way that it is compatible with MagickCow's object properties and systems.
class MagickCowImportOperator(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    # region Blender Specific Configuration
    
    bl_idname = "object.magickcow_import" # bl_idname has to follow the pattern: "category.custom_name", where category can be something common in Blender like "object", "mesh", "scene" or a custom text. bl_iname must also be an unique identifier for each operator, and it must also be in lowercase and snake_case.
    bl_label = "MagickCow Import JSON"
    bl_description = "MagickCow import MagickaPUP JSON file into Blender scene"

    # endregion

    # region Export Panel Configuration
    
    filename_ext = ".json"
    filter_glob : bpy.props.StringProperty(default = "*.json", options = {"HIDDEN"})

    # endregion

    # region Main Importer Entry Point

    def execute(self, context):
        return {"FINISHED"} # TODO : Implement

    # endregion

# endregion

# region Blender Import Panel functions, Register and Unregister functions

def menu_func_import(self, context):
    self.layout.operator(MagickCowImportOperator.bl_idname, text = "Import Scene from MagickaPUP JSON file (.json)")

def register_importers():
    bpy.utils.register_class(MagickCowImportOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister_importers():
    bpy.utils.unregister_class(MagickCowImportOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

# endregion
