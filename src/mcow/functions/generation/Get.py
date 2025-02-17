# region Get Stage

# This section contains classes whose purpose is to define the logic of the Get Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Getter class.
class MCow_Data_Getter:
    def __init__(self):
        return
    
    def get(self):
        return None # Return an empty object by default since the base class does not implement the data getting for any specific class.

    # region Comment

    # Returns a list of meshes in the form of a tuple (obj, transform, material_index).
    # Segments a single mesh into multiple meshes based on the indices of the applied materials.
    # This is used because it is easier to just export a new mesh for each material than it is to implement BiTree nodes and multi material XNA models...
    
    # endregion
    def get_mesh_segments(self, obj):
        
        # NOTE : The return value of this function is a list filled with tuples of form (mesh_object, material_index)
        
        mesh = obj.data
        num_materials = len(mesh.materials)

        # If there are no materials, then add the mesh to the list of found meshes 
        if num_materials <= 0:
            ans = [(obj, 0)]
        
        # If there are materials, then add each segment of the mesh that uses an specific material as a separate mesh for simplicity
        else:

            found_polygons_with_material_index = [0 for i in range(0, num_materials)]
            for poly in mesh.polygons:
                found_polygons_with_material_index[poly.material_index] += 1
            
            ans = []
            for index, count in enumerate(found_polygons_with_material_index):
                if count > 0:
                    ans.append((obj, index))
        
        return ans

# Data Getter class for Maps / Levels
class MCow_Data_Getter_Map(MCow_Data_Getter):
    def __init__(self):
        super().__init__()
        return
    
    def get(self):
        return self._get_scene_data()
    
    # region Comment - _get_scene_data_add_collision
    
    # If the parent is an animated level part, then we add the collision to whatever collision channel the parent corresponds to.
    # Otherwise, we add it to the collision channel of the object itself.
    
    # endregion
    def _get_scene_data_add_collision(self, found_objects_current, obj, transform, parent):
        collision_index = 0
        if parent is None:
            collision_index = find_collision_material_index(obj.magickcow_collision_material)
        else:
            collision_index = find_collision_material_index(parent.magickcow_collision_material)
        found_objects_current.collisions[collision_index].append((obj, transform))

    # TODO : Modify this method to internally call the get_mesh_segments() method
    # region Comment - _get_scene_data_add_mesh
        # NOTE : The reason we do this process rather than actually implementing BiTreeNode support is for 3 major reasons
        # 1) BiTree Nodes don't actually contain material data at all. Yes, their existance is literally useless, they just segment things up and don't even
        # contain a different effect for a given part of a root node...
        #
        # 2) BiTreeNodes are just badly optimized in Magicka and consume more memory than they should.
        # A BiTreeNode's purpose is literally to just assign a different material to a given part of a root node's vertex buffer than the one assigned on the root node.
        # This assignment process goes by starting at a certain vertex index and giving a number of primitives that are contained by said node (the root node does this as well).
        # This means that for every single island of faces that make use of a given material, there will be a new BiTreeNode generated.
        # This is a problem, because if a mesh in Blender has 2 materials, it is not guaranteed to have only 2 nodes in the binary tree structure. If the materials are assigned on different polygon islands,
        # then the generated binary tree structure will generate a node for the same material multiple times, since a node can only represent a material assignment for contiguous faces within the vertex buffer.
        #
        # 3) BiTreeNodes are just badly optimized : Episode 2:
        # Another problem of using the BiTreeNode setup is that each node added is located on the heap, thus, there will be an increase in memory fragmentation. Root nodes are instead located within a list, so
        # most of their data will at least be contiguous in memory.
        # In short, BiTreeNodes in Magicka's code pointlessly increase the memory consumption, and the memory budget for a Magicka map is about 2GB at most since Magicka is 32 bits, and of the 4GB available
        # for a 32 bit process, 2 of those have already been consumed by the game code itself and most assets, so the remaining budget is quite small, and using only root nodes reduces the memory footprint a lot.
        #
        # In short, this is literally the only way to get multi material mesh support in Magicka. Magicka's meshes only support one material per mesh, so the trick we do is just segment the mesh into multiple different
        # meshes, each containing all of the polygons for a given material that was assigned in Blender to that mesh.
    # endregion
    def _get_scene_data_add_mesh(self, found_objects_list, obj, transform):
        mesh = obj.data
        num_materials = len(mesh.materials)
        
        if num_materials > 0:
            found_polygons_indices = [0 for i in range(num_materials)]
            # Check every polygon in the mesh and increase the usage count of the material index used by each polygon
            for poly in obj.data.polygons:
                found_polygons_indices[poly.material_index] += 1
        else:
            # Create a dummy list with only one entry, which has to contain any value greater than 0 so as to indicate that at least one polygon has been foud to make use of material index 0.
            # This is because in Blender, polygons that don't have any material assigned use the material index 0 by default.
            found_polygons_indices = [69] # In this case, I use 69 cauze lol, but the value 1 would suffice just fine.
            # Either that or just embed the call found_objects_list.append((obj, transform, 0)) within the else block and discard the dummy list entirely.
            # We keep it like this in case we want to add more code in the future appart from the append() call, so as to prevent code duplication...
        
        # Add the meshes that have been found to contain at least 1 polgyon that uses the current material
        for idx, found in enumerate(found_polygons_indices):
            if found > 0: # If there are no polygons in this mesh with this material assigned, discard it entirely and don't add it for processing.
                found_objects_list.append((obj, transform, idx))

    def _get_scene_data_rec(self, found_objects_global, found_objects_current, objects, parent = None):
        
        for obj in objects:
            
            # Get object transform
            transform = get_object_transform(obj, parent)
            
            # Ignore objects that are set to not export, as well as their children objects.
            if not obj.magickcow_allow_export:
                continue
            
            # Handle object data creation according to object type.
            if obj.type == "MESH":
                
                if len(obj.data.vertices) <= 0:
                    continue # Discard meshes with no vertices, as they are empty meshes and literally have no data worth exporting.

                if obj.data.magickcow_mesh_type == "GEOMETRY":
                    # found_objects_current.meshes.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.meshes, obj, transform)
                    
                    if obj.magickcow_collision_enabled:
                        self._get_scene_data_add_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "COLLISION":
                    self._get_scene_data_add_collision(found_objects_current, obj, transform, parent)
                    
                elif obj.data.magickcow_mesh_type == "WATER":
                    # found_objects_current.waters.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.waters, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "LAVA":
                    # found_objects_current.lavas.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_current.lavas, obj, transform)
                
                elif obj.data.magickcow_mesh_type == "NAV":
                    found_objects_current.nav_meshes.append((obj, transform)) # Nav meshes ignore materials, for now. In the future, they could use it as a reference for the type of navigation offered by an area.
                
                elif obj.data.magickcow_mesh_type == "FORCE_FIELD":
                    # Only add it to the global scope because animated level parts cannot contain force fields.
                    # Allows "malformed" (with a hierarchy that would not be correct in game) scenes to export successfully and work correctly in game.
                    # found_objects_global.force_fields.append((obj, transform))
                    self._get_scene_data_add_mesh(found_objects_global.force_fields, obj, transform)
            
            elif obj.type == "LIGHT":
                
                # TODO : This will need to be reworked the day support for static level bitree child nodes is added... which may actually never come if there's no technical reason to support it...
                # We would need to probably roll back to having an input bool variable in this function that says if the parent object is an animated object or not.
                # Or we could analyse the parent's type with parent.type and check if it is an empty of "BONE" type or not. We'll see what is chosen in the future, but for now, fuck it.
                if parent is not None:
                    found_objects_current.lights.append((obj, transform))
                
                found_objects_global.lights.append((obj, transform)) # Always add it to the global scope of the static level data because lights are stored like that in Magicka's code. Animated level parts only store a reference to a light.
            
            elif obj.type == "EMPTY":
                # This case does nothing because we DO want to allow using NONE type empties as a way to organize the scene, and using continue here would just skip child generation.
                # Do note that the better and encouraged way to do things in Blender with this addon is with collections, but this is still a possibility...
                if obj.magickcow_empty_type == "NONE":
                    pass # This used to do continue, but now it's just a nop because we actually want to get the children objects and export those, unless manually disabled.
                elif obj.magickcow_empty_type == "LOCATOR":
                    found_objects_current.locators.append((obj, transform))
                elif obj.magickcow_empty_type == "TRIGGER":
                    found_objects_current.triggers.append((obj, transform))
                elif obj.magickcow_empty_type == "PARTICLE":
                    found_objects_current.particles.append((obj, transform))
                elif obj.magickcow_empty_type == "PHYSICS_ENTITY":
                    # We append them only to the global objects because animated level parts cannot contain this type of object.
                    # If an animated level part contains an object of this type in the Blender scene, it will be exported as part of the static level data instead.
                    # Allows partially "malformed" scenes to export just fine.
                    found_objects_global.physics_entities.append((obj, transform))
            
            # Handle recursive call according to whether the current root object is a bone (root of an animated level part) or not.
            if obj.type == "EMPTY" and obj.magickcow_empty_type == "BONE":
            
                # Ignore exporting animated level parts if animation export is disabled.
                if not bpy.context.scene.mcow_scene_animation:
                    continue
                
                found_objects_new = MCow_Map_SceneObjectsFound()
                
                self._get_scene_data_rec(found_objects_global, found_objects_new, obj.children, obj)
                
                found_objects_current.animated_parts.append((obj, transform, found_objects_new))
            else:
                self._get_scene_data_rec(found_objects_global, found_objects_current, obj.children, parent)

    def _get_scene_data(self):
        
        # Get the root objects from the scene
        root_objects = get_scene_root_objects()
        
        # Create an instance of the found objects class. It will get passed around by the recursive calls to form a tree-like structure, adding the found objects to it and its children.
        found_objects = MCow_Map_SceneObjectsFound()
        
        # Call the recursive function and start getting the data.
        self._get_scene_data_rec(found_objects, found_objects, root_objects, None)
        
        return found_objects

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
        self._get_scene_data_rec(found_objects, root_objects[0].children, 0)
        
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
