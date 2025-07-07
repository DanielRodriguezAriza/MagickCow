# region XNA Model Classes

# TODO : Maybe rename this class when you make the code across level data generation and physics entity data generation more generic, since this is a class that both types of scene use internally...
class XNA_Model:
    def __init__(self):
        self.tag = None # Always null in Magicka, so we should not care about this tbh...
        self.bones = []
        self.vertex_declarations = [] # NOTE : These I had chosen to always generate to be the same on the make stage for map generation, so maybe we can just discard this property and never use it for anything?
        self.model_meshes = []

class XNA_Model_Bone:
    def __init__(self):
        self.index = 0
        self.name = "none"
        self.transform = None # NOTE : This is a transform matrix, and we could either use a tuple for it or structure it with a blender matrix class or use our own class for this.
        self.parent = -1
        self.children = []

class XNA_Model_Mesh:
    def __init__(self):
        self.name = "none"
        self.parent_bone = 0
        self.bounding_sphere = None
        self.vertex_buffer = []
        self.index_buffer = []
        self.mesh_parts = None # NOTE : Rather than implementing mesh parts, what my exporter does is simply adding a new model mesh to the exported data, so this should always be pretty much almost the exact same for all types of models, so we could ignore implementing this here and always write the same data in the make stage (except for the number of vertices, primitive count, vertex declaration index and shared resource index. Other than that, the rest of the data is always the same.)

# endregion
