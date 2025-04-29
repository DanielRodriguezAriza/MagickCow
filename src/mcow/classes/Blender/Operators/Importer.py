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
        return "XnbFileData" in json_dict and "PrimaryObject" in json_dict["XnbFileData"] and "SharedResources" in json_dict["XnbFileData"] and "$type" in json_dict["XnbFileData"]["PrimaryObject"]

    # endregion

    # region Importer Implementation

    def import_data(self, context):

        # Load the file data into a string
        success, json_string = self.read_file_contents(self.filepath)
        if not success:
            self.report({"ERROR"}, "Could not load the input file!")
            return {"CANCELLED"}
        
        # Parse the string into a JSON dict
        success, json_data = self.read_json_data(json_string)
        if not success:
            self.report({"ERROR"}, "The input file is not a valid JSON file!")
            return {"CANCELLED"}
        
        # Check if the JSON is a valid MagickaPUP JSON file (checks if it contains the minimum fields required for an MPUP JSON document)
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

        # Perform import process
        try:

            type_string = json_data["XnbFileData"]["PrimaryObject"]["$type"]

            # Check what the $type string is for the import.
            # If the type is known, process it.
            # If it's not a known type, then error out and cancel the operation.

            if type_string == "level_model": # TODO : Make the type strings consistent... use PascalCase rather than snake_case for consistency with the new nomenclature planned for mpup
                ans = self.import_data_map(json_data)
            elif type_string == "PhysicsEntity":
                ans = self.import_data_physics_entity(json_data)
            elif type_string == "xna_model": # TODO : Same thing here...
                ans = self.import_data_xna_model(json_data)
            else:
                ans = self.import_data_unknown(type_string)

        except MagickCowException as e:
            self.report({"ERROR"}, f"Failed to import data: {e}")
            return {"CANCELLED"}

        return ans
    
    def import_data_internal(self, data, importer):
        importer.exec(data)
    
    def import_data_map(self, data):
        self.import_data_internal(data, MCow_ImportPipeline_Map())
        return {"FINISHED"}

    def import_data_physics_entity(self, data):
        self.report({"ERROR"}, "Import operations for Physics Entity are not supported yet!")
        return {"CANCELLED"}
    
    def import_data_xna_model(self, data):
        self.import_data_internal(data, MCow_ImportPipeline_XnaModel())
        return {"FINISHED"}

    def import_data_unknown(self, type_string):
        self.report({"ERROR"}, f"Content of type \"{type_string}\" is not supported by MagickCow!")
        return {"CANCELLED"}
    
    # NOTE : Reference method contents for types of assets that mcow should support but that are yet to be implemented.
    # NOTE : Maybe in the future it would make more sense to just return {"FINISHED"} at the end of the main import function rather than ans, and use MCowNotImplemented() exceptions or whatever to signal errors? they are caught by the try-catch block up there, so yeah... maybe it's cleaner that way...
    # def import_data_whatever(self, data):
    #     # self.report({"ERROR"}, "Import operation for Whatever Thing is not supported yet!")
    #     # return {"CANCELLED"}

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
