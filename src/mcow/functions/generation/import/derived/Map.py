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
    
    def import_model_collision(self, collision):
        pass
    
    def import_camera_collision(self, collision):
        pass
    
    def import_triggers(self, triggers):
        pass
    
    def import_locators(self, locators):
        pass
    
    def import_nav_mesh(self, nav_mesh):
        pass
    
    # endregion

    # region Import Methods - Internal

    # TODO : Finish implementing (what's left as of now is modifying the properties of the spawned in light so that it uses the values that it has read from the JSON data)
    # TODO : Handle translating vectors from Y up to Z up...
    def import_light(self, light):
        # Read the light data
        # TODO : Maybe in the future, encapsulate this into a read method, so that we can read this automatically in any other place or something...
        name = light["LightName"]
        position = vec3_point_to_z_up(self.read_vector_3(light["Position"]))
        direction = self.read_vector_3(light["Direction"]) # TODO : Handle direction transform from Y up to Z up.
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

    def import_collision_channel(self, collision):
        pass

    # endregion

# endregion
