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

    def read_mesh_buffer_data(self, vertex_declaration, vertex_buffer, index_buffer):

        vertices = []
        indices = []

        # NOTE : If any of these offset values is negative, then that means that the value was not found, so we cannot add that information to our newly generated Blender mesh data.
        vertex_offset_position = -1
        vertex_offset_normal = -1
        vertex_offset_tangent = -1
        vertex_offset_color = -1

        vertex_declaration_entries = vertex_declaration["entries"]
        for idx, entry in enumerate(vertex_declaration_entries):
            # NOTE : Commented out lines are data from the entry that we do not need to compose a mesh in Blender / that we do not use yet.
            # stream = entry["stream"]
            offset = entry["offset"]
            element_format = entry["elementFormat"]
            # element_method = entry["elementMethod"]
            element_usage = entry["elementUsage"]
            # usage_index = entry["usageIndex"]
            
            # Offset - Position
            if element_usage == 0:
                vertex_offset_position = offset
            
            # Offset - Normal
            elif element_usage == 3:
                vertex_offset_normal = offset
            
            # Offset - Tangent
            elif element_usage == 6:
                vertex_offset_tangent = offset
            
            # Offset - Color
            elif element_usage == 10:
                vertex_offset_color = offset


        

        return vertices, indices

# endregion
