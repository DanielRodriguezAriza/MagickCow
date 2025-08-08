# region Import Data Pipeline class - Base class

class MCow_ImportPipeline:
    def __init__(self):
        self._cached_import_path = ""
        self._cached_textures = {}
        return
    
    def exec(self, data, path):
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
    # TODO : Find a way to handle input buffers that have more than one property on a given type... read up how D3D handles that and copy that behaviour.
    # Can probably be fixed either by changing the winding order or adding normal data parsing.
    def read_mesh_buffer_data(self, vertex_stride, vertex_declaration, vertex_buffer, index_buffer):

        vertex_buffer_internal = vertex_buffer["Buffer"]
        index_buffer_internal = index_buffer["data"]

        # Output variables
        # This function will generate a vertex buffer and an index buffer in a pydata format that Blender can understand through its Python API to generate a new mesh data block.
        vertices = []
        indices = [index_buffer_internal[i:i+3] for i in range(0, len(index_buffer_internal), 3)] # This one is actually pretty fucking trivial, because it is already in a format that is 1:1 for what we require lol... all we have to do, is split the buffer into a list of sublists, where every sublist contains 3 elements, which are the indices of each triangle. Whether the input XNA index buffer has an index size that is 16 bit or 32 bit does not matter, since the numbers on the JSON text documented are already translated to whatever the width of Python's integers is anyway, so no need to handle that.
        normals = []
        uvs = []

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
                chunk = buffer[(offset + vertex_offset_position) : (offset + vertex_offset_position + 12)] # The 12 comes from 3 * 4 = 12 bytes, because we read 3 floats for the vertex position.
                data = struct.unpack("<fff", chunk) # NOTE : As of now, we're always assuming that vertex position is in the format vec3. In the future, when we add support for other formats (if required), then make it so that we have a vertex_attribute_fmt variable or whatever, and assign it above, when we read the attributes' description / vertex layout on the vertex declaration parsing part of the code.
                vertices.append(point_to_z_up(data))

        # If the input vertex data has a normal attribute for each vertex, then read it.
        if vertex_offset_normal >= 0:
            for offset in range(0, len(vertex_buffer_internal), vertex_stride):
                chunk = buffer[(offset + vertex_offset_normal) : (offset + vertex_offset_normal + 12)] # 3 f32 * 4 bytes = 12 bytes
                data = struct.unpack("<fff", chunk)
                normals.append(point_to_z_up(data))

        # If the input vertex has an UV attribute for each vertex, then read it.
        if vertex_offset_uv >= 0:
            for offset in range(0, len(vertex_buffer_internal), vertex_stride):
                chunk = buffer[(offset + vertex_offset_uv) : (offset + vertex_offset_uv + (2 * 4))] # 2 f32 for UVs
                data = struct.unpack("<ff", chunk)
                uvs.append(uv_to_z_up(data))

        # Return a tuple with all the extracted mesh data.
        return vertices, indices, normals, uvs

    # endregion

    # region Read Methods - Collision Mesh

    def read_collision_mesh(self, has_collision, json_vertices, json_triangles):
        
        # If the collision is set to false, then we have no collision.
        # If the collision is set to true but we have 0 collision vertices, then we don't have collision either.
        if not has_collision or len(json_vertices) <= 0:
            return (False, [], [])

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["index0"], tri["index1"], tri["index2"]) for tri in json_triangles]

        return (True, mesh_vertices, mesh_triangles)

    # endregion

    # region Read Methods - Materials

    def read_effect(self, name, effect):
        mat = bpy.data.materials.new(name = name)
        mat.use_nodes = True

        effect_type = None
        effect_reader = None
        effect_generator = None

        if "$type" in effect:
            effect_type_json = effect["$type"]
            if effect_type_json == "effect_deferred":
                effect_type = "EFFECT_DEFERRED"
                effect_reader = self.read_effect_deferred
                effect_generator = self.generate_effect_deferred
            
            elif effect_type_json == "effect_deferred_liquid":
                effect_type = "EFFECT_LIQUID_WATER"
                effect_reader = self.read_effect_liquid_water
                effect_generator = None
            
            elif effect_type_json == "effect_lava":
                effect_type = "EFFECT_LIQUID_LAVA"
                effect_reader = self.read_effect_liquid_lava
                effect_generator = None
            
            elif effect_type_json == "effect_additive":
                effect_type = "EFFECT_ADDITIVE"
                effect_reader = self.read_effect_additive
                effect_generator = None
            
            else:
                raise MagickCowImportException(f"Unknown material effect type : \"{effect_type_json}\"")
        
        elif "vertices" in effect and "indices" in effect and "declaration" in effect:
            effect_type = "EFFECT_FORCE_FIELD"
            effect_reader = self.read_effect_force_field
        
        else:
            raise MagickCowImportException("The input data does not contain a valid material effect")

        # Assign the values and execute the selected functions
        if effect_type is not None:
            mat.mcow_effect_type = effect_type
        if effect_reader is not None:
            effect_reader(mat, effect)
        if bpy.context.scene.mcow_scene_import_textures and effect_generator is not None:
            effect_generator(mat, effect) # Only generate material nodes in the event that texture import is enabled. Note that this needs to be cleaned up in the future for more complex support. This is kind of a hacky workaround, mostly due to the meaning the weird nomenclature used gives to this...

        return mat

    def create_effect_material_node_texture(self, nodes, location, texture_data):
        # Create the texture node and return it so that the caller can use it and link it up
        texture_node = nodes.new(type="ShaderNodeTexImage")
        texture_node.location = location
        texture_node.image = texture_data
        return texture_node

    def texture_load(self, texture_path_relative):
        
        # Compute the absolute path
        texture_path_absolute = path_join(path_get_str_directory(self._cached_import_path), texture_path_relative)
        
        # If the texture is already cached, then return it
        if texture_path_absolute in self._cached_textures:
            return self._cached_textures[texture_path_absolute]
        
        # If the texture is not already cached, then we try to load it and cache it
        
        # Get all matching texture files
        matching_texture_files = path_match_files(texture_path_absolute)
        
        # If no matches were found, then cache "None", since that means that the file was not found this time around
        if len(matching_texture_files) <= 0:
            self._cached_textures[texture_path_absolute] = None
            return None
        
        # If matches were found, then pick the first one and use it
        chosen_texture_file = matching_texture_files[0]

        # Cache the chosen texture file and return the generated texture data
        texture_data = bpy.data.images.load(chosen_texture_file)
        self._cached_textures[texture_path_absolute] = texture_data
        return texture_data

    def create_effect_material_nodes_effect_deferred(self, material, color0, diffuse0, normal0, color1, diffuse1, normal1):
        # Get nodes and links
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear out the default nodes from the node graph (we could skip this step, but just in case)
        nodes.clear()

        # Basic BSDF material setup:
        
        # 1) Material Output Node:
        output_node = nodes.new(type = "ShaderNodeOutputMaterial")
        output_node.location = (400, 0)
        
        # 2) Principled BSDF Node:
        bsdf_node = nodes.new(type = "ShaderNodeBsdfPrincipled")
        bsdf_node.location = (0, 0)

        # 3) Link BSDF node to output node
        links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        # 4) Create the rest of the nodes

        # color0

        # Node Diffuse 0
        diffuse0_data = self.texture_load(diffuse0)
        diffuse0_node = nodes.new(type="ShaderNodeTexImage")
        diffuse0_node.location = (-1668, 1336)
        diffuse0_node.width = 240
        diffuse0_node.height = 100
        diffuse0_node.label = "Diffuse0"
        diffuse0_node.image = diffuse0_data

        # Node Normal 0
        normal0_data = self.texture_load(normal0)
        normal0_node = nodes.new(type="ShaderNodeTexImage")
        normal0_node.location = (-1668, 1054)
        normal0_node.width = 240
        normal0_node.height = 100
        normal0_node.label = "Normal0"
        normal0_node.image = normal0_data

        # Node Diffuse 1
        diffuse1_data = self.texture_load(diffuse1)
        diffuse1_node = nodes.new(type="ShaderNodeTexImage")
        diffuse1_node.location = (-1622, 637)
        diffuse1_node.width = 240
        diffuse1_node.height = 100
        diffuse1_node.label = "Diffuse1"
        diffuse1_node.image = diffuse1_data

        # Node Normal 1
        normal1_data = self.texture_load(normal1)
        normal1_node = nodes.new(type="ShaderNodeTexImage")
        normal1_node.location = (-1619, 355)
        normal1_node.width = 240
        normal1_node.height = 100
        normal1_node.label = "Normal1"
        normal1_node.image = normal1_data

        # Node Color 0
        mulcolor0_node = nodes.new(type="ShaderNodeMix")
        mulcolor0_node.location = (-1333, 1465)
        mulcolor0_node.width = 140
        mulcolor0_node.height = 100
        mulcolor0_node.label = "MulColor0"
        node.data_type = "RGBA"
        node.blend_type = "MULTIPLY"
        mulcolor0_node.inputs[7].default_value = color0

        # Diffuse Texture 0
        diffuse0_data = self.texture_load(diffuse0)
        if texture_data_diffuse is not None:
            texture_diffuse_node = self.create_effect_material_node_texture(nodes, (-200, -200), texture_data_diffuse)
            links.new(texture_diffuse_node.outputs["Color"], bsdf_node.inputs["Base Color"])
            links.new(texture_diffuse_node.outputs["Alpha"], bsdf_node.inputs["Alpha"]) # Yes, Magicka stores the alpha channel within the diffuse texture itself.

        # 5) Link up the nodes

        # fas




        # All of this stuff doesn't really matter, it's just for visualization and stuff...
        # Although in the future we COULD modify it so that we reference these nodes for the actual values during export.
        # idk, maybe the visualization being synced up with custom mats should just be the user's responsibility... but we'll see about that in the future when the time comes.

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

    def generate_effect_deferred(self, material, effect):
        # Get relevant properties
        diffuse0 = effect["DiffuseTexture0"]
        diffuse1 = effect["DiffuseTexture1"]
        normal0 = effect["NormalTexture0"]
        normal1 = effect["NormalTexture1"]
        color0 = self.read_color_rgb(effect["DiffuseColor0"])
        color1 = self.read_color_rgb(effect["DiffuseColor1"])

        # Generate the material nodes themselves
        self.create_effect_material_nodes_effect_deferred(material, color0, diffuse0, normal0, color1, diffuse1, normal1)

    # endregion

# endregion
