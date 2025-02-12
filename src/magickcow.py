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

