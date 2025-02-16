# region Make Stage

# This section contains classes whose purpose is to define the logic of the Make Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Maker class.
class MCow_Data_Maker:
    def __init__(self):
        return
    
    def make(self):
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

    # This once used to be an useful function... now, it is quite an useless wrapper! :D
    def make_effect(self, matname, fallback_type = "GEOMETRY"):
        material_contents = self.get_material(matname, fallback_type)
        return material_contents

    # endregion

# Data Maker class for Maps / Levels
class MCow_Data_Maker_Map(MCow_Data_Maker):
    def __init__(self):
        super().__init__()
        return
    
    def make(self, make_data):
        # TODO : Implement
        ans = {}
        return ans

# Data Maker class for Physics entities
class MCow_Data_Maker_PhysicsEntity(MCow_Data_Maker):
    def __init__(self):
        super().__init__()
        return

    def make(self, make_data):
        generated_scene_data, shared_resources_data = make_data
        return self.make_xnb_file(self.make_physics_entity(generated_scene_data), self.make_shared_resources_list(shared_resources_data))

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
