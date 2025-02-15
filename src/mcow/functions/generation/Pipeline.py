# region Data Generation pipeline classes

# The classes within this region define the top level logic of the pipeline for data generation for MagickCow.
# The data generator classes within this region make use of the internal lower level Get Stage, Generate Stage and Make Stage classes.

# NOTE : When implementing a new MagickCow data pipeline class, the top level / main logic must be implemented within the process_scene_data() method.

# TODO : Implement all classes here

class MCow_Data_Pipeline:
    def __init__(self):
        pass
    
    def process_scene_data(self):
        pass

def MCow_Data_Pipeline_Map(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        return
    
    def process_scene_data(self):
        pass

def MCow_Data_Pipeline_PhysicsEntity(self):
    def __init__(self):
        super().__init__()
        return
    
    def process_scene_data(self):
        pass

# endregion
