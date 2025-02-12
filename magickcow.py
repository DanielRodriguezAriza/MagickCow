# region Comments

# TODO : Possibly change a lot of this stuff by encapsulating all of the "make_" methods into actual classes? with their own "generate()", "get_object()"/"make()", etc methods... idk...
# TODO : Rework all of the useless tuple copying by merging the JSON-style object make_ step with the generate_ step, maybe? I mean, it would be easier to keep them separate if the information was stored within proper classes and each had their make_data and generate_data functions.

# NOTE : I hate coding in python, it looks like 90% of the code is fucking comments, seriously, just having a decent type system would prevent having to make so many comments to clear stuff up. No, type annotations are not good enough...
# NOTE : Well, I don't really hate coding in python, it's pretty cool, but fuck me this code has to be one of the most wall of text filled pieces of code I have ever written. The comments are insane.

# TODO : Re-enable the global try catch on the exporter code so that we can get proper error handling. This was simply disabled so that we could get on what line exceptions took place during debugging...
# TODO : There's a bug when dealing with meshes that have 0 triangles. Discard those by seeing their triangle count on the get stage both on the map and physics entity handling code...
# TODO : Fix issue where attaching a light or other orientation based objects to a locator causes the resulting rotation values to be wrong (the locator has a pretty shitty rotation undo fix which is fucking things up...)

# endregion

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

# region Imports

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
from collections import namedtuple

# endregion

# region Custom Exception Classes

# Dummy exception class that is literally the same as the base Exception class.
# Only exists to make it possible for the main export exception try-catch blocks to still print the line on which the error took place when a different type of exception or error takes place.
# This way we prevent catching all of them and retain debugability to a certain degree... 
class MagickCowExportException(Exception):
    pass

# endregion

# region Classes and Named Tuples

# region Blender GSD Object classes

# NOTE : GSD = Get Stage Data
# TODO : Get rid of this unused class or update all of the code to use this rather than passing (obj, transform) pairs around...

# This is the base class for a Get Stage Data Object.
# It contains a pointer to the blender object and a transform matrix which contains the transform relative to the parent as it would be defined within the XNB file
# Note that the transform matrix does not necessarily match with the obj.matrix_world or with the obj.matrix_local, as the obj.parent (blender parent) is not necessarily the "parent" that we'd use within the XNB file...
class GSDObject:
    def __init__(self, obj, transform):
        self.obj = obj
        self.transform = transform

# endregion

# region Meshes

class MagickCowMesh:
    def __init__(self, obj, transform):
        self.obj = obj
        self.transform = transform
        self.invtrans = transform.inverted().transposed()
        self.mesh = None
        self.bm = None
        self._calculate_mesh_data() # Apply modifiers, triangulate mesh, generate bm, etc...
    
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

# region XNA classes

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

# region Map

class SceneObjectsFound:
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
        
        # NOTE : These 2 ahead can only be found on static level data, can't be within animated level parts.
        self.physics_entities = []
        self.force_fields = []

class SceneObjectsGeneratedStatic:
    def __init__(self):
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = []
        self.particles = []
        self.collisions = []
        self.nav_mesh = None
        self.animated_parts = []
        self.physics_entities = []
        self.force_fields = []

class SceneObjectsGeneratedAnimated:
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

# region Physics Entity

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

# endregion

# region Utility Class

class MagickCowUtility:
    
    class Scene:
        def GetObjectsAll():
            objects = bpy.data.objects
            return objects
        
        def GetObjectsRoot():
            bpyobjects = bpy.data.objects
            objects = [obj for obj in bpyobjects if obj.parent is None]
            return objects
        
        def GetObjectsChildrenAll(obj):
            objects = []
            MagickCowUtility.Scene.GetObjectsChildrenAllRec(obj, objects)
            return objects
        
        def GetObjectsChildrenAllRec(obj, children_list):
            # NOTE : Alternatively we could use children_list.extend(obj.children) and then iterate over the list making the recursive calls.
            for child in obj.children:
                children_list.append(child)
                MagickCowUtility.Scene.GetObjectsChildrenAllRec(child, children_list)

        def GetObjectsChildrenImmediate(obj):
            objects = obj.children
            return objects
    
    # TODO : Either implement this or get rid of it, depends on how you decide to handle Y up conversion in the end...
    class Math:
        
        # NOTE : As of now, it seems like Blender does not support non-trivial transform matrices, stuff such as shearing and whatnot... Magicka doesn't seem to support those either, and most of the objects that
        # use transform matrices seem to be point data such as locators and whatnot, so it's not like it would be worth it to do any of that...
        # The point I'm trying to bring across is the fact that basically for this reason we're doing the cheap, quick and dirty Z up to Y up conversion by switching axes and flipping a sign rather than using
        # a transform matrix, because matrix operations are just far less optimal IN PYTHON... sad, I know, but whatever, good enough for now...

        def transform_to_y_up(transform_matrix):
            reutnr

# endregion

# region General Purpose Utility Functions

# TODO : Move a lot of this functionality into the generic DataGenerator base class...

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

def find_light_type_index(light):
    return find_element_index(["POINT", "SUN", "SPOT"], light, 0)

def find_collision_material_index(material):
    return find_element_index(["GENERIC", "GRAVEL", "GRASS", "WOOD", "SNOW", "STONE", "MUD", "REFLECT", "WATER", "LAVA"], material, 0)

def find_light_variation_type_index(light_variation):
    return find_element_index(["NONE", "SINE", "FLICKER", "CANDLE", "STROBE"], light_variation, 0)

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

# region Generator classes

# region Comment - DataGenerator
    # A generic class for data generation.
    # This class contains methods to generate data that is generic to all types of assets.
    # Each specific Data generator class will implement data generation methods that are specific for each type of asset to be exported.
    # NOTE : At some point in the future, it may make sense to move much of the logic here to some intermediate DataGenerator class (that inherits from the base one) that implements all of the 3D related operations and materials / effects / shared resources handling which some other forms of files that we could generate may not deal with... for example character creation...
# endregion
class DataGenerator:
    
    # region Constructor
    
    def __init__(self):

        # Start of DataGenerator Initalization

        # Other data goes here...

        # Dictionary for Shared Resources
        self.dict_shared_resources = {}
        
        # Dictionary for Cached Effects (Materials)
        self.dict_effects = {}

        # Cached Effects Initialization
        # Setup all default material data beforehand (not required as the process would still work even if this was not done, but whatever... basically this works as a sort of precaching, but since it is
        # not compiletime because this is not C, there really is not much point ot it, altough maybe making the dict with self.dict_effects = {"base/whatever" : {blah blah blah...}, ...} could actually
        # be faster in future versions of Python, idk)
        for current_type in ["GEOMETRY", "WATER", "LAVA"]:
            self.dict_effects[self.generate_default_effect_name(current_type)] = self.generate_default_effect_data(current_type)

        # End of DataGenerator Initalization
        return 
    
    # endregion

    # region Auxiliary Functions

    # region Scene Rotation

    # region Deprecated

    # Iterates over all of the root objects of the scene and rotates them by the input angle in degrees around the specified axis.
    # The rotation takes place around the world origin (0,0,0), so it would be equivalent to attaching all objects to a parent located in the world origin and then rotating said parent.
    # This way, there is no hierarchical requirements for scene export, since all root objects will be translated properly, and thus the child objects will also be automatically translated to the coorect coordinates.
    def rotate_scene_old_1(self, angle_degrees = 90, axis = "X"):
        root_objects = get_scene_root_objects()
        for obj in root_objects:
            obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees))
        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.
    
    def rotate_objects_global_old_2(self, objects, angle_degrees, axis):
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(angle_degrees), 4, axis)
        for obj in objects:
            # obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees)) # idk why this doesn't work for all objects, I guess I'd know if only Blender's documentation had any information related to it. Oh well!
            obj.matrix_world = rotation_matrix @ obj.matrix_world

    
    def rotate_objects_local_old_2(self, objects, angle_degrees, axis):
        axis_num = find_element_index(["X", "Y", "Z"], axis, 0)
        for obj in objects:
            obj.rotation_euler[axis_num] += math.radians(angle_degrees)

    # NOTE : It also iterates over the locator objects and rotates them in the opposite direction.
    # This is because the rotation of the transform obtained after rotating the scene is only useful for objects where we need to translate other data, such as points and vectors (meshes, etc...)
    # In the case of locators, we directly use the transform matrix of the object itself, which means that the extra 90 degree rotation is going to change the orientation of the locators by 90 degrees.
    # This can be fixed by manually rotating the locators... or by having the rotate_scene() function do it for us, so the users will never know that it even happened! 
    # NOTE : Another fix would be to have a single world root object of sorts, and having to attach all objects to that root. That way, we would only have to rotate that one single root by 90 degrees and nothing else, no corrections required...
    # TODO : Basically make it so that we also have a root object in map scenes, just like we do in physics entity scenes...
    def rotate_scene_old_2(self, angle_degrees = 90, axis = "X"):
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

        self.rotate_objects_global_old_2(root_objects, angle_degrees, axis) # Rotate the entire scene
        self.rotate_objects_local_old_2(objects_to_correct, -1.0 * angle_degrees, axis) # The correction rotation goes in the opposite direction to the input rotation

        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.

    # endregion

    # NOTE : First we rotate by -90º, then to unrotate we rotate by +90º, this way we can pass from Z up to to Y up coords
    # TODO : Once you implement the new scene root system for the map exporting side of the code, you will be capable of getting rid of the _aux suffix for this method's name.
    # Also, get rid of the rotate_scene() method within the map data generator class...
    # TODO : To be able to use this simpler root based rotation for map scenes, we need to find a way to translate rotations. We don't have to have the 90 degree rotation fix for empties anymore, sure, but
    # previously we did not apply any rotation fix to lights either... why? because lights with a rotation apply over a direction vector. What this means is that without the rotation fix, all of my final rotations
    # are Z up based, even tho my final points will be Y up based... or maybe I'm confused and this is actually wrong?
    # NOTE : Actually, now that I think about it, wouldn't we still have to undo rotations locally for point data whose location, rotation and scalre are exported with a matrix? If you think about it, lights are not affected despite being point data because their direction is exported as a director vector. I need to think about this shit tbh...
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

    # Aux functions to perform rotations without having to remember what values and axes are specifically required when exporting a scene to Magicka.
    # Makes it easier to go from Z up to Y up, progress the scene, and then go back from Y up to Z up.
    def do_scene_rotation(self):
        self.rotate_scene(-90, "X")
    
    def undo_scene_rotation(self):
        self.rotate_scene(90, "X")

    # endregion

    # region Shared Resources Related Operations

    def add_shared_resource(self, resource_name, resource_content):
        if resource_name not in self.dict_shared_resources:
            num_resources = len(self.dict_shared_resources)
            resource_index = num_resources + 1 # Use the current count of resources as the index of each element (note that indices for shared resources in XNB files start at 1, not 0)
            self.dict_shared_resources[resource_name] = (resource_index, resource_content) # Store the resource index and its contents
            return resource_index
        else:
            idx, content = self.dict_shared_resources[resource_name]
            return idx

    def get_shared_resource_index(self, resource_name):
        if resource_name in self.dict_shared_resources:
            idx, content = self.dict_shared_resources[resource_name]
            return idx
        return 0 # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    # NOTE : The input has to be a dictionary
    def make_shared_resources_list(self, shared_resources_dict):
        ans = []
        for key, resource in shared_resources_dict.items():
            idx, content = resource
            ans.append(content)
        return ans
    
    # endregion

    # region Materials / Effects Related Operations

    # Returns the full path for a given material file. It does not check in the file system, all it does is append the selected path for material files to the given blender material name.
    # Automatically appends the ".json" extension if the material name does not end in ".json" to ensure that the correct file name is generated.
    # All validity checkign is performed later, when the actual contents of the file are retrieved, where the system checks for whether this file exists or not.
    def get_material_path(self, matname):
        ans = path_append(bpy.context.scene.mcow_scene_base_path, matname)
        if ans.endswith(".json"):
            return ans
        return ans + ".json"

    # Gets the full material name used on a mesh. This full name corresponds to the full path + filename of the JSON file that corresponds to the effect represented by the material's name.
    # If the mesh does not have a material assigned, it uses as material name the name "base/default"
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

    # Creates material data.
    # If the material is created for the first time, it is loaded from the JSON file containing its data, and the result is cached for future uses.
    # If the material had already been created before, it uses the previously cached result to prevent having to load the file multiple times.
    # This way, multiple disk accesses are prevented when loading the same material / effect multiple times.
    def create_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name not in self.dict_effects:
            self.dict_effects[material_name] = self.generate_effect_data(material_name, fallback_type)

    # Gets the material from the materials dictionary. Used in the make stage.
    # If for some reason the material were to not have been created previously (could only happen if there were some bug in the code that would need to be fixed ASAP),
    # then it would just re-generate the default effect data based on the fallback type. That feature exists as a last measure and we should not rely on it to export working files!!! 
    def get_material(self, material_name, fallback_type = "GEOMETRY"):
        if material_name in self.dict_effects:
            return self.dict_effects[material_name]
        return self.generate_default_effect_data(fallback_type)

    # endregion

    # endregion

    # region Get (Aux methods for Get stage)

    # Returns a list of meshes in the form of a tuple (obj, transform, material_index).
    # Segments a single mesh into multiple meshes based on the indices of the applied materials.
    # This is used because it is easier to just export a new mesh for each material than it is to implement BiTree nodes and multi material XNA models...
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

    # endregion

    # region Generate

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
        mcow_mesh = MagickCowMesh(obj, transform)
        
        # Generate material data
        matname = self.get_material_name(obj, material_index)
        self.create_material(matname, mcow_mesh.mesh.magickcow_mesh_type)

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
        mcow_mesh = MagickCowMesh(obj, transform)
        
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

    # region Make

    # region Make - XNA

    # NOTE : This is obviously NOT the structure of a binary XNB file... this is just the JSON text based way of organizing the data for an XNB file that MagickaPUP uses.
    # This comment is pretty absurd as it states the obvious for myself... I just made it for future readers so that they don't tear the balls out trying to figure out wtf is going on, even tho I think it should be pretty obvious.
    def make_xnb_file(self, primary_object, shared_resources):
        ans = {
            "PrimaryObject" : primary_object,
            "SharedResources" : shared_resources
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

    # This once used to be an useful function... now, it is quite an useless wrapper! :D
    def make_effect(self, matname, fallback_type = "GEOMETRY"):
        material_contents = self.get_material(matname, fallback_type)
        return material_contents

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
class DataGeneratorMap(DataGenerator):

    # region Constructor

    def __init__(self):

        super().__init__()

        self.time_get = 0
        self.time_generate = 0
        self.time_make = 0

        self.objects_get = None
        self.objects_generate = None
        self.objects_make = None

        return
    
    # endregion

    # region Bounding Box Related Operations

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

    # region Public Methods

    # This method returns the final dictionary obtained in the make stage.
    # The method handles the entire process of generating all of the data, rotating the scene, etc...
    def process_scene_data(self):
        
        # Before generating scene data, rotate the scene roots by +90 degrees around the X axis around the world origin <0,0,0> to align with Magicka's Y Up coordinate system.
        # This way, the rest of the code does not need to perform any transformations manually, because it all gets precomputed with a C code level rotation done by Blender's
        # underlying implementation, which is way faster and speeds up the export process by a ton (python is so slow!!! shocker!!! who would have thought???)
        # Note that this rotation will affect the actual objects of the scene, so we must undo it later.
        # Also, if the process ahead fails, the rotation won't get undone, so it would be wise to add a try-catch-finally block, but for now this is good enough.
        self.rotate_scene_old_2(-90)

        # Get Scene Objects (Get Stage)
        # Obtains the references to all of the blender objects in the scene
        time_start = time.time()
        self.dgen_get_scene_data()
        time_end = time.time()
        self.time_get = time_end - time_start
        
        # Generate Scene Data (Generate Stage)
        # Generates objects that contain the data processed and translated from blender's representation to Magicka's representation
        time_start = time.time()
        self.dgen_generate_scene_data()
        time_end = time.time()
        self.time_generate = time_end - time_start

        # Undo the rotation, as the data has already been generated and stored with the correct Y up coordinates.
        # NOTE : this could have some precission errors with certain rotations, so it would be wiser to save the old rotation and restore it rather than undoing the rotation, but it's ok for now.
        # self.rotate_scene_old_2(90)
        
        # Make Scene Data (Make Stage)
        # Make the dictionary objects that will be stored within the final exported JSON file.
        time_start = time.time()
        self.dgen_make_scene_data()
        time_end = time.time()
        self.time_make = time_end - time_start
        
        # TODO : Get the actual answer dictionary...
        ans = self.objects_make
        return ans

    # endregion

    # region Main Entry Points

    # These methods launch the processes that contain the entire logic for each stage of the scene export process.

    # 24/09/2024 @ 18:33 I just fucking realised what the dgen_ prefix sounds like, holly fucking shit, how did I not think of this before??? LOL

    def dgen_get_scene_data(self):
        self.objects_get = self.get_scene_data()
    
    def dgen_generate_scene_data(self):
        self.objects_generate = self.generate_scene_data(self.objects_get)

    def dgen_make_scene_data(self):
        self.objects_make = self.make_scene_data(self.objects_generate, self.make_shared_resources_list(self.dict_shared_resources))

    # endregion
    
    # region "Get Data" / "Find Data" Functions

    # If the parent is an animated level part, then we add the collision to whatever collision channel the parent corresponds to.
    # Otherwise, we add it to the collision channel of the object itself.
    def gsd_add_found_collision(self, found_objects_current, obj, transform, parent):
        collision_index = 0
        if parent is None:
            collision_index = find_collision_material_index(obj.magickcow_collision_material)
        else:
            collision_index = find_collision_material_index(parent.magickcow_collision_material)
        found_objects_current.collisions[collision_index].append((obj, transform))

    # region Comment
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
    def gsd_add_mesh(self, found_objects_list, obj, transform):
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

    def get_scene_data_rec(self, found_objects_global, found_objects_current, objects, parent = None):
        
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
                    self.gsd_add_mesh(found_objects_current.meshes, obj, transform)
                    
                    if obj.magickcow_collision_enabled:
                        self.gsd_add_found_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "COLLISION":
                    self.gsd_add_found_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "WATER":
                    # found_objects_current.waters.append((obj, transform))
                    self.gsd_add_mesh(found_objects_current.waters, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "LAVA":
                    # found_objects_current.lavas.append((obj, transform))
                    self.gsd_add_mesh(found_objects_current.lavas, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "NAV":
                    found_objects_current.nav_meshes.append((obj, transform)) # Nav meshes ignore materials, for now. In the future, they could use it as a reference for the type of navigation offered by an area.
                
                elif obj.data.magickcow_mesh_type == "FORCE_FIELD":
                    # Only add it to the global scope because animated level parts cannot contain force fields.
                    # Allows "malformed" (with a hierarchy that would not be correct in game) scenes to export successfully and work correctly in game.
                    # found_objects_global.force_fields.append((obj, transform))
                    self.gsd_add_mesh(found_objects_global.force_fields, obj, transform)
            
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
                
                found_objects_new = SceneObjectsFound()
                
                self.get_scene_data_rec(found_objects_global, found_objects_new, obj.children, obj)
                
                found_objects_current.animated_parts.append((obj, transform, found_objects_new))
            else:
                self.get_scene_data_rec(found_objects_global, found_objects_current, obj.children, parent)

    def get_scene_data(self):
        
        # Get the root objects from the scene
        root_objects = get_scene_root_objects()
        
        # Create an instance of the found objects class. It will get passed around by the recursive calls to form a tree-like structure, adding the found objects to it and its children.
        found_objects = SceneObjectsFound()
        
        # Call the recursive function and start getting the data.
        self.get_scene_data_rec(found_objects, found_objects, root_objects, None)
        
        return found_objects

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

        return (obj, transform, obj.name, vertices, indices, matname, aabb)

    def generate_animated_mesh_data(self, obj, transform, matid):
        # NOTE : The animated mesh calculation is a bit simpler because it does not require computing the AABB, as it uses an user defined radius for a bounding sphere.

        mesh = obj.data

        # Generate basic mesh data
        vertices, indices, matname = self.generate_mesh_data(obj, transform, True, matid)
        
        # Add the material as a shared resource and get the shared resource index
        idx = self.add_shared_resource(matname, self.get_material(matname, mesh.magickcow_mesh_type))
        
        # Create the matrix that will be passed to the make stage
        matrix = self.generate_matrix_data(transform)
        
        return (obj, transform, obj.name, matrix, vertices, indices, idx)

    # NOTE : For now, both water and lava generation are identical, so they rely on the same generate_liquid_data() function.
    # In the past, they used to have their own identical functions just in case, but I haven't really found any requirements for that yet so yeah...
    # Maybe it could be useful to add some kind of exception throwing or error checking or whatever to prevent players from exporting maps where waters have materials that
    # are not deferred liquid effects and lavas that are not lava effects?
    # NOTE : Liquids do not require any form of bounding box or sphere calculations, so they use the underlying generate_mesh_data() function rather than any of the other wrappers.
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
        light_type = find_light_type_index(light.type)
        
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
    
    # NOTE : Triggers in Magicka start on a corner point, but the representation of an empty is centered around its origin point.
    # To make it easier for users to visualize, we will be translating the data as follows:
    #  - move the trigger's position along each axis by half of the position on that axis, using the forward, right and up vectors of the object to ensure that the translation is correct.
    #  - multiply by 2 the scale of the trigger.
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
        generated_scene_objects.meshes           = self.generate_static_meshes_data(found_scene_objects.meshes)
        generated_scene_objects.waters           = self.generate_static_liquids_data(found_scene_objects.waters)
        generated_scene_objects.lavas            = self.generate_static_liquids_data(found_scene_objects.lavas)
        generated_scene_objects.lights           = self.generate_static_lights_data(found_scene_objects.lights)
        generated_scene_objects.locators         = self.generate_static_locators_data(found_scene_objects.locators)
        generated_scene_objects.triggers         = self.generate_static_triggers_data(found_scene_objects.triggers)
        generated_scene_objects.particles        = self.generate_static_particles_data(found_scene_objects.particles)
        generated_scene_objects.collisions       = self.generate_static_collisions_data(found_scene_objects.collisions)
        generated_scene_objects.nav_mesh         = self.generate_static_nav_meshes_data(found_scene_objects.nav_meshes)
        generated_scene_objects.physics_entities = self.generate_static_physics_entities_data(found_scene_objects.physics_entities)
        generated_scene_objects.force_fields     = self.generate_static_force_fields_data(found_scene_objects.force_fields)
    
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
            generated_child = SceneObjectsGeneratedAnimated()
            self.generate_scene_data_animated_rec(child, generated_child)
            generated_scene_objects.animated_parts.append(generated_child)

    def generate_scene_data_animated(self, found_scene_objects, generated_scene_objects):
        for part in found_scene_objects.animated_parts:
            generated_part = SceneObjectsGeneratedAnimated()
            self.generate_scene_data_animated_rec(part, generated_part)
            generated_scene_objects.animated_parts.append(generated_part)
    
    def generate_scene_data_internal(self, found_scene_objects, generated_scene_objects):
        self.generate_scene_data_static(found_scene_objects, generated_scene_objects)
        self.generate_scene_data_animated(found_scene_objects, generated_scene_objects)
    
    def generate_scene_data(self, found_scene_objects):
        generated_scene_objects = SceneObjectsGeneratedStatic()
        self.generate_scene_data_internal(found_scene_objects, generated_scene_objects)
        return generated_scene_objects
    
    # endregion

    # endregion

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
        obj, transform, name, vertices, indices, matname, aabb = mesh
        primitives = int(len(indices) / 3) # Magicka's primitives are always triangles, and the mesh was triangulated, so this calculation is assumed to always be correct.
        ans = {
            "isVisible" : True,
            "castsShadows" : True,
            "sway" : 0,
            "entityInfluence" : 0,
            "groundLevel" : -10,
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
            "collisionDataCamera" : self.make_collision((False, [], [])), # For now, hard code no collision data for camera collision. Or whatever the fuck this truly is...
            "numTriggers" : len(triggers),
            "triggers" : triggers,
            "numLocators" : len(locators),
            "locators" : locators,
            "navMesh" : nav_mesh
        }
        return ans

    # endregion

    def make_scene_data(self, generated_scene_data, shared_resources_list):
        ans = self.make_xnb_file(self.make_level_model(generated_scene_data), shared_resources_list)
        return ans

    # endregion

# region Comment - DataGeneratorPhysicsEntity
    # This data generator class is dedicated toward generating the data for physics entities.
    # The export process is pretty different from that of map scenes, but it also has multiple similarities.
    # One of the similarities is that physics entities contain an XNB model class within it, which means that the animated level part side of the code is pretty much almost identical to what this class requires.
# endregion
class DataGeneratorPhysicsEntity(DataGenerator):

    # region Constructor

    def __init__(self):
        super().__init__()
        return
    
    # endregion

    # region Process Scene Data

    # TODO : Implement
    def process_scene_data(self):
        # Get
        get_stage_physics_entity = self.get()

        # Generate
        generate_stage_physics_entity = self.generate(get_stage_physics_entity)

        # Make
        make_stage_physics_entity = self.make(generate_stage_physics_entity, self.dict_shared_resources)

        return make_stage_physics_entity

    # endregion

    # region Get Stage

    def get(self):
        return self.get_scene_data()

    def get_scene_data(self):

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
        self.get_scene_data_rec(found_objects, root_objects[0].children, 0)
        
        return found_objects
    
    def get_scene_data_rec(self, found_objects, current_objects, parent_bone_index):
        
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
                    self.get_scene_data_add_mesh(found_objects, obj, transform, parent_bone_index) # TODO : Implement relative transform calculations
                
                # Process meshes for collision geometry
                elif mesh_type == "COLLISION":
                    found_objects.collisions.append(obj)
            
            # Process objects of type empty, which should be roots and bones
            elif obj.type == "EMPTY":
                
                # Process empties for bones
                if obj.mcow_physics_entity_empty_type == "BONE":
                    
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
                    self.get_scene_data_rec(found_objects, obj.children, current_bone.index) # NOTE : The index we pass is literally the index of the bone we just added to the found objects' bones list.

                # Process empties for bounding boxes
                elif obj.mcow_physics_entity_empty_type == "BOUNDING_BOX":
                    # Add the found bounding box
                    found_objects.boxes.append(obj)


            # NOTE : We ignore objects of any type other than empties and meshes when getting objects to be processed for physics entity generation.
            # No need for an else case because we do nothing else within the loop.

    def get_scene_data_add_mesh(self, found_objects, obj, transform, parent_bone_index):
        segments = self.get_mesh_segments(obj)
        ans = [(segment_obj, transform, material_index, parent_bone_index) for segment_obj, material_index in segments]
        found_objects.model.meshes.extend(ans)

    # endregion

    # region Generate Stage

    def generate(self, found_objects):
        # TODO : Implement everything else
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
        shared_resource_index = self.add_shared_resource(matname, self.get_material(matname))
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

    # region Make Stage

    def make(self, generated_scene_data, shared_resources_data):
        return self.make_xnb_file(self.make_physics_entity(generated_scene_data), self.make_shared_resources_list(shared_resources_data))

    def make_physics_entity(self, generated_data): # TODO : Add parameters
        # TODO : Implement literally everything
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
            "numBones" : len(bones),
            "bones" : self.make_model_bones(bones),
            "numVertexDeclarations" : 1,
            "vertexDeclarations" : self.make_vertex_declaration_default(),
            "numModelMeshes" : len(meshes),
            "modelMeshes" : self.make_model_meshes(meshes)
        }
        return ans
    
    def make_model_bones(self, bones):
        ans = [self.make_model_bone(bone) for bone in bones]
        return ans
    
    def make_model_bone(self, bone):
        ans = {
            "index" : bone.index,
            "name" : bone.name,
            "transform" : self.make_matrix(bone.transform),
            "parent" : bone.parent,
            "children" : bone.children
        }
        return ans

    def make_model_meshes(self, meshes):
        ans = [self.make_model_mesh(mesh) for mesh in meshes]
        return ans
    
    def make_model_mesh(self, mesh):
        name, parent_bone_index, vertices, indices, shared_resource_index = mesh
        ans = {
            "name" : name,
            "parentBone" : parent_bone_index,
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
            "meshParts" : {
                "streamOffset" : 0,
                "baseVertex" : 0,
                "numVertices" : len(vertices),
                "startIndex" : 0,
                "primitiveCount" : len(vertices) / 3,
                "vertexDeclarationIndex" : 0,
                "tag" : None, # Always null in Magicka...,
                "sharedResourceIndex" : shared_resource_index
            }
        }
        return ans

    # endregion
    

# endregion

# region Blender Operator classes for JSON Exporter.

# This class is the exporter operator for all types of files that can be generated by MagickCow.
# NOTE : In the past, we used to have a different export operator for each type of object. Now, they all contain their code within this operator, since the export type is selected on the scene panel.
# We still separate the logic in different methods tho, that way things are easier to deal with, but we only have 1 single exporter operator class rather than multiple classes.
class MagickCowExporterOperator(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    
    # region Blender specific configuration:
    
    bl_idname = "object.magickcow_map"
    bl_label = "MagickCow Export Map"
    bl_description = "MagickCow Export Map to JSON file"
    filename_ext = ".json"

    # endregion
    
    # region Exporter Panel Config

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
        except MagickCowExportException as e:
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

    def export_data_physics_entity(self, context):
        return self.export_data_func(context, "Physics Entity", DataGeneratorPhysicsEntity())

    def export_data_map(self, context):
        return self.export_data_func(context, "Map", DataGeneratorMap())
    
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

# region Blender Operator classes for N-Key Panel

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
        
        if obj.data.magickcow_mesh_type == "GEOMETRY":
            self.draw_mesh_geometry(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        elif obj.data.magickcow_mesh_type in ["WATER", "LAVA"]:
            self.draw_mesh_liquid(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        elif obj.data.magickcow_mesh_type == "COLLISION":
            self.draw_mesh_collision(layout, obj)
        elif obj.data.magickcow_mesh_type == "FORCE_FIELD":
            self.draw_mesh_force_field(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        return
    
    def draw_mesh_geometry(self, layout, obj):
        layout.prop(obj, "magickcow_collision_enabled")
        if(obj.magickcow_collision_enabled):
            layout.prop(obj, "magickcow_collision_material") # 1
    
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

# region Blender Operator classes for Scene Panel

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


# endregion

# region Register functions

def register_properties_classes():
    # Resistances
    bpy.utils.register_class(MagickCowProperty_Resistance)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

    # Gibs
    bpy.utils.register_class(MagickCowProperty_Gib)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

def unregister_properties_classes():
    # Resistances
    bpy.utils.unregister_class(MagickCowProperty_Resistance)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

    # Gibs
    bpy.utils.unregister_class(MagickCowProperty_Gib)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

# endregion

# endregion

# region Blender Object Properties Register, Unregister and Update

# region Object Properties - Map / Level

# NOTE : The name of these parameters is important, as Blender internally calls them using "self = ..." and "context = ...".
# If the names are different, the function will not properly allow objects to be modified.
def update_properties_map_empty(self, context):
    
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
            self.show_name = True
                
        elif self.magickcow_empty_type == "TRIGGER":
            self.empty_display_type = "CUBE"
            self.show_name = True
        
        elif self.magickcow_empty_type == "PARTICLE":
            self.empty_display_type = "SPHERE"
            self.show_name = False
        
        elif self.magickcow_empty_type == "BONE":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = True
        
        elif self.magickcow_empty_type == "PHYSICS_ENTITY":
            self.empty_display_type = "ARROWS"
            self.show_name = False

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

def register_properties_map_mesh():
    mesh = bpy.types.Mesh
    
    # region Object type for mesh objects:
    
    mesh.magickcow_mesh_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object",
        items = [
            ("GEOMETRY", "Geometry", "This object will be exported as a piece of level geometry"),
            ("COLLISION", "Collision", "This object will be exported as a piece of level collision"),
            ("WATER", "Water", "This object will be exported as a liquid of type \"Water\""),
            ("LAVA", "Lava", "This object will be exported as a liquid of type \"Lava\""),
            ("NAV", "Nav", "This object will be exported as a nav mesh"),
            ("FORCE_FIELD", "Force Field", "This object will be exported as a force field")
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

def register_properties_map_light():
    light = bpy.types.Light

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
        default = 5.0
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
        size = 3 # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
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
        default = 1.0
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
        description = "Determine whether the light should cast shadows or not",
        default = True
    )

def unregister_properties_map_light():
    light = bpy.types.Light
    
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
            self.show_name = True
        
        elif self.mcow_physics_entity_empty_type == "ROOT":
            self.empty_display_type = "SPHERE"
            self.show_name = False
        
        elif self.mcow_physics_entity_empty_type == "BOUNDING_BOX":
            self.empty_display_type = "CUBE"
            self.show_name = True

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

# region Blender Export Panel functions, Register and Unregister functions

def menu_func(self, context):
    self.layout.operator(MagickCowExporterOperator.bl_idname, text = "Export Scene to MagickaPUP JSON file (.json)")

def register_exporters():
    bpy.utils.register_class(MagickCowExporterOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister_exporters():
    bpy.utils.unregister_class(MagickCowExporterOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

# endregion

# region Blender Scene Panel functions, Register and Unregister functions

def update_properties_scene_empty(self, context):
    # NOTE : This is an aux function whose purpose is to restore all of the empties to their saved state
    self.show_name = self.magickcow_empty_original_setting_display_name
    self.empty_display_type = self.magickcow_empty_original_setting_display_type

def update_properties_scene(self, context):
    
    # NOTE : The "self" parameter is simply ignored in this case, we just want to iterate over all of the objects of type empty in the scene and call their respective update methods.
    if context.scene.mcow_scene_mode == "MAP":
        fn = update_properties_map_empty
    
    elif context.scene.mcow_scene_mode == "PHYSICS_ENTITY":
        fn = update_properties_physics_entity_empty
    
    else:
        fn = update_properties_scene_empty
    
    empties = [obj for obj in bpy.data.objects if obj.type == "EMPTY"]
    for empty in empties:
        fn(empty, context)

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

    # Register the scene panel itself
    bpy.utils.register_class(MagickCowScenePanel)

def unregister_properties_scene():
    
    # Unregister properties for the scene panel
    del bpy.types.Scene.mcow_scene_mode
    del bpy.types.Scene.mcow_scene_json_pretty
    del bpy.types.Scene.mcow_scene_json_indent
    del bpy.types.Scene.mcow_scene_base_path
    del bpy.types.Scene.mcow_scene_animation

    # Unregister the scene panel
    bpy.utils.unregister_class(MagickCowScenePanel)

# endregion

# region Main Addon Entry Point

def register():
    # Register custom property classes
    register_properties_classes()

    # Register the Export Panel
    register_exporters()

    # Register the Object Properties and Object Properties Panel
    register_properties_object()

    # Register the Scene Properties and Scene Properties Panel
    register_properties_scene()

def unregister():
    # Register custom property classes
    unregister_properties_classes()

    # Unregister the Export Panel
    unregister_exporters()

    # Unregister the Object Properties and Object Properties Panel
    unregister_properties_object()

    # Unregister the Scene Properties and Scene Properties Panel
    unregister_properties_scene()

if __name__ == "__main__":
    register()

# endregion
