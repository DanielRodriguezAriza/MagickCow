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
        raise MagickCowNotImplementedException("Import Map is not implemented yet!")
    
    def import_leve_model(self, level_model):
        pass

    def import_model_mesh(self, model):
        pass
    
    def import_animated_parts(self, animated_parts):
        pass
    
    def import_lights(self, lights):
        pass
    
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

class MCow_ImportPipeline_PhysicsEntity(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        raise MagickCowNotImplementedException("Import PhysicsEntity is not implemented yet!")

# endregion
