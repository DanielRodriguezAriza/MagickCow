# region Data Generation pipeline classes

# The classes within this region define the top level logic of the pipeline for data generation for MagickCow.
# The data generator classes within this region make use of the internal lower level Get Stage, Generate Stage and Make Stage classes.

# NOTE : When implementing a new MagickCow data pipeline class, the top level / main logic must be implemented within the process_scene_data() method.

# NOTE : As of now, part of the scene preprocessing (such as scene rotation) takes place in this step in between MCow_Data_Whatever processor classes.
# Those steps could maybe be moved into separate preprocessor classes?

# region Comment - Steps of the pipeline

# This section contains a comment that describes the steps of the data generation pipeline.
# Each of the stages should return the following type of objects:

# Get Stage:
# The Get Stage class for each data pipeline should return an object containing lists of tuples with all of the objects to export from the scene, as well as
# their transforms relative to their parent in Magicka's target tree-like data structure.

# Generate Stage:
# The Generate Stage class for each data pipeline should return a tuple with the generated objects and the generated dicts with shared resources
# as well as other cached data, such as the generated materials (effects) and such.

# Make Stage:
# The Make Stage class for each data pipeline should return a dict which will be finally serialized into a JSON string.
# This dict should describe in a MagickaPUP compatible JSON structure the generated object / scene data.

# endregion

class MCow_Data_Pipeline:
    
    # region Constructor
    
    def __init__(self):
        return

    # endregion
    
    # region Scene Processing

    # Main scene processing entry point method
    # This method returns the final dictionary obtained in the make stage.
    # The method handles the entire process of generating all of the data for the scene that is being exported.
    # Each class that inherits from this base class implements its own version of this method.
    def process_scene_data(self):
        # NOTE : Maybe throw an exception here to denote that the base class should never be instantiated and used?
        # We could also throw in the constructor and just never call it in the derived classes.
        return {}
    
    # endregion

    # region Scene Rotation

    # region Deprecated

    # region Comment

    # Iterates over all of the root objects of the scene and rotates them by the input angle in degrees around the specified axis.
    # The rotation takes place around the world origin (0,0,0), so it would be equivalent to attaching all objects to a parent located in the world origin and then rotating said parent.
    # This way, there is no hierarchical requirements for scene export, since all root objects will be translated properly, and thus the child objects will also be automatically translated to the coorect coordinates.
    
    # endregion
    def rotate_scene_old_1(self, angle_degrees = 90, axis = "X"):
        root_objects = get_scene_root_objects()
        for obj in root_objects:
            obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees))
        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.
    
    def _rotate_objects_global(self, objects, angle_degrees, axis):
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(angle_degrees), 4, axis)
        for obj in objects:
            # obj.rotation_euler.rotate_axis(axis, math.radians(angle_degrees)) # idk why this doesn't work for all objects, I guess I'd know if only Blender's documentation had any information related to it. Oh well!
            obj.matrix_world = rotation_matrix @ obj.matrix_world

    # region Comment - rotate_objects_local_old_2

    # NOTE : For future reference, read this comment, very important, I had forgotten about how I had implemented this and just wasted like 40 mins trying to figure out where the Y up conversion was done for
    # locators...
    # basically, the trick is the following:
    # If you rotate in blender an object by -90d in the X axis to pass it to Y up, the rotation value stays wrong because now it is rotated by -90d around X.
    # To solve this, objects that require matrix data to be stored such as locators get their rotation undone... but if we undid the rotation through blender's rotations, we would go back to what we had before!
    # For example, imagine an object in Blender Z up with rot <0d, 0d, 45d>
    # If we rotate -90d around X, we end up with <-90d, 45d, 0d>
    # If we rotate +90d around X, we end up with <0d, 0d, 45d> again... so what's the solution?
    # The solution is what we do in this function... which is "faking" the "unrotation" process.
    # We manually add +90d to the X axis, which does not compute a real rotation as one would expect when using Blender rotation operations, but it does change the numeric value of the rotation, so the final
    # rotation will be <0d, 45d, 0d>, which is what we wanted!
    # This is such a fucking hack that I don't know how I had forgotten about this implementation detail... it is true that I've been many months away from the code, but Jesus fucking Christ, this is a really
    # important implementation detail to remember...

    # NOTE : Maybe I should apply this "unrotation" process to bones too? they work just fine with the "Z up" rotation value within their matrices tho, since all coordinates are relative, so whatever...
    # for now at least...

    # endregion
    def _rotate_objects_local(self, objects, angle_degrees, axis):
        axis_num = find_element_index(["X", "Y", "Z"], axis, 0)
        for obj in objects:
            obj.rotation_euler[axis_num] += math.radians(angle_degrees)

    # region Comment

    # NOTE : It also iterates over the locator objects and rotates them in the opposite direction.
    # This is because the rotation of the transform obtained after rotating the scene is only useful for objects where we need to translate other data, such as points and vectors (meshes, etc...)
    # In the case of locators, we directly use the transform matrix of the object itself, which means that the extra 90 degree rotation is going to change the orientation of the locators by 90 degrees.
    # This can be fixed by manually rotating the locators... or by having the rotate_scene() function do it for us, so the users will never know that it even happened! 
    # NOTE : Another fix would be to have a single world root object of sorts, and having to attach all objects to that root. That way, we would only have to rotate that one single root by 90 degrees and nothing else, no corrections required...
    # TODO : Basically make it so that we also have a root object in map scenes, just like we do in physics entity scenes...
    
    # endregion
    def _rotate_scene(self, angle_degrees = -90, axis = "X"):
        # Objects that are "roots" of the Blender scene
        root_objects = []

        # Point data objects that need to have their transform matrix corrected
        # region Comment
            # Objects that use their raw transform matrix as a way to represent their transform in game, such as locators.
            # They need to be corrected, since the transform matrix in Blender will contain the correct translation and scale, but will have a skewed rotation, because of the 90 degree rotation we use as
            # a hack to align the scene with the Y up coordinate system, so we need to correct it by undoing the 90 degree rotation locally around their origin point for every object of this type after
            # having performed the global 90 degree rotation around <0,0,0>
        # endregion
        objects_to_correct = []
        
        # All of the objects in the scene
        all_objects = get_all_objects()

        for obj in all_objects:
            if obj.parent is None:
                root_objects.append(obj)
            if obj.type == "EMPTY" and obj.magickcow_empty_type in ["LOCATOR", "PHYSICS_ENTITY"]:
                objects_to_correct.append(obj)

        self._rotate_objects_global(root_objects, angle_degrees, axis) # Rotate the entire scene
        self._rotate_objects_local(objects_to_correct, -1.0 * angle_degrees, axis) # The correction rotation goes in the opposite direction to the input rotation

        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.

    # endregion

    # region Experimental

    # region Comment
    
    # NOTE : First we rotate by -90º, then to unrotate we rotate by +90º, this way we can pass from Z up to to Y up coords
    # TODO : Once you implement the new scene root system for the map exporting side of the code, you will be capable of getting rid of the _aux suffix for this method's name.
    # Also, get rid of the rotate_scene() method within the map data generator class...
    # TODO : To be able to use this simpler root based rotation for map scenes, we need to find a way to translate rotations. We don't have to have the 90 degree rotation fix for empties anymore, sure, but
    # previously we did not apply any rotation fix to lights either... why? because lights with a rotation apply over a direction vector. What this means is that without the rotation fix, all of my final rotations
    # are Z up based, even tho my final points will be Y up based... or maybe I'm confused and this is actually wrong?
    # NOTE : Actually, now that I think about it, wouldn't we still have to undo rotations locally for point data whose location, rotation and scalre are exported with a matrix? If you think about it, lights are not affected despite being point data because their direction is exported as a director vector. I need to think about this shit tbh...
    
    # endregion
    def rotate_scene(self, angle_degrees, axis = "X"):
        roots = self.get_scene_roots()
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(angle_degrees), 4, axis)
        for root in roots: # We should only have 1 single root, which is validated on the exporter side, but we support multi-root scenes here to prevent getting funny results if we make any changes in the future...
            root.matrix_world = rotation_matrix @ root.matrix_world
        bpy.context.view_layer.update() # Force the scene to update so that the rotation is properly applied before we start evaluating the objects in the scene.
    
    def get_scene_roots_map(self):
        roots = [obj for obj in bpy.data.objects if (obj.parent is None and obj.magickcow_empty_type == "ROOT")]
        return roots
    
    def get_scene_roots_physics_entity(self):
        roots = [obj for obj in bpy.data.objects if (obj.parent is None and obj.mcow_physics_entity_empty_type == "ROOT")]
        return roots

    def get_scene_roots(self):
        if bpy.context.scene.mcow_scene_mode == "MAP":
            return self.get_scene_roots_map()
        elif bpy.context.scene.mcow_scene_mode == "PHYSICS_ENTITY":
            return self.get_scene_roots_physics_entity()
        return [] # In the case where the selected mode is not any of the implemented ones, we then return an empty list.

    # region Comment

    # Aux functions to perform rotations without having to remember what values and axes are specifically required when exporting a scene to Magicka.
    # Makes it easier to go from Z up to Y up, progress the scene, and then go back from Y up to Z up.
    
    # endregion
    def do_scene_rotation(self):
        self.rotate_scene(-90, "X")
    
    def undo_scene_rotation(self):
        self.rotate_scene(90, "X")

    # endregion

    # endregion

class MCow_Data_Pipeline_Map(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        self._cache = MCow_Data_Pipeline_Cache()
        self._get = MCow_Data_Getter_Map()
        self._gen = MCow_Data_Generator_Map(self._cache)
        self._mkr = MCow_Data_Maker_Map(self._cache)
        return
    
    def process_scene_data(self):
        self._rotate_scene()
        data_get = self._get.get()
        data_gen = self._gen.generate(data_get)
        data_mkr = self._mkr.make(data_gen)
        return data_mkr

class MCow_Data_Pipeline_PhysicsEntity(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        self._cache = MCow_Data_Pipeline_Cache()
        self._get = MCow_Data_Getter_PhysicsEntity()
        self._gen = MCow_Data_Generator_PhysicsEntity(self._cache)
        self._mkr = MCow_Data_Maker_PhysicsEntity(self._cache)
        return
    
    def process_scene_data(self):
        self._rotate_scene()
        data_get = self._get.get()
        data_gen = self._gen.generate(data_get)
        data_mkr = self._mkr.make(data_gen)
        return data_mkr

# endregion
