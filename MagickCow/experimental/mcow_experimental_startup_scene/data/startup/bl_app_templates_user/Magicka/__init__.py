import bpy
from bpy.app.handlers import persistent

@persistent
def load_handler(_):
    # Retarded empty load handler because we don't really need to do anything on the scene...
    # This only exists because it is necessary for the startup scene to load properly.
    # In the future, it could become useful if I need to change things on start up, maybe
    # invoke mcow specific functionality that could potentially break if we just hard code it into the file
    # (ie: stuff that changes between versions and would be better to just apply as a transform or whatever)
    pass

def register():
    bpy.app.handlers.load_factory_startup_post.append(load_handler)


def unregister():
    bpy.app.handlers.load_factory_startup_post.remove(load_handler)
