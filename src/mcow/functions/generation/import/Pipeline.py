# region Import Data Generation pipeline classes

class MCow_ImportPipeline:
    def __init__(self):
        return
    
    def exec(self, data):
        # The base class should never be used because it does not implement any specific type of pipeline for any kind of object, so it literally cannot import any sort of data...
        raise MagickCowImportException("Cannot execute base import pipeline!")
        return None

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
            import_light(light)
    
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

    def import_light(self, light):
        name = light["LightName"]
        position = light["Position"]
        direction = light["Direction"]

        # TODO : Finish implementing

    # endregion

class MCow_ImportPipeline_PhysicsEntity(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        raise MagickCowNotImplementedException("Import PhysicsEntity is not implemented yet!")

# endregion
