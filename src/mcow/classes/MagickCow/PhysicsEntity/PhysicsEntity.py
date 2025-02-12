# region Physics Entity Classes

# region Get Stage Classes

# NOTE : The Map side of the code could be reworked to be similar to how the physics entity side is going to work.
# Basically, here, rather than having different structures for the get and generate stages, since we're going to be storing the same type of data in both cases, just in different states / forms, what I've done is
# that I'm basically having a "stroage" data structure for each type of data structure that exists within physics entities in the format of their XNB files.

class Storage_PhysicsEntity:
    def __init__(self):
        # self.roots = [] # NOTE : If we have more than one root, what do we do? do we error out or do we export multiple objects? and if we export multiple objects, do we put them into the same file in a list like structure and modify MagickaPUP to support input JSON files with lists of docs inside, or do we export each object to its own file? and what naming scheme to use? etc etc...
        self.root = None
        self.collisions = [] # Collision meshes
        self.boxes = [] # Bounding boxes
        self.model = Storage_PhysicsEntity_Model()

class Storage_PhysicsEntity_Model:
    def __init__(self):
        self.meshes = []
        self.bones = []

class PE_Storage_Bone:
    def __init__(self):
        self.obj = None
        self.transform = None
        self.index = 0
        self.parent = -1
        self.children = []

# endregion

# region Generate Stage Classes

class PE_Generate_PhysicsEntityData:
    def __init__(self):
        self.physics_entity_id = "default"
        self.is_movable = False
        self.is_pushable = False
        self.is_solid = True
        self.mass = 200
        self.max_hit_points = 300
        self.can_have_status = True
        self.resistances = []
        self.gibs = []
        self.gib_trail_effect = ""
        self.hit_effect = ""
        self.visual_effects = []
        self.sound_banks = ""
        self.model = XNA_Model()
        self.has_collision = False
        self.collision_vertices = []
        self.collision_triangles = []
        self.bounding_boxes = []
        self.events = []
        self.has_advanced_settings = True
        self.advanced_settings = None

# NOTE : In truth, the game only supports a single bounding box, but the reading code can take N bounding boxes.
# The thing is that only the first read bounding box is preserved, the rest are just discarded. In any case, we add support for exporting as many bounding boxes as we want, even tho only one will be used in the end...
class PE_Generate_BoundingBox:
    def __init__(self):
        self.id = "bb"
        self.position = None # vec3
        self.scale = None # vec3
        self.rotation = None # quaternion / vec4

class PE_Generate_Resistance:
    def __init__(self, element = "Earth", multiplier = 1, modifier = 0):
        self.element = element
        self.multiplier = multiplier
        self.modifier = modifier

class PE_Generate_Gib:
    def __init__(self, model = "", mass = 1, scale = 1):
        self.model = model
        self.mass = mass
        self.scale = scale

class PE_Generate_Bone:
    def __init__(self):
        self.index = 0
        self.name = "bone"
        self.transform = None
        self.parent = -1
        self.children = []


# endregion

# endregion
