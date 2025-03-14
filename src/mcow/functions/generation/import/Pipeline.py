# region Import Data Generation pipeline classes

class MCow_ImportPipeline:
    def __init__(self):
        return
    
    def exec(self, data):
        return MagickCowImportException() # The base class should never be used because it does not implement any specific type of pipeline for any kind of object, so it literally cannot import any sort of data...

class MCow_ImportPipeline_Map(MCow_ImportPipeline):
    def __init__(self):
        return
    
    def exec(self, data):
        raise MagickCowNotImplementedException()

class MCow_ImportPipeline_PhysicsEntity(MCow_ImportPipeline):
    def __init__(self):
        return
    
    def exec(self, data):
        raise MagickCowNotImplementedException()

# endregion
