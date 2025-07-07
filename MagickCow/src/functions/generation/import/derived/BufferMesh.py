# region Import Pipeline - Buffer Mesh

# NOTE : This region refers to functions required for importing "buffer meshes", aka, meshes constructed from a vertex buffer and an index buffer.

# region Comment - mcow_import_buffer_mesh()

# This function reads the data of an input vertex buffer and index buffer and generates an object according to the input data.
# The generated object and data block are returned.

# endregion
def mcow_import_buffer_mesh(name, vertex_stride, vertex_declaration, vertex_buffer, index_buffer):
    # Read the vertex and index buffer data
    mesh_vertices, mesh_triangles, mesh_normals = mcow_read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

    # Create mesh data and mesh object
    mesh = bpy.data.meshes.new(name = name)
    obj = bpy.data.objects.new(name = name, object_data = mesh)

    # Link the object to the scene
    bpy.context.collection.objects.link(obj)

    # Generate the mesh data from the vertex buffer and index buffer
    mesh.from_pydata(mesh_vertices, [], mesh_triangles)
    mesh.update()

    # Select the object so that we can use bpy.ops over this mesh
    obj.select_set(state=True)
    bpy.context.view_layer.objects.active = obj

    # Apply smooth shading to get some default normal groups going
    bpy.ops.object.shade_smooth()

    # region Unused Content

    # Set the vertex normals from the imported data
    # Option 1: Calculate loop normals
    # loop_normals = []
    # for poly in mesh.polygons:
    #     for loop_index in poly.loop_indices:
    #         vertex_index = mesh.loops[loop_index].vertex_index
    #         loop_normals.append(mesh_normals[vertex_index].normalized())
    # mesh.normals_split_custom_set(loop_normals)
    # mesh.update()
    # Option 2: Use the per-vertex normals directly
    # mesh.normals_split_custom_set_from_vertices(mesh_normals)
    # mesh.update()
    # NOTE : This code is disabled for now, since after today's Blender update, importing normals is pretty much broken AFAIK and will lead to geometry that simply crashes on edit.
    # I guess we'll just have to wait for them to patch this out and get their shit together before we can use custom normals...
    # For now, the split faces generate some pretty nice normals automatically, so I guess we'll live with those for now and that's it...

    # Flip the normals so that their direction matches the one expected by Blender
    # bpy.ops.object.mode_set(mode="EDIT")
    # bpy.ops.mesh.flip_normals()
    # bpy.ops.object.mode_set(mode="OBJECT")
    # NOTE : This code is disabled for now, because since 4.2, flipping normals crashes the editor, so we can't fix this either unless I manually flip them myself on import!!!
    # WOW BLENDER IS SO GOOD!!!!

    # endregion

    # Return the generated object and mesh data block
    return obj, mesh

# region Comment - mcow_read_buffer_data()

# This function allows reading the data of an input vertex buffer and index buffer, using a vertex declaration and specifying a custom vertex stride.
# The function returns buffers converted into a format that Blender understands.

# TODO : Fix the fact that the imported mesh has inverted normals!
# TODO : Find a way to handle input buffers that have more than one property on a given type... read up how D3D handles that and copy that behaviour.
# Can probably be fixed either by changing the winding order or adding normal data parsing.

# endregion
def mcow_read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer):

    vertex_buffer_internal = vertex_buffer["Buffer"]
    index_buffer_internal = index_buffer["data"]

    # Output variables
    # This function will generate a vertex buffer and an index buffer in a pydata format that Blender can understand through its Python API to generate a new mesh data block.
    vertices = []
    indices = [index_buffer_internal[i:i+3] for i in range(0, len(index_buffer_internal), 3)] # This one is actually pretty fucking trivial, because it is already in a format that is 1:1 for what we require lol... all we have to do, is split the buffer into a list of sublists, where every sublist contains 3 elements, which are the indices of each triangle. Whether the input XNA index buffer has an index size that is 16 bit or 32 bit does not matter, since the numbers on the JSON text documented are already translated to whatever the width of Python's integers is anyway, so no need to handle that.
    normals = []

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

    return vertices, indices, normals

# endregion
