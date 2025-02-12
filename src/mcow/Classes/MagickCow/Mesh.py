# region Meshes

class MCow_Mesh:
    def __init__(self, obj, transform):
        self.obj = obj
        self.transform = transform
        self.invtrans = transform.inverted().transposed()
        self.mesh = None
        self.bm = None
        self._calculate_mesh_data() # Apply modifiers, triangulate mesh, generate bm, etc...
    
    def __del__(self):
        self.bm.free()

    def _calculate_mesh_data(self):
        self._select_object(self.obj)
        self._apply_modifiers(self.obj)
        self._triangulate_mesh(self.obj)
    
    def _select_object(self, obj):
        obj.select_set(state = True)
        bpy.context.view_layer.objects.active = obj

    def _apply_modifiers(self, obj):
        for mod in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier = mod.name)
    
    def _triangulate_mesh(self, obj):
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        self.mesh = mesh
        self.bm = bm


# endregion
