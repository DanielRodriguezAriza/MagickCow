# region Blender Operator classes for JSON Importer.

# This is the Blender Operator class for importing MagickaPUP JSON files into the scene.
# This operator allows Blender to transform the contents of a JSON file into a set of objects laid out on the scene in a way that it is compatible with MagickCow's object properties and systems.
class MagickCowImportOperator(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    # region Blender Specific Configuration
    
    bl_idname = "object.magickcow_import" # bl_idname has to follow the pattern: "category.custom_name", where category can be something common in Blender like "object", "mesh", "scene" or a custom text. bl_iname must also be an unique identifier for each operator, and it must also be in lowercase and snake_case.
    bl_label = "MagickCow Import MagickaPUP JSON"
    bl_description = "Import Scene from MagickaPUP JSON file (.json)"

    # endregion

    # region Export Panel Configuration
    
    filename_ext = ".json"
    filter_glob : bpy.props.StringProperty(default = "*.json", options = {"HIDDEN"})

    # endregion

    # region Main Importer Entry Point

    def execute(self, context):
        return self.import_data(context)

    # endregion

    # region Aux methods

    def read_file_contents(self, file_path):
        try:
            with open(file_path, "r") as file:
                contents = file.read()
                return True, contents
        except Exception as e:
            return False, None

    def read_json_data(self, json_string):
        try:
            data = json.loads(json_string)
            return True, data
        except Exception as e:
            return False, None

    # endregion

    # region Importer Implementation

    def import_data(self, context):

        success, json_string = self.read_file_contents(self.filepath)
        if not success:
            self.report({"ERROR"}, "Could not load the input file!")
            return {"CANCELLED"}
        
        success, json_data = self.read_json_data(json_string)
        if not success:
            self.report({"ERROR"}, "The input file is not a valid JSON file!")
            return {"CANCELLED"}
        
        if "XnbFileData" not in json_data or "$type" not in json_data["XnbFileData"]:
            self.report({"ERROR"}, "The input JSON file is not a valid MagickaPUP JSON file!")
            return {"CANCELLED"}

        return {"FINISHED"}

    def import_data_unknown(self, context):
        self.report({"ERROR"}, "Cannot import scene data of unknown type!")
        return {"CANCELLED"}

    # endregion

# endregion

# region Blender Import Panel functions, Register and Unregister functions

def menu_func_import(self, context):
    self.layout.operator(MagickCowImportOperator.bl_idname, text = "MagickaPUP JSON (.json)")

def register_importers():
    bpy.utils.register_class(MagickCowImportOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister_importers():
    bpy.utils.unregister_class(MagickCowImportOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

# endregion
