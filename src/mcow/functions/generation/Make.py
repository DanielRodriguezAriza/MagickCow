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
            "numBones" : len(bones),
            "bones" : self.make_model_bones(bones),
            "numVertexDeclarations" : 1,
            "vertexDeclarations" : [self.make_vertex_declaration_default()],
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
