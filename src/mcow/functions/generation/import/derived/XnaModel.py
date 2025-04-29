# region Import Data Pipeline class - Xna Model

# TODO : Clean up all of the duplicated logic from the Map importer pipeline class

class MCow_ImportPipeline_XnaModel(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        xna_model = data["XnbFileData"]["PrimaryObject"]
        self.import_xna_model(xna_model)

    def import_xna_model(self, xna_model):
        # Get model properties
        bones = xna_model["bones"]
        vertex_declarations = xna_model["vertexDeclarations"]
        model_meshes = xna_model["modelMeshes"]

        # Import the root bone of the model
        root_bone_obj = self.import_bone(bones[0], None)

        # Import the child meshes of this animated level part
        self.import_model_meshes(root_bone_obj, bones, vertex_declarations, model_meshes)

        return root_bone_obj
    
    def import_bone(self, bone_data, parent_bone_obj):
        # Get bone properties
        bone_name = bone_data["name"]
        bone_transform = self.read_mat4x4(bone_data["transform"]) # NOTE : This transform is relative to the parent bone of this part. If no parent exists, then obviously it's in global coordinates, since it is relative to the parent, which is the world origin.

        # Create bone object
        bone_obj = bpy.data.objects.new(name=bone_name, object_data=None)
        
        # Set bone transform and attach to parent if there's a parent bone object
        if parent_bone_obj is None:
            bone_obj.matrix_world = bone_transform # Set the matrix world transform matrix
        else:
            bone_obj.parent = parent_bone_obj # Attach the generate bone to the existing parent bone
            bone_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4) # Clear the parent inverse matrix that Blender calculates.
            bone_obj.matrix_basis = bone_transform # Set the relative transform
            # region Comment - Clearing out parent inverse matrix
            
            # We clear the parent inverse matrix that Blender calculates.
            # This way, the relative offset behaviour we get is what we would expect in literally any other 3D software on planet Earth.
            # Note that I'm NOT saying that Blender's parent inverse is useless... no, it's pretty nice... sometimes... but in this case? it's a fucking pain in the ass. So we clear it out.
            # We also could clear it with bpy.ops, but that's a pain in the butt, so easier to just do what bpy.ops does under the hood, which is setting the inverse matrix to the identity,
            # which is the same as having no inverse parent matrix.
            # For more information regarding the parent inverse matrix, read: https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Parenting#Clear_Parent_Inverse_Clarified
            # It will all make sense...
            
            # NOTE : Quote from the article (copy-pasted here just in case the link goes dead at some point in the future):
            # Normally, when a parent relationship is set up, if the parent has already had an object transformation applied, the child does not immediately inherit that.
            # Instead, it only picks up subsequent changes to the parent’s object transformation. What happens is that, at the time the parent relationship is set up, the inverse of the current parent
            # object transformation is calculated and henceforth applied before passing the parent transformation onto the child.
            # This cancels out the initial transformation, leaving the child where it is to start with.
            # This inverse is not recomputed when the parent object is subsequently moved or subject to other object transformations, so the child follows along thereafter.
            # The "Clear Parent Inverse" function sets this inverse transformation to the identity transformation, so the child picks up the full parent object transformation.

            # endregion
        
        # Link the object to the scene
        bpy.context.collection.objects.link(bone_obj)

        # Set mcow properties
        bone_obj.magickcow_empty_type = "BONE"

        # TODO : Refine the handling of the bounding sphere, maybe fully figure out what it does and maybe even auto-generate it like the bounding box for static mesh level parts.

        return bone_obj

    def import_model_meshes(self, root_bone_obj, bones, vertex_declarations, model_meshes):
        for model_mesh in model_meshes:
            
            parent_bone_index = model_mesh["parentBone"]
            parent_bone_data = bones[parent_bone_index]

            json_vertex_buffer = model_mesh["vertexBuffer"]
            json_index_buffer = model_mesh["indexBuffer"]
            
            mesh_parts = model_mesh["meshParts"]

            total_vertices = 0
            for mesh_part in mesh_parts:
                total_vertices += mesh_part["numVertices"]
            vertex_stride = len(json_vertex_buffer["Buffer"]) // total_vertices

            for mesh_part in mesh_parts:
                
                # region Comment - Mesh Parts Handling

                # TODO : Add proper mesh part handling in the future in the event that any of the vanilla maps have model meshes with multiple mesh parts rather than just 1.
                # Note that all mesh parts share the same vertex and index buffers, but they allow assigning different share resource indices (different material effects) to a segment of the mesh,
                # as well as different vertex declarations.

                # endregion
                
                vertex_declaration_index = mesh_part["vertexDeclarationIndex"]
                json_vertex_declaration = vertex_declarations[vertex_declaration_index]

                self.import_model_mesh(root_bone_obj, parent_bone_data, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer)

                share_resource_index = mesh_part["sharedResourceIndex"] # TODO : Add shared resource handling

    def import_model_mesh(self, obj_root_bone, json_parent_bone, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer):
        # Generate mesh data, create mesh data block and create Blender mesh object
        obj, mesh = mcow_import_buffer_mesh(json_parent_bone["name"], vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer)

        # Assign mcow properties
        mesh.magickcow_mesh_type = "GEOMETRY"

        # Attach to parent bone object and set relative object transform
        transform = self.read_mat4x4(json_parent_bone["transform"])
        obj.parent = obj_root_bone
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        obj.matrix_basis = transform

        # Create material data
        # TODO : Implement material handling


# endregion
