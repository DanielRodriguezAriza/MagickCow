# region Comments

# NOTE : Comments lie, code doesn't...
# A lot of the comments under "TODO" markers within this file are possibly outdated. As the codebase grows, it becomes harder and harder to maintain the comments LOL...
# The "NOTE"s are still relevant tho. A lot of really large comments exist for the sake of explaining how some weird pieces of the code actually work.

# TODO : Remove a lot of the outdated TODOs... like the one talking about encapsulating everything within classes LOL, that part's already been finished!

# TODO : Possibly change a lot of this stuff by encapsulating all of the "make_" methods into actual classes? with their own "generate()", "get_object()"/"make()", etc methods... idk...
# TODO : Rework all of the useless tuple copying by merging the JSON-style object make_ step with the generate_ step, maybe? I mean, it would be easier to keep them separate if the information was stored within proper classes and each had their make_data and generate_data functions.

# NOTE : I hate coding in python, it looks like 90% of the code is fucking comments, seriously, just having a decent type system would prevent having to make so many comments to clear stuff up. No, type annotations are not good enough...
# NOTE : Well, I don't really hate coding in python, it's pretty cool, but fuck me this code has to be one of the most wall of text filled pieces of code I have ever written. The comments are insane.

# TODO : Re-enable the global try catch on the exporter code so that we can get proper error handling. This was simply disabled so that we could get on what line exceptions took place during debugging...
# TODO : There's a bug when dealing with meshes that have 0 triangles. Discard those by seeing their triangle count on the get stage both on the map and physics entity handling code...
# TODO : Fix issue where attaching a light or other orientation based objects to a locator causes the resulting rotation values to be wrong (the locator has a pretty shitty rotation undo fix which is fucking things up...)

# TODO : Maybe modify the names of the blender properties bpy.props used by the objects and scene panel so that they are located within a custom object of their own for easier localization? Something like a dict?
# Maybe something like this:
"""

mcow_props : {
    type : bpy.props.enumproperty(whatever...),
    mesh_properties : {
        etc...
    },
    empty_properties : {
        etc...
    }
    liquid_properties : {
        etc...
    }
}

"""
# Or whatever the fuck, idk... we'll see if this is even possible in the first place...

# TODO : Fix Make stage material getting step by adding material cache dict as input tuple ok mk stage

"""
TODOs @20/07/2025:
    - Refactor the export pipeline to work using:
        - Free functions
        - Coordinate transform functions (remove the retarded 90º rotation stuff...)
        - Use despgraph evaluation rather than converting objects into real instances and applying modifiers in place...
            - NOTE : This may allow us to get rid of the fucking dumb ass shit that forces us to save scenes before we can export!
    
    - Refactor the import pipeline to work the same way...
    
    - Modify the scene creation options to allow generating the data in-place rather than having stupid new scene file creation stuff...
        - NOTE : This may actually still need the scene to be saved somewhere so that we can link up textures of the default / example scenes stuff without any issues... or maybe we can make them asset library files so that users can add them at will? kinda wonky and hacky, but better than nothing...
    
    - Change material caching to use id(mat) instead of mat.name once we have implemented the despgraph export system rather than the currently destructive one.
        - This will be useful because with the destructive method, linked objects are made into local copies, so the material names, text file names, etc... basically, all data block names are fixed up by adding .00x suffixes to prevent name collisions. This is done automatically by Blender, so it all comes together quite naturally. Once the despgraph method is used, this will obviously break the current caching system. Since linked objects are still technically referencing unique objects in memory, and we don't care about the fact that their memory address is different on every single program execution, we can then very easily determine that using id(obj), which gets the memory address of the object, is a good way to implement caching once the name based system stops working with the future planned despgraph based export system, which should be faster and consume less memory, we'll see if the need ever comes...
    
    - Maybe add the possibility of making all mcow bpy props library overridable, just in case that becomes useful in the future... some user is bound to have an usecase for that!
"""

# endregion
