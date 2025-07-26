# region Mesh Class

# TODO : Change logic to use despgraph and .to_mesh() on instances instead of copying entire data blocks... will make things faster and avoid the problem described in the comment below,
# within MCow_Mesh's constructor function, "__init__()".

class MCow_Mesh:
    def __init__(self, obj, transform):

        # Ensure that data is single user so that modifiers can be applied
        # region Comment
        # Copy the data so that we can apply modifiers, but only if the object's data has more than 1 user.
        # Also, yes, this makes it so that the original is still sitting there in memory, but we don't care for the most part about this as of now.
        # Maybe if someone were to work with an extremely large mesh they would then feel the impact of copying multiple GBs at a time, but that's on them for not segmenting their mesh properly...
        # endregion
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        
        # Assign values to local variables
        self.obj = obj
        self.transform = transform
        self.invtrans = transform.inverted().transposed()
        self.mesh = None
        self.bm = None

        # Apply modifiers, triangulate mesh, generate bm, etc...
        self._calculate_mesh_data()
    
    def __del__(self):
        self.bm.free()

    def _calculate_mesh_data(self):
        self._select_object()
        self._apply_modifiers()
        self._triangulate_mesh()
        self._compute_tangents()
    
    def _select_object(self):
        self.obj.select_set(state = True)
        bpy.context.view_layer.objects.active = self.obj

    def _apply_modifiers(self):
        for mod in self.obj.modifiers:
            bpy.ops.object.modifier_apply(modifier = mod.name)
    
    def _triangulate_mesh(self):
        mesh = self.obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        self.mesh = mesh
        self.bm = bm

    def _compute_tangents(self):
        self.mesh.calc_tangents()

# endregion
