# region Pipeline Cache Classes

# The classes within this region correspond to cache dicts and other cache objects that must be shared across different steps of the pipeline.

# TODO : Implement logic for adding and getting shared resources and effects
class MCow_Data_Pipeline_Cache:
    def __init__(self):
        self._cache_shared_resources = {} # Cache Dictionary for Shared Resources generated
        self._cache_generated_effects = {} # Cache Dictionary for Material Effects generated

# endregion
