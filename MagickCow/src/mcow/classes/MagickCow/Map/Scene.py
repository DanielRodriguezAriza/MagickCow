# region Map Classes

class MCow_Map_SceneObjectsFound:
    def __init__(self):
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = []
        self.particles = []
        self.collisions = [[] for i in range(10)] # Each collision layer is a list of objects that were found within said layer.
        self.nav_meshes = []
        self.animated_parts = []
        
        # NOTE : These fields ahead can only be found on static level data, can't be within animated level parts.
        self.physics_entities = []
        self.force_fields = []
        self.camera_collision_meshes = []

class MCow_Map_SceneObjectsGeneratedStatic:
    def __init__(self):
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = []
        self.particles = []
        self.collisions = []
        self.camera_collision_mesh = None
        self.nav_mesh = None
        self.animated_parts = []
        self.physics_entities = []
        self.force_fields = []

class MCow_Map_SceneObjectsGeneratedAnimated:
    def __init__(self):
        self.bone = None # The root bone of this animated level part.
        self.meshes = []
        self.waters = []
        self.lavas = []
        self.lights = []
        self.locators = []
        self.triggers = [] # NOTE : Animated level parts cannot contain triggers! This should be removed and the get stage code modified accordingly...
        self.particles = []
        self.collision = None # We store a single collision channel / layer, because the entire animated part has to have the same collision type. Child parts can have their own collision type tho.
        self.nav_mesh = None
        self.animation = None
        self.animated_parts = []

# endregion
