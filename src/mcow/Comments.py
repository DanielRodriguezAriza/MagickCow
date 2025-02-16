# region Comments

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

# endregion
