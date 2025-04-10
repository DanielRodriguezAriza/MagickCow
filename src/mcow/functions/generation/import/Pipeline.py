# region Import Data Pipeline class - Base class

class MCow_ImportPipeline:
    def __init__(self):
        return
    
    def exec(self, data):
        # The base class should never be used because it does not implement any specific type of pipeline for any kind of object, so it literally cannot import any sort of data...
        raise MagickCowImportException("Cannot execute base import pipeline!")
        return None
    
    def read_vector_3(self, vec3):
        ans = (vec3["x"], vec3["y"], vec3["z"])
        return ans
    
    def read_vector_4(self, vec4):
        ans = (vec4["x"], vec4["y"], vec4["z"], vec4["w"])
        return ans
    
    # TODO : Add option to handle reading vectors as Y up or Z up... maybe add a bool or a different method that specifies if we want to perform Y up to Z up conversion.

# endregion
