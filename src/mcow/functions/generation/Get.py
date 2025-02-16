# region Get Stage

# This section contains classes whose purpose is to define the logic of the Get Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Getter class.
class MCow_Data_Getter:
    def __init__(self):
        return
    
    def get(self):
        return None # Return an empty object by default since the base class does not implement the data getting for any specific class.

# Data Getter class for Maps / Levels
class MCow_Data_Getter_Map(MCow_Data_Getter):
    def __init__(self):
        super().__init__()
        return
    
    def get(self):
        # TODO : Implement
        return None

# Data Getter class for Physics entities
class MCow_Data_Getter_PhysicsEntity(MCow_Data_Getter):
    def __init__(self):
        super().__init__()
        return
    
    def get(self):
        return self._get_scene_data()

    def _get_scene_data(self):

        # NOTE : We have to make sure that we only have 1 single object of type "ROOT" in the scene, and that it is also a root within the scene. All other root objects that are not of type "ROOT" will be ignored.
        # Objects of type "ROOT" within the tree hierarchy but that are not true roots will trigger an error.

        # NOTE : For now, we only handle exporting 1 single physics entity object per physics entity scene.

        # Get all of the objects in the scene that are of type "ROOT"
        all_objects_of_type_root = [obj for obj in bpy.data.objects if (obj.type == "EMPTY" and obj.mcow_physics_entity_empty_type == "ROOT")]
        if len(all_objects_of_type_root) != 1:
            raise MagickCowExportException("Physics Entity Scene must contain exactly 1 Root!")

        # Get all of the objects in the scene that are roots (have no parent) and are of type "ROOT"
        root_objects = [obj for obj in bpy.data.objects if (obj.parent is None and obj.type == "EMPTY" and obj.mcow_physics_entity_empty_type == "ROOT")]
        if len(root_objects) != 1:
            raise MagickCowExportException("Physics Entity Scene Root object must be at the root of the scene!")

        # Get the objects in the scene and form a tree-like structure for exporting.
        found_objects = Storage_PhysicsEntity()
        found_objects.root = root_objects[0]
        
        scene_root_bone = PE_Storage_Bone()
        scene_root_bone.obj = found_objects.root
        scene_root_bone.transform = found_objects.root.matrix_world
        scene_root_bone.index = 0
        scene_root_bone.parent = -1
        scene_root_bone.children = []

        found_objects.model.bones.append(scene_root_bone) # The root object will act as a bone for us when exporting the mesh. We add a list with element -1 because that is how we signal that there are no parent bones for the root bone.
        self.get_scene_data_rec(found_objects, root_objects[0].children, 0)
        
        return found_objects
    
    def _get_scene_data_rec(self, found_objects, current_objects, parent_bone_index):
        
        for obj in current_objects:

            # Ignore objects that are marked as no export. This also excludes all children from the export process.
            if not obj.magickcow_allow_export:
                continue
            
            # Calculate the transform for this object, relative to what is considered its parent in the Magicka tree structure
            if parent_bone_index < 0:
                transform = get_object_transform(obj, None)
            else:
                transform = get_object_transform(obj, found_objects.model.bones[parent_bone_index].obj)

            # Process objects of type mesh, which should be visual geometry meshes and collision meshes
            if obj.type == "MESH":
                mesh = obj.data
                mesh_type = mesh.mcow_physics_entity_mesh_type

                # Process meshes for visual geometry
                if mesh_type == "GEOMETRY":
                    self._get_scene_data_add_mesh(found_objects, obj, transform, parent_bone_index) # TODO : Implement relative transform calculations
                
                # Process meshes for collision geometry
                elif mesh_type == "COLLISION":
                    found_objects.collisions.append(obj)
            
            # Process objects of type empty, which should be roots and bones
            elif obj.type == "EMPTY":
                
                # Process empties for bones
                if obj.mcow_physics_entity_empty_type == "BONE":
                    
                    # Throw an exception if the found bone has a name that is reserved
                    reserved_bone_names = ["Root", "RootNode"]
                    bone_name_lower = obj.name.lower()
                    for name in reserved_bone_names: # NOTE : We could have used "if bone_name_lower in reserved_bone_names:" instead, but I would prefer to keep the reserved strings just as they are stored within the XNB file rather than hardcoding them in full lowercase. This is because I don't exactly remember as of now whether XNA checks for exact bone names or if it is not case sensitive. I'd need to check again, but whatever. Also, these reserved bone names are not because of XNA, they are just present in ALL physics entity files within Magicka's base game data, so it's a Magicka animation system requirement instead.
                        if bone_name_lower == name.lower():
                            raise MagickCowExportException(f"The bone name \"{name}\" is reserved!")

                    # Add the current bone to the list of found bones

                    current_bone = PE_Storage_Bone()
                    current_bone.obj = obj
                    current_bone.transform = transform
                    current_bone.index = len(found_objects.model.bones) # NOTE : We don't subtract 1 because the current bone has not been added to the list yet!!!
                    current_bone.parent = parent_bone_index
                    current_bone.children = []

                    found_objects.model.bones.append(current_bone)
                    
                    # Update the list of child bone indices for the parent bone
                    found_objects.model.bones[current_bone.parent].children.append(current_bone.index)

                    # Make recursive call to get all of the data of the child objects of this bone.
                    self._get_scene_data_rec(found_objects, obj.children, current_bone.index) # NOTE : The index we pass is literally the index of the bone we just added to the found objects' bones list.

                # Process empties for bounding boxes
                elif obj.mcow_physics_entity_empty_type == "BOUNDING_BOX":
                    # Add the found bounding box
                    found_objects.boxes.append(obj)


            # NOTE : We ignore objects of any type other than empties and meshes when getting objects to be processed for physics entity generation.
            # No need for an else case because we do nothing else within the loop.

    def _get_scene_data_add_mesh(self, found_objects, obj, transform, parent_bone_index):
        segments = self.get_mesh_segments(obj)
        ans = [(segment_obj, transform, material_index, parent_bone_index) for segment_obj, material_index in segments]
        found_objects.model.meshes.extend(ans)

# endregion
