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

    def read_collision_mesh(self, collision):
        has_collision = collision["hasCollision"]
        
        if not has_collision:
            return (False, [], [])
        
        json_vertices = collision["vertices"]
        json_triangles = collision["triangles"]

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
            
            else:
                raise MagickCowImportException(f"Unknown material effect type : \"{effect_type}\"")
        
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

    # endregion

# endregion
