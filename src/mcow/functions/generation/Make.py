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
