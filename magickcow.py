# ../mcow/License.py
# region License

# MIT License
# 
# Copyright (c) 2024 Daniel Rodríguez Ariza
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# endregion

# ../mcow/Comments.py
# region Comments

# NOTE : Comments lie, code doesn't...
# A lot of the comments under "TODO" markers within this file are possibly outdated. As the codebase grows, it becomes harder and harder to maintain the comments LOL...
# The "NOTE"s are still relevant tho. A lot of really large comments exist for the sake of explaining how some weird pieces of the code actually work.

# TODO : Remove a lot of the outdated TODOs... like the one talking about encapsulating everything within classes LOL, that part's already been finished!

# TODO : Possibly change a lot of this stuff by encapsulating all of the "make_" methods into actual classes? with their own "generate()", "get_object()"/"make()", etc methods... idk...
# TODO : Rework all of the useless tuple copying by merging the JSON-style object make_ step with the generate_ step, maybe? I mean, it would be easier to keep them separate if the information was stored within proper classes and each had their make_data and generate_data functions.

# NOTE : I hate coding in python, it looks like 90% of the code is fucking comments, seriously, just having a decent type system would prevent having to make so many comments to clear stuff up. No, type annotations are not good enough...
# NOTE : Well, I don't really hate coding in python, it's pretty cool, but fuck me this code has to be one of the most wall of text filled pieces of code I have ever written. The comments are insane.

# TODO : Re-enable the global try catch on the exporter code so that we can get proper error handling. This was simply disabled so that we could get on what line exceptions took place during debugging...
# TODO : There's a bug when dealing with meshes that have 0 triangles. Discard those by seeing their triangle count on the get stage both on the map and physics entity handling code...
# TODO : Fix issue where attaching a light or other orientation based objects to a locator causes the resulting rotation values to be wrong (the locator has a pretty shitty rotation undo fix which is fucking things up...)

# TODO : Maybe modify the names of the blender properties bpy.props used by the objects and scene panel so that they are located within a custom object of their own for easier localization? Something like a dict?
# Maybe something like this:
"""

mcow_props : {
    type : bpy.props.enumproperty(whatever...),
    mesh_properties : {
        etc...
    },
    empty_properties : {
        etc...
    }
    liquid_properties : {
        etc...
    }
}

"""
# Or whatever the fuck, idk... we'll see if this is even possible in the first place...

# TODO : Fix Make stage material getting step by adding material cache dict as input tuple ok mk stage

# endregion

# ../mcow/BlenderInfo.py
# region BL Info

bl_info = {
    "name" : "MagickCow Asset Exporter Addon",
    "blender" : (3, 0, 0),
    "category" : "Export",
    "description" : "Exports the mesh data of the BLEND file to an intermediate JSON file to be used by MagickaPUP to generate a XNB file compatible with Magicka.",
    "author" : "potatoes",
    "version" : (1, 0, 0)
}

# endregion

# ../mcow/Imports.py
# region Imports

# NOTE : 12/02/2025 @ 4:53 AM Just installed the fake bpy module and python module for VS Code for the first time... bruh...
# This pylint line is not really needed, but some older versions of VS Code appear to have some issues loading the fake bpy module, so I'm adding it here for anyone who uses
# VS Code as their text editor and decides to check out the inner workings of this addon's code...
# pylint: disable=fixme, import-error
import bpy
import bpy_extras
import json
import os
import struct
import bmesh
import array
import math
import mathutils
import time
from collections import namedtuple # TODO : Get rid of this fucker, namedtuples are way slower than regular tuples AND run of the mill classes, so this module was pretty much a waste of time...

# endregion

# ../mcow/classes/MagickCow/Exception.py
# region Exception Classes

# region Comment - Why the fuck do these exception classes exist

# The exception classes here are mostly just dummy classes that inherit directly from the Exception class without adding anything else.
# They are pretty much literally just the same as the base Python Exception class.
# They only exist to make it possible for the export and import pipelines to communicating with the main import and export Blender operator classes through the main execution try-catch block.
# This allows MagickCow specific errors to print a nicer Blender {"CANCELLED"} import / export error, while still allowing base Exceptions caused by errors in the code to print on the console
# the line on which the error took place.
# This way, different types of non-mcow errors and exceptions can be skipped in the try-catch block, which prevents catching all of the exceptions and allows us to retain debugability to a
# certain degree...
# In short, most of this stuff is just a fucking hack and does nothing special.
# Just abusing the fact that in Python it is normal for control flow to be manipulated through exceptions... Stop Iteration, anyone? lmao...

# endregion

# Base MagickCow exception class
class MagickCowException(Exception):
    pass

# Exception class for export pipeline exceptions
class MagickCowExportException(MagickCowException):
    pass

# Exception class for import pipeline exceptions
class MagickCowImportException(MagickCowException):
    pass

# Exception class for content that is not implemented yet
class MagickCowNotImplementedException(MagickCowException):
    pass

# endregion

# ../mcow/classes/MagickCow/Mesh.py
# region Mesh Class

class MCow_Mesh:
    def __init__(self, obj, transform):

        # Ensure that data is single user so that modifiers can be applied
        # region Comment
        # Copy the data so that we can apply modifiers, but only if the object's data has more than 1 user.
        # Also, yes, this makes it so that the original is still sitting there in memory, but we don't care for the most part about this as of now.
        # Maybe if someone were to work with an extremely large mesh they would then feel the impact of copying multiple GBs at a time, but that's on them for not segmenting their mesh properly...
        # endregion
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        
        # Assign values to local variables
        self.obj = obj
        self.transform = transform
        self.invtrans = transform.inverted().transposed()
        self.mesh = None
        self.bm = None

        # Apply modifiers, triangulate mesh, generate bm, etc...
        self._calculate_mesh_data()
    
    def __del__(self):
        self.bm.free()

    def _calculate_mesh_data(self):
        self._select_object(self.obj)
        self._apply_modifiers(self.obj)
        self._triangulate_mesh(self.obj)
    
    def _select_object(self, obj):
        obj.select_set(state = True)
        bpy.context.view_layer.objects.active = obj

    def _apply_modifiers(self, obj):
        for mod in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier = mod.name)
    
    def _triangulate_mesh(self, obj):
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        self.mesh = mesh
        self.bm = bm


# endregion

# ../mcow/classes/MagickCow/Map/Scene.py
# region Map Classes

class MCow_Map_SceneObjectsFound:
    def __init__(self):
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = []
        self.particles = []
        self.collisions = [[] for i in range(10)] # Each collision layer is a list of objects that were found within said layer.
        self.nav_meshes = []
        self.animated_parts = []
        
        # NOTE : These fields ahead can only be found on static level data, can't be within animated level parts.
        self.physics_entities = []
        self.force_fields = []
        self.camera_collision_meshes = []

class MCow_Map_SceneObjectsGeneratedStatic:
    def __init__(self):
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = []
        self.particles = []
        self.collisions = []
        self.camera_collision_mesh = None
        self.nav_mesh = None
        self.animated_parts = []
        self.physics_entities = []
        self.force_fields = []

class MCow_Map_SceneObjectsGeneratedAnimated:
    def __init__(self):
        self.bone = None # The root bone of this animated level part.
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = [] # NOTE : Animated level parts cannot contain triggers! This should be removed and the get stage code modified accordingly...
        self.particles = []
        self.collision = None # We store a single collision channel / layer, because the entire animated part has to have the same collision type. Child parts can have their own collision type tho.
        self.nav_mesh = None
        self.animation = None
        self.animated_parts = []

# endregion

# ../mcow/classes/MagickCow/PhysicsEntity/PhysicsEntity.py
# region Physics Entity Classes

# region Get Stage Classes

# NOTE : The Map side of the code could be reworked to be similar to how the physics entity side is going to work.
# Basically, here, rather than having different structures for the get and generate stages, since we're going to be storing the same type of data in both cases, just in different states / forms, what I've done is
# that I'm basically having a "stroage" data structure for each type of data structure that exists within physics entities in the format of their XNB files.

class Storage_PhysicsEntity:
    def __init__(self):
        # self.roots = [] # NOTE : If we have more than one root, what do we do? do we error out or do we export multiple objects? and if we export multiple objects, do we put them into the same file in a list like structure and modify MagickaPUP to support input JSON files with lists of docs inside, or do we export each object to its own file? and what naming scheme to use? etc etc...
        self.root = None
        self.collisions = [] # Collision meshes
        self.boxes = [] # Bounding boxes
        self.model = Storage_PhysicsEntity_Model()

class Storage_PhysicsEntity_Model:
    def __init__(self):
        self.meshes = []
        self.bones = []

class PE_Storage_Bone:
    def __init__(self):
        self.obj = None
        self.transform = None
        self.index = 0
        self.parent = -1
        self.children = []

# endregion

# region Generate Stage Classes

class PE_Generate_PhysicsEntityData:
    def __init__(self):
        self.physics_entity_id = "default"
        self.is_movable = False
        self.is_pushable = False
        self.is_solid = True
        self.mass = 200
        self.max_hit_points = 300
        self.can_have_status = True
        self.resistances = []
        self.gibs = []
        self.gib_trail_effect = ""
        self.hit_effect = ""
        self.visual_effects = []
        self.sound_banks = ""
        self.model = XNA_Model()
        self.has_collision = False
        self.collision_vertices = []
        self.collision_triangles = []
        self.bounding_boxes = []
        self.events = []
        self.has_advanced_settings = True
        self.advanced_settings = None

# NOTE : In truth, the game only supports a single bounding box, but the reading code can take N bounding boxes.
# The thing is that only the first read bounding box is preserved, the rest are just discarded. In any case, we add support for exporting as many bounding boxes as we want, even tho only one will be used in the end...
class PE_Generate_BoundingBox:
    def __init__(self):
        self.id = "bb"
        self.position = None # vec3
        self.scale = None # vec3
        self.rotation = None # quaternion / vec4

class PE_Generate_Resistance:
    def __init__(self, element = "Earth", multiplier = 1, modifier = 0):
        self.element = element
        self.multiplier = multiplier
        self.modifier = modifier

class PE_Generate_Gib:
    def __init__(self, model = "", mass = 1, scale = 1):
        self.model = model
        self.mass = mass
        self.scale = scale

class PE_Generate_Bone:
    def __init__(self):
        self.index = 0
        self.name = "bone"
        self.transform = None
        self.parent = -1
        self.children = []


# endregion

# endregion

# ../mcow/classes/XNA/Matrix.py
# region XNA Math Class

# NOTE : This class' implementation looks to me like it's pretty inefficient and could be improved by a lot by using a single linear buffer rather than a list of lists, but whatever... we'll deal with this shit for now.
# NOTE : Matrices in XNA are always 4x4
class XNA_Matrix:
    # NOTE : The constructor returns the identity matrix by default
    def __init__(self, M11 = 1, M12 = 0, M13 = 0, M14 = 0, M21 = 0, M22 = 1, M23 = 0, M24 = 0, M31 = 0, M32 = 0, M33 = 1, M34 = 0, M41 = 0, M42 = 0, M43 = 0, M44 = 1):
        self.matrix = [[0 for j in range(0, 4)] for i in range(0, 4)]
        
        self.matrix[0][0] = M11
        self.matrix[0][1] = M12
        self.matrix[0][2] = M13
        self.matrix[0][3] = M14

        self.matrix[1][0] = M21
        self.matrix[1][1] = M22
        self.matrix[1][2] = M23
        self.matrix[1][3] = M24

        self.matrix[2][0] = M31
        self.matrix[2][1] = M32
        self.matrix[2][2] = M33
        self.matrix[2][3] = M34

        self.matrix[3][0] = M41
        self.matrix[3][1] = M42
        self.matrix[3][2] = M43
        self.matrix[3][3] = M44
    
    # TODO : Maybe add some "consturctor" static methods that return matrices constructed from specific input types? stuff like XNA_Matrix.FromBlenderMatrix(mat), XNA_Matrix.FromWhatever(...), etc...

# endregion

# ../mcow/classes/XNA/Model.py
# region XNA Model Classes

# TODO : Maybe rename this class when you make the code across level data generation and physics entity data generation more generic, since this is a class that both types of scene use internally...
class XNA_Model:
    def __init__(self):
        self.tag = None # Always null in Magicka, so we should not care about this tbh...
        self.bones = []
        self.vertex_declarations = [] # NOTE : These I had chosen to always generate to be the same on the make stage for map generation, so maybe we can just discard this property and never use it for anything?
        self.model_meshes = []

class XNA_Model_Bone:
    def __init__(self):
        self.index = 0
        self.name = "none"
        self.transform = None # NOTE : This is a transform matrix, and we could either use a tuple for it or structure it with a blender matrix class or use our own class for this.
        self.parent = -1
        self.children = []

class XNA_Model_Mesh:
    def __init__(self):
        self.name = "none"
        self.parent_bone = 0
        self.bounding_sphere = None
        self.vertex_buffer = []
        self.index_buffer = []
        self.mesh_parts = None # NOTE : Rather than implementing mesh parts, what my exporter does is simply adding a new model mesh to the exported data, so this should always be pretty much almost the exact same for all types of models, so we could ignore implementing this here and always write the same data in the make stage (except for the number of vertices, primitive count, vertex declaration index and shared resource index. Other than that, the rest of the data is always the same.)

# endregion

# ../mcow/classes/Blender/Data/Data.py
# region Custom Blender Property types and related Blender Operator classes

# This region contains classes that describe custom property types for Blender.
# Note that these properties can be used on any place in Blender, such as object properties or scene properties.

# region Resistances

# TODO : Maybe make the elements enum into some kind of function that returns the result of the bpy.props.EnumProperty() call so that we can make element enums anywhere we want?
# Also, think about adding support for all of the possible values for elements, including stuff like "Beams" and whatnot...
class MagickCowProperty_Resistance(bpy.types.PropertyGroup):
    element : bpy.props.EnumProperty(
        name = "Element",
        description = "Magical element described by this entry",
        items = [
            ("Water", "Water", "Water Element"),
            ("Life", "Life", "Life Element"),
            ("Shield", "Shield", "Shield Element"),
            ("Cold", "Cold", "Cold Element"),
            ("Lighting", "Lighting", "Electricity Element"),
            ("Arcane", "Arcane", "Arcane Element"),
            ("Earth", "Earth", "Earth Element"),
            ("Fire", "Fire", "Fire Element"),
            ("Steam", "Steam", "Steam Element"),
            ("Ice", "Ice", "Ice Element"),
            ("Poison", "Poison", "Poison Element")
        ],
        default = "Earth"
    )
    multiplier : bpy.props.FloatProperty(
        name = "Multiplier",
        description = "Multiplies the effects applied by the selected element. If set to 1, the value will be unchanged and the default damage will be applied. If set to a negative value, the effects of the spell will be inverted. If set to 0, the spell will have no effect unless specified on the modifier property.",
        default = 1
    )
    modifier : bpy.props.FloatProperty(
        name = "Modifier",
        description = "Modifies the effects applied by the selected element. If set to 0, the value will be unchaged.",
        default = 0
    )

class MAGICKCOW_OT_Operator_Resistance_AddItem(bpy.types.Operator):
    bl_label = "Add"
    bl_idname = "magickcow.resistance_add_item"
    def execute(self, context):
        obj = context.object
        obj.mcow_physics_entity_resistances.add()
        return {"FINISHED"}

class MAGICKCOW_OT_Operator_Resistance_RemoveItem(bpy.types.Operator):
    bl_label = "Remove"
    bl_idname = "magickcow.resistance_remove_item"
    index : bpy.props.IntProperty() # NOTE : For this property to be accessible from the outside without errors, we need to use ":" rather than "=" on assignment, for some reason...
    def execute(self, context):
        obj = context.object
        if self.index >= 0 and self.index < len(obj.mcow_physics_entity_resistances): # NOTE : This check is not really necessary considering how we're assured that the index should theoretically always be correct when iterating on the collection.
            obj.mcow_physics_entity_resistances.remove(self.index)
        return {"FINISHED"}

def register_property_class_resistance():
    bpy.utils.register_class(MagickCowProperty_Resistance)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

def unregister_property_class_resistance():
    bpy.utils.unregister_class(MagickCowProperty_Resistance)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

# endregion

# region Gibs

class MagickCowProperty_Gib(bpy.types.PropertyGroup):
    model : bpy.props.StringProperty(
        name = "Model",
        description = "Path to the file that contains the model used for this gib",
        default = "..\\..\\Models\\AnimatedProps\\Dungeons\\gib_slime01_0"
    )

    mass : bpy.props.FloatProperty(
        name = "Mass",
        description = "The mass of this gib",
        default = 20
    )

    scale : bpy.props.FloatProperty(
        name = "Scale",
        description = "The scale of this gib",
        default = 1
    )

class MAGICKCOW_OT_Operator_Gib_AddItem(bpy.types.Operator):
    bl_label = "Add"
    bl_idname = "magickcow.gibs_add_item"
    def execute(self, context):
        obj = context.object
        obj.mcow_physics_entity_gibs.add()
        return {"FINISHED"}

class MAGICKCOW_OT_Operator_Gib_RemoveItem(bpy.types.Operator):
    bl_label = "Remove"
    bl_idname = "magickcow.gibs_remove_item"
    index : bpy.props.IntProperty()
    def execute(self, context):
        obj = context.object
        if self.index >= 0 and self.index < len(obj.mcow_physics_entity_gibs):
            obj.mcow_physics_entity_gibs.remove(self.index)
        return {"FINISHED"}

def register_property_class_gib():
    bpy.utils.register_class(MagickCowProperty_Gib)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

def unregister_property_class_gib():
    bpy.utils.unregister_class(MagickCowProperty_Gib)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

# endregion

# region Global Property Register and Unregister functions

def register_properties_classes():
    register_property_class_resistance() # Resistances
    register_property_class_gib() # Gibs
    

def unregister_properties_classes():
    unregister_property_class_resistance() # Resistances
    unregister_property_class_gib() # Gibs

# endregion

# endregion

# ../mcow/classes/Blender/Operators/Exporter.py
# region Blender Operator classes for JSON Exporter.

# This class is the exporter operator for all types of files that can be generated by MagickCow.
# NOTE : In the past, we used to have a different export operator for each type of object. Now, they all contain their code within this operator, since the export type is selected on the scene panel.
# We still separate the logic in different methods tho, that way things are easier to deal with, but we only have 1 single exporter operator class rather than multiple classes.
class MagickCowExportOperator(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    
    # region Blender specific configuration:
    
    bl_idname = "object.magickcow_export"
    bl_label = "MagickCow Export MagickaPUP JSON"
    bl_description = "Export Scene to MagickaPUP JSON file (.json)"

    # endregion
    
    # region Exporter Panel Config

    filename_ext = ".json"
    filter_glob : bpy.props.StringProperty(default = "*.json", options = {'HIDDEN'})
    
    # region Deprecated

    # Discarded code where the properties used to depend on the export operator itself. Now they are global to the scene config / data instead.
    # region Deprecated Code
    # mcow_setting_export_path : bpy.props.StringProperty(
    #     name = "Config Path",
    #     description = "Select the path in which the exporter will look for the base folder. This folder contains JSON files which correspond to effects (materials) that will be applied to the surfaces that have a material with the name of the corresponding effect file to be used.",
    #     default = "C:\\"
    # )
    # 
    # mcow_setting_export_animation_data : bpy.props.BoolProperty(
    #     name = "Export Animation Data",
    #     description = "Determines whether the animation side of the scene will be exported or not.\n - If True : The animated level parts will be exported, including all of the child objects and animation data.\n - If False : The animated level parts will be completely ignored and not exported. All children components, including geometry, lights, and any other type of object, that is attached to animated level parts, will also be ignored.\n - Note : The animated level parts root still needs to be present for the exporter to properly generate the level data.",
    #     default = False
    # )
    # 
    # mcow_setting_export_pretty : bpy.props.BoolProperty(
    #     name = "Pretty JSON Format",
    #     description = "The JSON file will be exported with indentation and newlines for easier reading. Slows down export times due to the extra processing required. It also increases the resulting file size due to the extra characters required for newlines and indentation. Recommended to only enable this setting if debugging the output of the generated JSON file is absolutely necessary, specially when working with large maps with high level of detail.",
    #     default = False
    # )
    # 
    # mcow_setting_export_indent : bpy.props.IntProperty(
    #     name = "Indent Depth",
    #     description = "Number of space characters to use in the output JSON file for indentation. This setting is ignored if pretty JSON formatting is disabled.",
    #     default = 2,
    #     min = 1,
    #     max = 256 # Who the fuck is going to need this tho??? Anyone who is dicking around and wants to find out the limit, I guess.
    # )

    # endregion

    # endregion

    # endregion

    # region JSON aux methods

    # NOTE : We use json.dumps to make a string rather than json.dump to dump directly into a file because json.dump is absurdly slow, but json.dumps and then writing the generated string into a file is way faster...
    # Maybe some weird python buffering shenanigans? Oh how I miss fprintf...
    def json_dump_str(self, context, obj_dict):

        is_pretty = context.scene.mcow_scene_json_pretty
        selected_indent = context.scene.mcow_scene_json_indent if context.scene.mcow_scene_json_char == "SPACE" else "\t"

        if is_pretty:
            return json.dumps(obj_dict, indent = selected_indent, separators = (",", ":"), check_circular = False)
        return json.dumps(obj_dict, indent = None, separators = (",", ":"), check_circular = False)

    # endregion

    # region Main Exporter Code

    def execute(self, context):
        return self.export_data(context)
    
    def export_data(self, context):
        scene = context.scene
        export_mode = scene.mcow_scene_mode
        ans = {} # This is an empty object, but the type of answer object we expect from the export functions is a Blender message, something like {"FINISHED"} or {"CANCELLED"} or whatever.
        
        # Save (backup) the scene state as it was before exporting the scene
        # NOTE : The bpy.data properties used to check if the file is saved are the following: 
        # - is_saved : checks if the scene is saved into a file
        # - is_dirty : checks if the latest state in memory has been saved to the file on disk
        if (not bpy.data.is_saved) or bpy.data.is_dirty:
            self.report({"ERROR"}, "Cannot export the scene if it has not been saved!")
            return {"CANCELLED"}
        
        # Perform export process
        try:
            if export_mode == "MAP":
                ans = self.export_data_map(context)
            elif export_mode == "PHYSICS_ENTITY":
                ans = self.export_data_physics_entity(context)
            else:
                ans = self.export_data_none(context)
        except MagickCowException as e:
            self.report({"ERROR"}, f"Failed to export data: {e}")
            return {"CANCELLED"}
        finally:
            # Load (restore) the scene state as it was before exporting the scene
            # This undoes the scene rotations, modifier applications, etc... basically performs and undo that undoes all destructive changes that were performed when exporting the scene
            # This happens within the finally block so that it always takes place even if an error were to happen during export, which prevents the mcow exporter from breaking the scene during export.
            bpy.ops.wm.open_mainfile(filepath = bpy.data.filepath)

        return ans

    def export_data_none(self, context):
        self.report({"ERROR"}, "Cannot export scene data unless a scene export mode is selected!")
        return {"CANCELLED"}

    def export_data_map(self, context):
        return self.export_data_func(context, "Map", MCow_Data_Pipeline_Map())

    def export_data_physics_entity(self, context):
        return self.export_data_func(context, "Physics Entity", MCow_Data_Pipeline_PhysicsEntity())
    
    def write_to_file(self, contents):
        try:
            with open(self.filepath, 'w') as outfile:
                outfile.write(contents)
            self.report({"INFO"}, f"Successfully exported data to file \"{self.filepath}\"")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export data: {e}")
            return {"CANCELLED"}

    def export_data_func(self, context, name, generator):
        self.report({"INFO"}, f"Exporting to MagickaPUP .json {name} file...")

        xnb_dict = generator.process_scene_data()
        json_str = self.json_dump_str(context, xnb_dict)

        return self.write_to_file(json_str)

    # endregion

# endregion

# region Blender Export Panel functions, Register and Unregister functions

def menu_func_export(self, context):
    self.layout.operator(MagickCowExportOperator.bl_idname, text = "MagickaPUP JSON (.json)")

def register_exporters():
    bpy.utils.register_class(MagickCowExportOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister_exporters():
    bpy.utils.unregister_class(MagickCowExportOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

# endregion

# ../mcow/classes/Blender/Operators/Importer.py
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

# ../mcow/classes/Blender/Panels/Materials.py
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
            material_mode = material.mcow_effect_mode
            material_type = material.mcow_effect_type

            layout.prop(material, "mcow_effect_mode")

            if material_mode == "MAT":
                layout.prop(material, "mcow_effect_type")
                if material_type == "EFFECT_DEFERRED":
                    self.draw_effect_deferred(layout, material)
                elif material_type == "EFFECT_LIQUID_WATER":
                    self.draw_effect_water(layout, material)
                elif material_type == "EFFECT_LIQUID_LAVA":
                    self.draw_effect_lava(layout, material)
                elif material_type == "EFFECT_FORCE_FIELD":
                    self.draw_effect_force_field(layout, material)
                elif material_type == "EFFECT_ADDITIVE":
                    self.draw_effect_additive(layout, material)
            elif material_mode == "DOC":
                layout.prop(material, "mcow_effect_path")
    
    # From here on out, we have custom draw methods for each type of material
    def draw_effect_deferred(self, layout, material):
        layout.prop(material, "mcow_effect_deferred_alpha")
        layout.prop(material, "mcow_effect_deferred_sharpness")
        layout.prop(material, "mcow_effect_deferred_vertex_color_enabled")

        layout.prop(material, "mcow_effect_deferred_reflection_map_enabled")
        layout.prop(material, "mcow_effect_deferred_reflection_map")

        layout.prop(material, "mcow_effect_deferred_diffuse_texture_0_alpha_disabled")
        layout.prop(material, "mcow_effect_deferred_alpha_mask_0_enabled")
        layout.prop(material, "mcow_effect_deferred_diffuse_color_0")
        layout.prop(material, "mcow_effect_deferred_specular_amount_0")
        layout.prop(material, "mcow_effect_deferred_specular_power_0")
        layout.prop(material, "mcow_effect_deferred_emissive_amount_0")
        layout.prop(material, "mcow_effect_deferred_normal_power_0")
        layout.prop(material, "mcow_effect_deferred_reflection_intensity_0")
        layout.prop(material, "mcow_effect_deferred_diffuse_texture_0")
        layout.prop(material, "mcow_effect_deferred_material_texture_0")
        layout.prop(material, "mcow_effect_deferred_normal_texture_0")

        layout.prop(material, "mcow_effect_deferred_has_second_set")

        layout.prop(material, "mcow_effect_deferred_diffuse_texture_1_alpha_disabled")
        layout.prop(material, "mcow_effect_deferred_alpha_mask_1_enabled")
        layout.prop(material, "mcow_effect_deferred_diffuse_color_1")
        layout.prop(material, "mcow_effect_deferred_specular_amount_1")
        layout.prop(material, "mcow_effect_deferred_specular_power_1")
        layout.prop(material, "mcow_effect_deferred_emissive_amount_1")
        layout.prop(material, "mcow_effect_deferred_normal_power_1")
        layout.prop(material, "mcow_effect_deferred_reflection_intensity_1")
        layout.prop(material, "mcow_effect_deferred_diffuse_texture_1")
        layout.prop(material, "mcow_effect_deferred_material_texture_1")
        layout.prop(material, "mcow_effect_deferred_normal_texture_1")
    
    def draw_effect_water(self, layout, material):
        pass
    
    def draw_effect_lava(self, layout, material):
        pass
    
    def draw_effect_force_field(self, layout, material):
        layout.prop(material, "mcow_effect_force_field_color")
        layout.prop(material, "mcow_effect_force_field_width")
        layout.prop(material, "mcow_effect_force_field_alpha_power")
        layout.prop(material, "mcow_effect_force_field_alpha_fallof_power")
        layout.prop(material, "mcow_effect_force_field_max_radius")
        layout.prop(material, "mcow_effect_force_field_ripple_distortion")
        layout.prop(material, "mcow_effect_force_field_map_distortion")
        layout.prop(material, "mcow_effect_force_field_vertex_color_enabled")
        layout.prop(material, "mcow_effect_force_field_displacement_map")
        layout.prop(material, "mcow_effect_force_field_ttl")
    
    def draw_effect_additive(self, layout, material):
        layout.prop(material, "mcow_effect_additive_color_tint")
        layout.prop(material, "mcow_effect_additive_vertex_color_enabled")
        layout.prop(material, "mcow_effect_additive_texture_enabled")
        layout.prop(material, "mcow_effect_additive_texture")

# endregion

# region Register and Unregister Functions - Internal

def register_properties_material_generic(material):
    material.mcow_effect_type = bpy.props.EnumProperty(
        name = "Material Type",
        description = "Determines the type of this material",
        items = [
            ("EFFECT_DEFERRED", "Deferred", "Deferred material. Used for opaque objects. This is the default configuration for level geometry materials."),
            ("EFFECT_ADDITIVE", "Additive", "Additive material. Used for objects with transparency."), # NOTE : Be mindful of the performance impact of using additive (transparent) materials. Magicka suffers of overdraw issues with transparent materials, just like any other game engine.
            ("EFFECT_LIQUID_WATER", "Water", "Water material. Used for surfaces of type water."),
            ("EFFECT_LIQUID_LAVA", "Lava", "Lava material. Used for surfaces of type lava."),
            ("EFFECT_FORCE_FIELD", "Force Field", "Force Field material. Used for surfaces of type force field.")
        ],
        default = "EFFECT_DEFERRED" # This is the best default option for obvious reasons. First because of performance reasons. Second because most objects an user will add will be opaque level geometry, so this is the best default setting.
    )

    material.mcow_effect_mode = bpy.props.EnumProperty(
        name = "Origin Type",
        description = "Determines the type of origin for the configuration for this material",
        items = [
            ("DOC", "JSON Document", "The configuration for this material will be obtained from the selected JSON file."), # Origin : Json Document data.
            ("MAT", "Blender Material", "The configuration for this material will be obtained from the material configuration as laid on the Blender panel.") # Origin : Blender panel data. This is a sort of "inline" mode
        ],
        default = "MAT"
    )

    material.mcow_effect_path = bpy.props.StringProperty(
        name = "Path",
        description = "Determines the path where the JSON file is located",
        default = ""
    )

def unregister_properties_material_generic(material):
    del material.mcow_effect_type
    del material.mcow_effect_mode
    del material.mcow_effect_path

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

    material.mcow_effect_deferred_reflection_map_enabled = bpy.props.BoolProperty(
        name = "Reflection Map Enabled",
        default = False
    )

    material.mcow_effect_deferred_reflection_map = bpy.props.StringProperty(
        name = "Reflection Map",
        default = ""
    )

    material.mcow_effect_deferred_diffuse_texture_0_alpha_disabled = bpy.props.BoolProperty(
        name = "Diffuse Texture 0 Alpha Disabled",
        default = True
    )

    material.mcow_effect_deferred_alpha_mask_0_enabled = bpy.props.BoolProperty(
        name = "Alpha Mask 0 Enabled",
        default = False
    )

    material.mcow_effect_deferred_diffuse_color_0 = bpy.props.FloatVectorProperty(
        name = "Diffuse Color 0",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_deferred_specular_amount_0 = bpy.props.FloatProperty(
        name = "Specular Amount 0",
        default = 0
    )

    material.mcow_effect_deferred_specular_power_0 = bpy.props.FloatProperty(
        name = "Specular Power 0",
        default = 20
    )

    material.mcow_effect_deferred_emissive_amount_0 = bpy.props.FloatProperty(
        name = "Emissive Amount 0",
        default = 0
    )

    material.mcow_effect_deferred_normal_power_0 = bpy.props.FloatProperty(
        name = "Normal Power 0",
        default = 1
    )

    material.mcow_effect_deferred_reflection_intensity_0 = bpy.props.FloatProperty(
        name = "Reflection Intensity 0",
        default = 0
    )

    material.mcow_effect_deferred_diffuse_texture_0 = bpy.props.StringProperty(
        name = "Diffuse Texture 0",
        default = "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0"
    )

    material.mcow_effect_deferred_material_texture_0 = bpy.props.StringProperty(
        name = "Material Texture 0",
        default = ""
    )

    material.mcow_effect_deferred_normal_texture_0 = bpy.props.StringProperty(
        name = "Normal Texture 0",
        default = ""
    )

    material.mcow_effect_deferred_has_second_set = bpy.props.BoolProperty(
        name = "Has Second Set",
        default = False
    )

    material.mcow_effect_deferred_diffuse_texture_1_alpha_disabled = bpy.props.BoolProperty(
        name = "Diffuse Texture 1 Alpha Disabled",
        default = True
    )

    material.mcow_effect_deferred_alpha_mask_1_enabled = bpy.props.BoolProperty(
        name = "Alpha Mask 1 Enabled",
        default = False
    )

    material.mcow_effect_deferred_diffuse_color_1 = bpy.props.FloatVectorProperty(
        name = "Diffuse Color 1",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_deferred_specular_amount_1 = bpy.props.FloatProperty(
        name = "Specular Amount 1",
        default = 0.0
    )

    material.mcow_effect_deferred_specular_power_1 = bpy.props.FloatProperty(
        name = "Specular Power 1",
        default = 0.0
    )

    material.mcow_effect_deferred_emissive_amount_1 = bpy.props.FloatProperty(
        name = "Emissive Amount 1",
        default = 0.0
    )

    material.mcow_effect_deferred_normal_power_1 = bpy.props.FloatProperty(
        name = "Normal Power 1",
        default = 0.0
    )

    material.mcow_effect_deferred_reflection_intensity_1 = bpy.props.FloatProperty(
        name = "Reflection Intensity 1",
        default = 0.0
    )

    material.mcow_effect_deferred_diffuse_texture_1 = bpy.props.StringProperty(
        name = "Diffuse Texture 1",
        default = ""
    )

    material.mcow_effect_deferred_material_texture_1 = bpy.props.StringProperty(
        name = "Material Texture 1",
        default = ""
    )

    material.mcow_effect_deferred_normal_texture_1 = bpy.props.StringProperty(
        name = "Normal Texture 1",
        default = ""
    )

    # NOTE : On the GUI side, maybe expose these properties under the labels "texture set 0" and "texture set 1" or whatever the fuck so that we can have some better organization,
    # maybe even make the window expandable or whatever, or add an enabled / disabled option for the second texture / material info set. Something like "bool secondMaterialSetEnabled"...

def unregister_properties_material_geometry(material):
    del material.mcow_effect_deferred_alpha
    del material.mcow_effect_deferred_sharpness
    del material.mcow_effect_deferred_vertex_color_enabled

    del material.mcow_effect_deferred_reflection_map_enabled
    del material.mcow_effect_deferred_reflection_map

    del material.mcow_effect_deferred_diffuse_texture_0_alpha_disabled
    del material.mcow_effect_deferred_alpha_mask_0_enabled
    del material.mcow_effect_deferred_diffuse_color_0
    del material.mcow_effect_deferred_specular_amount_0
    del material.mcow_effect_deferred_specular_power_0
    del material.mcow_effect_deferred_emissive_amount_0
    del material.mcow_effect_deferred_normal_power_0
    del material.mcow_effect_deferred_reflection_intensity_0
    del material.mcow_effect_deferred_diffuse_texture_0
    del material.mcow_effect_deferred_material_texture_0
    del material.mcow_effect_deferred_normal_texture_0

    del material.mcow_effect_deferred_has_second_set

    del material.mcow_effect_deferred_diffuse_texture_1_alpha_disabled
    del material.mcow_effect_deferred_alpha_mask_1_enabled
    del material.mcow_effect_deferred_diffuse_color_1
    del material.mcow_effect_deferred_specular_amount_1
    del material.mcow_effect_deferred_specular_power_1
    del material.mcow_effect_deferred_emissive_amount_1
    del material.mcow_effect_deferred_normal_power_1
    del material.mcow_effect_deferred_reflection_intensity_1
    del material.mcow_effect_deferred_diffuse_texture_1
    del material.mcow_effect_deferred_material_texture_1
    del material.mcow_effect_deferred_normal_texture_1

def register_properties_material_water(material):
    pass

def unregister_properties_material_water(material):
    pass

def register_properties_material_lava(material):
    pass

def unregister_properties_material_lava(material):
    pass

def register_properties_material_force_field(material):
    material.mcow_effect_force_field_color = bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    material.mcow_effect_force_field_width = bpy.props.FloatProperty(
        name = "Width",
        default = 0.5
    )

    material.mcow_effect_force_field_alpha_power = bpy.props.FloatProperty(
        name = "Alpha Power",
        default = 4
    )

    material.mcow_effect_force_field_alpha_fallof_power = bpy.props.FloatProperty(
        name = "Alpha Falloff Power",
        default = 2
    )

    material.mcow_effect_force_field_max_radius = bpy.props.FloatProperty(
        name = "Max Radius",
        default = 4
    )

    material.mcow_effect_force_field_ripple_distortion = bpy.props.FloatProperty(
        name = "Ripple Distortion",
        default = 2
    )

    material.mcow_effect_force_field_map_distortion = bpy.props.FloatProperty(
        name = "Map Distortion",
        default = 0.53103447
    )

    material.mcow_effect_force_field_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        default = True
    )

    material.mcow_effect_force_field_displacement_map = bpy.props.StringProperty(
        name = "Displacement Map",
        default = "..\\..\\Textures\\Liquids\\WaterNormals_0"
    )

    material.mcow_effect_force_field_ttl = bpy.props.FloatProperty(
        name = "Time",
        default = 1
    )

def unregister_properties_material_force_field(material):
    del material.mcow_effect_force_field_color
    del material.mcow_effect_force_field_width
    del material.mcow_effect_force_field_alpha_power
    del material.mcow_effect_force_field_alpha_fallof_power
    del material.mcow_effect_force_field_max_radius
    del material.mcow_effect_force_field_ripple_distortion
    del material.mcow_effect_force_field_map_distortion
    del material.mcow_effect_force_field_vertex_color_enabled
    del material.mcow_effect_force_field_displacement_map
    del material.mcow_effect_force_field_ttl

def register_properties_material_additive(material):
    material.mcow_effect_additive_color_tint = bpy.props.FloatVectorProperty(
        name = "Color Tint",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3
    )

    # NOTE : Maybe in the future, this property should be automatically determined for ALL of the material effect types, based on whether the object has a vertex color layer or not? idk...
    # Also, these properties that are common across different types of material effects should maybe be modified to be added in the generic props rather than having them duplicated.
    # For now, this is ok, but this should probably be reworked in the future.
    material.mcow_effect_additive_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        default = False
    )

    material.mcow_effect_additive_texture_enabled = bpy.props.BoolProperty(
        name = "Texture Enabled",
        default = True
    )

    material.mcow_effect_additive_texture = bpy.props.StringProperty(
        name = "Texture",
        default = "..\\Textures\\Surface\\Nature\\Atmosphere\\light_ray00_0" # NOTE : Maybe find a better default for this, like a grass texture or whatever?
    )

def unregister_properties_material_additive(material):
    del material.mcow_effect_additive_color_tint
    del material.mcow_effect_additive_vertex_color_enabled
    del material.mcow_effect_additive_texture_enabled
    del material.mcow_effect_additive_texture

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
    register_properties_material_additive(material)

    # Register the material properties panel
    register_properties_panel_class_material()

def unregister_properties_material():
    # Get reference to Blender material type
    material = bpy.types.Material

    # Unregister the material properties
    unregister_properties_material_generic(material)
    unregister_properties_material_geometry(material)
    unregister_properties_material_water(material)
    unregister_properties_material_lava(material)
    unregister_properties_material_force_field(material)
    unregister_properties_material_additive(material)

    # Unregister the material properties panel
    unregister_properties_panel_class_material()

# endregion

# endregion

# ../mcow/classes/Blender/Panels/Objects.py
# region Blender Panel Classes for N-Key Panel

# region Internal logic classes

# NOTE : This is a dummy class that exists to draw empty panels
class MagickCowPanelObjectPropertiesNone:
    def draw(self, layout, obj):
        layout.label(text = "No available properties:")
        layout.label(text = " - Export mode is \"None\"!")

class MagickCowPanelObjectPropertiesGeneric:
    # Properties that must be displayed for all objects no matter their type
    def draw(self, layout, obj):
        # NOTE : For information stored within an Ojbect, we use obj directly. For information stored within a specific type, we must access obj.data
        layout.prop(obj, "magickcow_allow_export")
        return

class MagickCowPanelObjectPropertiesMap:
    
    # Base draw function. Calls the specific drawing functions based on the type of the selected object.
    def draw(self, layout, obj):
        
        # If the object exists (the user is currently selecting an object), draw the properties in the panel
        # The displayed properties are changed depending on the type of the selected object
        # This "if obj" thing could be an early return with "if not obj" or whatever, but all examples I've seen do it like this, so there must be a pythonic reason to do this...
        if obj:
            if obj.type == "LIGHT":
                self.draw_light(layout, obj)
            elif obj.type == "MESH":
                self.draw_mesh(layout, obj)
            elif obj.type == "EMPTY":
                self.draw_empty(layout, obj)
    
    # Properties that must be displayed for empties
    def draw_empty(self, layout, obj):
        layout.prop(obj, "magickcow_empty_type")
        
        if obj.magickcow_empty_type == "LOCATOR":
            layout.prop(obj, "magickcow_locator_radius")
        elif obj.magickcow_empty_type == "PARTICLE":
            layout.prop(obj, "magickcow_particle_name")
            layout.prop(obj, "magickcow_particle_range")
        elif obj.magickcow_empty_type == "PHYSICS_ENTITY":
            layout.prop(obj, "magickcow_physics_entity_name")
        elif obj.magickcow_empty_type == "BONE":
            layout.prop(obj, "magickcow_locator_radius")
            layout.prop(obj, "magickcow_bone_affects_shields")
            layout.prop(obj, "magickcow_collision_enabled")
            if obj.magickcow_collision_enabled:
                layout.prop(obj, "magickcow_collision_material")
    
    
    # Properties that must be displayed for lights
    def draw_light(self, layout, obj):
        layout.prop(obj.data, "magickcow_light_type")
        layout.prop(obj.data, "magickcow_light_color_diffuse")
        layout.prop(obj.data, "magickcow_light_color_ambient")
        layout.prop(obj.data, "magickcow_light_variation_type")
        layout.prop(obj.data, "magickcow_light_variation_speed")
        layout.prop(obj.data, "magickcow_light_variation_amount")
        layout.prop(obj.data, "magickcow_light_reach")
        layout.prop(obj.data, "magickcow_light_use_attenuation")
        layout.prop(obj.data, "magickcow_light_sharpness")
        layout.prop(obj.data, "magickcow_light_cutoffangle")
        layout.prop(obj.data, "magickcow_light_intensity_diffuse")
        layout.prop(obj.data, "magickcow_light_intensity_ambient")
        layout.prop(obj.data, "magickcow_light_intensity_specular")
        layout.prop(obj.data, "magickcow_light_shadow_map_size")
        layout.prop(obj.data, "magickcow_light_casts_shadows")
    
    
    # README : The collision layer / material appears under 2 if blocks in this code, not that it's bad, but important to remember when editing in the future.
    # Properties that must be displayed for meshes
    def draw_mesh(self, layout, obj):
        layout.prop(obj.data, "magickcow_mesh_type")
        
        mesh_type = obj.data.magickcow_mesh_type

        if mesh_type == "GEOMETRY":
            self.draw_mesh_geometry(layout, obj)
        
        elif mesh_type in ["WATER", "LAVA"]: # TODO : Maybe replace this with a single "LIQUID" type and then have the distinction between lava and water be done at the material level? or maybe have a subtype category / liquid type, which enforces the liquid type if the material does not match or whatever... or we could just sync it with the material, idk, we'll see in the future. For now, I just do it like this and that's it.
            self.draw_mesh_liquid(layout, obj)
        
        elif mesh_type == "COLLISION":
            self.draw_mesh_collision(layout, obj)
        
        elif mesh_type == "NAV":
            self.draw_mesh_nav(layout, obj)

        elif mesh_type == "FORCE_FIELD":
            self.draw_mesh_force_field(layout, obj)
        
        elif mesh_type == "CAMERA":
            self.draw_mesh_camera(layout, obj)

        return
    
    def draw_mesh_geometry(self, layout, obj):

        layout.prop(obj.data, "magickcow_mesh_is_visible")
        layout.prop(obj.data, "magickcow_mesh_casts_shadows")

        layout.prop(obj, "magickcow_collision_enabled")
        if(obj.magickcow_collision_enabled):
            layout.prop(obj, "magickcow_collision_material") # 1
        
        layout.prop(obj.data, "magickcow_mesh_advanced_settings_enabled")
        if(obj.data.magickcow_mesh_advanced_settings_enabled):
            layout.prop(obj.data, "magickcow_mesh_sway")
            layout.prop(obj.data, "magickcow_mesh_entity_influence")
            layout.prop(obj.data, "magickcow_mesh_ground_level")
    
    def draw_mesh_liquid(self, layout, obj):
        layout.prop(obj.data, "magickcow_mesh_can_drown")
        layout.prop(obj.data, "magickcow_mesh_freezable")
        layout.prop(obj.data, "magickcow_mesh_autofreeze")
    
    def draw_mesh_collision(self, layout, obj):
        layout.prop(obj, "magickcow_collision_material") # 2

    def draw_mesh_force_field(self, layout, obj):
        # layout.prop(obj.data, "magickcow_force_field_ripple_color")
        return
    
    # def draw_mesh_vertex_properties(self, layout, obj):
    #     layout.prop(obj.data, "magickcow_vertex_color_enabled")

    def draw_mesh_nav(self, layout, obj):
        pass

    def draw_mesh_camera(self, layout, obj):
        pass

class MagickCowPanelObjectPropertiesPhysicsEntity:
    
    def draw(self, layout, obj):
        if obj:
            if obj.type == "EMPTY":
                self.draw_empty(layout, obj)
            elif obj.type == "MESH":
                self.draw_mesh(layout, obj)
    
    def draw_empty(self, layout, obj):
        obj_type = obj.mcow_physics_entity_empty_type
        layout.prop(obj, "mcow_physics_entity_empty_type")
        if obj_type == "ROOT":
            self.draw_empty_root(layout, obj)
        elif obj_type == "BONE":
            self.draw_empty_bone(layout, obj)
    
    def draw_empty_root(self, layout, obj):
        # Simple properties
        layout.prop(obj, "mcow_physics_entity_is_movable")
        layout.prop(obj, "mcow_physics_entity_is_pushable")
        layout.prop(obj, "mcow_physics_entity_is_solid")
        layout.prop(obj, "mcow_physics_entity_mass")
        layout.prop(obj, "mcow_physics_entity_can_have_status")
        layout.prop(obj, "mcow_physics_entity_hitpoints")

        # NOTE : Using the layout.prop(obj, "mcow_physics_entity_resistances") method does not work for lists of properties ("collection properties"). You must use a box instead.

        # Resistances list
        layout.label(text="Resistances")
        layout.operator("magickcow.resistance_add_item")
        for index, item in enumerate(obj.mcow_physics_entity_resistances):
            box = layout.box()
            box.prop(item, "element")
            box.prop(item, "multiplier")
            box.prop(item, "modifier")
            remove_op = box.operator("magickcow.resistance_remove_item")
            remove_op.index = index
        
        # Gibs list
        layout.label(text="Gibs")
        layout.operator("magickcow.gibs_add_item")
        for index, item in enumerate(obj.mcow_physics_entity_gibs):
            box = layout.box()
            box.prop(item, "model")
            box.prop(item, "mass")
            box.prop(item, "scale")
            remove_op = box.operator("magickcow.gibs_remove_item")
            remove_op.index = index
    
    def draw_empty_bone(self, layout, obj):
        # TODO : Implement
        return

    def draw_mesh(self, layout, obj):
        mesh_type = obj.data.mcow_physics_entity_mesh_type
        layout.prop(obj.data, "mcow_physics_entity_mesh_type")
        if mesh_type == "GEOMETRY":
            self.draw_mesh_geometry(layout, obj)
        elif mesh_type == "COLLISION":
            self.draw_mesh_collision(layout, obj)
    
    # NOTE : Collision meshes for physics entities don't have specific collision materials / "channels", so we don't display them, unlike for level part collisions, which do have specific collision materials support.
    def draw_mesh_geometry(self, layout, obj):
        layout.prop(obj, "magickcow_collision_enabled") # Determines if complex collision is enabled or not for this visual mesh.
    
    def draw_mesh_collision(self, layout, obj):
        # NOTE : In the case of physics entities, draw nothing else, because they don't have collision material support, so we don't need to specify it.
        # layout.prop(obj, "magickcow_collision_material")
        return

# endregion

# This class is the one that controls the N-Key panel for selected object configuration.
class OBJECT_PT_MagickCowPropertiesPanel(bpy.types.Panel):

    bl_label = "MagickCow Properties"
    bl_idname = "OBJECT_PT_MagickCowProperties_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MagickCow"

    mcow_panel_none = MagickCowPanelObjectPropertiesNone()
    mcow_panel_generic = MagickCowPanelObjectPropertiesGeneric()
    mcow_panel_map = MagickCowPanelObjectPropertiesMap()
    mcow_panel_physics_entity = MagickCowPanelObjectPropertiesPhysicsEntity()

    # Base draw function. Calls the specific drawing functions based on the type of the selected object.
    def draw(self, context):
        # Get the panel's layout and the currently selected object
        layout = self.layout
        obj = context.object
        
        # Get the scene config to check what scene mode we're in
        mode = context.scene.mcow_scene_mode

        # Draw selected object properties
        # Calls the specific draw functions according to the selected scene mode
        if obj:
            if mode == "MAP":
                self.draw_panel(layout, obj, self.mcow_panel_map)
            elif mode == "PHYSICS_ENTITY":
                self.draw_panel(layout, obj, self.mcow_panel_physics_entity)
            else:
                self.draw_none(layout, obj) # Object panel draw call for case "NONE" or any other invalid value

    # NOTE : The reason I've implemented it like this is because I don't want the generic object properties to be displayed when working with the NONE scene export mode, that way we can quickly signal to the users that they forgot to configure their scene and avoid confusion when they look for settings on a panel and don't find it...
    def draw_panel(self, layout, obj, mcow_panel_type):
        self.mcow_panel_generic.draw(layout, obj) # Draw all of the properties that are common to all object types.
        mcow_panel_type.draw(layout, obj) # Draw all of the properties that are specific to the selected object type.

    def draw_none(self, layout, obj):
        self.mcow_panel_none.draw(layout, obj)

# endregion

# region Blender Object Properties Register, Unregister and Update

# region Object Properties - Map / Level

# NOTE : The name of these parameters is important, as Blender internally calls them using "self = ..." and "context = ...".
# If the names are different, the function will not properly allow objects to be modified.
def update_properties_map_empty(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return

    show_tags_true = bpy.context.scene.mcow_scene_display_tags
    show_tags_false = False

    if self.magickcow_empty_original_setting_must_update:
        # Restore the original settings and mark as updated / restored
        self.magickcow_empty_original_setting_must_update = False
        self.empty_display_type = self.magickcow_empty_original_setting_display_type
        self.show_name = self.magickcow_empty_original_setting_display_name
    
    else:
        # Save / Back Up the original settings
        self.magickcow_empty_original_setting_display_type = self.empty_display_type
        self.magickcow_empty_original_setting_display_name = self.show_name
    
    if self.magickcow_empty_type != "NONE":
        # Mark for restoration so that it will restore its original settings when returning to the default empty type ("NONE")
        self.magickcow_empty_original_setting_must_update = True
        
        # Perform the corresponding updates for each empty type
        if self.magickcow_empty_type == "LOCATOR":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
                
        elif self.magickcow_empty_type == "TRIGGER":
            self.empty_display_type = "CUBE"
            self.show_name = show_tags_true
        
        elif self.magickcow_empty_type == "PARTICLE":
            self.empty_display_type = "SPHERE"
            self.show_name = show_tags_false
        
        elif self.magickcow_empty_type == "BONE":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
        
        elif self.magickcow_empty_type == "PHYSICS_ENTITY":
            self.empty_display_type = "ARROWS"
            self.show_name = show_tags_false

def register_properties_map_empty():
    empty = bpy.types.Object
    
    # Object type for empty objects
    empty.magickcow_empty_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object",
        items = [
            ("NONE", "None", "This object will be treated as a regular empty object and will be ignored by the exporter"),
            ("ROOT", "Root", "This object will be exported as the root of the level scene"),
            ("LOCATOR", "Locator", "This object will be exported as a locator"),
            ("TRIGGER", "Trigger", "This object will be exported as a trigger"),
            ("PARTICLE", "Particle", "This object will be exported as a particle effect"),
            ("BONE", "Bone", "This object will be exported as a model bone for animated level parts"),
            ("PHYSICS_ENTITY", "Physics Entity", "This object will be exported as a physics entity"),
            # ("HIERARCHY_NODE", "Hierarchy Node", "This object will be used to structure the hierarchy of the scene. Allows the exporter to organize the objects in the scene.")
        ],
        default = "NONE", # By default, it will be marked as none, so you need to manually select whether you want the empty to be a locator or a trigger
        update = update_properties_map_empty
    )
    
    # Locator Properties
    empty.magickcow_locator_radius = bpy.props.FloatProperty(
        name = "Radius",
        description = "Radius of the locator",
        default = 2.0
    )
    
    # Particle Properties
    empty.magickcow_particle_name = bpy.props.StringProperty(
        name = "Particle",
        description = "Name of the effect XML file to use for this particle",
        default = "ambient_fire_torch"
    )
    
    empty.magickcow_particle_range = bpy.props.FloatProperty(
        name = "Range",
        description = "Range of the particle effect",
        default = 0.0
    )
    
    # Properties to save original settings of the empty (this is used in case we go back from a locator / trigger to a "none" default empty)
    empty.magickcow_empty_original_setting_display_type = bpy.props.StringProperty(
        name = "__original_display_type__",
        description = "Determines the original display type of the selected empty. Used to return to the original display config when selecting type None",
        default = "__none__",
        maxlen = 1024
    )
    empty.magickcow_empty_original_setting_display_name = bpy.props.BoolProperty(
        name = "__original_display_name__",
        description = "Determines the original display name of the selected empty. Used to return to the original display config when selecting type None",
        default = False
    )
    empty.magickcow_empty_original_setting_must_update = bpy.props.BoolProperty(
        name = "__original_display_must_update__",
        description = "Determines if the original display settings must be restored",
        default = False
    )
    
    # Bone Properties
    empty.magickcow_bone_affects_shields = bpy.props.BoolProperty(
        name = "Affects Shields",
        description = "Determines whether this animated level part will affect shields (wards) or not.",
        default = True
    )
    
    # Collision Properties
    empty.magickcow_collision_enabled = bpy.props.BoolProperty(
        name = "Has Collision",
        description = "Determines whether this object will have a collision mesh when exported or not.",
        default = True
    )
    empty.magickcow_collision_material = bpy.props.EnumProperty(
        name = "Collision Material",
        description = "Determine the collision material used by this object's collision",
        items = [
            ("GENERIC", "Generic", "The material will be marked as generic"),
            ("GRAVEL", "Gravel", "The material will be marked as gravel"),
            ("GRASS", "Grass", "The material will be marked as grass"),
            ("WOOD", "Wood", "The material will be marked as wood"),
            ("SNOW", "Snow", "The material will be marked as snow"),
            ("STONE", "Stone", "The material will be marked as stone"),
            ("MUD", "Mud", "The material will be marked as mud"),
            ("REFLECT", "Reflect", "The material will be marked as reflective. Allows beams (arcane and healing) to reflect from this surface. Used for objects like mirrors from R'lyeh."),
            ("WATER", "Water", "The material will be marked as water"),
            ("LAVA", "Lava", "The material will be marked as lava")
        ],
        default = "GENERIC"
    )

    # Physics Entity Properties
    empty.magickcow_physics_entity_name = bpy.props.StringProperty(
        name = "Template",
        description = "Name of the physics entity template XNB file to use for this physics entity",
        default = "barrel_explosive"
    )

def unregister_properties_map_empty():
    empty = bpy.types.Object
    
    del empty.magickcow_empty_type
    del empty.magickcow_locator_radius
    del empty.magickcow_empty_original_setting_display_type
    del empty.magickcow_empty_original_setting_display_name
    del empty.magickcow_empty_original_setting_must_update
    del empty.magickcow_particle_name
    del empty.magickcow_particle_range
    del empty.magickcow_bone_affects_shields
    del empty.magickcow_collision_enabled
    del empty.magickcow_collision_material
    del empty.magickcow_physics_entity_name

def update_properties_map_mesh(self, context):
    
    # Early return if the display sync is not enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return
    
    # Find all of the objects that are users of this mesh data block
    # Literally a fucking hack... I HATE this workaround to Blender's fucking bullshit hierarchy system that works like ass when doing stuff like this...
    users = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.data == self]
    
    # Update all of the properties that are object related but stored on the mesh data block
    for user in users:
        user.visible_shadow = self.magickcow_mesh_casts_shadows

def register_properties_map_mesh():
    mesh = bpy.types.Mesh
    
    # region Object type for mesh objects:
    
    mesh.magickcow_mesh_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object",
        items = [
            ("GEOMETRY", "Geometry", "This object will be exported as a piece of level geometry"), # Level Geometry
            ("COLLISION", "Collision", "This object will be exported as a piece of level collision"), # Level Collision / Collision - Level
            ("WATER", "Water", "This object will be exported as a liquid of type \"Water\""), # Liquid Water
            ("LAVA", "Lava", "This object will be exported as a liquid of type \"Lava\""), # Liquid Lava
            ("NAV", "Nav", "This object will be exported as a nav mesh"), # Nav Mesh / Navmesh
            ("FORCE_FIELD", "Force Field", "This object will be exported as a force field"), # Force Field
            ("CAMERA", "Camera", "This object will be exported as a collision mesh for camera collision") # Camera Collision / Collision - Camera
        ],
        default = "GEOMETRY"
    )

    # endregion
    
    # region Liquid properties (for both water and lava):
    
    mesh.magickcow_mesh_can_drown = bpy.props.BoolProperty(
        name = "Can Drown Entities",
        description = "Determines whether the entities that collide with this liquid's surface will die by drowning in the liquid or not. Useful for maps with shallow water like \"Eye Sockey Rink\", where entities can contact the liquid but will not instantly drown. Entities will drown both in water and lava when this setting is enabled for the selected liquid.",
        default = False
    )
    mesh.magickcow_mesh_freezable = bpy.props.BoolProperty(
        name = "Freezable",
        description = "Determines whether the liquid can be frozen or not. Note that liquid freezing works on a per vertex manner, meaning that a freezable surface needs to be subdivided to have enough vertices to allow for proper freezing behaviour.", # This is probably because it uses vertex painting / weights for freezing (makes sense if you think about how water sort of freezes in square patches in Magicka and Magicka 2). This means that a somewhat evenly distributed grid of vertices is the best way to go to make freezable liquids.
        default = False
    )
    mesh.magickcow_mesh_autofreeze = bpy.props.BoolProperty(
        name = "Auto Freeze",
        description = "Determines whether the liquid will freeze automatically or not. Useful for cold maps and areas like \"Frostjord\" where the environment is cold and water would logically freeze automatically into ice as time passes.",
        default = False
    )

    # endregion

    # region Force Field Properties

    # NOTE : Disabled because this property is now controlled via material JSON files.
    """
    mesh.magickcow_force_field_ripple_color = bpy.props.FloatVectorProperty(
        name = "Ripple Color",
        description = "Color used for the ripple effect displayed when an entity collides with the force field.\nThe lower the values, the more transparent they will appear. This means that color < 0.0, 0.0, 0.0 >, which corresponds to black, is displayed as a transparent ripple effect with no color tint.",
        subtype = "COLOR",
        default = (0.0, 0.0, 0.0),
        min = 0.0,
        max = 1.0,
        size = 3 # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
    )
    """

    # endregion

    # region Vertex Properties
    
    # NOTE : Some day in the future we may allow adding custom properties at will to the vertices, for now we're just going to roll with the same config for all meshes except for vertex color,
    # cause that's the only special case there is for now tbh. Something something ease of use etc etc...
    """
    mesh.magickcow_vertex_normal_enabled = bpy.props.BoolProperty(
        name = "Use Vertex Normals",
        description = "Allow vertex normals to be exported for this mesh",
        default = True
    )
    mesh.magickcow_vertex_tangent_enabled = bpy.props.BoolProperty(
        name = "Use Vertex Tangents",
        description = "Allow vertex tangents to be exported for this mesh",
        default = True
    )
    mesh.magickcow_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        description = "Export the vertex color property for this mesh",
        default = True
    )
    """
    # endregion

    # region Extra Deferred Effect Instance Properties / Advanced Mesh Settings

    mesh.magickcow_mesh_advanced_settings_enabled = bpy.props.BoolProperty(
        name = "Enable Advanced Settings",
        description = "Enable advanced mesh render settings related to the way the Deferred Effect instance will be rendered in-game.",
        default = False
    )

    # NOTE : These values properties describe values that correspond to parameters of the deferred effect's shader.
    # These values are ONLY applied by Magicka to static root node mesh parts of the level model, and they are applied to the RenderDeferredEffect instance (keyword INSTANCE!!!) used by said mesh part, which means
    # that this is a property that is not stored on the effect "material" file, but rather applied during runtime to specific instances of the material, and altough theoretically one could inject these values
    # into memory on effect instances that are assigned to animated level parts, these properties are actually only loaded by the game when reading them from root nodes, so they can only be used on static level parts.
    # The reader code for render deferred effects does NOT read these properties directly, so that means that the only way to modify them in vanilla Magicka executables is through the BiTreeRootNode's properties, which
    # set these values and then apply them to their material / effect instance.

    mesh.magickcow_mesh_sway = bpy.props.FloatProperty(
        name = "Sway",
        description = "Set the value of the \"sway\" property of the Deferred Effect instance used by this mesh. Determines how much sway the vertices of this mesh will have. Used to simulate swaying motions such as that of plants like grass and leaves.",
        default = 0.0
    )

    mesh.magickcow_mesh_entity_influence = bpy.props.FloatProperty(
        name = "Entity Influence",
        description = "Set the value of the \"EntityInfluence\" property of the Deferred Effect instance used by this mesh.",
        default = 0.0
    )

    mesh.magickcow_mesh_ground_level = bpy.props.FloatProperty(
        name = "Ground Level",
        description = "Set the value of the \"GroundLevel\" property of the Deferred Effect instance used by this mesh.",
        default = -10.0 # NOTE : We used to hard code this to -10 on the make stage, and it has worked pretty well as a default value for a long time up until now, so that's literally the only reason why -10 is the default value now that ground level is an editable property, because it's battle tested, and because of legacy reasons, lol... in short: It's -10 because history, no other objective reason. The first value I saw on the first map I decompiled was something close to this, so I just rounded the value and called it a day, and it's been like that ever since. Literally just that.
    )

    # endregion

    # region Mesh Visual Properties

    mesh.magickcow_mesh_is_visible = bpy.props.BoolProperty(
        name = "Is Visible",
        description = "Determine whether this mesh should be visible in-game or not",
        default = True,
        update = update_properties_map_mesh
    )

    mesh.magickcow_mesh_casts_shadows = bpy.props.BoolProperty(
        name = "Casts Shadows",
        description = "Determine whether this mesh should cast shadows over other meshes in-game or not",
        default = True,
        update = update_properties_map_mesh
    )

    # endregion

def unregister_properties_map_mesh():
    mesh = bpy.types.Mesh
    
    del mesh.magickcow_mesh_type
    del mesh.magickcow_mesh_can_drown
    del mesh.magickcow_mesh_freezable
    del mesh.magickcow_mesh_autofreeze
    # del mesh.magickcow_force_field_ripple_color

    # del mesh.magickcow_vertex_normal_enabled
    # del mesh.magickcow_vertex_tangent_enabled
    # del mesh.magickcow_vertex_color_enabled

    del mesh.magickcow_mesh_advanced_settings_enabled
    del mesh.magickcow_mesh_sway
    del mesh.magickcow_mesh_entity_influence
    del mesh.magickcow_mesh_ground_level

    del mesh.magickcow_mesh_is_visible
    del mesh.magickcow_mesh_casts_shadows

def update_properties_map_light(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return
    
    self.type = self.magickcow_light_type # The enum literally has the same strings under the hood, so we can just assign it directly.
    self.color = self.magickcow_light_color_diffuse # The color is normalized, so they are identical values.
    self.use_shadow = self.magickcow_light_casts_shadows # Update the use shadows property to match with the mcow config for visualization purposes.
    
    # Approximation for light radius and intensity because there is no way in modern Blender to set exact light radius for some reason.
    if self.type == "SUN":
        self.energy = 10 * self.magickcow_light_intensity_diffuse
    else:
        self.energy = 100 * self.magickcow_light_intensity_diffuse * self.magickcow_light_reach
        self.use_custom_distance = True
        self.cutoff_distance = self.magickcow_light_reach

def register_properties_map_light():
    light = bpy.types.Light

    # NOTE : If the values from the props synced with blender props are changed from the Blender UI panel, the sync breaks.
    # The syncing is performed only for visual reasons "in-editor" (aka for visualization within Blender to be prettier with lights using the right color and stuff...), the real final
    # values used should be extracted from the mcow properties, so this desync should not matter, as it is only visual, and will only last until the mcow prop is modified once more, syncing them again. 

    # Light type settings:
    # NOTE : The enum values are literally the same as Blender's base lights so that the update function can update the light types automatically.
    light.magickcow_light_type = bpy.props.EnumProperty(
        name = "",
        description = "",
        items = [
            ("POINT", "Point", "This light will be treated as a point light."),
            ("SUN", "Directional", "This light will be treated as a directional light (Sun)."),
            ("SPOT", "Spot", "This light will be treated as a spotlight.")
        ],
        default = "POINT",
        update = update_properties_map_light
    )

    # Light Variation Settings:
    light.magickcow_light_variation_type = bpy.props.EnumProperty(
        name = "Variation Type",
        description = "Determine the type of light variation to be used by this light source when exported.",
        items = [
            ("NONE", "None", "This light will have no variation"),
            ("SINE", "Sine", "This light will have the variation determined by a sine wave"),
            ("FLICKER", "Flicker", "This light will flicker"),
            ("CANDLE", "Candle", "This light will behave like a candle"),
            ("STROBE", "Strobe", "This light will behave like a strobe")
        ],
        default = "NONE"
    )
    
    light.magickcow_light_variation_speed = bpy.props.FloatProperty(
        name = "Variation Speed",
        description = "The speed of light variation",
        default = 0.0
    )
    
    light.magickcow_light_variation_amount = bpy.props.FloatProperty(
        name = "Variation Amount",
        description = "The amount of light variation",
        default = 0.0
    )
    
    # Light radius settings
    light.magickcow_light_reach = bpy.props.FloatProperty(
        name = "Reach",
        description = "The \"distance\" or \"radius\" of effect of the light.\n - For point lights, it defines the radius.\n - For spot lights, it defines the length of the light.\n - For directional lights, it is ignored.",
        default = 5.0,
        update = update_properties_map_light
    )
    
    # Light attenuation and cutoff settings
    light.magickcow_light_use_attenuation = bpy.props.BoolProperty(
        name = "Use Attenuation",
        description = "Determines if the light should use attenuation or not",
        default = False
    )
    
    light.magickcow_light_cutoffangle = bpy.props.FloatProperty(
        name = "Cutoff Angle",
        description = "Angle at which the light is cut off",
        default = 0.0
    )
    
    light.magickcow_light_sharpness = bpy.props.FloatProperty(
        name = "Sharpness",
        description = "Sharpness of the light",
        default = 0.0
    )
    
    # Light color properties
    light.magickcow_light_color_diffuse = bpy.props.FloatVectorProperty(
        name = "Diffuse Color",
        description = "Difuse color of the light",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3, # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
        update = update_properties_map_light
    )
    
    light.magickcow_light_color_ambient = bpy.props.FloatVectorProperty(
        name = "Ambient Color",
        description = "Ambient color of the light",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3 # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
    )
    
    # Intensity settings:
    light.magickcow_light_intensity_specular = bpy.props.FloatProperty(
        name = "Specular Intensity",
        description = "Specular intensity of the light",
        default = 0.0
    )
    
    light.magickcow_light_intensity_diffuse = bpy.props.FloatProperty(
        name = "Diffuse Intensity",
        description = "Intensity of the light's diffuse color emission. Acts as a multiplier over the diffuse color value. The result is NOT clamped to the [0,1] interval.",
        default = 1.0,
        update = update_properties_map_light
    )
    
    light.magickcow_light_intensity_ambient = bpy.props.FloatProperty(
        name = "Ambient Intensity",
        description = "Intensity of the light's ambient color. Acts as a multiplier over the ambient color value. The result is NOT clamped to the [0,1] interval.",
        default = 1.0
    )
    
    # Other light settings:
    light.magickcow_light_shadow_map_size = bpy.props.IntProperty(
        name = "Shadow Map Size",
        description = "Size of the shadow map used for the light",
        default = 64,
        min = 0
    )
    
    light.magickcow_light_casts_shadows = bpy.props.BoolProperty(
        name = "Casts Shadows",
        description = "Determine whether this light source should cast shadows or not",
        default = True,
        update = update_properties_map_light
    )

def unregister_properties_map_light():
    light = bpy.types.Light
    
    del light.magickcow_light_type
    del light.magickcow_light_variation_type
    del light.magickcow_light_variation_speed
    del light.magickcow_light_variation_amount
    del light.magickcow_light_reach
    del light.magickcow_light_use_attenuation
    del light.magickcow_light_cutoffangle
    del light.magickcow_light_sharpness
    del light.magickcow_light_color_diffuse
    del light.magickcow_light_color_ambient
    del light.magickcow_light_intensity_specular
    del light.magickcow_light_intensity_diffuse
    del light.magickcow_light_intensity_ambient
    del light.magickcow_light_shadow_map_size
    del light.magickcow_light_casts_shadows

def register_properties_map():
    # Register the properties for each object type
    register_properties_map_empty()
    register_properties_map_mesh()
    register_properties_map_light()

def unregister_properties_map():
    # Unregister the properties for each object type
    unregister_properties_map_empty()
    unregister_properties_map_mesh()
    unregister_properties_map_light()

# endregion

# region Object Properties - Physics Entity

# TODO : Implement
# TODO : In the future maybe rework the system so that custom properties are stored within dicts so that we can actually have a better organization and just delete the dict rather than each prop one by one?

def update_properties_physics_entity_empty(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return

    show_tags_true = bpy.context.scene.mcow_scene_display_tags
    show_tags_false = False

    if self.magickcow_empty_original_setting_must_update:
        # Restore the original settings and mark as updated / restored
        self.magickcow_empty_original_setting_must_update = False
        self.empty_display_type = self.magickcow_empty_original_setting_display_type
        self.show_name = self.magickcow_empty_original_setting_display_name
    
    else:
        # Save / Back Up the original settings
        self.magickcow_empty_original_setting_display_type = self.empty_display_type
        self.magickcow_empty_original_setting_display_name = self.show_name
    
    if self.mcow_physics_entity_empty_type != "NONE":
        # Mark for restoration so that it will restore its original settings when returning to the default empty type ("NONE")
        self.magickcow_empty_original_setting_must_update = True
        
        # Perform the corresponding updates for each empty type
        if self.mcow_physics_entity_empty_type == "BONE":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
        
        elif self.mcow_physics_entity_empty_type == "ROOT":
            self.empty_display_type = "SPHERE"
            self.show_name = show_tags_false
        
        elif self.mcow_physics_entity_empty_type == "BOUNDING_BOX":
            self.empty_display_type = "CUBE"
            self.show_name = show_tags_true

def register_properties_physics_entity_empty():
    
    empty = bpy.types.Object
    
    # region Properties - Generic

    # Object type for empty objects
    empty.mcow_physics_entity_empty_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object.",
        items = [
            ("NONE", "None", "This object will be treated as a regular empty object and will be ignored by the exporter."),
            ("ROOT", "Root", "This object will be exported as the root of a physics entity."),
            ("BONE", "Bone", "This object will be exported as a model bone for a physics entity."),
            ("BOUNDING_BOX", "Bounding Box", "This Object will be exported as a bounding box for the physics entity.")
        ],
        default = "NONE", # By default, it will be marked as none, so you need to manually select what type of point data object you want this to be
        update = update_properties_physics_entity_empty
    )

    # endregion

    # region Properties - Root

    # region Deprecated
    
    # NOTE : Discarded for now because I'm actually going to get the name / ID from the name of the root object in the inspector panel.
    # empty.mcow_physics_entity_id = bpy.props.StringProperty(
    #     name = "ID", # NOTE : The ID must be unique!!! each physics entity asset must have its own unique name within the game's data!!!
    #     description = "Determine the ID of this physics entity",
    #     default = "root"
    # )

    # endregion

    empty.mcow_physics_entity_is_movable = bpy.props.BoolProperty(
        name = "Is Movable", # This hurts me... movable is the "correct" modern spelling used nowadays, moveable is my preferred spelling, altough it is an archaism and nobody really uses it anymore... fuck me, but yeah, I'll pick whatever people use the most so as to make it more user friendly I guess...
        description = "Determines whether this physics entity can be moved or not.",
        default = False
    )

    empty.mcow_physics_entity_is_pushable = bpy.props.BoolProperty(
        name = "Is Pushable",
        description = "Determines whether this physics entity can be pushed or not.",
        default = False
    )

    empty.mcow_physics_entity_is_solid = bpy.props.BoolProperty(
        name = "Is Solid",
        description = "Determines whether this physics entity is solid or not.",
        default = True
    )

    empty.mcow_physics_entity_mass = bpy.props.FloatProperty(
        name = "Mass",
        description = "Determines the mass of this physics object.",
        default = 200
    )

    empty.mcow_physics_entity_hitpoints = bpy.props.IntProperty(
        name = "Health",
        description = "Determines the number of hit points for this physics object.",
        default = 300
    )

    empty.mcow_physics_entity_can_have_status = bpy.props.BoolProperty(
        name = "Can Have Status",
        description = "Determines whether the physics entity can have a status or not.",
        default = True
    )

    empty.mcow_physics_entity_resistances = bpy.props.CollectionProperty(
        type = MagickCowProperty_Resistance,
        name = "Resistances",
        description = "Determines the elemental resistances and weaknesses of this physics entity."
    )

    empty.mcow_physics_entity_gibs = bpy.props.CollectionProperty(
        type = MagickCowProperty_Gib,
        name = "Gibs",
        description = "List of the gibs spawned by this physics entity when destroyed."
    )

    # endregion
    
    return

def unregister_properties_physics_entity_empty():
    empty = bpy.types.Object

    del empty.mcow_physics_entity_empty_type

    del empty.mcow_physics_entity_is_movable
    del empty.mcow_physics_entity_is_pushable
    del empty.mcow_physics_entity_is_solid
    del empty.mcow_physics_entity_mass
    del empty.mcow_physics_entity_hitpoints
    del empty.mcow_physics_entity_can_have_status

    del empty.mcow_physics_entity_resistances
    del empty.mcow_physics_entity_gibs

    return

def register_properties_physics_entity_mesh():
    mesh = bpy.types.Mesh

    mesh.mcow_physics_entity_mesh_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determines the type of object this piece of geometry will be exported as.",
        items = [
            ("GEOMETRY", "Geometry", "This mesh will be exported as a piece of visual geometry for the physics entity."),
            ("COLLISION", "Collision", "This mesh will be exported as a collision mesh for the physics entity.")
        ],
        default = "GEOMETRY"
    )

def unregister_properties_physics_entity_mesh():
    mesh = bpy.types.Mesh

    del mesh.mcow_physics_entity_mesh_type

def register_properties_physics_entity():
    register_properties_physics_entity_empty()
    register_properties_physics_entity_mesh()

def unregister_properties_physics_entity():
    unregister_properties_physics_entity_empty()
    unregister_properties_physics_entity_mesh()

# endregion

# region Object Properties - Generic

# Generic properties are properties that all objects share no matter their type.

def register_properties_generic():
    obj = bpy.types.Object

    # Allow export option for all objects:
    obj.magickcow_allow_export = bpy.props.BoolProperty(
        name = "Export",
        description = "Determines whether this object will be exported or not. If set to false, the object will be ignored by the exporter, as well as all of its children objects.",
        default = True
    )

def unregister_properties_generic():
    obj = bpy.types.Object
    
    del obj.magickcow_allow_export

# endregion

# region Global Register and Unregister functions for objects

def register_properties_object():

    # Register the properties that all objects should have
    register_properties_generic()

    # Register the properties for each object type and for each scene mode type
    register_properties_map()
    register_properties_physics_entity()

    # Register the class for the properties panel itself
    bpy.utils.register_class(OBJECT_PT_MagickCowPropertiesPanel)

def unregister_properties_object():

    # Unregister the properties that all objects should have
    unregister_properties_generic()

    # Unregister the properties for each object type and for each scene mode type
    unregister_properties_map()
    unregister_properties_physics_entity()

    # Unregister the class for the properties panel itself
    bpy.utils.unregister_class(OBJECT_PT_MagickCowPropertiesPanel)

# endregion

# endregion

# ../mcow/classes/Blender/Panels/Scene.py
# region Blender Panel Classes for Scene Panel

# This class is the one that controls the N-Key panel for global scene config.
# region Comment
    # It is inspired by Valve's blender source tools, where they have the equivalent of this panel on the scene menu.
    # In my case, I am not sure this is the best way to go, as we could also make this an N-Key panel that works without selecting any objects, but as of now I have decided to make it like this because it feels
    # like it would make things less cluttered. The right most panel, which is where the scene panel is located by default, is pretty large by default and it is a location that makes sense for the kind of configuration
    # that it will store, so I'd rather put it there, since I believe this is more intuitive for Blender users than coming up with my own conventions.
# endregion
class MagickCowScenePanel(bpy.types.Panel):
    bl_label = "MagickCow Scene Configuration"
    bl_idname = "SCENE_PT_MagickCow_Scene_Tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene" # This makes the panel appear on under the Scene Properties.

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Scene Display Settings")
        layout.prop(scene, "mcow_scene_display_tags")
        layout.prop(scene, "mcow_scene_display_sync")

        layout.label(text="Scene Export Settings")
        layout.prop(scene, "mcow_scene_mode")
        layout.prop(scene, "mcow_scene_base_path")
        layout.prop(scene, "mcow_scene_animation")
        
        layout.label(text="JSON Export Settings")
        layout.prop(scene, "mcow_scene_json_pretty")
        if scene.mcow_scene_json_pretty:
            layout.prop(scene, "mcow_scene_json_char")
            if scene.mcow_scene_json_char == "SPACE":
                layout.prop(scene, "mcow_scene_json_indent")

# endregion

# region Blender Scene Panel functions, Register and Unregister functions

def update_properties_scene_none(self, context):
    # NOTE : This is an aux function whose purpose is to restore all of the empties to their saved state when setting the scene mode to None (aka neither Map nor PhysicsEntity export mode)
    empties = [obj for obj in bpy.data.objects if obj.type == "EMPTY"]
    for empty in empties:
        empty.show_name = empty.magickcow_empty_original_setting_display_name
        empty.empty_display_type = empty.magickcow_empty_original_setting_display_type

def update_properties_scene_map(self, context):
    
    empties = [obj for obj in bpy.data.objects if obj.type == "EMPTY"]
    for empty in empties:
        update_properties_map_empty(empty, context)
    
    lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
    for light in lights:
        update_properties_map_light(light, context)
    
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    for mesh in meshes:
        update_properties_map_mesh(mesh, context)

def update_properties_scene_physics_entity(self, context):
    empties = [obj for obj in bpy.data.objects if obj.type == "EMPTY"]
    for empty in empties:
        update_properties_physics_entity_empty(empty, context)

def update_properties_scene(self, context):
    
    # NOTE : The "self" parameter is simply ignored in this case.
    # We just want to iterate over all of the objects of a given set of types in the scene and call their respective update methods if required to keep the visualization up to date.

    if context.scene.mcow_scene_mode == "MAP":
        update_properties_scene_map(self, context)
    
    elif context.scene.mcow_scene_mode == "PHYSICS_ENTITY":
        update_properties_scene_physics_entity(self, context)
    
    else:
        update_properties_scene_none(self, context)

def register_properties_scene():

    # Register properties for the scene panel

    # By default, it will be marked as None, so you need to manually select what type of object you want to export the scene as.
    # This is done as a safeguard to prevent unexpectedly long export times or receiving an unexpected output exported file, which would needlessly waste the user's time if they
    # forget to pick the type when this could just error out quickly.
    # The resulting behaviour is that the program simply displays an error when the export button is pressed, notifying the user that the export process failed because no export type was chosen / selected.
    bpy.types.Scene.mcow_scene_mode = bpy.props.EnumProperty(
        name = "Export Mode",
        description = "Select the type of object that will be exported when exporting the current scene to a JSON file.",
        items = [
            ("NONE", "None", "The current scene will not be exported as any type of object. Exporting as a MagickaPUP JSON file will be disabled until the user selects what type of export they want to perform with the current scene."),
            ("MAP", "Map", "The current scene will be exported as an asset containing a map for Magicka."),
            ("PHYSICS_ENTITY", "Physics Entity", "The current scene will be exported as an asset containing a physics entity for Magicka.")
        ],
        default = "NONE",
        update = update_properties_scene
    )

    bpy.types.Scene.mcow_scene_json_pretty = bpy.props.BoolProperty(
        name = "Pretty Format",
        description = "The JSON file will be exported with indentation and newlines for easier reading. Slows down export times due to the extra processing required. Also increasing the resulting file size."
    )

    bpy.types.Scene.mcow_scene_json_indent = bpy.props.IntProperty(
        name = "Indent Depth",
        description = "Number of space characters to use in the output JSON file for indentation. This setting is ignored if pretty JSON formatting is disabled.",
        default = 2,
        min = 1,
        max = 256 # Again, who in the name of fuck will ever use this? I don't know, but fuck you if you do! lmao...
    )

    bpy.types.Scene.mcow_scene_json_char = bpy.props.EnumProperty(
        name = "Indent Character",
        description = "The character to be used to indent in the generated JSON files.",
        items = [
            ("SPACE", "Space", "Space character (' ')"),
            ("TAB", "Tab", "Tab character ('\\t')")
        ],
        default = "SPACE"
    )

    # NOTE : A list of benefits of storing all of the export config within the scene panel rather than the export menu:
    # - The settings are saved across sessions (extremely useful for the base folder path, it used to be extremely fucking annoying for it to disappear all the time when reopening a Blender project...)
    # - The settings are tied to a specific blend file within a single session rather than being carried over across scenes (if you have multiple scenes, and some are maps and others are assets, it can become a fucking pain in the ass to constantly have to change the export settings and fine tune them, when you could just do it once and be done with it...)
    # Note that having to reconfigure the export each time you make a new project is an extremely minor inconvenience compared to the crap one had to put up with before... not to mention that this is how Valve does it in their source tools for blender...
    # In short, it is far more benefitial to associate these settings on a per project basis than on a global basis for the entire editor...
    bpy.types.Scene.mcow_scene_base_path = bpy.props.StringProperty(
        name = "Base Directory Path",
        description = "Select the path in which the exporter will look for the base directory. This directory contains JSON files which correspond to effects (materials) that will be applied to the surfaces that have a material with the name of the corresponding effect file to be used.",
        default = "C:\\"
    )

    # TODO : Improve the description string so that it is more generic and also applies to all other forms of exportable object types / scene types rather than being specific to level (map) export.
    bpy.types.Scene.mcow_scene_animation = bpy.props.BoolProperty(
        name = "Export Animation Data",
        description = "Determines whether the animation data of the current scene will be exported or not.\n - If True : The animated level parts will be exported, including all of the child objects and animation data.\n - If False : The animated level parts will be completely ignored and not exported. All children components, including geometry, lights, and any other type of object, that is attached to animated level parts, will also be ignored.\n - Note : The animated level parts root still needs to be present for the exporter to properly generate the level data.",
        default = False
    )

    bpy.types.Scene.mcow_scene_display_tags = bpy.props.BoolProperty(
        name = "Display Object Tags",
        description = "Display name tags for point data objects such as locators and triggers.",
        default = True,
        update = update_properties_scene
    )

    bpy.types.Scene.mcow_scene_display_sync = bpy.props.BoolProperty(
        name = "Synchronize Displayed State",
        description = "Synchronize the displayed state with the internal state of MagickCow object configuration. Useful for visualization purposes.",
        default = True,
        update = update_properties_scene
    )

    # Register the scene panel itself
    bpy.utils.register_class(MagickCowScenePanel)

def unregister_properties_scene():
    
    # Unregister properties for the scene panel
    del bpy.types.Scene.mcow_scene_mode
    del bpy.types.Scene.mcow_scene_json_pretty
    del bpy.types.Scene.mcow_scene_json_indent
    del bpy.types.Scene.mcow_scene_base_path
    del bpy.types.Scene.mcow_scene_animation
    del bpy.types.Scene.mcow_scene_display_tags
    del bpy.types.Scene.mcow_scene_display_sync

    # Unregister the scene panel
    bpy.utils.unregister_class(MagickCowScenePanel)

# endregion

# ../mcow/functions/utility/Utility.py
# region General Purpose Utility Functions

# TODO : Move a lot of this functionality into the generic DataGenerator base class...
# TODO : Fucking cleanup this section of the code, this is fucking insane and I bet there's tons of unused functionality here that could fuck right off!

# Get transform of an object relative to the transform of another object.
# Returns transform of object_b relative to object_a
# We have 2 transforms, A and B. We want to get B relative to A. We have to calculate the inverse of A and apply it to B.
# Note : Blender works with column major matrices, so the multiplication order is as follows:
# 1) Get matrix A^-1 (inverse of A, which will represent the transform that takes us from A to the origin O)
# 2) Get final transform as B' = A^-1 * B to get the transform B relative to A.
# Can be thought of as calculating:
# B' = transform_that_goes_from_A_to_Origin(transform_that_goes_from_Origin_to_B())
def get_relative_transform_obj(obj_a, obj_b):
    matrix_a = obj_a.matrix_world
    matrix_b = obj_b.matrix_world
    matrix_a_inv = matrix_a.inverted()
    matrix_b_relative = matrix_a_inv @ matrix_b
    return matrix_b_relative

def get_relative_transform(matrix_a, matrix_b):
    matrix_a_inv = matrix_a.inverted()
    matrix_b_relative = matrix_a_inv @ matrix_b
    return matrix_b_relative


# Get the object transform relative to its parent.
# If the parent is a bone (animated level part), then the coordinates are relative to the parent.
# Otherwise, the coordinates will be global (relative to the world origin, which means that we could think of it as the parent being "None")
def get_object_transform(obj, parent = None):
    if parent is not None:
        return get_relative_transform(parent.matrix_world, obj.matrix_world) # returns a new matrix generated when using the @ operator to calculate the resulting transform matrix.
    return obj.matrix_world.copy() # make it into a copy to prevent carrying over a reference of the matrix.

# Clamp input value to the interval [min, max]
def clamp(n, min, max):
    ans = n
    if ans < min:
        ans = min
    elif ans > max:
        ans = max
    return ans

# Find index of the input element within the input list. Can be configured to return a default index value.
def find_element_index(elements_list, element, return_on_error = -1):
    for i in range(0, len(elements_list)):
        if elements_list[i] == element:
            return i
    return return_on_error

def find_element(elements_list, index, return_on_error = 0):
    if index >= 0 and index < len(elements_list):
        return elements_list[index]
    return elements_list[return_on_error]

def find_light_type_index(light):
    return find_element_index(["POINT", "SUN", "SPOT"], light, 0)

def find_light_type_name(light):
    return find_element(["POINT", "SUN", "SPOT"], light, 0)

def find_collision_material_index(material):
    return find_element_index(["GENERIC", "GRAVEL", "GRASS", "WOOD", "SNOW", "STONE", "MUD", "REFLECT", "WATER", "LAVA"], material, 0)

def find_collision_material_name(material):
    return find_element(["GENERIC", "GRAVEL", "GRASS", "WOOD", "SNOW", "STONE", "MUD", "REFLECT", "WATER", "LAVA"], material, 0)

def find_light_variation_type_index(light_variation):
    return find_element_index(["NONE", "SINE", "FLICKER", "CANDLE", "STROBE"], light_variation, 0)

def find_light_variation_type_name(light_variation):
    return find_element(["NONE", "SINE", "FLICKER", "CANDLE", "STROBE"], light_variation, 0)

# Scene object getters functions. They return objects according to the type of query made.
def get_all_objects():
    objs = bpy.data.objects
    return objs

def get_scene_root_objects():
    objs = get_all_objects()
    ans = []
    for obj in objs:
        if obj.parent is None:
            ans.append(obj)
    return ans

def get_immediate_children(obj): # "inmediato" en Inglés es con 2 'M's, no te líes xd
    ans = obj.children
    return ans

def get_all_children_rec(ans, obj):
    for child in obj.children:
        ans.append(child)
        get_all_children_rec(ans, child)

def get_all_children(obj):
    ans = []
    get_all_children_rec(ans, obj)
    return ans


# Append 2 paths together
def path_append(path1, path2):
    c1 = path1[-1]
    c2 = path2[0]
    
    path1_has_separator = (c1 == '/' or c1 == '\\')
    path2_has_separator = (c2 == '/' or c2 == '\\')
    
    separator = ""
    
    if path1_has_separator and path2_has_separator:
        separator = "."
    elif path1_has_separator or path2_has_separator:
        separator = ""
    else:
        separator = "/"
    
    return path1 + separator + path2


# Returns a tuple with forward, up and right vectors.
# Better to think of them as local-x-vector, local-y-vector and local-z-vector since we don't really know what is "forward" and "right" in Magicka, we only know that y is up.
# When we deal with the animated mesh format, we might eventually figure out what the "true" right and forward vectors are according to the devs of the game (what I mean with this is which axes are considered "forward" and "right" in the assets and in game code as they were created... maybe this is not even consistent between assets!)... for now, pfff... who knows!
def get_directional_vectors(input_matrix):
    # Get right, forward and up vectors
    x_vec = input_matrix.col[0].xyz
    y_vec = input_matrix.col[1].xyz
    z_vec = input_matrix.col[2].xyz
    
    # Normalize the vectors
    x_vec = x_vec.normalized()
    y_vec = y_vec.normalized()
    z_vec = z_vec.normalized()
    
    # Create tuple with the 3 directional vectors
    ans = (x_vec, y_vec, z_vec)
    
    return ans

# Function that reads the data of a JSON file and returns it as a dict.
# Mainly used to get data for materials (which are known as "effects" on Magicka's code)
# If the specified path does not exist, it returns by default an empty dict
def get_json_object(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    return {}

# endregion

# region Object Utility Functions

# TODO : Normalize the unit vector in case the input vector tuple is not normalized...
def get_orientation_vector(transform, unit_vector = (0.0, 0.0, -1.0)):
    # Orientation vector is obtained by rotating the unitary vector, for example <0,0,-1>, and making it face in the direction of the object. In short, rotation is stored as an orientation, which is a director vector that points toward the direction forward vector of the object (it IS the forward vector after all).
    loc, rotquat, scale = transform.decompose()
    vec = mathutils.Vector(unit_vector)
    vec = rotquat @ vec
    return vec

def get_transform_data(transform, unit_vector = (0.0, 0.0, -1.0)):
    loc, rotquat, scale = transform.decompose()
    vec = mathutils.Vector(unit_vector)
    orientation = rotquat @ vec
    return (loc, rotquat, scale, orientation)

# endregion

# region Animation Utility Functions

# Iterates over all of the FCurves of an animation Action and returns all of the frames in sorted order.
# This way, if an FCurve has different frames from another, the exported animation will still be correct.
# An example of this situation would be making an animation that has multiple keyframes for position (translation), but has only 2 keyframes for the rotation and one or none for the scale, etc...
# Each component of the transform has its own FCurve, and it is not guaranteed that the user always registered all of the properties on each keyframe, so it is better to be safe than sorry and fetch
# all of the existing keyframes, no matter what kind of information they represent / contain. That way, we will be able to just evaluate the position, rotation and scale on each of the registered frames.
# (Remember that Magicka's animation system requires having all 3 components on each frame, so this evaluation system is a pretty good solution as it is...)
def get_action_keyframes(action):
    frames = set()
    if action:
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                frames.add(keyframe.co[0])
    return sorted(frames)

# endregion

# region Vector Utility Functions

def vec3_point_to_y_up(vec3):
    ans = (vec3[0], vec3[2], -vec3[1])
    return ans

def vec3_point_to_z_up(vec3):
    ans = (vec3[0], -vec3[2], vec3[1])
    return ans

# NOTE : Maybe it would be better to not use this function since mathutils.Matrix already has the .transposed() method, which is probably faster... 
def mat4x4_mat_tranpose(m):
    transposed = [list(row) for row in zip(*m)]
    return transposed

# region Comment - mat4x4_buf2mat_rm2cm_yu2zu()
# Matrix 4x4 -> Matrix 4x4 
# linear buffer -> matrix
# row-major -> column-major
# Y-Up -> Z-Up
# endregion
def mat4x4_buf2mat_rm2cm_yu2zu(m):
    # NOTE : This code actually translates a row-major 4x4 matrix from Y up to Z up.
    # The objective is to be a bit more generic, so the function should transform asuming the input is in column major maybe?
    ans = [
        [ m[ 0], -m[ 8],  m[ 4],  m[12]],
        [-m[ 2],  m[10], -m[ 6], -m[14]],
        [ m[ 1], -m[ 9],  m[ 5],  m[13]],
        [ m[ 3], -m[11],  m[ 7],  m[15]]
    ]
    return ans

# Input: (x, y, z) in Y-Up
# Output: (x, y, z) in Z-Up
def point_to_z_up(p):
    return mathutils.Vector([p[0], -p[2], p[1]])

# Input: (x, y, z, w) in Y-Up
# Output: (w, x, y, z) in Z-Up
def quat_to_z_up(q):
    return mathutils.Quaternion([q[3], q[0], -q[2], q[1]])

# Input: (x, y, z) in Y-Up
# Output: (x, y, z) in Z-Up
def scale_to_z_up(s):
    return mathutils.Vector([s[0], s[2], s[1]])

# TODO : Implement these functions and change the exporter code to use this instead of the whole -X rotation bullshit.
# This change, when applied in a future update, will prevent the exporter from exporting wrong values when dealing with certain hierarchies.
# It will also completely get rid of the small margin of floating point precision error there exists when using a rotation matrix (float multiplications and divisions)
# rather than just swapping values and flipping signs, which preserve the same exact float values without any issues or precision errors when changing from z up to y up and viceversa.
# def point_to_y_up(p):
#     return None
# 
# def quat_to_y_up(q):
#     return None
# 
# def scale_to_y_up(s):
#     return None

# endregion

# ../mcow/functions/utility/Effect.py
# region Material Utility Functions

# NOTE : Magicka / XNA "Effects" are linked to Blender Materials on this Blender addon.

# NOTE : Here I'm sort of experimenting with static classes with @staticmethod to simulate namespaces in python... we'll see how it goes...
# Also going back to my snake_case C roots, which is more in line with PEP8. I'm just kind of tired of C#'s / Microsoft PascalCase I suppose.

class material_utility:
    
    # NOTE : The obj param is the blender Object param.
    # NOTE : The mesh param is the mesh data, aka, obj.data.
    # Basically, the nomenclature used here is the same as everywhere else. At some point in history it was not, but do not get confused, because now it is! Just keep that in mind or things will go south real fast...
    
    # region Blender Material

    # If the material does not exist, then we return None (null). Otherwise, we return the reference to the blender material instance itself.
    @staticmethod
    def get_material(obj, material_index):
        num_materials = len(obj.data.materials)
        if num_materials > 0:
            min_idx = 0
            max_idx = num_materials - 1
            if material_index >= min_idx and material_index <= max_idx:
                return obj.data.materials[material_index]
        return None

    # endregion

    # region Material Info / All Material Data (basically, get both the name and the data generated in one go with these functions)

    # NOTE : Basically, these are the top-level functions that you should try to use most of the time.

    @staticmethod
    def get_material_effect_info(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_name = material_utility.get_material_name(material, obj.data.magickcow_mesh_type)
        material_data = material_utility.get_material_data(material, obj.data.magickcow_mesh_type)
        return (material_name, material_data)

    @staticmethod
    def get_material_name_from_mesh(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_name = material_utility.get_material_name(material, obj.data.magickcow_mesh_type)
        return material_name
    
    @staticmethod
    def get_material_data_from_mesh(obj, material_index):
        material = material_utility.get_material(obj, material_index)
        material_data = material_utility.get_material_data(material, obj.data.magickcow_mesh_type)
        return material_data

    # endregion

    # region Material Name

    @staticmethod
    def get_material_name(material, fallback_type = "GEOMETRY"):
        if material is not None:
            return material_utility.get_material_name_instance(material)
        else:
            return material_utility.get_material_name_default(fallback_type)

    @staticmethod
    def get_material_name_default(fallback_type = "GEOMETRY"):
        ans = "base/default"

        if fallback_type == "GEOMETRY":
            ans = "base/default_geometry"
        elif fallback_type == "WATER":
            ans = "base/default_water"
        elif fallback_type == "LAVA":
            ans = "base/default_lava"
        elif fallback_type == "FORCE_FIELD":
            ans = "base/ff/default_force_field"

        return ans

    @staticmethod
    def get_material_name_instance(material):
        return material.name

    # endregion

    # region Material Data

    @staticmethod
    def get_material_data(material, fallback_type = "GEOMETRY"):
        if material is not None:
            return material_utility.get_material_data_instance(material)
        else:
            return material_utility.get_material_data_default(fallback_type)
    
    @staticmethod
    def get_material_data_default(fallback_type = "GEOMETRY"):
        # Default effect (for now it is the same as the one found within the "GEOMETRY" case)
        ans = {
            "$type": "effect_deferred",
            "Alpha": 0.400000006,
            "Sharpness": 1,
            "VertexColorEnabled": False,
            "UseMaterialTextureForReflectiveness": False,
            "ReflectionMap": "",
            "DiffuseTexture0AlphaDisabled": True,
            "AlphaMask0Enabled": False,
            "DiffuseColor0": {
                "x": 1,
                "y": 1,
                "z": 1
            },
            "SpecAmount0": 0,
            "SpecPower0": 20,
            "EmissiveAmount0": 0,
            "NormalPower0": 1,
            "Reflectiveness0": 0,
            "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
            "MaterialTexture0": "",
            "NormalTexture0": "",
            "HasSecondSet": False,
            "DiffuseTexture1AlphaDisabled": False,
            "AlphaMask1Enabled": False,
            "DiffuseColor1": None,
            "SpecAmount1": 0,
            "SpecPower1": 0,
            "EmissiveAmount1": 0,
            "NormalPower1": 0,
            "Reflectiveness1": 0,
            "DiffuseTexture1": None,
            "MaterialTexture1": None,
            "NormalTexture1": None
        }
        if fallback_type == "GEOMETRY":
            ans = {
                "$type": "effect_deferred",
                "Alpha": 0.400000006,
                "Sharpness": 1,
                "VertexColorEnabled": False,
                "UseMaterialTextureForReflectiveness": False,
                "ReflectionMap": "",
                "DiffuseTexture0AlphaDisabled": True,
                "AlphaMask0Enabled": False,
                "DiffuseColor0": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "SpecAmount0": 0,
                "SpecPower0": 20,
                "EmissiveAmount0": 0,
                "NormalPower0": 1,
                "Reflectiveness0": 0,
                "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
                "MaterialTexture0": "",
                "NormalTexture0": "",
                "HasSecondSet": False,
                "DiffuseTexture1AlphaDisabled": False,
                "AlphaMask1Enabled": False,
                "DiffuseColor1": None,
                "SpecAmount1": 0,
                "SpecPower1": 0,
                "EmissiveAmount1": 0,
                "NormalPower1": 0,
                "Reflectiveness1": 0,
                "DiffuseTexture1": None,
                "MaterialTexture1": None,
                "NormalTexture1": None
            }
        elif fallback_type == "WATER":
            ans = {
                "$type": "effect_deferred_liquid",
                "ReflectionMap": "",
                "WaveHeight": 1,
                "WaveSpeed0": {
                    "x": 0.00930232555,
                    "y": 0.0900000036
                },
                "WaveSpeed1": {
                    "x": -0.0046511637,
                    "y": 0.0883720964
                },
                "WaterReflectiveness": 0.216049388,
                "BottomColor": {
                    "x": 0.400000006,
                    "y": 0.400000006,
                    "z": 0.600000024
                },
                "DeepBottomColor": {
                    "x": 0.300000012,
                    "y": 0.400000006,
                    "z": 0.5
                },
                "WaterEmissiveAmount": 0.806896567,
                "WaterSpecAmount": 0.300000012,
                "WaterSpecPower": 24,
                "BottomTexture": "..\\Textures\\Surface\\Nature\\Ground\\rock_0",
                "WaterNormalMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "IceReflectiveness": 0,
                "IceColor": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "IceEmissiveAmount": 0,
                "IceSpecAmount": 1,
                "IceSpecPower": 20,
                "IceDiffuseMap": "..\\Textures\\Surface\\Nature\\Ground\\ice02_0",
                "IceNormalMap": "..\\Textures\\Liquids\\IceNrm_0"
            }
        elif fallback_type == "LAVA":
            ans = {
                "$type" : "effect_lava",
                "MaskDistortion" : 0.2,
                "Speed0" : {
                    "x" : 0.5,
                    "y" : 0.5
                },
                "Speed1" : {
                    "x" : 0.03,
                    "y" : 0.03
                },
                "LavaHotEmissiveAmount" : 3.0,
                "LavaColdEmissiveAmount" : 0.0,
                "LavaSpecAmount" : 0.0,
                "LavaSpecPower" : 20.0,
                "TempFrequency" : 0.5586,
                "ToneMap" : "..\\Textures\\Liquids\\LavaToneMap_0",
                "TempMap" : "..\\Textures\\Liquids\\LavaBump_0",
                "MaskMap" : "..\\Textures\\Liquids\\lavaMask_0",
                "RockColor" : {
                    "x" : 1,
                    "y" : 1,
                    "z" : 1
                },
                "RockEmissiveAmount" : 0.0,
                "RockSpecAmount" : 0.0,
                "RockSpecPower" : 20.0,
                "RockNormalPower" : 1.0,
                "RockTexture" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_0",
                "RockNormalMap" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_NRM_0"
            }
        elif fallback_type == "FORCE_FIELD":
            ans = {
                "color" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "width" : 0.5,
                "alphaPower": 4,
                "alphaFalloffPower" : 2,
                "maxRadius" : 4,
                "rippleDistortion" : 2,
                "mapDistortion" : 0.53103447,
                "vertexColorEnabled": False,
                "displacementMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "ttl": 1
            }
        # NOTE : No default fallback for additive effects exists in JSON mode, since geometry objects can have both deferred effects and additive effects, and for performance and logical reasons,
        # level geometry (mcow type "GEOMETRY") meshes with non-specified or non-valid materials are assumed to use deferred effects as fallback by default
        return ans

    @staticmethod
    def get_material_data_instance(material):
        if material.mcow_effect_mode == "DOC":
            return material_utility.get_material_data_instance_json(material)
        else:
            return material_utility.get_material_data_instance_blend(material)

    @staticmethod
    def get_material_data_instance_json(material):
        ans = get_json_object(material_utility.get_material_path(material))
        return ans
    
    @staticmethod
    def get_material_data_instance_blend(material):
        # TODO : Implement for each of the material types! You'll basically just need to extract the values from the blender panel and then arrange them in a json-like python dict.
        ans = {}
        return ans

    # endregion

    # region Material Path

    @staticmethod
    def get_material_path(material):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, material.mcow_effect_path)
        if not ans.endswith(".json"):
            ans = ans + ".json"
        return ans

    # endregion

# endregion

# ../mcow/functions/generation/export/Get.py
# region Get Stage

# This section contains classes whose purpose is to define the logic of the Get Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Getter class.
class MCow_Data_Getter:
    def __init__(self):
        return
    
    def get(self):
        return None # Return an empty object by default since the base class does not implement the data getting for any specific class.

    # region Comment

    # Returns a list of meshes in the form of a tuple (obj, transform, material_index).
    # Segments a single mesh into multiple meshes based on the indices of the applied materials.
    # This is used because it is easier to just export a new mesh for each material than it is to implement BiTree nodes and multi material XNA models...
    
    # endregion
    def get_mesh_segments(self, obj):
        
        # NOTE : The return value of this function is a list filled with tuples of form (mesh_object, material_index)
        
        mesh = obj.data
        num_materials = len(mesh.materials)

        # If there are no materials, then add the mesh to the list of found meshes 
        if num_materials <= 0:
            ans = [(obj, 0)]
        
        # If there are materials, then add each segment of the mesh that uses an specific material as a separate mesh for simplicity
        else:

            found_polygons_with_material_index = [0 for i in range(0, num_materials)]
            for poly in mesh.polygons:
                found_polygons_with_material_index[poly.material_index] += 1
            
            ans = []
            for index, count in enumerate(found_polygons_with_material_index):
                if count > 0:
                    ans.append((obj, index))
        
        return ans

# Data Getter class for Maps / Levels
class MCow_Data_Getter_Map(MCow_Data_Getter):
    def __init__(self):
        super().__init__()
        return
    
    def get(self):
        return self._get_scene_data()
    
    # region Comment - _get_scene_data_add_collision
    
    # If the parent is an animated level part, then we add the collision to whatever collision channel the parent corresponds to.
    # Otherwise, we add it to the collision channel of the object itself.
    
    # endregion
    def _get_scene_data_add_collision(self, found_objects_current, obj, transform, parent):
        collision_index = 0
        if parent is None:
            collision_index = find_collision_material_index(obj.magickcow_collision_material)
        else:
            collision_index = find_collision_material_index(parent.magickcow_collision_material)
        found_objects_current.collisions[collision_index].append((obj, transform))

    # TODO : Modify this method to internally call the get_mesh_segments() method
    # region Comment - _get_scene_data_add_mesh
        # NOTE : The reason we do this process rather than actually implementing BiTreeNode support is for 3 major reasons
        # 1) BiTree Nodes don't actually contain material data at all. Yes, their existance is literally useless, they just segment things up and don't even
        # contain a different effect for a given part of a root node...
        #
        # 2) BiTreeNodes are just badly optimized in Magicka and consume more memory than they should.
        # A BiTreeNode's purpose is literally to just assign a different material to a given part of a root node's vertex buffer than the one assigned on the root node.
        # This assignment process goes by starting at a certain vertex index and giving a number of primitives that are contained by said node (the root node does this as well).
        # This means that for every single island of faces that make use of a given material, there will be a new BiTreeNode generated.
        # This is a problem, because if a mesh in Blender has 2 materials, it is not guaranteed to have only 2 nodes in the binary tree structure. If the materials are assigned on different polygon islands,
        # then the generated binary tree structure will generate a node for the same material multiple times, since a node can only represent a material assignment for contiguous faces within the vertex buffer.
        #
        # 3) BiTreeNodes are just badly optimized : Episode 2:
        # Another problem of using the BiTreeNode setup is that each node added is located on the heap, thus, there will be an increase in memory fragmentation. Root nodes are instead located within a list, so
        # most of their data will at least be contiguous in memory.
        # In short, BiTreeNodes in Magicka's code pointlessly increase the memory consumption, and the memory budget for a Magicka map is about 2GB at most since Magicka is 32 bits, and of the 4GB available
        # for a 32 bit process, 2 of those have already been consumed by the game code itself and most assets, so the remaining budget is quite small, and using only root nodes reduces the memory footprint a lot.
        #
        # In short, this is literally the only way to get multi material mesh support in Magicka. Magicka's meshes only support one material per mesh, so the trick we do is just segment the mesh into multiple different
        # meshes, each containing all of the polygons for a given material that was assigned in Blender to that mesh.
    # endregion
    def _get_scene_data_add_mesh(self, found_objects_list, obj, transform):
        mesh = obj.data
        num_materials = len(mesh.materials)
        
        if num_materials > 0:
            found_polygons_indices = [0 for i in range(num_materials)]
            # Check every polygon in the mesh and increase the usage count of the material index used by each polygon
            for poly in obj.data.polygons:
                found_polygons_indices[poly.material_index] += 1
        else:
            # Create a dummy list with only one entry, which has to contain any value greater than 0 so as to indicate that at least one polygon has been foud to make use of material index 0.
            # This is because in Blender, polygons that don't have any material assigned use the material index 0 by default.
            found_polygons_indices = [69] # In this case, I use 69 cauze lol, but the value 1 would suffice just fine.
            # Either that or just embed the call found_objects_list.append((obj, transform, 0)) within the else block and discard the dummy list entirely.
            # We keep it like this in case we want to add more code in the future appart from the append() call, so as to prevent code duplication...
        
        # Add the meshes that have been found to contain at least 1 polgyon that uses the current material
        for idx, found in enumerate(found_polygons_indices):
            if found > 0: # If there are no polygons in this mesh with this material assigned, discard it entirely and don't add it for processing.
                found_objects_list.append((obj, transform, idx))

    def _get_scene_data_rec(self, found_objects_global, found_objects_current, objects, parent = None):
        
        for obj in objects:
            
            # Get object transform
            transform = get_object_transform(obj, parent)
            
            # Ignore objects that are set to not export, as well as their children objects.
            if not obj.magickcow_allow_export:
                continue
            
            # Handle object data creation according to object type.
            if obj.type == "MESH":
                
                if len(obj.data.vertices) <= 0:
                    continue # Discard meshes with no vertices, as they are empty meshes and literally have no data worth exporting.

                if obj.data.magickcow_mesh_type == "GEOMETRY":
                    # found_objects_current.meshes.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.meshes, obj, transform)
                    
                    if obj.magickcow_collision_enabled:
                        self._get_scene_data_add_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "COLLISION":
                    self._get_scene_data_add_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "WATER":
                    # found_objects_current.waters.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.waters, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "LAVA":
                    # found_objects_current.lavas.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.lavas, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "NAV":
                    found_objects_current.nav_meshes.append((obj, transform)) # Nav meshes ignore materials, for now. In the future, they could use it as a reference for the type of navigation offered by an area.
                
                elif obj.data.magickcow_mesh_type == "FORCE_FIELD":
                    # Only add it to the global scope because animated level parts cannot contain force fields.
                    # Allows "malformed" (with a hierarchy that would not be correct in game) scenes to export successfully and work correctly in game.
                    # found_objects_global.force_fields.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_global.force_fields, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "CAMERA":
                    found_objects_current.camera_collision_meshes.append((obj, transform))
            
            elif obj.type == "LIGHT":
                
                # TODO : This will need to be reworked the day support for static level bitree child nodes is added... which may actually never come if there's no technical reason to support it...
                # We would need to probably roll back to having an input bool variable in this function that says if the parent object is an animated object or not.
                # Or we could analyse the parent's type with parent.type and check if it is an empty of "BONE" type or not. We'll see what is chosen in the future, but for now, fuck it.
                if parent is not None:
                    found_objects_current.lights.append((obj, transform))
                
                found_objects_global.lights.append((obj, transform)) # Always add it to the global scope of the static level data because lights are stored like that in Magicka's code. Animated level parts only store a reference to a light.
            
            elif obj.type == "EMPTY":
                # This case does nothing because we DO want to allow using NONE type empties as a way to organize the scene, and using continue here would just skip child generation.
                # Do note that the better and encouraged way to do things in Blender with this addon is with collections, but this is still a possibility...
                if obj.magickcow_empty_type == "NONE":
                    pass # This used to do continue, but now it's just a nop because we actually want to get the children objects and export those, unless manually disabled.
                elif obj.magickcow_empty_type == "LOCATOR":
                    found_objects_current.locators.append((obj, transform))
                elif obj.magickcow_empty_type == "TRIGGER":
                    found_objects_current.triggers.append((obj, transform))
                elif obj.magickcow_empty_type == "PARTICLE":
                    found_objects_current.particles.append((obj, transform))
                elif obj.magickcow_empty_type == "PHYSICS_ENTITY":
                    # We append them only to the global objects because animated level parts cannot contain this type of object.
                    # If an animated level part contains an object of this type in the Blender scene, it will be exported as part of the static level data instead.
                    # Allows partially "malformed" scenes to export just fine.
                    found_objects_global.physics_entities.append((obj, transform))
            
            # Handle recursive call according to whether the current root object is a bone (root of an animated level part) or not.
            if obj.type == "EMPTY" and obj.magickcow_empty_type == "BONE":
            
                # Ignore exporting animated level parts if animation export is disabled.
                if not bpy.context.scene.mcow_scene_animation:
                    continue
                
                found_objects_new = MCow_Map_SceneObjectsFound()
                
                self._get_scene_data_rec(found_objects_global, found_objects_new, obj.children, obj)
                
                found_objects_current.animated_parts.append((obj, transform, found_objects_new))
            else:
                self._get_scene_data_rec(found_objects_global, found_objects_current, obj.children, parent)

    def _get_scene_data(self):
        
        # Get the root objects from the scene
        root_objects = get_scene_root_objects()
        
        # Create an instance of the found objects class. It will get passed around by the recursive calls to form a tree-like structure, adding the found objects to it and its children.
        found_objects = MCow_Map_SceneObjectsFound()
        
        # Call the recursive function and start getting the data.
        self._get_scene_data_rec(found_objects, found_objects, root_objects, None)
        
        return found_objects

# Data Getter class for Physics entities
class MCow_Data_Getter_PhysicsEntity(MCow_Data_Getter):
    def __init__(self):
        super().__init__()
        return
    
    def get(self):
        return self._get_scene_data()

    def _get_scene_data(self):

        # NOTE : We have to make sure that we only have 1 single object of type "ROOT" in the scene, and that it is also a root within the scene. All other root objects that are not of type "ROOT" will be ignored.
        # Objects of type "ROOT" within the tree hierarchy but that are not true roots will trigger an error.

        # NOTE : For now, we only handle exporting 1 single physics entity object per physics entity scene.

        # Get all of the objects in the scene that are of type "ROOT"
        all_objects_of_type_root = [obj for obj in bpy.data.objects if (obj.type == "EMPTY" and obj.mcow_physics_entity_empty_type == "ROOT")]
        if len(all_objects_of_type_root) != 1:
            raise MagickCowExportException("Physics Entity Scene must contain exactly 1 Root!")

        # Get all of the objects in the scene that are roots (have no parent) and are of type "ROOT"
        root_objects = [obj for obj in bpy.data.objects if (obj.parent is None and obj.type == "EMPTY" and obj.mcow_physics_entity_empty_type == "ROOT")]
        if len(root_objects) != 1:
            raise MagickCowExportException("Physics Entity Scene Root object must be at the root of the scene!")

        # Get the objects in the scene and form a tree-like structure for exporting.
        found_objects = Storage_PhysicsEntity()
        found_objects.root = root_objects[0]
        
        scene_root_bone = PE_Storage_Bone()
        scene_root_bone.obj = found_objects.root
        scene_root_bone.transform = found_objects.root.matrix_world
        scene_root_bone.index = 0
        scene_root_bone.parent = -1
        scene_root_bone.children = []

        found_objects.model.bones.append(scene_root_bone) # The root object will act as a bone for us when exporting the mesh. We add a list with element -1 because that is how we signal that there are no parent bones for the root bone.
        self._get_scene_data_rec(found_objects, root_objects[0].children, 0)
        
        return found_objects
    
    def _get_scene_data_rec(self, found_objects, current_objects, parent_bone_index):
        
        for obj in current_objects:

            # Ignore objects that are marked as no export. This also excludes all children from the export process.
            if not obj.magickcow_allow_export:
                continue
            
            # Calculate the transform for this object, relative to what is considered its parent in the Magicka tree structure
            if parent_bone_index < 0:
                transform = get_object_transform(obj, None)
            else:
                transform = get_object_transform(obj, found_objects.model.bones[parent_bone_index].obj)

            # Process objects of type mesh, which should be visual geometry meshes and collision meshes
            if obj.type == "MESH":
                mesh = obj.data
                mesh_type = mesh.mcow_physics_entity_mesh_type

                # Process meshes for visual geometry
                if mesh_type == "GEOMETRY":
                    # self._get_scene_data_add_bone(found_objects, obj, transform, parent_bone_index) # Add the mesh as a bone as well, each mesh has a bone associated.
                    self._get_scene_data_add_mesh(found_objects, obj, transform, parent_bone_index) # TODO : Implement relative transform calculations # len(found_objects.model.bones)

                # Process meshes for collision geometry
                elif mesh_type == "COLLISION":
                    found_objects.collisions.append(obj)
            
            # Process objects of type empty, which should be roots and bones
            elif obj.type == "EMPTY":
                
                # Process empties for bones
                if obj.mcow_physics_entity_empty_type == "BONE":
                    # Add the found bone
                    self._get_scene_data_add_bone(found_objects, obj, transform, parent_bone_index)

                # Process empties for bounding boxes
                elif obj.mcow_physics_entity_empty_type == "BOUNDING_BOX":
                    # Add the found bounding box
                    found_objects.boxes.append(obj)


            # NOTE : We ignore objects of any type other than empties and meshes when getting objects to be processed for physics entity generation.
            # No need for an else case because we do nothing else within the loop.

    def _get_scene_data_add_mesh(self, found_objects, obj, transform, parent_bone_index):
        segments = self.get_mesh_segments(obj)
        ans = [(segment_obj, transform, material_index, parent_bone_index) for segment_obj, material_index in segments]
        found_objects.model.meshes.extend(ans)

    def _get_scene_data_add_bone(self, found_objects, obj, transform, parent_bone_index):
        # Throw an exception if the found bone has a name that is reserved
        reserved_bone_names = ["Root", "RootNode"]
        bone_name_lower = obj.name.lower()
        for name in reserved_bone_names: # NOTE : We could have used "if bone_name_lower in reserved_bone_names:" instead, but I would prefer to keep the reserved strings just as they are stored within the XNB file rather than hardcoding them in full lowercase. This is because I don't exactly remember as of now whether XNA checks for exact bone names or if it is not case sensitive. I'd need to check again, but whatever. Also, these reserved bone names are not because of XNA, they are just present in ALL physics entity files within Magicka's base game data, so it's a Magicka animation system requirement instead.
            if bone_name_lower == name.lower():
                raise MagickCowExportException(f"The bone name \"{name}\" is reserved!")

        # Add the current bone to the list of found bones
        current_bone = PE_Storage_Bone()
        current_bone.obj = obj
        current_bone.transform = transform
        current_bone.index = len(found_objects.model.bones) # NOTE : We don't subtract 1 because the current bone has not been added to the list yet!!!
        current_bone.parent = parent_bone_index
        current_bone.children = []

        found_objects.model.bones.append(current_bone)
        
        # Update the list of child bone indices for the parent bone
        found_objects.model.bones[current_bone.parent].children.append(current_bone.index)

        # Make recursive call to get all of the data of the child objects of this bone.
        self._get_scene_data_rec(found_objects, obj.children, current_bone.index) # NOTE : The index we pass is literally the index of the bone we just added to the found objects' bones list.


# endregion

# ../mcow/functions/generation/export/Generate.py
# region Generate Stage

# region Comment - DataGenerator
    # A generic class for data generation.
    # This class contains methods to generate data that is generic to all types of assets.
    # Each specific Data generator class will implement data generation methods that are specific for each type of asset to be exported.
    # NOTE : At some point in the future, it may make sense to move much of the logic here to some intermediate DataGenerator class (that inherits from the base one) that implements all of the 3D related operations and materials / effects / shared resources handling which some other forms of files that we could generate may not deal with... for example character creation...
# endregion
class MCow_Data_Generator:
    
    # region Constructor
    
    def __init__(self, cache):
        self.cache = cache
        return 
    
    # endregion

    # region Generate

    # region Generate - Main Entry point
    
    def generate(self, found_objects):
        return None
    
    # endregion

    # region Generate - Deprecated Math

    def DEPRCATED_generate_matrix_data(self, transform):
        # The input matrix
        matrix = transform

        # The conversion matrix to go from Z up to Y up
        matrix_convert = mathutils.Matrix((
            (1,  0,  0,  0),
            (0,  0,  1,  0),
            (0, -1,  0,  0),
            (0,  0,  0,  1)
        ))

        # Calculate the Y up matrix
        matrix = matrix_convert @ matrix

        # Pass the matrix from column major to row major
        matrix = matrix.transposed() # XNA's matrices are row major, while Blender (and literally 90% of software in the planet) is column major... so we need to transpose the transform matrix.
        
        # Store as tuple
        m11 = matrix[0][0]
        m12 = matrix[0][1]
        m13 = matrix[0][2]
        m14 = matrix[0][3]
        m21 = matrix[1][0]
        m22 = matrix[1][1]
        m23 = matrix[1][2]
        m24 = matrix[1][3]
        m31 = matrix[2][0]
        m32 = matrix[2][1]
        m33 = matrix[2][2]
        m34 = matrix[2][3]
        m41 = matrix[3][0]
        m42 = matrix[3][1]
        m43 = matrix[3][2]
        m44 = matrix[3][3]
        ans = (m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34, m41, m42, m43, m44)
        return ans

    def DEPRCATED_generate_vector_point(self, point):
        ans = (point[0], -point[2], -point[1])
        return ans
    
    def DEPRCATED_generate_vector_direction(self, direction):
        ans = (direction[0], -direction[2], -direction[1])
        return ans

    def DEPRCATED_generate_vector_scale(self, scale):
        ans = (scale[0], scale[2], scale[1])
        return ans

    def DEPRCATED_generate_vector_uv(self, uv):
        ans = (uv[0], -uv[1]) # Invert the "Y axis" (V axis, controlled by Y property in Blender) of the UVs because Magicka has it inverted for some reason...
        return ans

    def DEPRCATED_generate_rotation(self, quat):
        ans = (quat[3], quat[0], -quat[2], quat[1]) # Pass to Y up coordinate system
        ans = (ans[1], ans[2], ans[3], ans[0]) # Reorganize the quaternion from Blender's (w, x, y, z) ordering to Magicka's (x, y, z, w) ordering
        return ans

    # endregion

    # region Generate - Math

    def generate_matrix_data(self, transform):
        matrix = transform
        matrix = matrix.transposed() # XNA's matrices are row major, while Blender (and literally 90% of software in the planet) is column major... so we need to transpose the transform matrix.
        m11 = matrix[0][0]
        m12 = matrix[0][1]
        m13 = matrix[0][2]
        m14 = matrix[0][3]
        m21 = matrix[1][0]
        m22 = matrix[1][1]
        m23 = matrix[1][2]
        m24 = matrix[1][3]
        m31 = matrix[2][0]
        m32 = matrix[2][1]
        m33 = matrix[2][2]
        m34 = matrix[2][3]
        m41 = matrix[3][0]
        m42 = matrix[3][1]
        m43 = matrix[3][2]
        m44 = matrix[3][3]
        ans = (m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34, m41, m42, m43, m44)
        return ans
    
    def generate_vector(self, vec):
        ans = (vec[0], vec[1], vec[2])
        return ans

    def generate_uv(self, uv):
        ans = (uv[0], -uv[1]) # Invert the "Y axis" (V axis, controlled by Y property in Blender) of the UVs because Magicka has it inverted for some reason...
        return ans

    def generate_quaternion(self, quat):
        ans = (quat[1], quat[2], quat[3], quat[0])
        return ans

    # endregion

    # region Generate - Mesh

    # region Generate - Mesh - Internal

    # This function returns both mesh and bm so that the caller can use the bm in case they need it.
    # NOTE : The user must free the bm manually.
    # TODO : Maybe add support in the future for an input bool param that will allow the bm to be freed automatically if the user does not need it? and maybe also change the return tuple to only contain mesh in that case.
    def mesh_triangulate(self, obj):
        # Obtain the mesh data from the input object.
        mesh = obj.data

        # Triangulate the mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        
        return mesh, bm

    def mesh_apply_modifiers(self, obj):
        # Obtain mesh data
        mesh = obj.data

        # Apply modifiers
        for mod in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=mod.name)

    # Gets the data of a mesh object after applying modifiers and triangulating the mesh
    def get_mesh_data(self, obj):
        # Make a copy of the obj and its data
        temp_obj = obj.copy()
        temp_obj.data = obj.data.copy()

        # Link the temp object to the scene
        bpy.context.collection.objects.link(temp_obj)

        # Select the copied object
        temp_obj.select_set(state=True)
        bpy.context.view_layer.objects.active = temp_obj

        # Apply modifiers
        self.mesh_apply_modifiers(temp_obj)

        # Triangulate mesh
        mesh, bm = self.mesh_triangulate(temp_obj)

        # Make a copy of the mesh data yet again before deleting the object (we do this because Blender is allowed to garbage collect the mesh at any point, if we did not do this, it may sometimes work, and sometimes fail)
        mesh = mesh.copy()

        # Delete the temporary object
        bpy.data.objects.remove(temp_obj, do_unlink=True)

        # Return the mesh and bmesh
        return mesh, bm # NOTE : mesh is freed automatically, bm needs to be freed manually by the caller.

    # endregion

    # region Generate - Mesh - Main

    # region Deprecated

    def generate_mesh_data_old_1(self, obj, transform, uses_material = True, material_index = 0):
        
        # Get the inverse-tranpose matrix of the object's transform matrix to use it on directional vectors (normals and tangents)
        # NOTE : The reason we do this is because vectors that represent points in space need to be translated, but vectors that represent directions don't, so we use the input transform matrix for point operations and the inverse-transpose matrix for direction vector operations, since that allows transforming vectors without displacing them (no translation) but properly preserves the other transformations (scale, rotation, shearing, whatever...)
        # NOTE : This operation is the equivalent of displacing 2 points using the input transform matrix, one P0(0,0,0) and another P1(n1,n2,n3), and then calculating the vector that goes from P0' to P1', but using the invtrans is faster because it only requires one single matrix calculation, which also has a faster underlying implementation in Python.
        invtrans = transform.inverted().transposed()

        # Get triangulated mesh
        mesh, bm = self.get_mesh_data(obj)
        
        # Get material name
        matname = self.get_material_name(obj, material_index)

        # If the mesh uses a material, generate the material data and store it
        if uses_material:
            self.create_material(matname, mesh.magickcow_mesh_type)
        
        # Define vertex buffer and index buffer
        vertices = []
        indices = []

        # Define vertex map (used to duplicate vertices to translate Blender's face based data such as UVs to vertex based data)
        vertices_map = {}
        
        # TODO : In future implementations, maybe allow configurable color layer name?
        # Get the Vertex color layer if it exists
        if len(mesh.color_attributes) > 0: # There exists at least 1 color attribute layer for this mesh
            color_layer = mesh.color_attributes[0] # Get the first layer for now
        else:
            color_layer = None
            color_default = (0.0, 0.0, 0.0, 0.0) if mesh.magickcow_mesh_type in ["WATER", "LAVA"] else (1.0, 1.0, 1.0, 0.0)
            # NOTE : It seems like vector <0,0,0,0> works universally and does not actually mean paint black the surface, not sure why...
            # it would make sense to use that vector in the future, but for now, we're rolling with this as it seems to work pretty nicely.
            # I'll get this polished even further in the future when I figure out more aobut how the Magicka shaders are coded internally...

        # Extract vertex data (vertex buffer and index buffer)
        # Generate the vertex map for vertex duplication
        # The map is used to generate duplicate vertices each time we find a vertex with non matching UVs so as to allow Blender styled UVs (per face) to work in Magicka (where UVs are per vertex, meaning we have to duplicate vertices in some cases). The map prevents having to make a duplicate vertex for every single face, making it so that we only have to duplicate the vertices where the UV data does not match between faces.
        # The algorithm is surprisingly fast, and I am quite happy with this result for now.
        global_vertex_index = 0
        for poly in mesh.polygons:
            
            # Ignore all polygons that don't have the same material index as the input material index.
            # NOTE : The default material index returned by surfaces that don't have an assigned material is 0, so the default input material index parameter for this function is also 0
            # so as to allow easy support for exporting meshes that have no material assigned.
            if poly.material_index != material_index:
                continue

            temp_indices = []
            for loop_idx in poly.loop_indices:
                loop = mesh.loops[loop_idx]
                vertex_idx = loop.vertex_index
                
                position = transform @ mesh.vertices[vertex_idx].co.to_4d()
                # position = M_conv @ position
                position = self.generate_vector(position)
                
                normal = invtrans @ loop.normal
                # normal = M_conv @ normal
                normal = self.generate_vector(normal)
                
                tangent = invtrans @ loop.tangent
                # tangent = M_conv @ tangent
                tangent = self.generate_vector(tangent)
                
                uv = mesh.uv_layers.active.data[loop_idx].uv
                uv = self.generate_uv(uv)
                
                # Check if the color layer is not null and then extract the color data. Otherwise, create a default color value.
                # btw, to make things faster in the future, we could actually not use an if on every single loop and just create a dummy list with 3 elements as color_layer.data or whatever...
                if color_layer is not None:
                    color = color_layer.data[loop_idx].color
                    color = (color[0], color[1], color[2], color[3])
                else:
                    # Default color value : vector < 1, 1, 1, 0 >
                    # region Comment
                        # The default color value should either be <1,1,1,1>, <0,0,0,1> or <1,1,1,0> or some other vector to that effect...
                        # The reason for picking the vector <1,1,1,0> is that the default vertex color will paint the surface with a color multiplication on top of the used textures, so the RGB section is
                        # ideal to have as <1,1,1> by default.
                        # The alpha channel is used to lerp between 2 texture sets on deferred effects, and the value 0 corresponds to the first texture set, so it is ideal to have the alpha value to 0 by default.
                        # The default value does not matter at all in the case of using an effect JSON file where the use vertex color attribute is set to false tho. But in case it is set to true, this is the best
                        # default vector in my opinion.
                    # endregion
                    color = color_default

                vertex = (global_vertex_index, position, normal, tangent, uv, color)
                
                # If the map entry does not exist (we have not added this vertex yet) or the vertex in the map has different UVs (we have found one of Blender's UVs seams caused by its face based UVs), then we create a new vertex entry or modify the entry that already exists.
                # Allows to reduce the number of duplicated vertices.
                # The duplicated vertices exist to allow the far more complex UVs that we can make when using the face based UV system that Blender has. The problem is that graphics APIs work with vertex based UVs, so we need to duplicate these vertices and generate new faces to get the correct results.
                if vertex_idx not in vertices_map: # if entry is not in map (new vertex, first time we see it)
                    vertices_map[vertex_idx] = []
                    vertices_map[vertex_idx].append(vertex)
                    temp_indices.append(global_vertex_index)
                    global_vertex_index += 1
                else: # if entry is in map...
                    matching_list_entry_found = False
                    matching_list_entry = (0, 0)
                    for list_entry in vertices_map[vertex_idx]:
                        if (list_entry[4][0] == uv[0] and list_entry[4][1] == uv[1]) and (list_entry[2][0] == normal[0] and list_entry[2][1] == normal[1] and list_entry[2][2] == normal[2]):
                            matching_list_entry_found = True
                            matching_list_entry = list_entry
                            break
                    if matching_list_entry_found: # if we found a matching entry in the list, then the vertex already exists, so we reuse it.
                        temp_indices.append(matching_list_entry[0])
                    else: # else, we didn't find any matching entries, so we create a new copy of the vertex with its new UV data.
                        vertices_map[vertex_idx].append(vertex)
                        temp_indices.append(global_vertex_index)
                        global_vertex_index += 1
            
            # Swap the points order so that they follow the same winding as Magicka.
            temp = temp_indices[0]
            temp_indices[0] = temp_indices[2]
            temp_indices[2] = temp
            
            indices += temp_indices
        
        # Generate the vertex buffer from the vertex map:
        # NOTE : We care about sorting the extracted data of the map based on the global vert idx, because, even tho part of the data is ordered by ascending order, the maps are still ordered by insertion order, and we insert lists of vertices for each key, so the global indices within those lists, while ordered, just looking over them and appending them will not give us the correct global index ordering, so we still need to sort the list...
        # Maybe some day I'll come up with a faster way to do this.
        # Also, we just append the vert directly rather than extracting it to remove the global index because that's the key we use for sorting, and because I don't really want to make yet another tuple copy... Python sure is slow for some of this stuff...
        for key, vertex_list in vertices_map.items():
            for vert in vertex_list:
                vertices.append(vert)
        vertices.sort() # Sorts the vertices based on the global vertex index, which is what the sort() method uses as sorting key by default for tuples.

        # Free the bm (for consistency, this is done at the end of the gen process for all different mesh types, but in truth, for this gen function it could be freed as soon as we get it)
        bm.free()

        # vertices : List<Vertex>; vertices is the vertex buffer, which is a list containing tuples of type Vertex one after another.
        # indices : List<int>; indices is the index buffer, which is a list of all of the indices ordered to generate the triangles. They are NOT grouped in any form of triangle struct, the indices are laid out just as they would be in memory.
        return (vertices, indices, matname)

    # endregion

    def generate_mesh_data(self, obj, transform, uses_material = True, material_index = 0):
        # Generate mesh data
        mcow_mesh = MCow_Mesh(obj, transform)
        
        # Generate material data
        matname = self.cache.add_material(obj, material_index)

        # Cache vertex color layer
        if len(mcow_mesh.mesh.color_attributes) > 0:
            color_layer = mcow_mesh.mesh.color_attributes[0]
        else:
            color_default = (0.0, 0.0, 0.0, 0.0) if mcow_mesh.mesh.magickcow_mesh_type in ["WATER", "LAVA"] else (1.0, 1.0, 1.0, 0.0)
            color_layer = None

        vertices = []
        indices = []

        vertices_map = {}

        polys = [poly for poly in mcow_mesh.mesh.polygons if poly.material_index == material_index] # Get all polygons where the material index matches that of the mesh we're currently generating.
        
        global_vertex_index = 0
        for poly in polys:
            temp_indices = []
            for loop_idx in poly.loop_indices:
                loop = mcow_mesh.mesh.loops[loop_idx]
                vertex_idx = loop.vertex_index
                
                position = mcow_mesh.transform @ mcow_mesh.mesh.vertices[vertex_idx].co.to_4d()
                position = self.generate_vector(position)

                normal = mcow_mesh.invtrans @ loop.normal
                normal = self.generate_vector(normal)

                tangent = mcow_mesh.invtrans @ loop.tangent
                tangent = self.generate_vector(tangent)

                uv = mcow_mesh.mesh.uv_layers.active.data[loop_idx].uv
                uv = self.generate_uv(uv)
                
                if color_layer is None:
                    color = color_default
                else:
                    color = color_layer.data[loop_idx].color
                    color = (color[0], color[1], color[2], color[3])

                # NOTE : Perhaps we could do the processing AFTER we isolate what unique vertices exist?

                vertex = (global_vertex_index, position, normal, tangent, uv, color)

                if vertex_idx not in vertices_map:
                    vertices_map[vertex_idx] = [vertex]
                    temp_indices.append(global_vertex_index)
                    vertices.append(vertex)
                    global_vertex_index += 1
                else:
                    matching_list_entry_found = False
                    matching_list_entry = None
                    for list_entry in vertices_map[vertex_idx]:
                        if (list_entry[4][0] == uv[0] and list_entry[4][1] == uv[1]) and (list_entry[2][0] == normal[0] and list_entry[2][1] == normal[1] and list_entry[2][2] == normal[2]):
                            matching_list_entry_found = True
                            matching_list_entry = list_entry
                            break
                    if matching_list_entry_found:
                        temp_indices.append(matching_list_entry[0])
                        vertices[matching_list_entry[0]] = vertex
                    else:
                        vertices_map[vertex_idx].append(vertex)
                        temp_indices.append(global_vertex_index)
                        vertices.append(vertex)
                        global_vertex_index += 1
            
            # Swap points order to follow the same vertex winding as in Magicka
            temp_indices = [temp_indices[2], temp_indices[1], temp_indices[0]]
            
            # Insert the data of these 3 new vertices into the index buffer
            indices.extend(temp_indices)

        return (vertices, indices, matname)

    def generate_mesh_data_testing_1(self, obj, transform, uses_material = True, material_index = 0):
        # Generate mesh data
        mcow_mesh = MCow_Mesh(obj, transform)
        
        # Generate material data
        matname = self.get_material_name(obj, material_index)
        self.create_material(matname, mcow_mesh.mesh.magickcow_mesh_type)

        # Cache vertex color layer
        if len(mcow_mesh.mesh.color_attributes) > 0:
            color_layer = mcow_mesh.mesh.color_attributes[0]
        else:
            color_default = (0.0, 0.0, 0.0, 0.0) if mcow_mesh.mesh.magickcow_mesh_type in ["WATER", "LAVA"] else (1.0, 1.0, 1.0, 0.0)
            color_layer = None

        vertices = [(0, (0,0,0), (0,0,0), (0,0,0), (0,0), (0,0,0,0)), (0, (0,0,0), (0,0,0), (0,0,0), (0,0), (0,0,0,0)), (0, (0,0,0), (0,0,0), (0,0,0), (0,0), (0,0,0,0))]
        indices = [0,1,2]

        vertices_map = {}

        polys = [poly for poly in mcow_mesh.mesh.polygons if poly.material_index == material_index] # Get all polygons where the material index matches that of the mesh we're currently generating.
        
        all_vertices_raw = [(idx, mcow_mesh.mesh.vertices[vertex.vertex_index].co, mcow_mesh.mesh.loops[vertex.vertex_index].normal, mcow_mesh.mesh.loops[vertex.vertex_index].tangent, mcow_mesh.mesh.uv_layers.active.data[vertex.vertex_index].uv) for idx, vertex in enumerate([poly.loop_indices for poly in polys])]
        """
        global_vertex_index = 0
        for poly in polys:
            temp_indices = []
            for loop_idx in poly.loop_indices:
                loop = mcow_mesh.mesh.loops[loop_idx]
                vertex_idx = loop.vertex_index

                position = mcow_mesh.transform @ mcow_mesh.mesh.vertices[vertex_idx].co.to_4d()
                position = self.generate_vector(position)

                normal = mcow_mesh.invtrans @ loop.normal
                normal = self.generate_vector(normal)

                tangent = mcow_mesh.invtrans @ loop.tangent
                tangent = self.generate_vector(tangent)

                uv = mcow_mesh.mesh.uv_layers.active.data[loop_idx].uv
                uv = self.generate_uv(uv)

                if color_layer is None:
                    color = color_default
                else:
                    color = color_layer.data[loop_idx].color
                    color = (color[0], color[1], color[2], color[3])
                
                vertex = (global_vertex_index, position, normal, tangent, uv, color)

                vertices.append(vertex)
                indices.append(global_vertex_index)
        """

        return (vertices, indices, matname)

    # endregion

    # endregion

    # endregion

# region Comment - DataGeneratorMap
    # This class is the one in charge of getting, generating and storing in a final dict the data that is found within the scene.
    # The reason this class exists outside of the main exporter operator class is to prevent its generated data from staying around in memory after the export process has finished.
    # This could also be avoided by passing all variables around through functions, but that was getting too messy for global-state-like stuff like shared resources and other information
    # that should be cacheable, so I ended up just making this intermediate class to handle that.
    # The main exporter operator makes an instance of this class and just calls the get(), generate() and make() methods when it has to.
    # That way, after the export function goes out of scope, so does the class and all of the generated and cached information gets freed.
    # It would be cool to be able to keep it in cache between exports, but what happens for example if a material / effect JSON file is modified and it is still in the cache?
    # The new version would never be read unless we would add a system that would allow this python script to check if the file has been updated from the last time it was cached, and that would be slower
    # than just reading the new file altogether, because sadly even small syscalls like getting a file's data are slooooooow in python.
    # Also that would make things harder to handle caching materials, shared resources and implementing object instance caching as well, etc... because what happens when you modify a Blender scene?
    # In short, that would add quite a bit of complexity, and it is not really worth it as of now.
#endregion
class MCow_Data_Generator_Map(MCow_Data_Generator):
    def __init__(self, cache):
        super().__init__(cache)
        return

    def generate(self, found_objects):
        ans = self.generate_scene_data(found_objects)
        return ans

    # region Bounding Box Related Operations

    # TODO : Rename these methods with generate_ prefix instead

    # Get the bounding box from a list of points.
    # Each point is a tuple of 3 numeric values.
    # The resulting AABB is represented as the min and max points of the bounding box.
    def get_bounding_box_internal(self, points):
        # If the found mesh doesn't have enough geometry to generate a bounding box, then return a predefined one with points set to <0,0,0>
        if len(points) <= 1: # Safety check in case there's an empty mesh in the scene or a mesh with less than a single poly
            return ((0, 0, 0), (0, 0, 0)) # Just return an empty AABB with the min and max points set to <0,0,0>
        
        # Otherwise, create a proper AABB iterating over all of the points and finding the min and max points of the mesh
        minx, miny, minz = points[0]
        maxx, maxy, maxz = points[0]
        for point in points:
            x,y,z = point
            if x < minx:
                minx = x
            if y < miny:
                miny = y
            if z < minz:
                minz = z
            if x > maxx:
                maxx = x
            if y > maxy:
                maxy = y
            if z > maxz:
                maxz = z
        min_point = (minx, miny, minz)
        max_point = (maxx, maxy, maxz)
        return (min_point, max_point)

    # Given 2 points that represent the AABB, it returns the same points altered in a way that it increases the size of the AABB.
    # The size increase is:
    # 1) the AABB is scaled to by a factor S of its input size
    # 2) the AABB is increased by a fixed length of N units of breathing room
    def get_bounding_box_with_breathing_room(self, minp, maxp, scale_factor, breathing_room_units):
        # Add half of the distance between min and max and add a fixed number of units as a breathing room.
        # This way, the bounding box will always be larger than the mesh itself, preventing the possibility of seeing mesh popping out of existence just by walking a few meters away from it.
        
        # Extract the point data from the input point tuples
        minx, miny, minz = minp
        maxx, maxy, maxz = maxp

        # Calculate the length of each side / axis of the AABB
        difx = maxx - minx
        dify = maxy - miny
        difz = maxz - minz

        # Apply the scaling factor to the length
        difx = difx * scale_factor
        dify = dify * scale_factor
        difz = difz * scale_factor

        # Add the breathing room units to the length
        difx = difx + breathing_room_units
        dify = dify + breathing_room_units
        difz = difz + breathing_room_units
        
        # Calculate the middle point
        midx = (maxx - minx) / 2.0
        midy = (maxy - miny) / 2.0
        midz = (maxz - minz) / 2.0

        # NOTE : To get the correct result, the new point data is calculated by adding the difference values to the middle point.
        # This is because the idea behind the scaling operation is to obtain the scaled up the AABB with a scaling factor around it's center point
        # so that it scales uniformly around its origin and contains the entire mesh properly.

        # Cache dif / 2.0
        difx2 = difx / 2.0
        dify2 = dify / 2.0
        difz2 = difz / 2.0

        # Compute the new min point data
        minx = midx - difx2
        miny = midy - dify2
        minz = midz - difz2
        minp = (minx, miny, minz)
        
        # Compute the new max point data
        maxx = midx + difx2
        maxy = midy + dify2
        maxz = midz + difz2
        maxp = (maxx, maxy, maxz)
        
        return (minp, maxp)

    # Public bounding box function.
    # Calculates the AABB given a set of points.
    def get_bounding_box(self, points):
        minp1, maxp1 = self.get_bounding_box_internal(points) # Calculate the min and max points for the AABB
        minp2, maxp2 = self.get_bounding_box_with_breathing_room(minp1, maxp1, 1.5, 2000) # Calculate the min and max points of the AABB with a breathing room as margin of error
        return (minp2, maxp2)

    # endregion
    
    # region "Generate Data" / "Transform Data" Functions

    def generate_aabb_data(self, vertices):
        # Define a list of points used to calculate the bounding box of the mesh.
        # The list is calculated by extracting the position property from the vertices.
        # NOTE : This is because the input vertices are expected in the format that the mesh data generation functions builds them, as a GPU-like vertex buffer.
        aabb_points = [vert[1] for vert in vertices]

        # Calculate the AABB. The computation is performed using the list of points previously calculated.
        # NOTE : We do not need to perform any Y up conversions here since the points from the vertices list are already in Y up.
        aabb = self.get_bounding_box(aabb_points)
        return aabb

    def generate_physics_entity_data(self, obj, transform):
        template = obj.magickcow_physics_entity_name
        matrix = self.generate_matrix_data(transform)
        return (template, matrix)

    def generate_static_mesh_data(self, obj, transform, matid):
        # Generate basic mesh data
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)

        # Generate AABB data
        aabb = self.generate_aabb_data(vertices)

        # Generate static mesh root node specific data
        if obj.data.magickcow_mesh_advanced_settings_enabled:
            sway = obj.data.magickcow_mesh_sway
            entity_influence = obj.data.magickcow_mesh_entity_influence
            ground_level = obj.data.magickcow_mesh_ground_level
        else:
            sway = bpy.types.Mesh.bl_rna.properties["magickcow_mesh_sway"].default
            entity_influence = bpy.types.Mesh.bl_rna.properties["magickcow_mesh_entity_influence"].default
            ground_level = bpy.types.Mesh.bl_rna.properties["magickcow_mesh_ground_level"].default

        return (obj, transform, obj.name, vertices, indices, matname, aabb, sway, entity_influence, ground_level)

    def generate_animated_mesh_data(self, obj, transform, matid):
        # NOTE : The animated mesh calculation is a bit simpler because it does not require computing the AABB, as it uses an user defined radius for a bounding sphere.

        mesh = obj.data

        # Generate basic mesh data
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)
        
        # Add the material as a shared resource and get the shared resource index
        idx = self.cache.add_shared_resource(matname, self.cache.get_material(matname, mesh.magickcow_mesh_type))
        
        # Create the matrix that will be passed to the make stage
        matrix = self.generate_matrix_data(transform)
        
        return (obj, transform, obj.name, matrix, vertices, indices, idx)

    # region Comment - generate_liquid_data
    
    # NOTE : For now, both water and lava generation are identical, so they rely on the same generate_liquid_data() function.
    # In the past, they used to have their own identical functions just in case, but I haven't really found any requirements for that yet so yeah...
    # Maybe it could be useful to add some kind of exception throwing or error checking or whatever to prevent players from exporting maps where waters have materials that
    # are not deferred liquid effects and lavas that are not lava effects?
    # NOTE : Liquids do not require any form of bounding box or sphere calculations, so they use the underlying generate_mesh_data() function rather than any of the other wrappers.
    
    # endregion
    def generate_liquid_data(self, obj, transform, matid):
        
        # Generate the mesh data (vertex buffer, index buffer and effect / material)
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)
        
        # Get Liquid Water / Lava config
        can_drown = obj.data.magickcow_mesh_can_drown
        freezable = obj.data.magickcow_mesh_freezable
        autofreeze = obj.data.magickcow_mesh_autofreeze
        
        return (vertices, indices, matname, can_drown, freezable, autofreeze)

    def generate_force_field_data(self, obj, transform, matid):
        # Generate the mesh data (vertex buffer, index buffer and effect / material, altough the material is ignored in this case)
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)
        return (vertices, indices, matname)

    def generate_light_reference_data(self, obj, transform):
        name = obj.name
        matrix = self.generate_matrix_data(transform)
        return (name, matrix)

    def generate_light_data(self, obj, transform):
        
        # Get the Light data field from the Blender object
        light = obj.data

        # Get Light name
        name = obj.name

        # Get transform data
        loc, rotquat, scale, orientation = get_transform_data(transform)

        # Get location and orientation / directional vector of the light
        position = self.generate_vector(loc)
        rotation = self.generate_vector(orientation)

        # Get Light Type (0 = point, 1 = directional, 2 = spot)
        # Returns 0 as default value. Malformed lights will have the resulting index 0, which corresponds to point lights.
        light_type = find_light_type_index(light.magickcow_light_type)
        
        # Get Light Properties
        reach = light.magickcow_light_reach # Basically the radius of the light, but it is named "reach" because the light can be a spot light and then it would be more like "max distance" or whatever...
        casts_shadows = light.magickcow_light_casts_shadows
        color_diffuse = light.magickcow_light_color_diffuse
        color_ambient = light.magickcow_light_color_ambient
        
        # Get Light variation Type
        # Returns 0 as default value. Malformed lights will have the resulting index 0, which corresponds to no variation.
        variation_type = find_light_variation_type_index(light.magickcow_light_variation_type)
        
        # Get Light Variation Properties
        variation_speed = light.magickcow_light_variation_speed
        variation_amount = light.magickcow_light_variation_amount
        
        # Other Light Properties
        shadow_map_size = light.magickcow_light_shadow_map_size
        attenuation = light.magickcow_light_use_attenuation
        cutoffangle = light.magickcow_light_cutoffangle
        sharpness = light.magickcow_light_sharpness
        
        # Intensity properties
        specular_amount = light.magickcow_light_intensity_specular
        diffuse_intensity = light.magickcow_light_intensity_diffuse
        ambient_intensity = light.magickcow_light_intensity_ambient
        
        # Modify color values by multiplying with intensity values:
        color_diffuse = color_diffuse * diffuse_intensity
        color_ambient = color_ambient * ambient_intensity
        
        return (name, position, rotation, light_type, variation_type, reach, attenuation, cutoffangle, sharpness, color_diffuse, color_ambient, specular_amount, variation_speed, variation_amount, shadow_map_size, casts_shadows)
    
    def generate_locator_data(self, obj, transform):
        name = obj.name
        radius = obj.magickcow_locator_radius
        matrix = self.generate_matrix_data(transform)
        return (name, matrix, radius)
    
    # region Comment - generate_trigger_data

    # NOTE : Triggers in Magicka start on a corner point, but the representation of an empty is centered around its origin point.
    # To make it easier for users to visualize, we will be translating the data as follows:
    #  - move the trigger's position along each axis by half of the position on that axis, using the forward, right and up vectors of the object to ensure that the translation is correct.
    #  - multiply by 2 the scale of the trigger.
    
    # endregion
    def generate_trigger_data(self, obj, transform):
        
        name = obj.name

        position, rotation_quat, scale = transform.decompose()
        
        # Get right, forward and up vectors
        x_vec = transform.col[0].xyz
        y_vec = transform.col[1].xyz
        z_vec = transform.col[2].xyz
        
        # Normalize the vectors
        x_vec = x_vec.normalized()
        y_vec = y_vec.normalized()
        z_vec = z_vec.normalized()
        
        # These additions and subtractions are completely based on the way that magicka's coords work.
        position = position - (x_vec * scale[0])
        position = position - (y_vec * scale[1])
        position = position - (z_vec * scale[2])

        # Increase the scale by multiplying it times 2 since our triggers have their middle point as their center while in Magicka that is not the origin
        scale = (scale[0] * 2.0, scale[1] * 2.0, scale[2] * 2.0) # NOTE : Scale is the equivalent of "side lengths" in Magicka's code.
        
        position = self.generate_vector(position)
        rotation = self.generate_quaternion(rotation_quat)
        scale = self.generate_vector(scale)
        
        return (name, position, rotation, scale)
    
    def generate_particle_data(self, obj, transform):
        
        particle_name_id = obj.name

        loc, rotquat, scale, ori = get_transform_data(transform, (0.0, -1.0, 0.0)) # The default forward vector for particles is <0,-1,0>

        pos = self.generate_vector(loc)
        rot = self.generate_vector(ori)

        particle_range = obj.magickcow_particle_range
        particle_name_type = obj.magickcow_particle_name
        
        return (particle_name_id, pos, rot, particle_range, particle_name_type)
    
    # region Generate Collision Data

    def generate_collision_data_part(self, obj, transform, last_vertex_index):
        
        # Triangulate the mesh
        mesh, bm = self.get_mesh_data(obj)
        
        # Declare vertex list and index list
        vertices = []
        indices = []
        
        # Store the number of vertices in the mesh:
        num_vertices = len(mesh.vertices)
        
        # Get List of Vertices
        for vert in mesh.vertices:
            position = transform @ vert.co
            position = self.generate_vector(position)
            vertices.append(position)
        
        # Extract vertex data
        global_vertex_idx = 0
        for poly in mesh.polygons:
            triangle_indices = [0, 0, 0]
            
            for loop_idx in poly.loop_indices:
                loop = mesh.loops[loop_idx]
                vertex_idx = loop.vertex_index
                
                triangle_indices[global_vertex_idx % 3] = vertex_idx
                global_vertex_idx += 1
            
            # NOTE : DO NOT Swap winding order for collision meshes!!!
            # For some reason, render triangles and collision triangles have different windings in Magicka, so that's why this is inconsistent with the code in the generate mesh func.
            # NOTE : Add last_vertex_index to the indices to allow patching together multiple vertex and index buffers from multiple collision meshes found within the same collision layer.
            triangle_indices_tuple = (triangle_indices[0] + last_vertex_index, triangle_indices[1] + last_vertex_index, triangle_indices[2] + last_vertex_index)
            
            indices.append(triangle_indices_tuple)
        
        # Free the bm
        bm.free()

        return (num_vertices, vertices, indices)
    
    def generate_collision_layer_data(self, found_collisions):
        last_vertex_index = 0
        layer_vertices = []
        layer_triangles = []
        for collision, transform in found_collisions:
            current_num_vertices, current_vertices, current_triangles = self.generate_collision_data_part(collision, transform, last_vertex_index)
            layer_vertices += current_vertices
            layer_triangles += current_triangles
            last_vertex_index += current_num_vertices
        return (layer_vertices, layer_triangles)
    
    def generate_collision_data(self, found_collisions):
        generated_collisions = [] # Will contain 10 elements, one for each collision layer
        for i in range(0, 10):
            found_collisions_layer = found_collisions[i]
            vertices, triangles = self.generate_collision_layer_data(found_collisions_layer)
            has_collision = len(vertices) > 0
            generated_collisions.append((has_collision, vertices, triangles))
        return generated_collisions
    
    def generate_collision_camera_data(self, found_camera_collisions):
        vertices, triangles = self.generate_collision_layer_data(found_camera_collisions)
        has_collision = len(vertices) > 0
        ans = (has_collision, vertices, triangles)
        return ans

    # endregion

    # region Generate NavMesh Data

    def get_edge(self, vert_a, vert_b):
        if vert_a > vert_b:
            return (vert_b, vert_a)
        return (vert_a, vert_b)
    
    def get_opposite_face(self, current_face_idx, faces_list):
        for i in range(0, len(faces_list)):
            if current_face_idx != faces_list[i]:
                return faces_list[i]
        return 65535

    def generate_nav_mesh_part(self, obj, transform, last_vertex_idx, last_triangle_idx):
        
        # Triangulate the mesh
        mesh, bm = self.get_mesh_data(obj)
        
        vertices = []
        triangles = []
        
        for vert in mesh.vertices:
            position = transform @ vert.co
            position = self.generate_vector(position)
            vertices.append(position)
        
        # This is quite the pain in the ass regarding Blender's python API...
        # For mesh.edges, each edge has a property edge.vertices, which has 2 vertex indices.
        # For bmesh.edges, each edge has a property edge.verts, which has 2 vertices from which you can extract more info, including the index by accessing bm.verts[i].index
        # What a pain in the ass... couldn't the API be a little bit more consistent? Makes me want to write a full blown wrapper of my own... thankfully BM does the exact same operation I could do by hand, only that it can do it faster because it doesn't rely entirely on slow Python loops... it also allows access to information that Blender knows of during runtime but refuses to expose through its regular mesh API... but ok...
        edges = {}
        for edge in bm.edges:
            current_edge = self.get_edge(edge.verts[0].index, edge.verts[1].index)
            current_faces = []
            for face in edge.link_faces:
                current_faces.append(face.index)
            edges[current_edge] = current_faces
        
        for poly in mesh.polygons:
            triangle = [0,0,0]
            idx = 0
            for loop_idx in poly.loop_indices:
                loop = mesh.loops[loop_idx]
                vertex_idx = loop.vertex_index
                
                triangle[idx] = vertex_idx + last_vertex_idx
                idx += 1
            
            # We don't need to translate the vertices to the Y up coordinate system here because the relative positions are still the same, so the distances remain the same.
            # Also because with the new implementation, the Y up transform is done automatically beforehand so it doesn't even matter, no more manually transforming each transform matrix in place.
            pos_a = mesh.vertices[triangle[0]].co
            pos_b = mesh.vertices[triangle[1]].co
            pos_c = mesh.vertices[triangle[2]].co
            
            mid_tr = (pos_a + pos_b + pos_c) / 3.0 # triangle midpoint
            mid_ab = (pos_b + pos_a) / 2.0 # edge AB midpoint
            mid_bc = (pos_c + pos_b) / 2.0 # edge BC midpoint
            mid_ca = (pos_a + pos_c) / 2.0 # edge CA midpoint
            
            # Compute the cost as the distance between the triangle midpoint and the midpoint of the edge between this polygon and the adjacent polygon on each edge.
            cost_ab = (mid_tr - mid_ab).length
            cost_bc = (mid_tr - mid_bc).length
            cost_ca = (mid_tr - mid_ca).length
            
            # Old implementation used to calculate cost like this. It's wrong, for obvious reasons, but it still gave a good enough result in open spaces.
            # I'm just keeping it around in case the code can be useful for debugging purposes later on, or for adding customized cost calculation settings on the N key panel or whatever...
            # cost_ab = (pos_b - pos_a).length
            # cost_bc = (pos_c - pos_b).length
            # cost_ca = (pos_a - pos_c).length
            
            neighbour_a = self.get_opposite_face(poly.index, edges[self.get_edge(triangle[0], triangle[1])])
            neighbour_b = self.get_opposite_face(poly.index, edges[self.get_edge(triangle[1], triangle[2])])
            neighbour_c = self.get_opposite_face(poly.index, edges[self.get_edge(triangle[2], triangle[0])])
            
            tri = (triangle[0], triangle[1], triangle[2], neighbour_a, neighbour_b, neighbour_c, cost_ab, cost_bc, cost_ca) # within Magicka's code, 65535 (max u16 value) is reserved as the "none" or "null" value for neighbour triangle indices.
            triangles.append(tri)
        
        # Free the bm (fun fact, this function is the only one that actually needs the bm to exist up until this point... again, keeping it everywhere else for consistency, and just in case it is needed in the future)
        bm.free()
        
        # Each Triangle = vertex_a, vertex_b, vertex_c, neighbour_a, neighbour_b, neighbour_c, cost_ab, cost_bc, cost_ca
        return (vertices, triangles)
    
    def generate_nav_mesh_data(self, found_meshes_nav):
        last_vertex_idx = 0
        last_triangle_idx = 0
        ans_vertices = []
        ans_triangles = []
        for obj, transform in found_meshes_nav:
            vertices, triangles = self.generate_nav_mesh_part(obj, transform, last_vertex_idx, last_triangle_idx)
            last_vertex_idx += len(vertices)
            last_triangle_idx += len(triangles)
            ans_vertices += vertices
            ans_triangles += triangles
        return (ans_vertices, ans_triangles)
    
    # endregion

    # region Generate Static Data
    
    # Aaaand... it's fucking deprecated! Because the dictionary is more than enough!
    # TODO : Remove!!!
    def generate_static_materials_data(self, generated_meshes):
        # region Comment
            # Create all of the materials for the meshes after creating the mesh data itself
            # This is a file access loop, which prevents stalling the program during the mesh creation loop and helps with performance a tiny bit.
            # This is because most systems have some form of caching for file access when accessing multiple files within the same path.
            # Also because the hard drive operates faster when performing sequential file accesses
            # In short, a dumb trick to get some disk I/O performance gain that mostly works in spinning disk drives, SSD still gets some performance out of this
            # but it's a fucking joke with how fast those are... basically it's kind of a dumb thing to do but I have found this to be faster in the HDDs where I've tested it, so yeah.
            # Also it helps to separate the mesh creation from the material creation because waiting for the disk I/O to finish and then waiting for a response from the OS always gives a small downtime
            # waiting when the process has already actually finished, but the system has not reported back to the program yet, so we can't continue generating mesh data for the next mesh yet until that's over.
            # Not like this optimization matters that much tho considering how materials are cached now and we avoid a lot of disk accesses, but still...
            # Also, caching the entire mesh generation function is not possible because this is an interpreted language, but the create material function is small enough that it can probably be cached, making
            # every iteration of the loop just a bit faster due it being sequential calls to the same function, which also places in the cache the dictionary accesses, so yeah...
            # In short, even if you don't believe it, this piece of shit actually makes this faster, not too much, but that small increment that shave off 1 or 2 seconds in a long file export process.
        # endregion
        for mesh in generated_meshes:
            obj, transform, vertices, indices, matname = mesh
            self.create_material(matname, obj.data.magickcow_mesh_type)

    def generate_static_meshes_data(self, found_meshes):
        ans = [self.generate_static_mesh_data(obj, transform, matid) for obj, transform, matid in found_meshes]
        return ans
    
    def generate_static_liquids_data(self, found_liquids):
        ans = [self.generate_liquid_data(obj, transform, matid) for obj, transform, matid in found_liquids]
        return ans

    def generate_static_lights_data(self, found_lights):
        ans = [self.generate_light_data(obj, transform) for obj, transform in found_lights]
        return ans

    def generate_static_locators_data(self, found_locators):
        ans = [self.generate_locator_data(obj, transform) for obj, transform in found_locators]
        return ans

    def generate_static_triggers_data(self, found_triggers):
        ans = [self.generate_trigger_data(obj, transform) for obj, transform in found_triggers]
        return ans

    def generate_static_particles_data(self, found_particles):
        ans = [self.generate_particle_data(obj, transform) for obj, transform in found_particles]
        return ans

    def generate_static_collisions_data(self, found_collisions):
        ans = self.generate_collision_data(found_collisions)
        return ans
    
    def generate_static_collisions_camera_data(self, found_camera_collisions):
        ans = self.generate_collision_camera_data(found_camera_collisions)
        return ans

    def generate_static_physics_entities_data(self, found_entities):
        ans = [self.generate_physics_entity_data(obj, transform) for obj, transform in found_entities]
        return ans
    
    def generate_static_force_fields_data(self, found_fields):
        ans = [self.generate_force_field_data(obj, transform, matid) for obj, transform, matid in found_fields]
        return ans

    # region Comment

    # NOTE : This is basically an "inlined" version of the final collision generation functions. It does the exact same thing.
    # The only reason this test exists is because I was debugging some slow down in the collision mesh generation and I assumed it was related to the extra function calls.
    # While it is true that Python function calls are slower than the inlined version, in this case the difference is extremely small and it is negligible...
    # the real cause was a mistake on the scene (I had forgotten to disable the complex collision generation on some super high poly mesh LOL)
    # The only reason I'm keeping this commented out in here is to remind myself of how the code would look like when inlined for future use, as this is pretty useful actually...
    # def generate_static_collisions_data(self, found_collisions):
    #     generated_collisions = [] # Will contain 10 elements, one for each collision layer
    #     for i in range(0, 10):
    #         found_collisions_layer = found_collisions[i]
    #         last_vertex_index = 0
    #         layer_vertices = []
    #         layer_triangles = []
    #         for collision, transform in found_collisions_layer:
    #             current_num_vertices, current_vertices, current_triangles = self.generate_collision_data_part(collision, transform, last_vertex_index)
    #             layer_vertices += current_vertices
    #             layer_triangles += current_triangles
    #             last_vertex_index += current_num_vertices
    #         generated_collisions.append((layer_vertices, layer_triangles))
    #     return generated_collisions
    
    # endregion

    def generate_static_nav_meshes_data(self, found_nav_meshes):
        ans = self.generate_nav_mesh_data(found_nav_meshes)
        return ans

    # endregion

    # region Generate Animated Data

    def generate_animated_meshes_data(self, found_meshes):
        ans = [self.generate_animated_mesh_data(obj, transform, matid) for obj, transform, matid in found_meshes]
        return ans

    def generate_animated_lights_data(self, found_lights):
        ans = [self.generate_light_reference_data(obj, transform) for obj, transform in found_lights]
        return ans

    # Aux function used to generate an animation tuple with a duration of 0 and an empty animation frame
    def generate_animation_data_empty(self, transform):
        duration = 0
        time = 0
        pos, rotquat, scale, orientation = get_transform_data(transform)

        pos = (pos[0], pos[1], pos[2])
        rot = (rotquat[1], rotquat[2], rotquat[3], rotquat[0])
        scale = (scale[0], scale[1], scale[2])

        frame = (time, pos, rot, scale)
        anim = (duration, [frame])
        
        return anim

    # This function takes in a bone object and its relative transfrom. It then processes the animation frames from blender's timeline to generate the animation data.
    # If the object has no animation data, then it internally calls generate_animation_data_empty().
    # This is useful as a fallback when creating animated level parts just for the sake of creating an interactable object with no animation.
    def generate_animation_data(self, obj, transform):
        
        # TODO : Cleanup, remove unused trash
        # Compute the parent transform (remember that obj.parent is not necessarily what we call a "parent" in this context... so that won't work!)
        # parent_transform = obj.matrix_world @ transform.inverted()

        # Cache an "empty" animation with a single dummy frame in case that the generated animation is not correct and has to be discarded, or in case that there is no animation data attached to this bone.
        empty_anim = self.generate_animation_data_empty(transform) # Note that the generated dummy frame has to have the same transform as that of the object to display it in the correct location in game.

        # If the object's animation data is None, there is no animation data at all, so we return the empty animation.
        anim_data = obj.animation_data
        if anim_data is None:
            return empty_anim
        
        # If the object's animation action is None, there is some animation data but it has no active action, so we return the empty animation.
        action = obj.animation_data.action
        if action is None:
            return empty_anim
        
        # Get a sorted set of the keyframes that contain any form of animation data in the timeline.
        blender_keyframes = get_action_keyframes(action)

        # If there are no keyframes, that means that the animation timeline is empty, so we return the empty animation as well.
        if len(blender_keyframes) <= 0:
            return empty_anim

        # Get other blender animation scene data
        blender_framerate = bpy.context.scene.render.fps
        time_per_frame = 1.0 / blender_framerate

        # Calculate animation duration by getting the last frame and the first frame and calculating the difference
        # Usually, the first frame would be located at 0 or 1, so this difference would not matter, but we're doing so anyway because it is possible to place the first frame at any point in the timeline.
        duration = blender_keyframes[-1] * time_per_frame - blender_keyframes[0] * time_per_frame
        
        # Get all of the actual frames with time, location, rotation and scale data
        frames = []
        for blender_frame in blender_keyframes:
            # Set the scene to the current frame
            bpy.context.scene.frame_set(int(blender_frame))
            bpy.context.view_layer.update() # Update the scene because it seems to fail to fetch the correct data when there are multiple animated objects on the scene...

            # Extract the information from the current frame
            # region Comment
                # This section right here is some old discarded code, but it is important to understand why things are coded the way that they are.
                # NOTE : Since this is animation data, these values are stored relative to the parent, so they are already in relative coordinates.
                # loc = obj.location.copy()
                # rot = obj.rotation_quaternion.copy()
                # scale = obj.scale.copy()
                # The problem is that these functions work over the local coordinate system of Blender, which means that we do not get the correct Y up coordinates that we require, because even tho
                # the world has been rotated previously by 90 degrees, the coordinates are stored local to the parent object, which means that animated level parts that are children to some other object
                # in the scene will NOT have the correct Y up coordinate system, and will still have a Z up coordinate system instead.
                # It is for that reason that we use the transform matrix that we input to this function. We calculated the relative coordinates by getting the difference between the object's global transform
                # and its parent's global transform, so it should contain a relative transform in Y up, as all of the global coordinates will always be in Y up.
            # endregion
            # We use the object transform as referenced from the object itself, because the transform changes on every single frame of the animation.
            # That way, we can extract the correct relative location. Do note that, since the root node of an entire skeletan structure is rotated by 90 degrees,
            # we don't care about the fact that obj.matrix_local is in Z up coordinates, since it will look correctly in game, because the root is already rotated.
            # The data will internally operate on Z up, but we don't care about that.
            loc, rot, scale, ori = get_transform_data(obj.matrix_local)

            # Translate the values to tuples
            loc = self.generate_vector(loc)
            rot = self.generate_quaternion(rot) # The rotation is a quaternion, so we represent it as a vec4 / tuple with 4 elements.
            scale = self.generate_vector(scale)

            # Get the time at which the frame takes place
            time = time_per_frame * int(blender_frame)

            # Make the frame and add it to the list of frames
            frame = (time, loc, rot, scale)
            frames.append(frame)

        ans = (duration, frames)

        return ans

    def generate_animated_bone_data(self, bone_obj, bone_transform):
        name = bone_obj.name
        matrix = self.generate_matrix_data(bone_transform)
        radius = bone_obj.magickcow_locator_radius
        collision_enabled = bone_obj.magickcow_collision_enabled
        collision_channel = find_collision_material_index(bone_obj.magickcow_collision_material)
        affects_shields = bone_obj.magickcow_bone_affects_shields
        bone_settings = (radius, collision_enabled, collision_channel, affects_shields)
        return (name, matrix, bone_settings)

    # endregion

    # region Generation entry point

    # NOTE : Some of the stuff generated on the static side of the code is not present on the animated side, so DO NOT call this function from the generate scene data animated functions as a way to simply the code...
    def generate_scene_data_static(self, found_scene_objects, generated_scene_objects):
        generated_scene_objects.meshes                = self.generate_static_meshes_data(found_scene_objects.meshes)
        generated_scene_objects.waters                = self.generate_static_liquids_data(found_scene_objects.waters)
        generated_scene_objects.lavas                 = self.generate_static_liquids_data(found_scene_objects.lavas)
        generated_scene_objects.lights                = self.generate_static_lights_data(found_scene_objects.lights)
        generated_scene_objects.locators              = self.generate_static_locators_data(found_scene_objects.locators)
        generated_scene_objects.triggers              = self.generate_static_triggers_data(found_scene_objects.triggers)
        generated_scene_objects.particles             = self.generate_static_particles_data(found_scene_objects.particles)
        generated_scene_objects.collisions            = self.generate_static_collisions_data(found_scene_objects.collisions)
        generated_scene_objects.camera_collision_mesh = self.generate_static_collisions_camera_data(found_scene_objects.camera_collision_meshes)
        generated_scene_objects.nav_mesh              = self.generate_static_nav_meshes_data(found_scene_objects.nav_meshes)
        generated_scene_objects.physics_entities      = self.generate_static_physics_entities_data(found_scene_objects.physics_entities)
        generated_scene_objects.force_fields          = self.generate_static_force_fields_data(found_scene_objects.force_fields)
    
    def generate_scene_data_static_TIMINGS(self, found_scene_objects, generated_scene_objects):
        t0 = time.time()
        generated_scene_objects.meshes     = self.generate_static_meshes_data(found_scene_objects.meshes)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"mesh = {totalt}")

        t0 = time.time()
        generated_scene_objects.waters     = self.generate_static_liquids_data(found_scene_objects.waters)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"waters = {totalt}")

        t0 = time.time()
        generated_scene_objects.lavas      = self.generate_static_liquids_data(found_scene_objects.lavas)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"lavas = {totalt}")

        t0 = time.time()
        generated_scene_objects.lights     = self.generate_static_lights_data(found_scene_objects.lights)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"lights = {totalt}")

        t0 = time.time()
        generated_scene_objects.locators   = self.generate_static_locators_data(found_scene_objects.locators)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"locators = {totalt}")

        t0 = time.time()
        generated_scene_objects.triggers   = self.generate_static_triggers_data(found_scene_objects.triggers)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"triggers = {totalt}")
        
        t0 = time.time()
        generated_scene_objects.particles  = self.generate_static_particles_data(found_scene_objects.particles)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"particles = {totalt}")

        t0 = time.time()
        generated_scene_objects.collisions = self.generate_static_collisions_data(found_scene_objects.collisions)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"collisions = {totalt}")

        t0 = time.time()
        generated_scene_objects.nav_mesh   = self.generate_static_nav_meshes_data(found_scene_objects.nav_meshes)
        t1 = time.time()
        totalt = t1 - t0
        self.report({"INFO"}, f"navmesh = {totalt}")
    
    # TODO : Fully implement!
    def generate_scene_data_animated_internal(self, bone_obj, bone_transform, found_scene_objects, generated_scene_objects):
        # Generate bone data (bone info such as the name, transform, etc...)
        generated_scene_objects.bone = self.generate_animated_bone_data(bone_obj, bone_transform)

        # Generate mesh and then use the material name to add it to the shared resources dictionary
        generated_scene_objects.meshes = self.generate_animated_meshes_data(found_scene_objects.meshes)
        
        # This time only generate light references and not full light data.
        generated_scene_objects.lights = self.generate_animated_lights_data(found_scene_objects.lights)

        # Same stuff as the static scene for the rest of the objects
        generated_scene_objects.waters     = self.generate_static_liquids_data(found_scene_objects.waters)
        generated_scene_objects.lavas      = self.generate_static_liquids_data(found_scene_objects.lavas)
        generated_scene_objects.locators   = self.generate_static_locators_data(found_scene_objects.locators)
        generated_scene_objects.triggers   = self.generate_static_triggers_data(found_scene_objects.triggers)
        generated_scene_objects.particles  = self.generate_static_particles_data(found_scene_objects.particles)
        generated_scene_objects.nav_mesh   = self.generate_static_nav_meshes_data(found_scene_objects.nav_meshes)

        # Generate aux array with all 10 collision layers. All layers except one will be empty, so we retrieve the correct one and store it in the final collision property of the generated data.
        aux_collisions = self.generate_static_collisions_data(found_scene_objects.collisions)
        generated_scene_objects.collision = aux_collisions[find_collision_material_index(bone_obj.magickcow_collision_material)]

        # Generate animation data. If there is no animation data, an animation with a default / "empty" frame will be created, as Magicka requires that all animated level parts have an animation with at least 1 frame, containing the object's resting position.
        generated_scene_objects.animation = self.generate_animation_data(bone_obj, bone_transform)
    
    def generate_scene_data_animated_rec(self, animated_part, generated_scene_objects):

        bone_obj, bone_transform, children_found = animated_part
        
        # NOTE : This function that we're calling really should just be part of this function, but for now we're separating it to make things a bit clearer when programming... I guess... or something...
        self.generate_scene_data_animated_internal(bone_obj, bone_transform, children_found, generated_scene_objects)

        # Iterate over the child animated level parts
        for child in children_found.animated_parts:
            generated_child = MCow_Map_SceneObjectsGeneratedAnimated()
            self.generate_scene_data_animated_rec(child, generated_child)
            generated_scene_objects.animated_parts.append(generated_child)

    def generate_scene_data_animated(self, found_scene_objects, generated_scene_objects):
        for part in found_scene_objects.animated_parts:
            generated_part = MCow_Map_SceneObjectsGeneratedAnimated()
            self.generate_scene_data_animated_rec(part, generated_part)
            generated_scene_objects.animated_parts.append(generated_part)
    
    def generate_scene_data_internal(self, found_scene_objects, generated_scene_objects):
        self.generate_scene_data_static(found_scene_objects, generated_scene_objects)
        self.generate_scene_data_animated(found_scene_objects, generated_scene_objects)
    
    def generate_scene_data(self, found_scene_objects):
        generated_scene_objects = MCow_Map_SceneObjectsGeneratedStatic()
        self.generate_scene_data_internal(found_scene_objects, generated_scene_objects)
        return generated_scene_objects
    
    # endregion

    # endregion

# region Comment - DataGeneratorPhysicsEntity
    # This data generator class is dedicated toward generating the data for physics entities.
    # The export process is pretty different from that of map scenes, but it also has multiple similarities.
    # One of the similarities is that physics entities contain an XNB model class within it, which means that the animated level part side of the code is pretty much almost identical to what this class requires.
# endregion
class MCow_Data_Generator_PhysicsEntity(MCow_Data_Generator):
    def __init__(self, cache):
        super().__init__(cache)
        return

    def generate(self, found_objects):
        ans = self.generate_physics_entity_data(found_objects)
        return ans

    def generate_physics_entity_data(self, data):

        obj = data.root

        ans = PE_Generate_PhysicsEntityData()

        ans.physics_entity_id = obj.name
        ans.is_movable = obj.mcow_physics_entity_is_movable
        ans.is_pushable = obj.mcow_physics_entity_is_pushable
        ans.is_solid = obj.mcow_physics_entity_is_solid
        ans.mass = obj.mcow_physics_entity_mass
        ans.max_hit_points = obj.mcow_physics_entity_hitpoints
        ans.can_have_status = obj.mcow_physics_entity_can_have_status

        # NOTE : The reason this has been implemented like this rather than passing the obj.whatever collection property itself is that in the future, we have no idea how Blender may decide to implement bpy props serialization, so better to be safe than sorry... even tho it might make things a little bit slower... fucking pythong I swear to God...
        ans.resistances = [PE_Generate_Resistance(resistance.element, resistance.multiplier, resistance.modifier) for resistance in obj.mcow_physics_entity_resistances]
        ans.gibs = [PE_Generate_Gib(gib.model, gib.mass, gib.scale) for gib in obj.mcow_physics_entity_gibs]

        # TODO : Figure out what these properties really do. In all objects I have decompiled, these are ALWAYS empty, so it seems like they are simply unused.
        ans.gib_trail_effect = ""
        ans.hit_effect = ""
        ans.visual_effects = []
        ans.sound_banks = ""
        # This is where the "unknown" properties end.

        ans.model = self.generate_model(data.model)


        # TODO : Finish adding all of the remaining values for the ans object

        ans.bounding_boxes = self.generate_bounding_boxes_data(data.boxes)

        return ans

    def generate_bounding_boxes_data(self, boxes):
        ans = [self.generate_bounding_box_data(box) for box in boxes]
        return ans
    
    def generate_bounding_box_data(self, box):

        ans = PE_Generate_BoundingBox()
        
        ans.id = box.name

        # TODO : Modify this data so that it is in a Y up coordinate system instead... this is just temporary stuff for now.
        # Note that it is actually NOT possible to fix this by just rotating the matrix of the root by 90º since bounding boxes are not stored attached to the model bones in the final XNB file...
        ans.position = tuple(box.location)
        ans.scale = tuple(box.scale)
        ans.rotation = tuple(box.rotation_euler.to_quaternion())

        return ans

    def generate_model(self, model_data):
        meshes = self.generate_model_meshes(model_data.meshes)
        bones = self.generate_model_bones(model_data.bones)
        return (meshes, bones)

    def generate_model_meshes(self, meshes):
        ans = [self.generate_model_mesh(obj, transform, matid, parent_bone_index) for obj, transform, matid, parent_bone_index in meshes]
        return ans

    def generate_model_mesh(self, obj, transform, matid, parent_bone_index):
        name = obj.name
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)
        shared_resource_index = self.cache.add_shared_resource(matname, self.cache.get_material(matname))
        return (name, parent_bone_index, vertices, indices, shared_resource_index)

    def generate_model_bones(self, bones):
        ans = [self.generate_model_bone(bone) for bone in bones]
        return ans

    def generate_model_bone(self, bone):
        ans = PE_Generate_Bone()
        ans.index = bone.index
        ans.name = bone.obj.name
        ans.transform = self.generate_matrix_data(bone.transform)
        ans.parent = bone.parent
        ans.children = bone.children
        return ans
    
# endregion

# ../mcow/functions/generation/export/Make.py
# region Make Stage

# This section contains classes whose purpose is to define the logic of the Make Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Maker class.
class MCow_Data_Maker:
    def __init__(self, cache):
        self.cache = cache
        return
    
    def make(self, generated_data):
        ans = {} # We return an empty object by default since this is the base class and it doesn't really implement any type of object data generation anyway, so yeah.
        return ans

    # region Make - XNA

    # NOTE : This is obviously NOT the structure of a binary XNB file... this is just the JSON text based way of organizing the data for an XNB file that MagickaPUP uses.
    # This comment is pretty absurd as it states the obvious for myself... I just made it for future readers so that they don't tear the balls out trying to figure out wtf is going on, even tho I think it should be pretty obvious.
    def make_xnb_file(self, primary_object, shared_resources):
        ans = {
            "XnbFileData": {
                "ContentTypeReaders" : [], # TODO : Get rid of this and make it so that we can automatically generate these based on usage on the MagickaPUP side.
                "PrimaryObject" : primary_object,
                "SharedResources" : shared_resources
            }
        }
        return ans
    
    # endregion

    # region Make - Math

    # region Make - Math - Matrices
    
    def make_matrix(self, transform_matrix):
        m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34, m41, m42, m43, m44 = transform_matrix
        ans = {
            "M11" : m11,
            "M12" : m12,
            "M13" : m13,
            "M14" : m14,
            "M21" : m21,
            "M22" : m22,
            "M23" : m23,
            "M24" : m24,
            "M31" : m31,
            "M32" : m32,
            "M33" : m33,
            "M34" : m34,
            "M41" : m41,
            "M42" : m42,
            "M43" : m43,
            "M44" : m44
        }
        return ans
    
    def make_matrix_identity(self):
        ans = {
            "M11" : 1,
            "M12" : 0,
            "M13" : 0,
            "M14" : 0,
            "M21" : 0,
            "M22" : 1,
            "M23" : 0,
            "M24" : 0,
            "M31" : 0,
            "M32" : 0,
            "M33" : 1,
            "M34" : 0,
            "M41" : 0,
            "M42" : 0,
            "M43" : 0,
            "M44" : 1
        }
        return ans

    # endregion

    # region Make - Math - Vectors

    def make_vector_2(self, vec2):
        ans = {
            "x" : vec2[0],
            "y" : vec2[1]
        }
        return ans
    
    def make_vector_3(self, vec3):
        ans = {
            "x" : vec3[0],
            "y" : vec3[1],
            "z" : vec3[2]
        }
        return ans
    
    def make_vector_4(self, vec4):
        ans = {
            "x" : vec4[0],
            "y" : vec4[1],
            "z" : vec4[2],
            "w" : vec4[3]
        }
        return ans

    # endregion

    # endregion

    # region Make - meshes, vertex declarations and effects

    def make_vertex_declaration_entry(self, entry):
        stream, offset, element_format, element_method, element_usage, usage_index = entry
        ans = {
            "stream" : stream,
            "offset" : offset,
            "elementFormat" : element_format,
            "elementMethod" : element_method,
            "elementUsage" : element_usage,
            "usageIndex" : usage_index
        }
        return ans

    def make_vertex_declaration(self, entries):
        entries_arr = []
        for entry in entries:
            declaration = self.make_vertex_declaration_entry(entry)
            entries_arr.append(declaration)
        ans = {
            "numEntries" : len(entries_arr),
            "entries" : entries_arr
        }
        return ans
    
    def make_vertex_declaration_default(self):
        return self.make_vertex_declaration([(0, 0, 2, 0, 0, 0), (0, 12, 2, 0, 3, 0), (0, 24, 1, 0, 5, 0), (0, 32, 2, 0, 6, 0), (0, 24, 1, 0, 5, 1), (0, 32, 2, 0, 6, 1), (0, 44, 3, 0, 10, 0)])
    
    def make_vertex_stride_default(self):
        # Old Stide was 44, the vertex color inclusion has changed that. No need to make special cases because it's actually quite slim, vertex color doesn't even bloat mesh memory usage that much despite the 2GB limit...
        # return 44 # 44 = 11*4; only 11 because we do not account for those vertex declarations that use usage index 1, because they overlap with already existing values from the usage index 0.
        return 60 # 60 because we include the vertex color now, which has its own vertex declaration.
    
    def make_vertex_buffer(self, vertices):
        buf = []
        for vertex in vertices:
            global_idx, position, normal, tangent, uv, color = vertex
            buffer_part = struct.pack("fffffffffffffff", position[0], position[1], position[2], normal[0], normal[1], normal[2], uv[0], uv[1], tangent[0], tangent[1], tangent[2], color[0], color[1], color[2], color[3])
            byte_array = bytearray(buffer_part)
            # int_array = array.array("i")
            # int_array.frombytes(byte_array)
            buf += byte_array
        ans = {
            "NumBytes" : len(buf),
            "Buffer" : buf
        }
        return ans
    
    def make_index_buffer(self, indices):
        # Always use 16 bit indices if we can fit the max value of the index within the u16 range [0, 65535]. If the max index is larger than that, then we start making use of 32 bit values
        # I don't really like this because it feels like it can be pretty slow to find the max element like this, but whatever... we'll keep it like this for now, since 99% of maps are most
        # likely not going to have such massive models within a single piece.
        index_size = 0
        num_bytes = len(indices) * 2
        if max(indices) > 65535:
            index_size = 1
            num_bytes = len(indices) * 4
        ans = {
            "indexSize" : index_size,
            "data" : indices,
            "numBytes" : num_bytes
        }
        return ans

    # region Comment - make_effect
    
    # This once used to be an useful function... now, it is quite an useless wrapper! :D
    # Literally just saves us from having to invoke the get_material() method from the self.cache...
    # Altough in the future we could modify the function to get specific resources rather than just materials?
    
    # endregion
    def make_effect(self, matname, fallback_type = "GEOMETRY"):
        material_contents = self.cache.get_material(matname, fallback_type)
        return material_contents

    # endregion

    # region Make - Other

    def make_shared_resources_list(self, cache):
        ans = []
        for key, resource in cache._cache_shared_resources.items():
            idx, content = resource
            ans.append(content)
        return ans

    # endregion

# Data Maker class for Maps / Levels
class MCow_Data_Maker_Map(MCow_Data_Maker):
    def __init__(self, cache):
        super().__init__(cache)
        return
    
    def make(self, generated_data):
        ans = self.make_xnb_file(self.make_level_model(generated_data), self.make_shared_resources_list(self.cache))
        return ans
    
    # region "Make Data" / "Format Data" Functions

    # region Make - Boundaries (Bounding Box, Bounding Sphere)

    def make_bounding_box(self, aabb):
        minp, maxp = aabb
        ans = {
            "Min" : {
                "x" : minp[0],
                "y" : minp[1],
                "z" : minp[2]
            },
            "Max" : {
                "x" : maxp[0],
                "y" : maxp[1],
                "z" : maxp[2]
            }
        }
        return ans

    # TODO : def make_bounding_sphere etc...

    # endregion

    # region Make - Meshes (Root Nodes, Effects / Materials, Vertex Buffers, Index Buffers, Vertex Declarations, etc...)

    def make_root_node(self, mesh):
        obj, transform, name, vertices, indices, matname, aabb, sway, entity_influence, ground_level = mesh
        primitives = int(len(indices) / 3) # Magicka's primitives are always triangles, and the mesh was triangulated, so this calculation is assumed to always be correct.
        ans = {
            "isVisible" : True,
            "castsShadows" : True,
            "sway" : sway,
            "entityInfluence" : entity_influence,
            "groundLevel" : ground_level,
            "numVertices" : len(vertices),
            "vertexStride" : self.make_vertex_stride_default(),
            "vertexDeclaration" : self.make_vertex_declaration_default(),
            "vertexBuffer" : self.make_vertex_buffer(vertices),
            "indexBuffer" : self.make_index_buffer(indices),
            "effect" : self.make_effect(matname, "GEOMETRY"),
            "primitiveCount" : primitives,
            "startIndex" : 0,
            "boundingBox" : self.make_bounding_box(aabb),
            "hasChildA" : False,
            "hasChildB" : False,
            "childA" : None,
            "childB" : None
        }
        return ans
    
    def make_root_nodes(self, meshes):
        ans = [self.make_root_node(mesh) for mesh in meshes]
        return ans

    # endregion

    # region Make - Lights

    def make_light(self, light):
        
        # Extract light data
        name, position, rotation, light_type, variation_type, reach, attenuation, cutoffangle, sharpness, color_diffuse, color_ambient, specular_amount, variation_speed, variation_amount, shadow_map_size, casts_shadows = light

        # Construct Answer dictionary
        ans = {
            "LightName" : name,
            "Position" : {
                "x" : position[0],
                "y" : position[1],
                "z" : position[2]
            },
            "Direction" : {
                "x" : rotation[0],
                "y" : rotation[1],
                "z" : rotation[2]
            },
            "LightType" : light_type,
            "LightVariationType" : variation_type,
            "Reach" : reach,
            "UseAttenuation" : attenuation,
            "CutoffAngle" : cutoffangle,
            "Sharpness" : sharpness,
            "DiffuseColor" : {
                "x" : color_diffuse[0],
                "y" : color_diffuse[1],
                "z" : color_diffuse[2]
            },
            "AmbientColor" : {
                "x" : color_ambient[0],
                "y" : color_ambient[1],
                "z" : color_ambient[2]
            },
            "SpecularAmount" : specular_amount,
            "VariationSpeed" : variation_speed,
            "VariationAmount" : variation_amount,
            "ShadowMapSize" : shadow_map_size,
            "CastsShadows" : casts_shadows
        }
        
        return ans
    
    def make_light_reference(self, light):
        name, transform = light
        matrix = self.make_matrix(transform)
        ans = {
            "name" : name,
            "position" : matrix
        }
        return ans

    def make_lights(self, lights):
        ans = [self.make_light(light) for light in lights]
        return ans

    def make_light_references(self, lights):
        ans = [self.make_light_reference(light) for light in lights]
        return ans

    # endregion

    # region Make - Collisions

    def make_collision_vertices(self, vertices):
        ans = []
        for v in vertices:
            x, y, z = v
            vert = {
                "x" : x,
                "y" : y,
                "z" : z
            }
            ans.append(vert)
        return ans
    
    def make_collision_triangles(self, triangles):
        ans = []
        for t in triangles:
            i0, i1, i2 = t
            triangle = {
                "index0" : i0,
                "index1" : i1,
                "index2" : i2
            }
            ans.append(triangle)
        return ans
    
    def make_collision_old(self, has_collision = False, vertices = [], triangles = []):
        ans = {
                "hasCollision" : False,
                "vertices" : [],
                "numTriangles" : 0,
                "triangles" : []
            }
        
        if has_collision:
            ans["hasCollision"] = has_collision
            ans["vertices"] = self.make_collision_vertices(vertices)
            ans["numTriangles"] = len(triangles)
            ans["triangles"] = self.make_collision_triangles(triangles)
        
        return ans
    
    def make_collision(self, collision = (False, [], [])):
        has_collision, vertices, triangles = collision
        ans = {
            "hasCollision" : has_collision,
            "vertices" : self.make_collision_vertices(vertices),
            "numTriangles" : len(triangles),
            "triangles" : self.make_collision_triangles(triangles)
        }
        return ans

    def make_collisions(self, collisions = [(False, [], []) for i in range(10)]):
        ans = [self.make_collision(collision) for collision in collisions]
        return ans

    # endregion

    # region Make - Point Data (Locators, Triggers, Particles)
    
    def make_locator(self, data):
        name, transform, radius = data
        ans = {
            "Name" : name,
            "Transform" : self.make_matrix(transform),
            "Radius" : radius
        }
        return ans
    
    def make_trigger(self, data):
        name, position, rotation, scale = data
        ans = {
            "Name" : name,
            "Position" : {
                "x" : position[0],
                "y" : position[1],
                "z" : position[2]
            },
            "SideLengths" : {
                "x" : scale[0],
                "y" : scale[1],
                "z" : scale[2]
            },
            "Rotation" : {
                "x" : rotation[0],
                "y" : rotation[1],
                "z" : rotation[2],
                "w" : rotation[3]
            }
        }
        return ans
    
    def make_particle(self, particle):
        name_id, vec1, vec2, particle_range, name_type = particle
        ans = {
            "id" : name_id,
            "vector1" : { # Location
                "x" : vec1[0],
                "y" : vec1[1],
                "z" : vec1[2]
            },
            "vector2" : { # Orientation / Direction / Director vector
                "x" : vec2[0],
                "y" : vec2[1],
                "z" : vec2[2]
            },
            "range" : particle_range,
            "name" : name_type
        }
        return ans


    def make_locators(self, locators):
        ans = [self.make_locator(locator) for locator in locators]
        return ans
    
    def make_triggers(self, triggers):
        ans = [self.make_trigger(trigger) for trigger in triggers]
        return ans
    
    def make_particles(self, particles):
        ans = [self.make_particle(particle) for particle in particles]
        return ans

    # endregion

    # region Make - Liquids

    def make_liquid(self, liquid_data, liquid_type_str1 = "liquid_water", liquid_type_str2 = "WATER"):
        vertices, indices, matname, can_drown, freezable, autofreeze = liquid_data
        ans = {
            "$type" : liquid_type_str1,
            "vertices" : self.make_vertex_buffer(vertices),
            "indices" : self.make_index_buffer(indices),
            "declaration" : self.make_vertex_declaration_default(),
            "vertexStride" : self.make_vertex_stride_default(),
            "numVertices" : len(vertices),
            "primitiveCount" : len(indices) // 3,
            "flag" : can_drown,
            "freezable" : freezable,
            "autofreeze" : autofreeze,
            "effect" : self.make_effect(matname, liquid_type_str2)
        }
        return ans

    def make_water(self, data):
        ans = self.make_liquid(data, "liquid_water", "WATER")
        return ans
    
    def make_lava(self, data):
        ans = self.make_liquid(data, "liquid_lava", "LAVA")
        return ans
    
    def make_liquids(self, waters_data, lavas_data):
        waters = [self.make_water(water) for water in waters_data]
        lavas = [self.make_lava(lava) for lava in lavas_data]
        liquids = waters + lavas
        return liquids

    # endregion

    # region Make - Nav Mesh

    def make_nav_mesh_triangle(self, triangle):
        vertex_a, vertex_b, vertex_c, neighbour_a, neighbour_b, neighbour_c, cost_ab, cost_bc, cost_ca = triangle
        ans = {
            "VertexA" : vertex_a,
            "VertexB" : vertex_b,
            "VertexC" : vertex_c,
            "NeighbourA" : neighbour_a,
            "NeighbourB" : neighbour_b,
            "NeighbourC" : neighbour_c,
            "CostAB" : cost_ab,
            "CostBC" : cost_bc,
            "CostCA" : cost_ca,
            "Properties" : 0 # By default, the properties will be 0, which corresponds with MovementProperties.Default (allow customization through vertex data / triangle data later on?)
        }
        return ans
    
    def make_nav_mesh_triangles(self, triangles):
        ans = []
        for t in triangles:
            tri = self.make_nav_mesh_triangle(t)
            ans.append(tri)
        return ans
    
    def make_nav_mesh_vertex(self, vertex):
        x, y, z = vertex
        ans = {
            "x" : x,
            "y" : y,
            "z" : z
        }
        return ans
    
    def make_nav_mesh_vertices(self, vertices):
        ans = []
        for v in vertices:
            vert = self.make_nav_mesh_vertex(v)
            ans.append(vert)
        return ans
    
    def make_nav_mesh(self, navmesh):
        vertices, triangles = navmesh
        ans = {
            "NumVertices" : len(vertices),
            "Vertices" : self.make_nav_mesh_vertices(vertices),
            "NumTriangles" : len(triangles),
            "Triangles" : self.make_nav_mesh_triangles(triangles)
        }
        return ans
    
    # endregion
    
    # region Make - Animation
    
    def make_animation_frame(self, frame):
        time, pos, rot, scale = frame
        ans = {
            "time" : time,
            "pose" : {
                "translation" : {
                    "x" : pos[0],
                    "y" : pos[1],
                    "z" : pos[2]
                },
                "orientation" : {
                    "x" : rot[0],
                    "y" : rot[1],
                    "z" : rot[2],
                    "w" : rot[3]
                },
                "scale" : {
                    "x" : scale[0],
                    "y" : scale[1],
                    "z" : scale[2]
                }
            }
        }
        return ans
    
    def make_animation_frames(self, frames):
        ans = [self.make_animation_frame(frame) for frame in frames]
        return ans

    def make_animation_frame_empty(self):
        ans = {
            "time" : 0,
            "pose" : {
                "translation" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "orientation" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0,
                    "w" : 1
                },
                "scale" : {
                    "x" : 1,
                    "y" : 1,
                    "z" : 1
                }
            }
        }
        return ans
    
    def make_animated_model_mesh(self, name, vertices, indices, shared_resource_index, mesh_bone_index, interact_radius):
        ans = {
            "name" : name,
            "parentBone" : mesh_bone_index,
            "boundingSphere" : {
                "Center" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "Radius" : interact_radius,
            },
            "vertexBuffer" : self.make_vertex_buffer(vertices),
            "indexBuffer" : self.make_index_buffer(indices),
            "meshParts" : [ # Always hard code a single mesh part
                {
                    "streamOffset" : 0,
                    "baseVertex" : 0,
                    "numVertices" : len(vertices),
                    "startIndex" : 0,
                    "primitiveCount" : int(len(indices) // 3),
                    "vertexDeclarationIndex" : 0, # Hard coded to always use the only vertex declaration we have
                    "tag" : None, # Hard coded to never use a tag (always null)
                    "sharedResourceIndex" : shared_resource_index
                }
            ]
        }
        return ans
    
    def make_animated_model(self, root_name, root_matrix, root_radius, meshes):
        
        children_indices = list(range(1, len(meshes) + 1)) # the children of each root bone is always one child bone for each mesh attached to this animated level part. The indices start at 1, so we make a list with len(meshes) elements, starting at 1 and ending in len(meshes) + 1. The root bone itself has index 0.
        root_bone = self.make_bone(0, root_name, root_matrix, -1, children_indices)
        
        bone_list = []
        bone_list.append(root_bone)
        
        model_meshes = []
        
        for i in range(0, len(meshes)):
            current_mesh_index = i
            current_bone_index = i + 1 # Add 1 to idx to generate correct child bone idx (parent is 0 always)

            current_mesh = meshes[current_mesh_index]

            obj, transform, name, matrix, vertices, indices, idx = current_mesh
            
            # Create bone data
            bone = self.make_bone(current_bone_index, name, matrix, 0, [])
            bone_list.append(bone)
            
            # Create model mesh data
            model_mesh = self.make_animated_model_mesh(name, vertices, indices, idx, current_bone_index, root_radius)
            model_meshes.append(model_mesh)
        
        ans = {
            "tag" : None, # None is translated to null, and that is the value that all of the tags seem to have in the XNB files, so hopefully we won't find this to be problematic in the future... can't wait for it to come back to bite me in the ass!
            "numBones" : len(bone_list), # 1 bone for the root and 1 bone per mesh, which is what I've observed within the official XNB files... hopefully this is the right way...
            "bones" : bone_list,
            "numVertexDeclarations" : 1, # Hard code this to only use 1 vertex declaration, the one we provide always in this addon
            "vertexDeclarations" : [
                self.make_vertex_declaration_default() # again, hard code the default vertex declaration
            ],
            "numModelMeshes" : len(model_meshes),
            "modelMeshes" : model_meshes
        }
        
        return ans
    
    def make_bone(self, index, name, matrix, parent, children):
        ans = {
            "index" : index,
            "name" : name,
            "transform" : self.make_matrix(matrix),
            "parent" : parent,
            "children" : children
        }
        return ans
    
    def make_mesh_settings(self, meshes):
        ans = {}
        for mesh in meshes:
            name = mesh[2]
            key = True
            value = True
            ans[name] = {
                "Key" : key,
                "Value" : value
            }
        return ans
    
    def make_animation(self, animation_frames = []):
        ans = {
            "numFrames" : len(animation_frames),
            "frames" : self.make_animation_frames(animation_frames)
        }
        return ans
    
    def make_animation_empty(self):
        ans = {
            "numFrames" : 1,
            "frames" : [
                self.make_animation_frame_empty()
            ]
        }
        return ans
    
    # TODO : Deprecated, remove!!!
    def make_animated_level_part_old(self, animated_part):
        
        # Extract bone data from the animated level part's root bone
        bone_name, bone_transfrom = animated_part.bone

        # Extract data from animated level part
        bone, objects, children = animated_part
        object_data, bone_data = bone
        bname, world, local = object_data
        name, radius, affects_shields, collision_enabled, collision_material_index = bone_data
        meshes, lights, locators, triggers, particles, collisions, waters, lavas, nav_mesh = objects
        
        # Animated mesh model
        animated_model = self.make_animated_model(name, local, radius, meshes)
        mesh_settings = self.make_mesh_settings(meshes)
        
        # Animated Lights
        animated_lights = []
        for current_light in lights:
            light = self.make_light_animated(current_light)
            animated_lights.append(light)
        
        # Animated Locators
        animated_locators = []
        for l in locators:
            locator = self.make_locator(l)
            animated_locators.append(locator)
        
        # Animated Triggers
        animated_triggers = []
        for t in triggers:
            trigger = self.make_trigger(t)
            animated_triggers.append(trigger)
        
        # Animated Particles / Effects
        animated_effects = []
        for p in particles:
            effect = self.make_particle(p)
            animated_effects.append(effect)
        
        # Animated Liquids
        animated_liquids = []
        for w in waters:
            water = self.make_water(waters)
            animated_liquids.append(water)
        for l in lavas:
            lava = self.make_lava(lavas)
            animated_liquids.append(lava)
        
        # Animated Collisions
        col_vertices, col_indices = collisions
        animated_collision = self.make_collision_data(collision_enabled, col_vertices, col_indices)
        
        # Animated Nav Mesh
        animated_nav_mesh = self.make_nav_mesh(nav_mesh)
        has_nav_mesh = True if animated_nav_mesh["NumVertices"] > 0 else False
        
        # Animation Data
        animation_duration = 0
        animation = self.make_animation_empty()
        
        # Children Animated Level Parts
        children_animated_level_parts, children_lights = self.make_animated_scene(children)
        
        # Add the child animated level parts' lights to the list of lights that will be returned:
        lights += children_lights
        
        # The child light carry over step is so annoying to deal with... why did they decide to structure maps like this??
        # some kind of technical limitation that we don't know about yet ought to be the reason... otherwise, I just don't get it, lol...
        
        # Generate the answer JSON structured dictionary object:
        ans = {
            "name" : name,
            "affectsShields" : affects_shields,
            "model" : animated_model, # TODO : Modify this fn to just take as input the model data, and maybe we merge it in here or outside
            "numMeshSettings" : len(mesh_settings),
            "meshSettings" : mesh_settings, # TODO : Implement... need to loop over all meshes, with their names, and generate the data... need to use special function for that actually, because default mesh making fn does not save mesh object name, fuck...
            "numLiquids" : len(animated_liquids),
            "liquids" : animated_liquids,
            "numLocators" : len(animated_locators),
            "locators" : animated_locators,
            "animationDuration" : animation_duration,
            "animation" : animation, # self.make_animation(animation_frames),
            "numEffects" : len(animated_effects),
            "effects" : animated_effects,
            "numLights" : len(animated_lights),
            "lights" : animated_lights,
            "hasCollision" : collision_enabled,
            "collisionMaterial" : collision_material_index,
            "collisionVertices" : animated_collision["vertices"],
            "numCollisionTriangles" : animated_collision["numTriangles"],
            "collisionTriangles" : animated_collision["triangles"],
            "hasNavMesh" : has_nav_mesh,
            "navMesh" : animated_nav_mesh,
            "numChildren" : len(children),
            "children" : children_animated_level_parts # The children animated level parts are basically the same structure as the root level animated level parts, so we can reuse this kinda badly named function...
        }
        
        return (ans, lights) # Regular lights have to be returned so that they can be added to the base level structure... weird, but this is how Magicka's level format works.
    
    # TODO : Implement Fully!!!!
    # NOTE : Animated level parts cannot contain triggers!
    def make_animated_level_part(self, animated_part):
        
        # Extract Bone Data
        bone_name, bone_matrix, bone_settings = animated_part.bone
        radius, collision_enabled, collision_material_index, affects_shields = bone_settings

        # Animated Model
        animated_model = self.make_animated_model(bone_name, bone_matrix, radius, animated_part.meshes)

        # Mesh Settings
        mesh_settings = self.make_mesh_settings(animated_part.meshes)

        # Liquids
        animated_liquids = self.make_liquids(animated_part.waters, animated_part.lavas)

        # Locators
        animated_locators = self.make_locators(animated_part.locators)

        # Animation Data:
        animation_duration, animation_frames = animated_part.animation
        animation = self.make_animation(animation_frames)

        # Effects / Particles
        animated_effects = self.make_particles(animated_part.particles)

        # Lights
        animated_lights = self.make_light_references(animated_part.lights)

        # Collision
        if collision_enabled:
            animated_collision = self.make_collision(animated_part.collision)
        else:
            animated_collision = self.make_collision((False, [], []))

        # Nav Mesh
        animated_nav_mesh = self.make_nav_mesh(animated_part.nav_mesh)
        has_nav_mesh = len(animated_part.nav_mesh[0]) > 0

        # Child animated level parts
        children_animated_level_parts = self.make_animated_level_parts(animated_part.animated_parts)

        # Create JSON structure with a dictionary
        ans = {
            "name" : bone_name,
            "affectsShields" : affects_shields,
            "model" : animated_model,
            "numMeshSettings" : len(mesh_settings),
            "meshSettings" : mesh_settings,
            "numLiquids" : len(animated_liquids),
            "liquids" : animated_liquids,
            "numLocators" : len(animated_locators),
            "locators" : animated_locators,
            "animationDuration" : animation_duration,
            "animation" : animation,
            "numEffects" : len(animated_effects),
            "effects" : animated_effects,
            "numLights" : len(animated_lights),
            "lights" : animated_lights,
            "hasCollision" : collision_enabled,
            "collisionMaterial" : collision_material_index,
            "collisionVertices" : animated_collision["vertices"],
            "numCollisionTriangles" : animated_collision["numTriangles"],
            "collisionTriangles" : animated_collision["triangles"],
            "hasNavMesh" : has_nav_mesh,
            "navMesh" : animated_nav_mesh,
            "numChildren" : len(children_animated_level_parts),
            "children" : children_animated_level_parts
        }

        return ans

    def make_animated_level_parts(self, parts):
        ans = [self.make_animated_level_part(part) for part in parts]
        return ans

    # endregion

    # region Make - Deprecated Stuff!!!

    # TODO : Remove, this is deprecated!!!
    def make_static_scene(self, scene_data):
        in_meshes, in_lights, in_locators, in_triggers, in_particles, in_collisions, in_waters, in_lavas, in_navmesh = scene_data
        
        # Level Model Roots (Level Geometry / meshes)
        roots = []
        for mesh in in_meshes:
            root = self.make_root_node(mesh)
            roots.append(root)
        
        # Lights
        lights = []
        for light in in_lights:
            l = self.make_light(light)
            lights.append(l)
        
        # Locators
        locators = []
        for in_locator in in_locators:
            locator = self.make_locator(in_locator)
            locators.append(locator)
        
        # Triggers
        triggers = []
        for in_trigger in in_triggers:
            trigger = self.make_trigger(in_trigger)
            triggers.append(trigger)
        
        # Particle Effects
        particles = []
        for in_particle in in_particles:
            particle = self.make_particle(in_particle)
            particles.append(particle)
        
        # Collisions
        collisions = []
        for in_collision in in_collisions:
            collision_vertices, collision_triangles = in_collision
            collision = self.make_collision_data(True, collision_vertices, collision_triangles)
            collisions.append(collision)
        
        # Liquids
        liquids = [] # NOTE : The liquids list contains both water and lava
        for in_water in in_waters:
            water = self.make_water(in_water)
            liquids.append(water)
        for in_lava in in_lavas:
            lava = self.make_lava(in_lava)
            liquids.append(lava)
        
        # Navmesh
        navmesh = self.make_nav_mesh(in_navmesh)
        
        return (roots, lights, locators, triggers, particles, collisions, liquids, navmesh)
    
    # TODO : Remove, this is deprecated!!!
    def make_animated_scene(self, scene_data):
        # Animated Level Parts
        animated_parts = []
        animated_lights = []
        for in_part in scene_data:
            part, part_lights = self.make_animated_level_part(in_part)
            animated_parts.append(part)
            animated_lights += part_lights
        return (animated_parts, animated_lights)

    # endregion

    # region Make - Physics Entities

    def make_physics_entity(self, entity):
        template, matrix = entity
        ans = {
            "transform" : self.make_matrix(matrix),
            "template" : template
        }
        return ans

    def make_physics_entities(self, entities):
        ans = [self.make_physics_entity(entity) for entity in entities]
        return ans

    # endregion

    # region Make - Force Fields

    def make_force_field(self, force_field):
        vertices, indices, matname = force_field

        # NOTE : This is a "dummy" effect of sorts. Magicka does NOT use an effect class for this when reading force fields from the XNB file, which means that this information is embedded on the force field class
        # itself, but during object construction, under the hood, this data is used to generate an XNA effect. Kinda weird and inconsistent with the rest of the code, but yeah, makes sense from the point of view
        # that technically force fields can only support one single type of effect and they are only used in one place in the game anyway, so that could explain why they implemented it like that.
        # In short, we're piggybacking this onto the make_effect() function because it's gonna make things far easier to implement on the Blender side, but it's not necessarily semantically the best thing...
        temp_effect = self.make_effect(matname, "FORCE_FIELD")
        
        # NOTE : It probably would be more efficient to add the extra fields to the temp_effect dict rather than reading them from the temp_effect dict and assigning them to a new one because of the lookup time for a dict...
        ans = {
            "color" : temp_effect["color"],
            "width" : temp_effect["width"],
            "alphaPower": temp_effect["alphaPower"],
            "alphaFalloffPower" : temp_effect["alphaFalloffPower"],
            "maxRadius" : temp_effect["maxRadius"],
            "rippleDistortion" : temp_effect["rippleDistortion"],
            "mapDistortion" : temp_effect["mapDistortion"],
            "vertexColorEnabled": temp_effect["vertexColorEnabled"],
            "displacementMap": temp_effect["displacementMap"],
            "ttl": temp_effect["ttl"],
            "vertices" : self.make_vertex_buffer(vertices),
            "indices" : self.make_index_buffer(indices),
            "declaration" : self.make_vertex_declaration_default(),
            "vertexStride" : self.make_vertex_stride_default(),
            "numVertices" : len(vertices),
            "primitiveCount" : (len(indices) // 3)
        }
        return ans
    
    def make_force_fields(self, force_fields):
        ans = [self.make_force_field(force_field) for force_field in force_fields]
        return ans

    # endregion

    # region Make - Level Model
    
    def make_level_model(self, generated_scene_data):
        
        roots = self.make_root_nodes(generated_scene_data.meshes)
        liquids = self.make_liquids(generated_scene_data.waters, generated_scene_data.lavas)
        lights = self.make_lights(generated_scene_data.lights)
        locators = self.make_locators(generated_scene_data.locators)
        triggers = self.make_triggers(generated_scene_data.triggers)
        particles = self.make_particles(generated_scene_data.particles)
        collisions = self.make_collisions(generated_scene_data.collisions)
        camera_collisions = self.make_collision(generated_scene_data.camera_collision_mesh)
        nav_mesh = self.make_nav_mesh(generated_scene_data.nav_mesh)
        animated_parts = self.make_animated_level_parts(generated_scene_data.animated_parts)
        physics_entities = self.make_physics_entities(generated_scene_data.physics_entities)
        force_fields = self.make_force_fields(generated_scene_data.force_fields)

        ans = {
            "$type" : "level_model",
            "model" : {
                "NumRoots" : len(roots),
                "RootNodes" : roots,
            },
            "numAnimatedParts" : len(animated_parts),
            "animatedParts" : animated_parts,
            "numLights" : len(lights),
            "lights" : lights,
            "numEffects" : len(particles),
            "effects" : particles,
            "numPhysicsEntities" : len(physics_entities),
            "physicsEntities" : physics_entities,
            "numLiquids" : len(liquids),
            "liquids" : liquids,
            "numForceFields" : len(force_fields),
            "forceFields" : force_fields,
            "collisionDataLevel" : collisions,
            "collisionDataCamera" : camera_collisions,
            "numTriggers" : len(triggers),
            "triggers" : triggers,
            "numLocators" : len(locators),
            "locators" : locators,
            "navMesh" : nav_mesh
        }
        return ans

    # endregion

    # endregion

# Data Maker class for Physics entities
class MCow_Data_Maker_PhysicsEntity(MCow_Data_Maker):
    def __init__(self, cache):
        super().__init__(cache)
        return

    def make(self, generated_data):
        return self.make_xnb_file(self.make_physics_entity(generated_data), self.make_shared_resources_list(self.cache))

    def make_physics_entity(self, generated_data):
        # TODO : Implement all remaining data (events and advanced settings)
        # NOTE : Also need to polish the way that bounding boxes are obtained.
        # Figure out what those are exactly within Magicka. If they are what I think they are
        # (bbs like the visibility ones used for frustum culling in the level model side of things), then they could very easily be
        # automatically calculated rather than manually selected by the user... same thing applies to sphere collisions (radius) for bones and stuff like that...
        ans = {
            "$type" : "PhysicsEntity",
            "PhysicsEntityID" : generated_data.physics_entity_id,
            "IsMovable" : generated_data.is_movable,
            "IsPushable" : generated_data.is_pushable,
            "IsSolid" : generated_data.is_solid,
            "Mass" : generated_data.mass,
            "MaxHitPoints" : generated_data.max_hit_points,
            "CanHaveStatus" : generated_data.can_have_status,
            "Resistances" : self.make_resistances(generated_data.resistances),
            "Gibs" : self.make_gibs(generated_data.gibs),
            "GibTrailEffect" : generated_data.gib_trail_effect,
            "HitEffect" : generated_data.hit_effect,
            "VisualEffects" : generated_data.visual_effects,
            "SoundBanks" : generated_data.sound_banks,
            "Model" : self.make_model(generated_data.model),
            "HasCollision" : generated_data.has_collision,
            "CollisionVertices" : generated_data.collision_vertices,
            "CollisionTriangles" : generated_data.collision_triangles,
            "BoundingBoxes" : self.make_bounding_boxes(generated_data.bounding_boxes),
            "Events" : generated_data.events, # TODO : Implement make events method
            "HasAdvancedSettings" : generated_data.has_advanced_settings,
            "AdvancedSettings" : generated_data.advanced_settings # TODO : Implement make advanced settings method
        }
        return ans

    def make_bounding_boxes(self, boxes):
        ans = [self.make_bounding_box(box) for box in boxes]
        return ans
    
    def make_bounding_box(self, box):
        ans = {
            "ID" : box.id,
            "Position" : self.make_vector_3(box.position),
            "Scale" : self.make_vector_3(box.scale),
            "Rotation" : self.make_vector_4(box.rotation)
        }
        return ans

    def make_resistances(self, resistances):
        ans = [self.make_resistance(resistance) for resistance in resistances]
        return ans
    
    def make_resistance(self, resistance):
        ans = {
            "Elements" : resistance.element,
            "Multiplier" : resistance.multiplier,
            "Modifier" : resistance.modifier
        }
        return ans

    def make_gibs(self, gibs):
        ans = [self.make_gib(gib) for gib in gibs]
        return ans
    
    def make_gib(self, gib):
        ans = {
            "Model" : gib.model,
            "Mass" : gib.mass,
            "Scale" : gib.scale
        }
        return ans

    def make_model(self, model):
        meshes, bones = model
        ans = {
            "tag" : None, # Always null in Magicka...
            "numBones" : len(bones) + 2, # Add 2 bones because of Root and RootNode
            "bones" : self.make_model_bones(bones),
            "numVertexDeclarations" : 1,
            "vertexDeclarations" : [self.make_vertex_declaration_default()],
            "numModelMeshes" : len(meshes),
            "modelMeshes" : self.make_model_meshes(meshes)
        }
        return ans
    
    def make_model_bones(self, bones):
        ans_extra = self.make_model_bones_extra()
        ans_real = self.make_model_bones_real(bones)
        ans = []
        ans.extend(ans_extra)
        ans.extend(ans_real)
        return ans

    def make_model_bone(self, index, name, transform, parent, children):
        ans = {
            "index" : index,
            "name" : name,
            "transform" : transform,
            "parent" : parent,
            "children" : children
        }
        return ans

    def make_model_bones_real(self, bones):
        ans = [self.make_model_bone_real(bone) for bone in bones]
        return ans

    def make_model_bone_real(self, bone):
        return self.make_model_bone(bone.index + 2, bone.name, self.make_matrix(bone.transform), bone.parent + 2, bone.children) # Add 2 on bone.index and bone.parent because of Root and RootNode bones

    def make_model_bones_extra(self):
        transform = {
            "M11": 1,
            "M12": 0,
            "M13": 0,
            "M14": 0,
            "M21": 0,
            "M22": 1,
            "M23": 0,
            "M24": 0,
            "M31": 0,
            "M32": 0,
            "M33": 1,
            "M34": 0,
            "M41": 0,
            "M42": 0,
            "M43": 0,
            "M44": 1
        }
        ans = [
            self.make_model_bone(0, "Root", transform, -1, [1]),
            self.make_model_bone(1, "RootNode", transform, 0, [2]),
        ]
        return ans

    def make_model_meshes(self, meshes):
        ans = [self.make_model_mesh(mesh) for mesh in meshes]
        return ans
    
    def make_model_mesh(self, mesh):
        name, parent_bone_index, vertices, indices, shared_resource_index = mesh
        ans = {
            "name" : name,
            "parentBone" : parent_bone_index + 2, # Add 2 because of the Root and RootNode bones
            "boundingSphere" : { # TODO : Implement customizable bounding sphere for each mesh
                "Center" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "Radius" : 1.5
            },
            "vertexBuffer" : self.make_vertex_buffer(vertices),
            "indexBuffer" : self.make_index_buffer(indices),
            "meshParts" : [
                {
                    "streamOffset" : 0,
                    "baseVertex" : 0,
                    "numVertices" : len(vertices),
                    "startIndex" : 0,
                    "primitiveCount" : int(len(vertices) / 3),
                    "vertexDeclarationIndex" : 0,
                    "tag" : None, # Always null in Magicka...,
                    "sharedResourceIndex" : shared_resource_index
                }
            ]
        }
        return ans

# endregion

# ../mcow/functions/generation/export/Pipeline.py
# region Data Generation pipeline classes

# The classes within this region define the top level logic of the pipeline for data generation for MagickCow.
# The data generator classes within this region make use of the internal lower level Get Stage, Generate Stage and Make Stage classes.

# NOTE : When implementing a new MagickCow data pipeline class, the top level / main logic must be implemented within the process_scene_data() method.

# NOTE : As of now, part of the scene preprocessing (such as scene rotation) takes place in this step in between MCow_Data_Whatever processor classes.
# Those steps could maybe be moved into separate preprocessor classes?

# region Comment - Steps of the pipeline

# This section contains a comment that describes the steps of the data generation pipeline.
# Each of the stages should return the following type of objects:

# Get Stage:
# The Get Stage class for each data pipeline should return an object containing lists of tuples with all of the objects to export from the scene, as well as
# their transforms relative to their parent in Magicka's target tree-like data structure.

# Generate Stage:
# The Generate Stage class for each data pipeline should return a tuple with the generated objects and the generated dicts with shared resources
# as well as other cached data, such as the generated materials (effects) and such.

# Make Stage:
# The Make Stage class for each data pipeline should return a dict which will be finally serialized into a JSON string.
# This dict should describe in a MagickaPUP compatible JSON structure the generated object / scene data.

# endregion

class MCow_Data_Pipeline:
    
    # region Constructor
    
    def __init__(self):
        return

    # endregion
    
    # region Scene Processing

    # Main scene processing entry point method
    # This method returns the final dictionary obtained in the make stage.
    # The method handles the entire process of generating all of the data for the scene that is being exported.
    # Each class that inherits from this base class implements its own version of this method.
    def process_scene_data(self):
        # Throw an exception here to denote that the base class should never be instantiated and used.
        # Callers should use the derived classes instead, which actually implement specific pipelines for each type of exportable object.
        raise MagickCowExportException("Cannot execute base export pipeline!")
        return None
    
    # endregion

    # region Scene Rotation

    # region Deprecated

    # region Comment

    # Iterates over all of the root objects of the scene and rotates them by the input angle in degrees around the specified axis.
    # The rotation takes place around the world origin (0,0,0), so it would be equivalent to attaching all objects to a parent located in the world origin and then rotating said parent.
    # This way, there is no hierarchical requirements for scene export, since all root objects will be translated properly, and thus the child objects will also be automatically translated to the coorect coordinates.
    
    # endregion
    def rotate_scene_old_1(self, angle_degrees = 90, axis = "X"):
        root_objects = get_scene_root_objects()
        for obj in root_objects:
            obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees))
        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.
    
    def _rotate_objects_global(self, objects, angle_degrees, axis):
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(angle_degrees), 4, axis)
        for obj in objects:
            # obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees)) # idk why this doesn't work for all objects, I guess I'd know if only Blender's documentation had any information related to it. Oh well!
            obj.matrix_world = rotation_matrix @ obj.matrix_world

    # region Comment - rotate_objects_local_old_2

    # NOTE : For future reference, read this comment, very important, I had forgotten about how I had implemented this and just wasted like 40 mins trying to figure out where the Y up conversion was done for
    # locators...
    # basically, the trick is the following:
    # If you rotate in blender an object by -90d in the X axis to pass it to Y up, the rotation value stays wrong because now it is rotated by -90d around X.
    # To solve this, objects that require matrix data to be stored such as locators get their rotation undone... but if we undid the rotation through blender's rotations, we would go back to what we had before!
    # For example, imagine an object in Blender Z up with rot <0d, 0d, 45d>
    # If we rotate -90d around X, we end up with <-90d, 45d, 0d>
    # If we rotate +90d around X, we end up with <0d, 0d, 45d> again... so what's the solution?
    # The solution is what we do in this function... which is "faking" the "unrotation" process.
    # We manually add +90d to the X axis, which does not compute a real rotation as one would expect when using Blender rotation operations, but it does change the numeric value of the rotation, so the final
    # rotation will be <0d, 45d, 0d>, which is what we wanted!
    # This is such a fucking hack that I don't know how I had forgotten about this implementation detail... it is true that I've been many months away from the code, but Jesus fucking Christ, this is a really
    # important implementation detail to remember...

    # NOTE : Maybe I should apply this "unrotation" process to bones too? they work just fine with the "Z up" rotation value within their matrices tho, since all coordinates are relative, so whatever...
    # for now at least...

    # endregion
    def _rotate_objects_local(self, objects, angle_degrees, axis):
        axis_num = find_element_index(["X", "Y", "Z"], axis, 0)
        for obj in objects:
            obj.rotation_euler[axis_num] += math.radians(angle_degrees)

    # region Comment

    # NOTE : It also iterates over the locator objects and rotates them in the opposite direction.
    # This is because the rotation of the transform obtained after rotating the scene is only useful for objects where we need to translate other data, such as points and vectors (meshes, etc...)
    # In the case of locators, we directly use the transform matrix of the object itself, which means that the extra 90 degree rotation is going to change the orientation of the locators by 90 degrees.
    # This can be fixed by manually rotating the locators... or by having the rotate_scene() function do it for us, so the users will never know that it even happened! 
    # NOTE : Another fix would be to have a single world root object of sorts, and having to attach all objects to that root. That way, we would only have to rotate that one single root by 90 degrees and nothing else, no corrections required...
    # TODO : Basically make it so that we also have a root object in map scenes, just like we do in physics entity scenes...
    
    # endregion
    def _rotate_scene(self, angle_degrees = -90, axis = "X"):
        # Objects that are "roots" of the Blender scene
        root_objects = []

        # Point data objects that need to have their transform matrix corrected
        # region Comment
            # Objects that use their raw transform matrix as a way to represent their transform in game, such as locators.
            # They need to be corrected, since the transform matrix in Blender will contain the correct translation and scale, but will have a skewed rotation, because of the 90 degree rotation we use as
            # a hack to align the scene with the Y up coordinate system, so we need to correct it by undoing the 90 degree rotation locally around their origin point for every object of this type after
            # having performed the global 90 degree rotation around <0,0,0>
        # endregion
        objects_to_correct = []
        
        # All of the objects in the scene
        all_objects = get_all_objects()

        for obj in all_objects:
            if obj.parent is None:
                root_objects.append(obj)
            if obj.type == "EMPTY" and obj.magickcow_empty_type in ["LOCATOR", "PHYSICS_ENTITY"]:
                objects_to_correct.append(obj)

        self._rotate_objects_global(root_objects, angle_degrees, axis) # Rotate the entire scene
        self._rotate_objects_local(objects_to_correct, -1.0 * angle_degrees, axis) # The correction rotation goes in the opposite direction to the input rotation

        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.

    # endregion

    # region Experimental

    # region Comment
    
    # NOTE : First we rotate by -90º, then to unrotate we rotate by +90º, this way we can pass from Z up to to Y up coords
    # TODO : Once you implement the new scene root system for the map exporting side of the code, you will be capable of getting rid of the _aux suffix for this method's name.
    # Also, get rid of the rotate_scene() method within the map data generator class...
    # TODO : To be able to use this simpler root based rotation for map scenes, we need to find a way to translate rotations. We don't have to have the 90 degree rotation fix for empties anymore, sure, but
    # previously we did not apply any rotation fix to lights either... why? because lights with a rotation apply over a direction vector. What this means is that without the rotation fix, all of my final rotations
    # are Z up based, even tho my final points will be Y up based... or maybe I'm confused and this is actually wrong?
    # NOTE : Actually, now that I think about it, wouldn't we still have to undo rotations locally for point data whose location, rotation and scalre are exported with a matrix? If you think about it, lights are not affected despite being point data because their direction is exported as a director vector. I need to think about this shit tbh...
    
    # endregion
    def rotate_scene(self, angle_degrees, axis = "X"):
        roots = self.get_scene_roots()
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(angle_degrees), 4, axis)
        for root in roots: # We should only have 1 single root, which is validated on the exporter side, but we support multi-root scenes here to prevent getting funny results if we make any changes in the future...
            root.matrix_world = rotation_matrix @ root.matrix_world
        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.
    
    def get_scene_roots_map(self):
        roots = [obj for obj in bpy.data.objects if (obj.parent is None and obj.magickcow_empty_type == "ROOT")]
        return roots
    
    def get_scene_roots_physics_entity(self):
        roots = [obj for obj in bpy.data.objects if (obj.parent is None and obj.mcow_physics_entity_empty_type == "ROOT")]
        return roots

    def get_scene_roots(self):
        if bpy.context.scene.mcow_scene_mode == "MAP":
            return self.get_scene_roots_map()
        elif bpy.context.scene.mcow_scene_mode == "PHYSICS_ENTITY":
            return self.get_scene_roots_physics_entity()
        return [] # In the case where the selected mode is not any of the implemented ones, we then return an empty list.

    # region Comment

    # Aux functions to perform rotations without having to remember what values and axes are specifically required when exporting a scene to Magicka.
    # Makes it easier to go from Z up to Y up, progress the scene, and then go back from Y up to Z up.
    
    # endregion
    def do_scene_rotation(self):
        self.rotate_scene(-90, "X")
    
    def undo_scene_rotation(self):
        self.rotate_scene(90, "X")

    # endregion

    # endregion

class MCow_Data_Pipeline_Map(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        self._cache = MCow_Data_Pipeline_Cache()
        self._get = MCow_Data_Getter_Map()
        self._gen = MCow_Data_Generator_Map(self._cache)
        self._mkr = MCow_Data_Maker_Map(self._cache)
        return
    
    def process_scene_data(self):
        self._rotate_scene()
        data_get = self._get.get()
        data_gen = self._gen.generate(data_get)
        data_mkr = self._mkr.make(data_gen)
        return data_mkr

class MCow_Data_Pipeline_PhysicsEntity(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        self._cache = MCow_Data_Pipeline_Cache()
        self._get = MCow_Data_Getter_PhysicsEntity()
        self._gen = MCow_Data_Generator_PhysicsEntity(self._cache)
        self._mkr = MCow_Data_Maker_PhysicsEntity(self._cache)
        return
    
    def process_scene_data(self):
        self._rotate_scene()
        data_get = self._get.get()
        data_gen = self._gen.generate(data_get)
        data_mkr = self._mkr.make(data_gen)
        return data_mkr

# endregion

# ../mcow/functions/generation/export/PipelineCache.py
# region Pipeline Cache Classes

# The classes within this region correspond to cache dicts and other cache objects that must be shared across different steps of the pipeline.

# TODO : Implement logic for adding and getting shared resources and effects
# TODO : Add the remaining functions LOL (eg: the ones used within the _create_default_values_effects() method)
class MCow_Data_Pipeline_Cache:
    
    # region Constructor
    
    def __init__(self):
        self._cache_shared_resources = {} # Cache Dictionary for Shared Resources generated
        self._cache_generated_effects = {} # Cache Dictionary for Material Effects generated

    # endregion

    # region Private Methods

    def _create_default_values(self):
        self._create_default_values_effects() # Initialize the values for the Material Effects cache with default values
    
    def _create_default_values_effects(self, effect_types = ["GEOMETRY", "WATER", "LAVA"]):
        # region Comment

        # Cached Effects Initialization
        # Setup all default material data beforehand (not required as the process would still work even if this was not done, but whatever... basically this works as a sort of precaching, but since it is
        # not compiletime because this is not C, there really is not much point ot it, altough maybe making the dict with self.dict_effects = {"base/whatever" : {blah blah blah...}, ...} could actually
        # be faster in future versions of Python, idk)

        # endregion
        for effect_type in effect_types:
            self._cache_generated_effects[self._create_default_effect_name(effect_type)] = self._create_default_effect_data(current_type)
    
    # endregion

    # region Public Methods - Shared Resources

    def add_shared_resource(self, resource_name, resource_content):
        if resource_name not in self._cache_shared_resources:
            num_resources = len(self._cache_shared_resources)
            resource_index = num_resources + 1 # Use the current count of resources as the index of each element (note that indices for shared resources in XNB files start at 1, not 0)
            self._cache_shared_resources[resource_name] = (resource_index, resource_content) # Store the resource index and its contents
            return resource_index
        else: # If the resource was already within the list, we don't add it again, we just return the index
            idx, content = self.dict_shared_resources[resource_name]
            return idx

    def get_shared_resource(self, resource_name):
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return (idx, content)
        return (0, None) # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    def get_shared_resource_index(self, resource_name):
        # NOTE : Same as the get function, but instead of returning the content, we only return the index.
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return idx
        return 0 # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.
    
    # endregion

    # region Public Methods - Material Effects

    # region Comment - get_material_path
    # Returns the full path for a given material file. It does not check in the file system, all it does is append the selected path for material files to the given blender material name.
    # Automatically appends the ".json" extension if the material name does not end in ".json" to ensure that the correct file name is generated.
    # All validity checkign is performed later, when the actual contents of the file are retrieved, where the system checks for whether this file exists or not.
    # endregion
    def get_material_path(self, matname):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, matname)
        if ans.endswith(".json"):
            return ans
        return ans + ".json"

    # region Comment - get_material_name
    # Gets the full material name used on a mesh. This full name corresponds to the full path + filename of the JSON file that corresponds to the effect represented by the material's name.
    # If the mesh does not have a material assigned, it uses as material name the name "base/default"
    # endregion
    # TODO : Get rid of this function maybe? and all of the whole material path bullshit, since we no longer use the material name as the path to the actual asset...
    def get_material_name(self, obj, material_index = 0):
        # Get mesh
        mesh = obj.data
        
        # Get material name
        matname = mesh.materials[material_index].name if len(mesh.materials) > 0 else self.generate_default_effect_name(mesh.magickcow_mesh_type)
        matname = self.get_material_path(matname)
        
        return matname
    
    # region Generate Material / Effect Data Functions
    
    # These are literally bordering the edge between the "make" and "generate" stages, since it returns a JSON-like dict object...
    # They used to be part of the make stage, so all file reading was done there and data generation was uninterrupted, but the shared_object stuff is now done in the generate stage so we have to move this somewhere...
    
    # TODO : Implement something similar to what the following comment says...
    # The good thing about putting it in this stage is that at least it is easier to make this generation dependant on the default collision channel or something fancy like that, so it becomes easier to
    # quickly debug a map without having it all look like stone...

    def generate_default_effect_name(self, fallback_type = "GEOMETRY"):
        ans = "base/default"

        if fallback_type == "GEOMETRY":
            ans = "base/default_geometry"
        elif fallback_type == "WATER":
            ans = "base/default_water"
        elif fallback_type == "LAVA":
            ans = "base/default_lava"
        elif fallback_type == "FORCE_FIELD":
            ans = "base/ff/default_force_field"

        return ans

    def generate_default_effect_data(self, fallback_type = "GEOMETRY"):
        # Default effect (for now it is the same as the one found within the "GEOMETRY" case)
        ans = {
            "$type": "effect_deferred",
            "Alpha": 0.400000006,
            "Sharpness": 1,
            "VertexColorEnabled": False,
            "UseMaterialTextureForReflectiveness": False,
            "ReflectionMap": "",
            "DiffuseTexture0AlphaDisabled": True,
            "AlphaMask0Enabled": False,
            "DiffuseColor0": {
                "x": 1,
                "y": 1,
                "z": 1
            },
            "SpecAmount0": 0,
            "SpecPower0": 20,
            "EmissiveAmount0": 0,
            "NormalPower0": 1,
            "Reflectiveness0": 0,
            "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
            "MaterialTexture0": "",
            "NormalTexture0": "",
            "HasSecondSet": False,
            "DiffuseTexture1AlphaDisabled": False,
            "AlphaMask1Enabled": False,
            "DiffuseColor1": None,
            "SpecAmount1": 0,
            "SpecPower1": 0,
            "EmissiveAmount1": 0,
            "NormalPower1": 0,
            "Reflectiveness1": 0,
            "DiffuseTexture1": None,
            "MaterialTexture1": None,
            "NormalTexture1": None
        }
        if fallback_type == "GEOMETRY":
            ans = {
                "$type": "effect_deferred",
                "Alpha": 0.400000006,
                "Sharpness": 1,
                "VertexColorEnabled": False,
                "UseMaterialTextureForReflectiveness": False,
                "ReflectionMap": "",
                "DiffuseTexture0AlphaDisabled": True,
                "AlphaMask0Enabled": False,
                "DiffuseColor0": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "SpecAmount0": 0,
                "SpecPower0": 20,
                "EmissiveAmount0": 0,
                "NormalPower0": 1,
                "Reflectiveness0": 0,
                "DiffuseTexture0": "..\\Textures\\Surface\\Nature\\Ground\\grass_lush00_0",
                "MaterialTexture0": "",
                "NormalTexture0": "",
                "HasSecondSet": False,
                "DiffuseTexture1AlphaDisabled": False,
                "AlphaMask1Enabled": False,
                "DiffuseColor1": None,
                "SpecAmount1": 0,
                "SpecPower1": 0,
                "EmissiveAmount1": 0,
                "NormalPower1": 0,
                "Reflectiveness1": 0,
                "DiffuseTexture1": None,
                "MaterialTexture1": None,
                "NormalTexture1": None
            }
        elif fallback_type == "WATER":
            ans = {
                "$type": "effect_deferred_liquid",
                "ReflectionMap": "",
                "WaveHeight": 1,
                "WaveSpeed0": {
                    "x": 0.00930232555,
                    "y": 0.0900000036
                },
                "WaveSpeed1": {
                    "x": -0.0046511637,
                    "y": 0.0883720964
                },
                "WaterReflectiveness": 0.216049388,
                "BottomColor": {
                    "x": 0.400000006,
                    "y": 0.400000006,
                    "z": 0.600000024
                },
                "DeepBottomColor": {
                    "x": 0.300000012,
                    "y": 0.400000006,
                    "z": 0.5
                },
                "WaterEmissiveAmount": 0.806896567,
                "WaterSpecAmount": 0.300000012,
                "WaterSpecPower": 24,
                "BottomTexture": "..\\Textures\\Surface\\Nature\\Ground\\rock_0",
                "WaterNormalMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "IceReflectiveness": 0,
                "IceColor": {
                    "x": 1,
                    "y": 1,
                    "z": 1
                },
                "IceEmissiveAmount": 0,
                "IceSpecAmount": 1,
                "IceSpecPower": 20,
                "IceDiffuseMap": "..\\Textures\\Surface\\Nature\\Ground\\ice02_0",
                "IceNormalMap": "..\\Textures\\Liquids\\IceNrm_0"
            }
        elif fallback_type == "LAVA":
            ans = {
                "$type" : "effect_lava",
                "MaskDistortion" : 0.2,
                "Speed0" : {
                    "x" : 0.5,
                    "y" : 0.5
                },
                "Speed1" : {
                    "x" : 0.03,
                    "y" : 0.03
                },
                "LavaHotEmissiveAmount" : 3.0,
                "LavaColdEmissiveAmount" : 0.0,
                "LavaSpecAmount" : 0.0,
                "LavaSpecPower" : 20.0,
                "TempFrequency" : 0.5586,
                "ToneMap" : "..\\Textures\\Liquids\\LavaToneMap_0",
                "TempMap" : "..\\Textures\\Liquids\\LavaBump_0",
                "MaskMap" : "..\\Textures\\Liquids\\lavaMask_0",
                "RockColor" : {
                    "x" : 1,
                    "y" : 1,
                    "z" : 1
                },
                "RockEmissiveAmount" : 0.0,
                "RockSpecAmount" : 0.0,
                "RockSpecPower" : 20.0,
                "RockNormalPower" : 1.0,
                "RockTexture" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_0",
                "RockNormalMap" : "..\\Textures\\Surface\\Nature\\Ground\\lavarock00_NRM_0"
            }
        elif fallback_type == "FORCE_FIELD":
            ans = {
                "color" : {
                    "x" : 0,
                    "y" : 0,
                    "z" : 0
                },
                "width" : 0.5,
                "alphaPower": 4,
                "alphaFalloffPower" : 2,
                "maxRadius" : 4,
                "rippleDistortion" : 2,
                "mapDistortion" : 0.53103447,
                "vertexColorEnabled": False,
                "displacementMap": "..\\Textures\\Liquids\\WaterNormals_0",
                "ttl": 1
            }
        return ans
    
    def generate_effect_data(self, mat_file_name, fallback_type = "GEOMETRY"):
        ans = get_json_object(mat_file_name)
        if len(ans) > 0:
            return ans
        return self.generate_default_effect_data(fallback_type)

    # endregion

    # NOTE : Maybe this one should be deprecated.
    # region Comment - create_material()
    # Creates material data.
    # If the material is created for the first time, it is loaded from the JSON file containing its data, and the result is cached for future uses.
    # If the material had already been created before, it uses the previously cached result to prevent having to load the file multiple times.
    # This way, multiple disk accesses are prevented when loading the same material / effect multiple times.
    # endregion
    def create_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name not in self._cache_generated_effects:
            self._cache_generated_effects[material_name] = self.generate_effect_data(material_name, fallback_type)

    # region Comment - add_material()
    
    # Adds material data.
    # If the material is created for the first time, it is loaded from either the JSON file containing its data, or the blender material panel config.
    # The result is cached for future uses under the name of this material.
    # If the material has alredy been created previously, then it uses the previously cached result to prevent having to load the file multiple times.
    # This prevents performing multiple disk accesses when loading the same material effect multiple times if the material type is set to read from a JSON document.

    # Input: blender_object, material_index
    # Output: generated_material_name

    # endregion
    def add_material(self, obj, material_index):
        material_name = material_utility.get_material_name_from_mesh(obj, material_index)
        if material_name not in self._cache_generated_effects:
            self._cache_generated_effects[material_name] = material_utility.get_material_data_from_mesh(obj, material_index)
        return material_name

    # region Comment - get_material()
    # Gets the material from the materials dictionary. Used in the make stage.
    # If for some reason the material were to not have been created previously (could only happen if there were some bug in the code that would need to be fixed ASAP),
    # then it would just re-generate the default effect data based on the fallback type. That feature exists as a last measure and we should not rely on it to export working files!!! 
    # endregion
    def get_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name in self._cache_generated_effects:
            return self._cache_generated_effects[material_name]
        return self.generate_default_effect_data(fallback_type)

    # endregion


# endregion

# ../mcow/functions/generation/import/Pipeline.py
# region Import Data Pipeline class - Base class

class MCow_ImportPipeline:
    def __init__(self):
        return
    
    def exec(self, data):
        # The base class should never be used because it does not implement any specific type of pipeline for any kind of object, so it literally cannot import any sort of data...
        raise MagickCowImportException("Cannot execute base import pipeline!")
        return None
    
    # region Read Methods - Raw

    def read_vec2_raw(self, vec2):
        ans = (vec2["x"], vec2["y"])
        return ans

    def read_vec3_raw(self, vec3):
        ans = (vec3["x"], vec3["y"], vec3["z"])
        return ans
    
    def read_vec4_raw(self, vec4):
        ans = (vec4["x"], vec4["y"], vec4["z"], vec4["w"])
        return ans
    
    # Read a 4 by 4 matrix as a linear buffer
    def read_mat4x4_buf_raw(self, mat4x4):
        m11 = mat4x4["M11"]
        m12 = mat4x4["M12"]
        m13 = mat4x4["M13"]
        m14 = mat4x4["M14"]
        m21 = mat4x4["M21"]
        m22 = mat4x4["M22"]
        m23 = mat4x4["M23"]
        m24 = mat4x4["M24"]
        m31 = mat4x4["M31"]
        m32 = mat4x4["M32"]
        m33 = mat4x4["M33"]
        m34 = mat4x4["M34"]
        m41 = mat4x4["M41"]
        m42 = mat4x4["M42"]
        m43 = mat4x4["M43"]
        m44 = mat4x4["M44"]

        mat = [m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34, m41, m42, m43, m44]

        return mat

    # Read a 4 by 4 matrix as a matrix (list of lists)
    def read_mat4x4_mat_raw(self, mat4x4):
        m11 = mat4x4["M11"]
        m12 = mat4x4["M12"]
        m13 = mat4x4["M13"]
        m14 = mat4x4["M14"]
        m21 = mat4x4["M21"]
        m22 = mat4x4["M22"]
        m23 = mat4x4["M23"]
        m24 = mat4x4["M24"]
        m31 = mat4x4["M31"]
        m32 = mat4x4["M32"]
        m33 = mat4x4["M33"]
        m34 = mat4x4["M34"]
        m41 = mat4x4["M41"]
        m42 = mat4x4["M42"]
        m43 = mat4x4["M43"]
        m44 = mat4x4["M44"]

        mat = [
            [m11, m12, m13, m14],
            [m21, m22, m23, m24],
            [m31, m32, m33, m34],
            [m41, m42, m43, m44]
        ]

        return mat

    # endregion

    # region Read Methods - Transform Y up to Z up
    
    def read_point(self, point):
        point_data = (point["x"], point["y"], point["z"])
        ans = point_to_z_up(point_data)
        return ans

    def read_quat(self, q):
        quat_data = (q["x"], q["y"], q["z"], q["w"])
        ans = quat_to_z_up(quat_data)
        return ans

    def read_scale(self, scale):
        scale_data = (scale["x"], scale["y"], scale["z"])
        ans = scale_to_z_up(scale_data)
        return ans

    def read_mat4x4(self, mat4x4):
        mat = mathutils.Matrix(mat4x4_buf2mat_rm2cm_yu2zu(self.read_mat4x4_buf_raw(mat4x4)))
        return mat

    # endregion

    # region Read Methods - Other

    def read_color_rgb(self, color):
        return mathutils.Vector((color["x"], color["y"], color["z"]))

    # endregion

    # region Read Methods - Vertex Buffer, Index Buffer, Vertex Declaration
    
    # TODO : Fix the fact that the imported mesh has inverted normals!
    # Can probably be fixed either by changing the winding order or adding normal data parsing.
    def read_mesh_buffer_data(self, vertex_stride, vertex_declaration, vertex_buffer, index_buffer):

        vertex_buffer_internal = vertex_buffer["Buffer"]
        index_buffer_internal = index_buffer["data"]

        # Output variables
        # This function will generate a vertex buffer and an index buffer in a pydata format that Blender can understand through its Python API to generate a new mesh data block.
        vertices = []
        indices = [index_buffer_internal[i:i+3] for i in range(0, len(index_buffer_internal), 3)] # This one is actually pretty fucking trivial, because it is already in a format that is 1:1 for what we require lol... all we have to do, is split the buffer into a list of sublists, where every sublist contains 3 elements, which are the indices of each triangle. Whether the input XNA index buffer has an index size that is 16 bit or 32 bit does not matter, since the numbers on the JSON text documented are already translated to whatever the width of Python's integers is anyway, so no need to handle that.

        # Vertex Attribute Offsets
        # NOTE : If any of these offset values is negative, then that means that the value was not found on the vertex declaration, so we cannot add that information to our newly generated Blender mesh data.
        vertex_offset_position = -1
        vertex_offset_normal = -1
        vertex_offset_tangent = -1
        vertex_offset_color = -1
        vertex_offset_uv = -1

        # Parse the vertex declarations to find the offsets for each of the vertex attributes
        vertex_declaration_entries = vertex_declaration["entries"]
        for idx, entry in enumerate(vertex_declaration_entries):
            # NOTE : Commented out lines are data from the entry that we do not need to compose a mesh in Blender / that we do not use yet.
            # stream = entry["stream"]
            offset = entry["offset"]
            element_format = entry["elementFormat"]
            # element_method = entry["elementMethod"]
            element_usage = entry["elementUsage"]
            # usage_index = entry["usageIndex"]
            
            # Read Attribute Offsets and handle Attribute Formats:
            # Position
            if element_usage == 0:
                vertex_offset_position = offset
                if element_format != 2:
                    raise MagickCowImportException(f"Element Format {element_format} is not supported for vertex position!")
            # Normal
            elif element_usage == 3:
                vertex_offset_normal = offset
                if element_format != 2:
                    raise MagickCowImportException(f"Element Format {element_format} is not supported for vertex normal!")
            # UV
            elif element_usage == 5:
                vertex_offset_uv = offset
                if element_format != 1:
                    raise MagickCowImportException(f"Element Format {element_format} is not supported for vertex UV!")
            # Tangent
            elif element_usage == 6:
                vertex_offset_tangent = offset
                if element_format != 2:
                    raise MagickCowImportException(f"Element Format {element_format} is not supported for vertex tangent!")
            # Color
            elif element_usage == 10:
                vertex_offset_color = offset
                if element_format == 0:
                    pass
                elif element_format == 3:
                    pass
                elif element_format == 4:
                    pass
                else:
                    raise MagickCowImportException(f"Element Format {element_format} is not supported for vertex color!")

            # NOTE : Supported Types / Element Formats:
            # Only the vec2, vec3 and vec4 types / formats are supported for reading as of now, as those are the types that I have found up until now that are used by Magicka's files.
            # Any other type will receive support for import in the future.

            # NOTE : Supported Attributes / Element Usages:
            # Only the position, normal, UV (TextureCoordinate), tangent and color properties are supported.
            # Anything else is considered to be irrelevant as of now for importing Magicka meshes into a Blender scene, but support will come if said features are found to be useful.

        # Read Vertex data into a byte array / buffer so that we can use Python's struct.unpack() to perform type-punning-like byte reinterpretations (this would be so much fucking easier in C tho! fuck my life...)
        buffer = bytes(vertex_buffer_internal)

        # If the input vertex data has a position attribute for each vertex, then read it.
        if vertex_offset_position >= 0:
            for offset in range(0, len(vertex_buffer_internal), vertex_stride):
                chunk = buffer[(offset + vertex_offset_position) : (offset + 12)] # The 12 comes from 3 * 4 = 12 bytes, because we read 3 floats for the vertex position.
                data = struct.unpack("<fff", chunk) # NOTE : As of now, we're always assuming that vertex position is in the format vec3. In the future, when we add support for other formats (if required), then make it so that we have a vertex_attribute_fmt variable or whatever, and assign it above, when we read the attributes' description / vertex layout on the vertex declaration parsing part of the code.
                vertices.append(point_to_z_up(data))

        return vertices, indices

    # endregion

    # region Read Methods - Collision Mesh

    def read_collision_mesh(self, has_collision, json_vertices, json_triangles):
        
        if not has_collision:
            return (False, [], [])

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["index0"], tri["index1"], tri["index2"]) for tri in json_triangles]

        return (True, mesh_vertices, mesh_triangles)

    # endregion

    # region Read Methods - Materials

    def read_effect(self, name, effect):
        mat = bpy.data.materials.new(name = name)
        mat.use_nodes = True

        if "$type" in effect:
            effect_type_json = effect["$type"]
            if effect_type_json == "effect_deferred":
                effect_type = "EFFECT_DEFERRED"
                effect_reader = self.read_effect_deferred
            
            elif effect_type_json == "effect_deferred_liquid":
                effect_type = "EFFECT_LIQUID_WATER"
                effect_reader = self.read_effect_liquid_water
            
            elif effect_type_json == "effect_lava":
                effect_type = "EFFECT_LIQUID_LAVA"
                effect_reader = self.read_effect_liquid_lava
            
            elif effect_type_json == "effect_additive":
                effect_type = "EFFECT_ADDITIVE"
                effect_reader = self.read_effect_additive
            
            else:
                raise MagickCowImportException(f"Unknown material effect type : \"{effect_type_json}\"")
        
        elif "vertices" in effect and "indices" in effect and "declaration" in effect:
            effect_type = "EFFECT_FORCE_FIELD"
            effect_reader = self.read_effect_force_field
        
        else:
            raise MagickCowImportException("The input data does not contain a valid material effect")

        mat.mcow_effect_type = effect_type
        effect_reader(mat, effect)

        return mat

    def read_effect_deferred(self, material, effect):
        material.mcow_effect_deferred_alpha = effect["Alpha"]
        material.mcow_effect_deferred_sharpness = effect["Sharpness"]
        material.mcow_effect_deferred_vertex_color_enabled = effect["VertexColorEnabled"]

        material.mcow_effect_deferred_reflection_map_enabled = effect["UseMaterialTextureForReflectiveness"]
        material.mcow_effect_deferred_reflection_map = effect["ReflectionMap"]

        material.mcow_effect_deferred_diffuse_texture_0_alpha_disabled = effect["DiffuseTexture0AlphaDisabled"]
        material.mcow_effect_deferred_alpha_mask_0_enabled = effect["AlphaMask0Enabled"]
        material.mcow_effect_deferred_diffuse_color_0 = self.read_color_rgb(effect["DiffuseColor0"])
        material.mcow_effect_deferred_specular_amount_0 = effect["SpecAmount0"]
        material.mcow_effect_deferred_specular_power_0 = effect["SpecPower0"]
        material.mcow_effect_deferred_emissive_amount_0 = effect["EmissiveAmount0"]
        material.mcow_effect_deferred_normal_power_0 = effect["NormalPower0"]
        material.mcow_effect_deferred_reflection_intensity_0 = effect["Reflectiveness0"]
        material.mcow_effect_deferred_diffuse_texture_0 = effect["DiffuseTexture0"]
        material.mcow_effect_deferred_material_texture_0 = effect["MaterialTexture0"]
        material.mcow_effect_deferred_normal_texture_0 = effect["NormalTexture0"]

        material.mcow_effect_deferred_has_second_set = effect["HasSecondSet"] # NOTE : This is done since on the C# side, our strings and vecs are still nullable, so this can fail even on valid effect json data... it would be ideal if we made it non nullable, obviously, but that's yet to come. As of now, this is the way that things work, for now, will be fixed in the future.
        if material.mcow_effect_deferred_has_second_set:
            material.mcow_effect_deferred_diffuse_texture_1_alpha_disabled = effect["DiffuseTexture1AlphaDisabled"]
            material.mcow_effect_deferred_alpha_mask_1_enabled = effect["AlphaMask1Enabled"]
            material.mcow_effect_deferred_diffuse_color_1 = self.read_color_rgb(effect["DiffuseColor1"])
            material.mcow_effect_deferred_specular_amount_1 = effect["SpecAmount1"]
            material.mcow_effect_deferred_specular_power_1 = effect["SpecPower1"]
            material.mcow_effect_deferred_emissive_amount_1 = effect["EmissiveAmount1"]
            material.mcow_effect_deferred_normal_power_1 = effect["NormalPower1"]
            material.mcow_effect_deferred_reflection_intensity_1 = effect["Reflectiveness1"]
            material.mcow_effect_deferred_diffuse_texture_1 = effect["DiffuseTexture1"]
            material.mcow_effect_deferred_material_texture_1 = effect["MaterialTexture1"]
            material.mcow_effect_deferred_normal_texture_1 = effect["NormalTexture1"]

    def read_effect_liquid_water(self, material, effect):
        pass
    
    def read_effect_liquid_lava(self, material, effect):
        pass
    
    def read_effect_force_field(self, material, effect):
        material.mcow_effect_force_field_color = self.read_color_rgb(effect["color"])
        material.mcow_effect_force_field_width = effect["width"]
        material.mcow_effect_force_field_alpha_power = effect["alphaPower"]
        material.mcow_effect_force_field_alpha_fallof_power = effect["alphaFalloffPower"]
        material.mcow_effect_force_field_max_radius = effect["maxRadius"]
        material.mcow_effect_force_field_ripple_distortion = effect["rippleDistortion"]
        material.mcow_effect_force_field_map_distortion = effect["mapDistortion"]
        material.mcow_effect_force_field_vertex_color_enabled = effect["vertexColorEnabled"]
        material.mcow_effect_force_field_displacement_map = effect["displacementMap"]
        material.mcow_effect_force_field_ttl = effect["ttl"]

    def read_effect_additive(self, material, effect):
        material.mcow_effect_additive_color_tint = self.read_color_rgb(effect["colorTint"])
        material.mcow_effect_additive_vertex_color_enabled = effect["vertexColorEnabled"]
        material.mcow_effect_additive_texture_enabled = effect["textureEnabled"]
        if material.mcow_effect_additive_texture_enabled: # NOTE : Same note as the deferred material reading code.
            material.mcow_effect_additive_texture = effect["texture"]

    # endregion

# endregion

# ../mcow/functions/generation/import/derived/Map.py
# region Import Data Pipeline class - LevelModel / Map

# TODO : Solve the vertex winding issues on all of the mesh imports... except collisions, which actually have the correct winding as of now.

# TODO : Implement all import functions...
class MCow_ImportPipeline_Map(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        self._cached_lights = {} # Cache object that stores the lights that have been generated so that they can be referenced on the animated level parts import side of the code. Remember that in Magicka's file format, lights are stored on the static level data, but the animated level data can move lights by referencing them through their ID.
        return
    
    def exec(self, data):
        level_model = data["XnbFileData"]["PrimaryObject"]
        self.import_level_model(level_model)
    
    def import_level_model(self, level_model):
        # Get the data entries from the level model JSON dict object.
        level_model_mesh = level_model["model"]
        animated_parts = level_model["animatedParts"]
        lights = level_model["lights"]
        effects = level_model["effects"]
        physics_entities = level_model["physicsEntities"]
        liquids = level_model["liquids"]
        force_fields = level_model["forceFields"]
        model_collision = level_model["collisionDataLevel"]
        camera_collision = level_model["collisionDataCamera"]
        triggers = level_model["triggers"]
        locators = level_model["locators"]
        nav_mesh = level_model["navMesh"]
        
        # Import level lights and cache them so that they can be referenced and parented when importing the animated level data.
        lights_objs = self.import_lights(lights)
        for light_obj in lights_objs:
            self._cached_lights[light_obj.name] = light_obj

        # Execute the import functions for each of the types of data found within the level model JSON dict.
        self.import_level_model_mesh(level_model_mesh)
        self.import_animated_parts(animated_parts)
        # NOTE : We used to import the lights here before, just as they were ordered within the JSON file, but the truth is that Magicka's file format for maps requires referencing lights
        # When importing the animated level parts, so we import the lights first and then everything else.
        self.import_effects(effects)
        self.import_physics_entities(physics_entities)
        self.import_liquids(liquids)
        self.import_force_fields(force_fields)
        self.import_model_collision(model_collision)
        self.import_camera_collision(camera_collision)
        self.import_triggers(triggers)
        self.import_locators(locators)
        self.import_nav_mesh(nav_mesh)

    # region Import Methods - Top Level

    def import_level_model_mesh(self, model):
        root_nodes = model["RootNodes"]
        for idx, root_node in enumerate(root_nodes):
            self.import_root_node(idx, root_node)
    
    def import_animated_parts(self, animated_parts):
        for part in animated_parts:
            self.import_animated_part(part, None)
    
    def import_lights(self, lights):
        ans = [self.import_light(light) for light in lights]
        return ans
    
    def import_effects(self, effects):
        ans = [self.import_effect(effect) for effect in effects]
        return ans
    
    def import_physics_entities(self, physics_entities):
        for idx, physics_entity in enumerate(physics_entities):
            self.import_physics_entity(idx, physics_entity)
    
    def import_liquids(self, liquids):
        ans = [self.import_liquid(idx, liquid) for idx, liquid in enumerate(liquids)]
        return ans
    
    def import_force_fields(self, force_fields):
        for idx, force_field in enumerate(force_fields):
            self.import_force_field(idx, force_field)
    
    def import_model_collision(self, collision_data):
        for idx, collision_channel in enumerate(collision_data):
            self.import_collision_mesh_level(collision_channel, idx)
    
    def import_camera_collision(self, collision_data):
        self.import_collision_mesh_camera(collision_data)
    
    def import_triggers(self, triggers):
        for trigger in triggers:
            self.import_trigger(trigger)
    
    def import_locators(self, locators):
        ans = [self.import_locator(locator) for locator in locators]
        return ans
    
    def import_nav_mesh(self, nav_mesh):
        # NOTE : The generated nav mesh has inverted normals, and I have no idea as of now if that has any negative impact on the AI's behaviour.
        # So for now, this is ok I suppose, since I have not seen anything within Magicka's code that would point to the face orientation of the nav mesh
        # being taken into account... so this should be ok, but it would be ideal to solve this issue so that people who import maps don't have to deal with the ugly
        # inverted normals, or maybe it's ok, idk.
        name = "nav_mesh_static"

        json_vertices = nav_mesh["Vertices"]
        json_triangles = nav_mesh["Triangles"]

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["VertexA"], tri["VertexB"], tri["VertexC"]) for tri in json_triangles]

        mesh = bpy.data.meshes.new(name = name)
        obj = bpy.data.objects.new(name = name, object_data = mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        mesh.magickcow_mesh_type = "NAV"
    
    # endregion

    # region Import Methods - Internal

    def import_light(self, light):
        # Read the light data
        name = light["LightName"]
        position = self.read_point(light["Position"])
        direction = self.read_point(light["Direction"]) # We use the read_point function, but that's because the translation for any spatial 3D vector, both those that represent points and directions, is the same when transforming from Z-up to Y-up and viceversa.
        light_type = find_light_type_name(light["LightType"])
        variation_type = find_light_variation_type_name(light["LightVariationType"])
        reach = light["Reach"]
        use_attenuation = light["UseAttenuation"]
        cutoff_angle = light["CutoffAngle"]
        sharpness = light["Sharpness"]
        color_diffuse_raw = self.read_color_rgb(light["DiffuseColor"])
        color_ambient_raw = self.read_color_rgb(light["AmbientColor"])
        specular = light["SpecularAmount"]
        variation_speed = light["VariationSpeed"]
        variation_amount = light["VariationAmount"]
        shadow_map_size = light["ShadowMapSize"]
        casts_shadows = light["CastsShadows"]

        # Calculate normalized color RGB values
        color_diffuse = color_diffuse_raw.normalized()
        color_ambient = color_ambient_raw.normalized()
        
        # Calculate light intensity values for the new normalized RGB values
        # region Comment - intensity value calculation
        # NOTE : The results obtained may not be 100% correct. This is the best approximation I could come up with. An input color may have an intensity of a different magnitude for each of the color channels.
        # This code is built on the assumption that the intensity is assumed to be the same multiplier for all channels, even tho it can be manually set to anything by hand. Obviously this assumption is made
        # Because of the intensity property found on the leftover fbx map file within the Magicka game files, which points to the direction that devs deliberatedly made all maps to respect this constraint.
        # Users could edit this by hand if they wanted tho. The best solution in the future would be to actually add support for individual intensity values for each channel. 
        # endregion
        color_diffuse_intensity = color_diffuse_raw.length
        color_ambient_intensity = color_ambient_raw.length

        # Create the light data and modify its properties
        light_data = bpy.data.lights.new(name=name, type=light_type)

        # Create the light object
        light_object = bpy.data.objects.new(name=name, object_data=light_data)

        # Add the light object to the scene (link object to collection)
        bpy.context.collection.objects.link(light_object)

        # Modify light object properties
        light_object.location = position
        light_object.rotation_mode = "QUATERNION" # Set rotation mode to quaternion for the light object.
        light_object.rotation_quaternion = mathutils.Vector((0, 0, -1)).rotation_difference(direction)

        # Modify light mcow properties
        light_data.magickcow_light_type = light_type
        light_data.magickcow_light_variation_type = variation_type
        light_data.magickcow_light_variation_speed = variation_speed
        light_data.magickcow_light_variation_amount = variation_amount
        light_data.magickcow_light_reach = reach
        light_data.magickcow_light_use_attenuation = use_attenuation
        light_data.magickcow_light_cutoffangle = cutoff_angle
        light_data.magickcow_light_sharpness = sharpness
        light_data.magickcow_light_color_diffuse = color_diffuse
        light_data.magickcow_light_color_ambient = color_ambient
        light_data.magickcow_light_intensity_specular = specular
        light_data.magickcow_light_intensity_diffuse = color_diffuse_intensity
        light_data.magickcow_light_intensity_ambient = color_ambient_intensity
        light_data.magickcow_light_shadow_map_size = shadow_map_size
        light_data.magickcow_light_casts_shadows = casts_shadows

        # Return the generated object
        return light_object

    def import_collision_mesh_generic_internal(self, name, json_has_collision, json_vertices, json_triangles):
        has_collision, vertices, triangles = self.read_collision_mesh(json_has_collision, json_vertices, json_triangles)
        if has_collision:
            mesh = bpy.data.meshes.new(name=name)
            obj = bpy.data.objects.new(name=name, object_data=mesh)
            bpy.context.collection.objects.link(obj)
            mesh.from_pydata(vertices, [], triangles)
            mesh.update()
            return (True, obj, mesh)
        else:
            return (False, None, None)

    def import_static_collision_mesh(self, collision, name):
        json_has_collision = collision["hasCollision"]
        json_vertices = collision["vertices"]
        json_triangles = collision["triangles"]
        return self.import_collision_mesh_generic_internal(name, json_has_collision, json_vertices, json_triangles)

    def import_collision_mesh_level(self, collision, channel_index = 0):
        channel_name = find_collision_material_name(channel_index)
        name = f"collision_mesh_model_{channel_index}_{channel_name}"

        has_collision, obj, mesh = self.import_static_collision_mesh(collision, name)

        if has_collision:
            mesh.magickcow_mesh_type = "COLLISION"
            obj.magickcow_collision_material = channel_name

    def import_collision_mesh_camera(self, collision):
        name = "collision_mesh_camera"

        has_collision, obj, mesh = self.import_static_collision_mesh(collision, name)

        if has_collision:
            mesh.magickcow_mesh_type = "CAMERA"

    def import_locator(self, locator):
        # Get the properties of the locator from the json data
        name = locator["Name"]
        transform = self.read_mat4x4(locator["Transform"])
        radius = locator["Radius"]

        # region Comment - empty display explanation
        # NOTE : The display type is updated automatically when we change the property empty.magickcow_empty_type, since it is linked to an update function,
        # so we don't need to call this ourselves by hand. I'm leaving this code behind so that you can remember why we don't do it.
        # empty.empty_display_type = "PLAIN_AXES"
        # endregion
        # Create empty object and add it to the scene and modify its properties
        empty = bpy.data.objects.new(name = name, object_data = None)
        empty.matrix_world = transform

        # Link the object to the current scene collection
        bpy.context.collection.objects.link(empty)

        # Update the mcow properties
        empty.magickcow_empty_type = "LOCATOR"
        empty.magickcow_locator_radius = radius

        # Return the generated object
        return empty

    def import_trigger(self, trigger):
        # Extract the data from the json object
        name = trigger["Name"]
        position = self.read_point(trigger["Position"])
        scale = self.read_scale(trigger["SideLengths"])
        rotation = self.read_quat(trigger["Rotation"])

        # Create the empty object trigger on the Blender scene and assign the properties
        empty = bpy.data.objects.new(name = name, object_data = None)
        
        # Link the object to the scene
        bpy.context.collection.objects.link(empty)

        # Assign the properties to the created empty object
        # NOTE : These values that we are assigning here are the ones used by Magicka's engine in-game.
        # After this, we apply some corrections so that the values are exactly the ones that Blender needs to use.
        empty.location = position
        empty.rotation_mode = "QUATERNION" # Change the rotation mode to quaternion so that we can apply quaternion rotations. Yes, in blender, if you don't change the rotation mode from "XYZ" to "QUATERNION", the rotation_quaternion property will literally do fucking nothing at all...
        empty.rotation_quaternion = rotation
        empty.scale = scale / 2.0 # Set the scale to half of the side of the in-game trigger side lengths because the trigger origin in Magicka is on a corner, but in Blender it's on the center of the trigger's volume.

        # Update the context view layer after changing the location, rotation and scale, so that we can access the most updated values for the transform matrix.
        # Blender does not update this value until it finishes evaluating everything for the next frame, which means that we need to force blender to perform an extra evaluation here
        # so that accessing obj.matrix_world returns the expected value rather than an outdated value.
        bpy.context.view_layer.update()
        
        # Get the relative transform vectors (forward vector, up vector and right vector) of the object on the Blender scene.
        # These will be used to apply some relative translations.
        x_vec = empty.matrix_world.col[0].xyz.normalized()
        y_vec = empty.matrix_world.col[1].xyz.normalized()
        z_vec = empty.matrix_world.col[2].xyz.normalized()

        # Apply corrections to trigger location.
        # Apply a relative transform by half of the in-game scale (which is 100% of the in-Blender scale, since we already divided the scale by half in a previous step)
        # so that the origin point is now aligned with the center of the trigger's volume rather than the corner of the trigger's volume.
        empty.location += x_vec * empty.scale[0]
        empty.location -= y_vec * empty.scale[1]
        empty.location += z_vec * empty.scale[2]

        # Change the mcow empty type. This also updates the empty display type automatically.
        empty.magickcow_empty_type = "TRIGGER"

    def import_effect(self, effect):
        effect_name = effect["id"]
        effect_position = self.read_point(effect["vector1"])
        effect_orientation = self.read_point(effect["vector2"])
        effect_range = effect["range"]
        effect_name = effect["name"]

        obj = bpy.data.objects.new(name = effect_name, object_data = None)
        
        obj.location = effect_position
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = mathutils.Vector((0, -1, 0)).rotation_difference(effect_orientation)

        bpy.context.collection.objects.link(obj)

        obj.magickcow_empty_type = "PARTICLE"
        obj.magickcow_particle_name = effect_name
        obj.magickcow_particle_range = effect_range

        return obj

    def import_physics_entity(self, idx, physics_entity):
        template = physics_entity["template"]
        transform = self.read_mat4x4(physics_entity["transform"])

        obj = bpy.data.objects.new(name=f"physics_entity_{idx}", object_data = None)

        obj.matrix_world = transform

        bpy.context.collection.objects.link(obj)

        obj.magickcow_empty_type = "PHYSICS_ENTITY"
        obj.magickcow_physics_entity_name = template

    def import_root_node(self, idx, root_node):
        # Read root node properties
        is_visible = root_node["isVisible"]
        casts_shadows = root_node["castsShadows"]
        sway = root_node["sway"] # Now that we know what these 3 properties are, we can assign them without any issues!
        entity_influence = root_node["entityInfluence"] # same
        ground_level = root_node["groundLevel"] # same
        vertex_stride = root_node["vertexStride"]
        vertex_declaration = root_node["vertexDeclaration"]
        vertex_buffer = root_node["vertexBuffer"]
        index_buffer = root_node["indexBuffer"]
        effect = root_node["effect"]
        primitive_count = root_node["primitiveCount"]
        # start_index = root_node["startIndex"] # We always read all of the geometry, so for us, the start index is always 0. This is because we just merge all of the contents of child nodes into the same object, since they share the same vertex buffer anwyways. Keeping child nodes as individual objects is more work than it's worth, and it's pretty pointless for 99% of cases anyway...
        # bounding_box = root_node["boundingBox"] # We auto generate a new AABB on export anyways, so this value is not really required.
        
        # region Comment - Child nodes support
        
        # NOTE : Child node support is not required. Children nodes do not have any way of moving geometry around, so they cannot be used to reuse parent geometry at a different location without generating a new vertex buffer.
        # Tbh, I don't really know what the fuck they are for, seeing the code, they are pretty much useless, and I have no clue what the Magicka devs were smoking when they conjured up this idea.
        # All we do in this importer addon is read the entire vertex buffer data and generate a single mesh, which effectively does the same as merging all of the child nodes with their parent nodes into a single mesh.
        # I mean, after all, that IS exactly how they are organized in memory within the vertex buffer data itself. The only purpose that child nodes have is to give different bounding boxes to different segments of
        # the mesh, which is pretty useless in 99% of usecases, and we auto generate those anyway, so yeah. Pretty much, just a premature optimization that actually just bloats memory use unnecessarily and fucks up cache alignment for no reason...
        # has_child_a = ["hasChildA"]
        # has_child_b = ["hasChildB"]
        # child_a = ["childA"]
        # child_b = ["childB"]
        
        # endregion

        # Read the vertex and index buffer data
        mesh_vertices, mesh_triangles = self.read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

        # Create mesh data and mesh object
        name = f"mesh_{idx}"
        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        # Asign the mcow mesh properties to the generated mesh data
        mesh.magickcow_mesh_is_visible = is_visible
        mesh.magickcow_mesh_casts_shadows = casts_shadows
        mesh.magickcow_mesh_advanced_settings_enabled = True # We can't really compare equality between the float values of the advanced settings due to precission errors, so we might as well just enable these... besides, these default values were picked by me, so 90% of maps will not have them like that anyway.
        mesh.magickcow_mesh_sway = sway
        mesh.magickcow_mesh_entity_influence = entity_influence
        mesh.magickcow_mesh_ground_level = ground_level
        
        # Asign the mcow object properties to the generated object
        obj.magickcow_collision_enabled = False # We disable the complex collision generation for thei mported mesh since the imported scene already has all of the collision meshes baked into the collision channel meshes, and since we don't want to accidentally add extra collisions on export, we might as well just disable it and assume that the collision channels are what the user expects to get / see on import.

        # Set the mcow mesh type
        mesh.magickcow_mesh_type = "GEOMETRY" # NOTE : This is already the default anyways, so we don't need the statement, but it's here for correctness, just in case the default changes in the future.

        # Read material data and append it to the generated mesh
        material_name = f"material_mesh_{idx}"
        mat = self.read_effect(material_name, root_node["effect"])
        mesh.materials.append(mat)

    def import_liquid(self, idx, liquid):
        # Read the properties from the JSON object
        liquid_type = liquid["$type"]
        vertex_buffer = liquid["vertices"]
        index_buffer = liquid["indices"]
        vertex_declaration = liquid["declaration"]
        vertex_stride = liquid["vertexStride"]
        primitive_count = liquid["primitiveCount"]

        can_drown = liquid["flag"]
        can_freeze = liquid["freezable"]
        can_auto_freeze = liquid["autofreeze"]

        effect = liquid["effect"]

        # Read vertex buffer data and index buffer data
        mesh_vertices, mesh_triangles = self.read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

        # Create mesh data and mesh object
        name = f"liquid_{idx}_{liquid_type}"
        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        # Get mcow mesh type from input liquid type.
        # NOTE : In the future, this may be modified / removed, IF / when the WATER / LAVA system is deprecated / modified (if it ever happens)
        if liquid_type == "liquid_water":
            mesh_type = "WATER"
        elif liquid_type == "liquid_lava":
            mesh_type = "LAVA"
        else:
            raise MagickCowImportException(f"Imported liquid has unknown liquid type: \"{liquid_type}\"")
        
        # Assign mcow properties
        mesh.magickcow_mesh_type = mesh_type
        mesh.magickcow_mesh_can_drown = can_drown
        mesh.magickcow_mesh_freezable = can_freeze
        mesh.magickcow_mesh_autofreeze = can_auto_freeze

        # Create material and assign it to the mesh
        mat_name = f"liquid_material_{idx}_{liquid_type}"
        mat = self.read_effect(mat_name, effect)
        mesh.materials.append(mat)

        # Return the generated object for further use
        return obj

    def import_force_field(self, idx, force_field):
        # Get data from the input json object
        vertex_buffer = force_field["vertices"]
        index_buffer = force_field["indices"]
        vertex_declaration = force_field["declaration"]
        vertex_stride = force_field["vertexStride"]

        # Compute mesh data
        mesh_vertices, mesh_triangles = self.read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

        # Generate object and mesh data
        name = f"force_field_{idx}"
        mesh = bpy.data.meshes.new(name = name)
        obj = bpy.data.objects.new(name = name, object_data = mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        # Assign mcow properties to mesh
        mesh.magickcow_mesh_type = "FORCE_FIELD"

        # Create material data and assign it to the mesh
        mat_name = f"force_field_material_{idx}"
        mat = self.read_effect(mat_name, force_field) # NOTE : The material effect data is embedded within the force field object itself.
        mesh.materials.append(mat)

    def import_animated_part(self, part, parent):
        # region Comments - Stuff to figure out about the animated level part import implementation

        # TODO : Figure out how to deal with animated level parts from the base game which contain more than one bone... I just found one like that on wc_s4, and it sure will make things a bit harder to deal with.
        # Note that for my exporter implementation, I settled for every single part having a single bone, and any child bones being a separate part, which is what the vs boat map does, so yeah... this is gonna be
        # a bit complicated to deal with, I suppose...
        # NOTE : Considering how only the root bone of an animated level part can be moved (it's the one used to describe the motion), we have 2 possible solutions here:
        # 1) Modify the exporter so that child bones with no motion and identical collision channel as their parents are not added to separate animated level part on export, but rather they are added as child bones of the same XNA model hierarchy.
        # 2) Accept that the importer will translate things to the way mcow does it, just add a different child animated level part on import and have it exist so that we don't break pois. On export, it will be a separate animated level part, but theoretically, the outcome should be the same, so we just compile to an slightly different form hierarchy-wise.
        # Option 1 may be a bit more elegant, but option 2 requires far less work in the long run, and is probably just as valid. Also note that this would never even be a problem if the magicka devs hadn't made maps that contain for some fucking stupid reason multiple bones on the same animated level part, when only the root matters... which means that they just exist as a way to add different identifiers to pois but for the same fucking object, like wtf?
        # iirc, pois are identified with part_name.child_part_name.child_bone_name etc... which means that this does lead to different pois with different names, but they point to the same fucking visual object, so wtf?
        # This also means that we can't really get away with option 2, since that means that objects with geometry that must glow when pointing at a poi will no longer do so on recompilation... wtf... artificial problems...

        # NOTE : All of this may not matter at all if in the base game, these sort of "leaf" bones are never really used for anything and just exist for some fucking weird reason...
        # If that's the case, then we can just ignore them and import them as new bones, and go with route 1), which is what I'm gonna be implementing for now.
        # Also, as a warning, note that maybe the impl will change, but I'm sure I will forget to update this comment, so just be aware of the issue for future reference and look at the code to know what impl
        # is actually on the code right now...

        # NOTE : The "extra" bone names could correspond to the mesh names, no? iirc that's the way it works, I don't remember how I implemented it on the exporter, but now that I think about it, it very well could be...
        # TODO : Figure this part out again and then properly implement the fucking importer ffs...

        # endregion

        # TODO : Finish implementing

        # Get properties for the animated level part
        name = part["name"] # NOTE : For now, we're taking the bone name from the part name. From what I've seen, these should always match (the name of this part and the name of the root bone of this part), but if in the future I find any examples on the base game that don't match, then it would be important to revise this implementation and change it.
        affects_shields = part["affectShields"]

        model = part["model"]
        mesh_settings = part["meshSettings"] # TODO : Implement mesh settings handling
        
        liquids = part["liquids"]
        locators = part["locators"]
        effects = part["effects"]

        lights = part["lights"]

        animation_duration = part["animationDuration"]
        animation = part["animation"]

        has_collision = part["hasCollision"]
        collision_material = part["collisionMaterial"]
        collision_vertices = part["collisionVertices"]
        collision_triangles = part["collisionTriangles"]

        has_nav_mesh = part["hasNavMesh"]
        nav_mesh = part["navMesh"]

        children = part["children"]

        # Internal import process

        # Import animated level part model mesh
        root_bone_obj = self.import_animated_model(model, parent)

        # Temporary Hack to set the transform of the bones to that of the first frame of the animation
        # NOTE : This part is a hacky workaround and should NOT be used in the final version.
        # Remove this piece of shit code once full animation import support is added, since that will also fix this issue!
        # NOTE : The transform operations applied in Blender to objects through their .location .rotation_quaternion / .rotation_euler and .scale are all performed relative to the parent, so no need to handle matrix_basis or matrix_world to ensure that we get the correct results.
        first_anim_frame = animation["frames"][0]["pose"]
        faf_pos = self.read_point(first_anim_frame["translation"])
        faf_rot = self.read_quat(first_anim_frame["orientation"])
        faf_scale = self.read_scale(first_anim_frame["scale"])
        root_bone_obj.location = faf_pos
        root_bone_obj.rotation_mode = "QUATERNION" # NOTE : Important to ensure that this is the rotation mode so that we can assign rotation quaternions...
        root_bone_obj.rotation_quaternion = faf_rot
        root_bone_obj.scale = faf_scale

        # Import Liquids
        self.import_animated_liquids(liquids, root_bone_obj)

        # Import Locators
        self.import_animated_locators(locators, root_bone_obj)

        # Import Effects
        self.import_animated_effects(effects, root_bone_obj)

        # Import lights
        self.import_animated_lights(lights, root_bone_obj)

        # Import collision
        self.import_animated_collision_mesh(has_collision, collision_material, collision_vertices, collision_triangles, root_bone_obj)

        # Import child animated parts
        for child_part in children:
            self.import_animated_part(child_part, root_bone_obj)

        # TODO : Implement property assignment, etc...

    # endregion

    # region Import Methods - Internal - Animated

    # TODO : Maybe in the future, make it so thatthese read functions become members of the base Importer Pipeline class so that the PhysicsEntity Importer can use it as well.
    
    def import_animated_model(self, model, parent_bone_obj):
        # Get model properties
        bones = model["bones"]
        vertex_declarations = model["vertexDeclarations"]
        model_meshes = model["modelMeshes"]

        # Import the root bone of the model
        root_bone_obj = self.import_bone(bones[0], parent_bone_obj)

        # Import the child meshes of this animated level part
        self.import_model_meshes(root_bone_obj, bones, vertex_declarations, model_meshes)

        return root_bone_obj

    # region Comment
    # TODO : Maybe make this function a generic importer pipeline function so that Physics Entities and other such objects can import bones as well?
    # Or at least part of its logic, since the empty object type is Map and PE specific, and when the skinned character mesh export / import support is added, we'll use armatures for that, so only the JSON
    # parsing side of things could be considered generic, everything else requires some specific treatment regarding the object creation process itself and the properties that must be added to properly
    # handle importing and object creation / generation.
    # endregion
    def import_bone(self, bone_data, parent_bone_obj):
        # Get bone properties
        bone_name = bone_data["name"]
        bone_transform = self.read_mat4x4(bone_data["transform"]) # NOTE : This transform is relative to the parent bone of this part. If no parent exists, then obviously it's in global coordinates, since it is relative to the parent, which is the world origin.

        # Create bone object
        bone_obj = bpy.data.objects.new(name=bone_name, object_data=None)
        
        # Set bone transform and attach to parent if there's a parent bone object
        if parent_bone_obj is None:
            bone_obj.matrix_world = bone_transform # Set the matrix world transform matrix
        else:
            bone_obj.parent = parent_bone_obj # Attach the generate bone to the existing parent bone
            bone_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4) # Clear the parent inverse matrix that Blender calculates.
            bone_obj.matrix_basis = bone_transform # Set the relative transform
            # region Comment - Clearing out parent inverse matrix
            
            # We clear the parent inverse matrix that Blender calculates.
            # This way, the relative offset behaviour we get is what we would expect in literally any other 3D software on planet Earth.
            # Note that I'm NOT saying that Blender's parent inverse is useless... no, it's pretty nice... sometimes... but in this case? it's a fucking pain in the ass. So we clear it out.
            # We also could clear it with bpy.ops, but that's a pain in the butt, so easier to just do what bpy.ops does under the hood, which is setting the inverse matrix to the identity,
            # which is the same as having no inverse parent matrix.
            # For more information regarding the parent inverse matrix, read: https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Parenting#Clear_Parent_Inverse_Clarified
            # It will all make sense...
            
            # NOTE : Quote from the article (copy-pasted here just in case the link goes dead at some point in the future):
            # Normally, when a parent relationship is set up, if the parent has already had an object transformation applied, the child does not immediately inherit that.
            # Instead, it only picks up subsequent changes to the parent’s object transformation. What happens is that, at the time the parent relationship is set up, the inverse of the current parent
            # object transformation is calculated and henceforth applied before passing the parent transformation onto the child.
            # This cancels out the initial transformation, leaving the child where it is to start with.
            # This inverse is not recomputed when the parent object is subsequently moved or subject to other object transformations, so the child follows along thereafter.
            # The "Clear Parent Inverse" function sets this inverse transformation to the identity transformation, so the child picks up the full parent object transformation.

            # endregion
        
        # Link the object to the scene
        bpy.context.collection.objects.link(bone_obj)

        # Set mcow properties
        bone_obj.magickcow_empty_type = "BONE"

        # TODO : Refine the handling of the bounding sphere, maybe fully figure out what it does and maybe even auto-generate it like the bounding box for static mesh level parts.

        return bone_obj

    def import_model_meshes(self, root_bone_obj, bones, vertex_declarations, model_meshes):
        for model_mesh in model_meshes:
            
            parent_bone_index = model_mesh["parentBone"]
            parent_bone_data = bones[parent_bone_index]

            json_vertex_buffer = model_mesh["vertexBuffer"]
            json_index_buffer = model_mesh["indexBuffer"]
            
            mesh_parts = model_mesh["meshParts"]

            total_vertices = 0
            for mesh_part in mesh_parts:
                total_vertices += mesh_part["numVertices"]
            vertex_stride = len(json_vertex_buffer["Buffer"]) // total_vertices

            for mesh_part in mesh_parts:
                
                # region Comment - Mesh Parts Handling

                # TODO : Add proper mesh part handling in the future in the event that any of the vanilla maps have model meshes with multiple mesh parts rather than just 1.
                # Note that all mesh parts share the same vertex and index buffers, but they allow assigning different share resource indices (different material effects) to a segment of the mesh,
                # as well as different vertex declarations.

                # endregion
                
                vertex_declaration_index = mesh_part["vertexDeclarationIndex"]
                json_vertex_declaration = vertex_declarations[vertex_declaration_index]

                self.import_model_mesh(root_bone_obj, parent_bone_data, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer)

                share_resource_index = mesh_part["sharedResourceIndex"] # TODO : Add shared resource handling

    def import_model_mesh(self, obj_root_bone, json_parent_bone, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer):
        # Generate mesh data
        mesh_vertices, mesh_triangles = self.read_mesh_buffer_data(vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer)

        # Create mesh data block and Blender object
        name = json_parent_bone["name"]
        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        # Assign mcow properties
        mesh.magickcow_mesh_type = "GEOMETRY"

        # Attach to parent bone object and set relative object transform
        transform = self.read_mat4x4(json_parent_bone["transform"])
        obj.parent = obj_root_bone
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        obj.matrix_basis = transform

        # Create material data
        # TODO : Implement material handling

    def import_animated_liquids(self, liquids_data, parent_obj):
        liquids_objs = self.import_liquids(liquids_data)
        if parent_obj is not None: # NOTE : Parent should never be None here, since we always generate a bone obj for each animated level part, but we add the None check just in case...
            for liquid_obj in liquids_objs:
                liquid_obj.parent = parent_obj
                liquid_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                liquid_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_locators(self, locators_data, parent_obj):
        locators_objs = self.import_locators(locators_data)
        if parent_obj is not None:
            for locator_obj in locators_objs:
                locator_obj.parent = parent_obj
                locator_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                locator_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_effects(self, effects_data, parent_obj):
        effects_objs = self.import_effects(effects_data)
        if parent_obj is not None:
            for effect_obj in effects_objs:
                effect_obj.parent = parent_obj
                effect_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                effect_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_lights(self, lights, parent_obj):
        if parent_obj is not None:
            for light in lights:
                name = light["name"]
                transform = self.read_mat4x4(light["position"])
                if name in self._cached_lights:
                    obj = self._cached_lights[name]
                    obj.parent = parent_obj
                    obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                    obj.matrix_basis = transform

    def import_animated_collision_mesh(self, json_has_collision, json_collision_material, json_vertices, json_triangles, parent_obj):
        # Get generic collision properties
        name = "animated_collision_mesh"
        collision_material = find_collision_material_name(json_collision_material)
        
        # Generate collision blender mesh data and blender object
        has_collision, obj, mesh = self.import_collision_mesh_generic_internal(name, json_has_collision, json_vertices, json_triangles)

        # If a collision mesh object was generated, set the mcow properties and attach to parent bone object
        if has_collision:
            mesh.magickcow_mesh_type = "COLLISION"
            obj.magickcow_collision_material = collision_material
        
            # Attach the collision mesh to the parent bone object and set the relative transform to the identity matrix
            if parent_obj is not None:
                obj.parent = parent_obj
                obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                obj.matrix_basis = mathutils.Matrix.Identity(4)

    # endregion

# endregion

# ../mcow/functions/generation/import/derived/PhysicsEntity.py
# region Import Data Pipeline class - PhysicsEntity

class MCow_ImportPipeline_PhysicsEntity(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        raise MagickCowNotImplementedException("Import PhysicsEntity is not implemented yet!")

# endregion

# ../mcow/Main.py
# region Main Addon Entry Point

def register():
    # Register custom property classes
    register_properties_classes()

    # Register the Import and Export Panels
    register_exporters()
    register_importers()

    # Register the Material, Object and Scene Properties and Property Panels
    register_properties_material()
    register_properties_object()
    register_properties_scene()

def unregister():
    # Register custom property classes
    unregister_properties_classes()

    # Unregister the Import and Export Panels
    unregister_exporters()
    unregister_importers()

    # Unregister the Material, Object and Scene Properties and Property Panels
    unregister_properties_material()
    unregister_properties_object()
    unregister_properties_scene()

if __name__ == "__main__":
    register()

# endregion

