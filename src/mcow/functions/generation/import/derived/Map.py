# region Import Data Pipeline class - LevelModel / Map

# TODO : Implement all import functions...
class MCow_ImportPipeline_Map(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        level_model = data["XnbFileData"]["PrimaryObject"]
        self.import_level_model(level_model)
    
    def import_level_model(self, level_model):
        # Get the data entries from the level model JSON dict object.
        model_mesh = level_model["model"]
        animated_parts = level_model["animatedParts"]
        lights = level_model["lights"]
        effects = level_model["effects"]
        physics_entities = level_model["physicsEntities"]
        liquids = level_model["liquids"]
        force_fields = level_model["forceFields"]
        model_collision = level_model["collisionDataLevel"]
        camera_collision = level_model["collisionDataCamera"]
        triggers = level_model["triggers"]
        locators = level_model["locators"]
        nav_mesh = level_model["navMesh"]
        
        # Execute the import functions for each of the types of data found within the level model JSON dict.
        self.import_model_mesh(model_mesh)
        self.import_animated_parts(animated_parts)
        self.import_lights(lights)
        self.import_effects(effects)
        self.import_physics_entities(physics_entities)
        self.import_liquids(liquids)
        self.import_force_fields(force_fields)
        self.import_model_collision(model_collision)
        self.import_camera_collision(camera_collision)
        self.import_triggers(triggers)
        self.import_locators(locators)
        self.import_nav_mesh(nav_mesh)

    # region Import Methods - Top Level

    def import_model_mesh(self, model):
        pass
    
    def import_animated_parts(self, animated_parts):
        pass
    
    def import_lights(self, lights):
        for light in lights:
            self.import_light(light)
    
    def import_effects(self, effects):
        pass
    
    def import_physics_entities(self, physics_entities):
        pass
    
    def import_liquids(self, liquids):
        pass
    
    def import_force_fields(self, force_fields):
        pass
    
    def import_model_collision(self, collision_data): # TODO : Add support to specify the type of collision channel that we're importing, as of now we're only going to be importing the mesh and that's it.
        for idx, collision_channel in enumerate(collision_data):
            self.import_collision_channel(f"collision_mesh_model_{idx}", collision_channel) # This would need an extra param to specify the collision channel index, but what happens then to the import camera collision function? those are the details we need to polish.
    
    def import_camera_collision(self, collision_data):
        self.import_collision_channel("collision_mesh_camera", collision_data)
    
    def import_triggers(self, triggers):
        for trigger in triggers:
            self.import_trigger(trigger)
    
    def import_locators(self, locators):
        for locator in locators:
            self.import_locator(locator)
    
    def import_nav_mesh(self, nav_mesh):
        pass
    
    # endregion

    # region Import Methods - Internal

    # TODO : Finish implementing (what's left as of now is modifying the properties of the spawned in light so that it uses the values that it has read from the JSON data)
    # TODO : Handle translating ALL vectors from Y up to Z up...
    def import_light(self, light):
        # Read the light data
        # TODO : Maybe in the future, encapsulate this into a read method, so that we can read this automatically in any other place or something...
        name = light["LightName"]
        position = self.read_point(light["Position"])
        direction = self.read_vec3_raw(light["Direction"]) # TODO : Handle direction transform from Y up to Z up.
        light_type = find_light_type_name(light["LightType"])
        variation_type = light["LightVariationType"]
        reach = light["Reach"]
        use_attenuation = light["UseAttenuation"]
        cutoff_angle = light["CutoffAngle"]
        sharpness = light["Sharpness"]
        color_diffuse = light["DiffuseColor"]
        color_ambient = light["AmbientColor"]
        specular = light["SpecularAmount"]
        variation_speed = light["VariationSpeed"]
        variation_amount = light["VariationAmount"]
        shadow_map_size = light["ShadowMapSize"]
        casts_shadows = light["CastsShadows"]

        # Create the light data and modify its properties
        light_data = bpy.data.lights.new(name=name, type=light_type)

        # Create the light object
        light_object = bpy.data.objects.new(name=name, object_data=light_data)

        # Add the light object to the scene (link object to collection)
        bpy.context.collection.objects.link(light_object)

        # Modify light object properties
        light_object.location = position

    def import_collision_channel(self, name, collision):
        has_collision = collision["hasCollision"]

        if not has_collision:
            return
        
        json_vertices = collision["vertices"]
        json_triangles = collision["triangles"]

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["index0"], tri["index1"], tri["index2"]) for tri in json_triangles]

        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

    def import_locator(self, locator):
        # Get the properties of the locator from the json data
        name = locator["Name"]
        transform = self.read_mat4x4(locator["Transform"])
        radius = locator["Radius"]

        # region Comment - empty display explanation
        # NOTE : The display type is updated automatically when we change the property empty.magickcow_empty_type, since it is linked to an update function,
        # so we don't need to call this ourselves by hand. I'm leaving this code behind so that you can remember why we don't do it.
        # empty.empty_display_type = "PLAIN_AXES"
        # endregion
        # Spawn empty object and add it to the scene and modify its properties
        empty = bpy.data.objects.new(name = name, object_data = None)
        empty.matrix_world = transform
        # empty.location = (0, 0, 0) # TODO : Implement transform reading so that we can extract the position, rotation, scale, etc...

        bpy.context.collection.objects.link(empty)

        empty.magickcow_empty_type = "LOCATOR"
        empty.magickcow_locator_radius = radius

    def import_trigger(self, trigger):
        # Extract the data from the json object
        name = trigger["Name"]
        position = self.read_point(trigger["Position"])
        scale = self.read_scale(trigger["SideLengths"]) * 0.5 # Divide by half the side of the trigger because the trigger origin in Magicka is on a corner, but in Blender is on the center of the trigger's volume.
        rotation = self.read_quat(trigger["Rotation"])

        # Create the empty object trigger on the Blender scene and assign the properties
        # NOTE : These values that we just assigned are the ones used by Magicka's engine in-game.
        # After this, we apply some corrections so that the values are exactly the ones that Blender needs to use.
        empty = bpy.data.objects.new(name = name, object_data = None)
        empty.location = position
        empty.rotation_quaternion = rotation
        empty.scale = scale
        
        # Get the relative transform vectors (forward vector, up vector and right vector) of the object on the Blender scene.
        # These will be used to apply some relative translations.
        x_vec = empty.matrix_world.col[0].xyz.normalized()
        y_vec = empty.matrix_world.col[1].xyz.normalized()
        z_vec = empty.matrix_world.col[2].xyz.normalized()

        # Apply a relative transform by half of the in-game scale (which is 100% of the in-Blender scale)
        # so that the origin point is now aligned with the center of the trigger's volume rather than the corner of the trigger's volume.
        empty.location += x_vec * scale
        empty.location += y_vec * scale
        empty.location += z_vec * scale

        # Link the object to the scene
        bpy.context.collection.objects.link(empty)

        # Change the mcow empty type. This also updates the empty display type automatically.
        empty.magickcow_empty_type = "TRIGGER"

    # endregion

# endregion
