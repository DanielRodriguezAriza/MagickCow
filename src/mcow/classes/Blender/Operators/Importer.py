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

    def is_valid_mpup_json(self, json_dict):
        return "XnbFileData" in json_data and "PrimaryObject" in json_data["XnbFileData"] and "SharedResources" in json_data["XnbFileData"] and "$type" in json_data["XnbFileData"]["PrimaryObject"]

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
        
        success = self.is_valid_mpup_json(json_data)
        if not success:
            self.report({"ERROR"}, "The input JSON file is not a valid MagickaPUP JSON file!")
            return {"CANCELLED"}
        
        # TODO : Finish implementing the import logic!
        # Also, maybe rename the export pipeline objects to use the Export keyword in their names (classes, vars and functions)?
        # Also, obviously get rid of these import operation not supported error once you actually implement import operations.
        # Keep the generic else case tho, that is required to error out when importing content of a type that mcow does not support.
        # For example, importing a sound here does not make any sense, so that will never be supported, and it will fall automatically within the else case always.

        # TODO : When importing the generic export function that will call the import method of the pipeline object, make sure to wrap it all up in a try-catch for custom mcow exceptions
        # That way, if anything goes wrong, we can catch it just fine.

        # Check what the $type string is for the import.
        # If the type is known, process it.
        # If it's not a known type, then error out and cancel the operation.
        type_string = json_data["XnbFileData"]["PrimaryObject"]["$type"]
        if type_string == "level_model": # TODO : Make the type strings consistent... use PascalCase rather than snake_case for consistency with the new nomenclature planned for mpup
            # TODO : Implement level model processing
            self.report({"ERROR"}, "Import operations for Level Model are not supported yet!")
            return {"CANCELLED"}
        elif type_string == "PhysicsEntity":
            pass # TODO : Implement physics entity processing
            self.report({"ERROR"}, "Import operations for Physics Entity are not supported yet!")
            return {"CANCELLED"}
        else:
            self.report({"ERROR"}, f"Content of type \"{type_string}\" is not supported by MagickCow!")
            return {"CANCELLED"}

        return {"FINISHED"} # What the fuck do I do with you now?

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
