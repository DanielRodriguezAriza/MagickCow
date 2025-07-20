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

def get_all_objects_in_view_layer():
    objs = bpy.context.view_layer.objects
    return objs

def get_scene_root_objects():
    objs = get_all_objects_in_view_layer()
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
