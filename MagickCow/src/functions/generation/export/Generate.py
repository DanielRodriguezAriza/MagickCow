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
            has_vertex_color = True
        else:
            color_default = (0.0, 0.0, 0.0, 0.0) if mcow_mesh.mesh.magickcow_mesh_type in ["WATER", "LAVA"] else (1.0, 1.0, 1.0, 0.0) # TODO : Get rid of this retarded logic in the future maybe...
            color_layer = None # LOL
            has_vertex_color = False

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
                position = mathutils.Vector((position[0], position[1], position[2]))

                normal = mcow_mesh.invtrans @ loop.normal
                normal = mathutils.Vector((normal[0], normal[1], normal[2])).normalized()

                tangent = mcow_mesh.invtrans @ loop.tangent
                tangent = mathutils.Vector((tangent[0], tangent[1], tangent[2])).normalized()

                binormal = normal.cross(tangent)
                binormal = binormal.normalized()

                uv = mcow_mesh.mesh.uv_layers.active.data[loop_idx].uv
                uv = self.generate_uv(uv)
                
                if has_vertex_color:
                    color = color_layer.data[loop_idx].color
                    color = (color[0], color[1], color[2], color[3])
                else:
                    color = color_default

                # NOTE : Perhaps we could do the processing AFTER we isolate what unique vertices exist?

                vertex = (global_vertex_index, position, normal, tangent, uv, color, binormal)

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

        return (vertices, indices, matname, has_vertex_color) # NOTE : In the future, maybe pass a vertex_info struct which contains information about whether we have a position, normal, tangent, color, uvs, etc... but for now, all meshes will have everything except for color, which only those with a color layer will have.

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
        vertices, indices, matname, has_color = self.generate_mesh_data(obj, transform, True, matid)

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

        return (obj, transform, obj.name, vertices, indices, matname, has_color, aabb, sway, entity_influence, ground_level)

    def generate_animated_mesh_data(self, obj, transform, matid):
        # NOTE : The animated mesh calculation is a bit simpler because it does not require computing the AABB, as it uses an user defined radius for a bounding sphere.

        mesh = obj.data

        # Generate basic mesh data
        vertices, indices, matname, has_color = self.generate_mesh_data(obj, transform, True, matid)
        
        # Add the material as a shared resource and get the shared resource index
        idx = self.cache.add_shared_resource(matname, self.cache.get_material(matname, mesh.magickcow_mesh_type))
        
        # Create the matrix that will be passed to the make stage
        matrix = self.generate_matrix_data(transform)
        
        return (obj, transform, obj.name, matrix, vertices, indices, has_color, idx)

    # region Comment - generate_liquid_data
    
    # NOTE : For now, both water and lava generation are identical, so they rely on the same generate_liquid_data() function.
    # In the past, they used to have their own identical functions just in case, but I haven't really found any requirements for that yet so yeah...
    # Maybe it could be useful to add some kind of exception throwing or error checking or whatever to prevent players from exporting maps where waters have materials that
    # are not deferred liquid effects and lavas that are not lava effects?
    # NOTE : Liquids do not require any form of bounding box or sphere calculations, so they use the underlying generate_mesh_data() function rather than any of the other wrappers.
    
    # endregion
    def generate_liquid_data(self, obj, transform, matid):
        
        # Generate the mesh data (vertex buffer, index buffer and effect / material)
        vertices, indices, matname, has_color = self.generate_mesh_data(obj, transform, True, matid)
        
        # Get Liquid Water / Lava config
        can_drown = obj.data.magickcow_mesh_can_drown
        freezable = obj.data.magickcow_mesh_freezable
        autofreeze = obj.data.magickcow_mesh_autofreeze
        
        return (vertices, indices, matname, has_color, can_drown, freezable, autofreeze)

    def generate_force_field_data(self, obj, transform, matid):
        # Generate the mesh data (vertex buffer, index buffer and effect / material, altough the material is ignored in this case)
        vertices, indices, matname, has_color = self.generate_mesh_data(obj, transform, True, matid)
        return (vertices, indices, matname, has_color)

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
        vertices, indices, matname, has_color = self.generate_mesh_data(obj, transform, True, matid)
        shared_resource_index = self.cache.add_shared_resource(matname, self.cache.get_material(matname))
        return (name, parent_bone_index, vertices, indices, has_color, shared_resource_index)

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
