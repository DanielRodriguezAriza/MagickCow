# region Data Generation pipeline classes

# The classes within this region define the top level logic of the pipeline for data generation for MagickCow.
# The data generator classes within this region make use of the internal lower level Get Stage, Generate Stage and Make Stage classes.

# NOTE : When implementing a new MagickCow data pipeline class, the top level / main logic must be implemented within the process_scene_data() method.

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
    def __init__(self):
        pass
    
    def process_scene_data(self):
        # NOTE : Maybe throw an exception here to denote that the base class should never be instantiated and used?
        # We could also throw in the constructor and just never call it in the derived classes.
        pass

def MCow_Data_Pipeline_Map(MCow_Data_Pipeline):
    def __init__(self):
        super().__init__()
        self._get = MCow_Data_Getter_Map()
        self._gen = MCow_Data_Generator_Map()
        self._mkr = MCow_Data_Maker_Map()
        return
    
    def process_scene_data(self):
        data_get = self._get.get()
        data_gen = self._gen.generate()
        data_mkr = self._mkr.make()
        return data_mkr

def MCow_Data_Pipeline_PhysicsEntity(self):
    def __init__(self):
        super().__init__()
        self._get = MCow_Data_Getter_PhysicsEntity()
        self._gen = MCow_Data_Generator_PhysicsEntity()
        self._mkr = MCow_Data_Maker_PhysicsEntity()
        return
    
    def process_scene_data(self):
        data_get = self._get.get()
        data_gen = self._gen.generate()
        data_mkr = self._mkr.make()
        return data_mrk

# endregion
