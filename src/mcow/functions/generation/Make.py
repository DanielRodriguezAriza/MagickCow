# region Make Stage

# This section contains classes whose purpose is to define the logic of the Make Stage of the code.

# TODO : Move logic from data generation classes into external functions and place them here...

# Base Data Maker class.
class MCow_Data_Maker:
    def __init__(self):
        return
    
    def make(self):
        ans = {} # We return an empty object by default since this is the base class and it doesn't really implement any type of object data generation anyway, so yeah.
        return ans

# Data Maker class for Maps / Levels
class MCow_Data_Maker_Map(MCow_Data_Maker):
    def __init__(self):
        super().__init__()
        return
    
    def make(self, make_data):
        # TODO : Implement
        ans = {}
        return ans

# Data Maker class for Physics entities
class MCow_Data_Maker_PhysicsEntity(MCow_Data_Maker):
    def __init__(self):
        super().__init__()
        return
    
    def make(self, make_data):
        # TODO : Implement
        ans = {}
        return ans

# endregion
