# region Pipeline Cache Classes

# The classes within this region correspond to cache dicts and other cache objects that must be shared across different steps of the pipeline.

# TODO : Implement logic for adding and getting shared resources and effects
# TODO : Add the remaining functions LOL (eg: the ones used within the _create_default_values_effects() method)
class MCow_Data_Pipeline_Cache:
    
    # region Constructor
    
    def __init__(self):
        self._cache_shared_resources = {} # Cache Dictionary for Shared Resources generated
        self._cache_generated_effects = {} # Cache Dictionary for Material Effects generated

    # endregion

    # region Private Methods

    def _create_default_values(self):
        self._create_default_values_effects() # Initialize the values for the Material Effects cache with default values
    
    def _create_default_values_effects(self, effect_types = ["GEOMETRY", "WATER", "LAVA"]):
        # region Comment

        # Cached Effects Initialization
        # Setup all default material data beforehand (not required as the process would still work even if this was not done, but whatever... basically this works as a sort of precaching, but since it is
        # not compiletime because this is not C, there really is not much point ot it, altough maybe making the dict with self.dict_effects = {"base/whatever" : {blah blah blah...}, ...} could actually
        # be faster in future versions of Python, idk)

        # endregion
        for effect_type in effect_types:
            self._cache_generated_effects[self._create_default_effect_name(effect_type)] = self._create_default_effect_data(current_type)
    
    # endregion

    # region Public Methods - Shared Resources

    def add_shared_resource(self, resource_name, resource_content):
        if resource_name not in self._cache_shared_resources:
            num_resources = len(self._cache_shared_resources)
            resource_index = num_resources + 1 # Use the current count of resources as the index of each element (note that indices for shared resources in XNB files start at 1, not 0)
            self._cache_shared_resources[resource_name] = (resource_index, resource_content) # Store the resource index and its contents
            return resource_index
        else: # If the resource was already within the list, we don't add it again, we just return the index
            idx, content = self.dict_shared_resources[resource_name]
            return idx

    def get_shared_resource(self, resource_name):
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return (idx, content)
        return (0, None) # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    def get_shared_resource_index(self, resource_name):
        # NOTE : Same as the get function, but instead of returning the content, we only return the index.
        if resource_name in self._cache_shared_resources:
            idx, content = self._cache_shared_resources[resource_name]
            return idx
        return 0 # Return 0 as invalid index because XNB files use index 0 for non valid resources. The first index for shared resources is 1.

    def make_shared_resources_list(self):
        ans = []
        for key, resource in self._cache_shared_resources.items():
            idx, content = resource
            ans.append(content)
        return ans
    
    # endregion

# endregion
