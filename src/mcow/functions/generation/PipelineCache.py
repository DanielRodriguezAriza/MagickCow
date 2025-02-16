# region Pipeline Cache Classes

# The classes within this region correspond to cache dicts and other cache objects that must be shared across different steps of the pipeline.

# TODO : Implement logic for adding and getting shared resources and effects
# TODO : Add the remaining functions LOL (eg: the ones used within the _create_default_values_effects() method)
class MCow_Data_Pipeline_Cache:
    def __init__(self):
        self._cache_shared_resources = {} # Cache Dictionary for Shared Resources generated
        self._cache_generated_effects = {} # Cache Dictionary for Material Effects generated

    def _create_default_values(self):
        self._create_default_values_effects() # Initialize the values for the Material Effects cache with default values
    
    # region Comment

    # Cached Effects Initialization
    # Setup all default material data beforehand (not required as the process would still work even if this was not done, but whatever... basically this works as a sort of precaching, but since it is
    # not compiletime because this is not C, there really is not much point ot it, altough maybe making the dict with self.dict_effects = {"base/whatever" : {blah blah blah...}, ...} could actually
    # be faster in future versions of Python, idk)

    # endregion
    def _create_default_values_effects(self, effect_types = ["GEOMETRY", "WATER", "LAVA"]):
        for effect_type in effect_types:
            self._cache_generated_effects[self._create_default_effect_name(effect_type)] = self._create_default_effect_data(current_type)

# endregion
