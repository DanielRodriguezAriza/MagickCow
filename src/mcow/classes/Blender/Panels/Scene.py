# region Blender Panel Classes for Scene Panel

# This class is the one that controls the N-Key panel for global scene config.
# region Comment
    # It is inspired by Valve's blender source tools, where they have the equivalent of this panel on the scene menu.
    # In my case, I am not sure this is the best way to go, as we could also make this an N-Key panel that works without selecting any objects, but as of now I have decided to make it like this because it feels
    # like it would make things less cluttered. The right most panel, which is where the scene panel is located by default, is pretty large by default and it is a location that makes sense for the kind of configuration
    # that it will store, so I'd rather put it there, since I believe this is more intuitive for Blender users than coming up with my own conventions.
# endregion
class MagickCowScenePanel(bpy.types.Panel):
    bl_label = "MagickCow Scene Configuration"
    bl_idname = "SCENE_PT_MagickCow_Scene_Tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene" # This makes the panel appear on under the Scene Properties.

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Scene Display Settings")
        layout.prop(scene, "mcow_scene_display_tags")
        layout.prop(scene, "mcow_scene_display_sync")

        layout.label(text="Scene Export Settings")
        layout.prop(scene, "mcow_scene_mode")
        layout.prop(scene, "mcow_scene_base_path")
        layout.prop(scene, "mcow_scene_animation")
        
        layout.label(text="JSON Export Settings")
        layout.prop(scene, "mcow_scene_json_pretty")
        if scene.mcow_scene_json_pretty:
            layout.prop(scene, "mcow_scene_json_char")
            if scene.mcow_scene_json_char == "SPACE":
                layout.prop(scene, "mcow_scene_json_indent")

# endregion

# region Blender Scene Panel functions, Register and Unregister functions

def update_properties_scene_empty(self, context):
    # NOTE : This is an aux function whose purpose is to restore all of the empties to their saved state
    self.show_name = self.magickcow_empty_original_setting_display_name
    self.empty_display_type = self.magickcow_empty_original_setting_display_type

def update_properties_scene(self, context):
    
    # NOTE : The "self" parameter is simply ignored in this case, we just want to iterate over all of the objects of type empty in the scene and call their respective update methods.
    if context.scene.mcow_scene_mode == "MAP":
        fn = update_properties_map_empty
    
    elif context.scene.mcow_scene_mode == "PHYSICS_ENTITY":
        fn = update_properties_physics_entity_empty
    
    else:
        fn = update_properties_scene_empty
    
    empties = [obj for obj in bpy.data.objects if obj.type == "EMPTY"]
    for empty in empties:
        fn(empty, context)

def register_properties_scene():

    # Register properties for the scene panel

    # By default, it will be marked as None, so you need to manually select what type of object you want to export the scene as.
    # This is done as a safeguard to prevent unexpectedly long export times or receiving an unexpected output exported file, which would needlessly waste the user's time if they
    # forget to pick the type when this could just error out quickly.
    # The resulting behaviour is that the program simply displays an error when the export button is pressed, notifying the user that the export process failed because no export type was chosen / selected.
    bpy.types.Scene.mcow_scene_mode = bpy.props.EnumProperty(
        name = "Export Mode",
        description = "Select the type of object that will be exported when exporting the current scene to a JSON file.",
        items = [
            ("NONE", "None", "The current scene will not be exported as any type of object. Exporting as a MagickaPUP JSON file will be disabled until the user selects what type of export they want to perform with the current scene."),
            ("MAP", "Map", "The current scene will be exported as an asset containing a map for Magicka."),
            ("PHYSICS_ENTITY", "Physics Entity", "The current scene will be exported as an asset containing a physics entity for Magicka.")
        ],
        default = "NONE",
        update = update_properties_scene
    )

    bpy.types.Scene.mcow_scene_json_pretty = bpy.props.BoolProperty(
        name = "Pretty Format",
        description = "The JSON file will be exported with indentation and newlines for easier reading. Slows down export times due to the extra processing required. Also increasing the resulting file size."
    )

    bpy.types.Scene.mcow_scene_json_indent = bpy.props.IntProperty(
        name = "Indent Depth",
        description = "Number of space characters to use in the output JSON file for indentation. This setting is ignored if pretty JSON formatting is disabled.",
        default = 2,
        min = 1,
        max = 256 # Again, who in the name of fuck will ever use this? I don't know, but fuck you if you do! lmao...
    )

    bpy.types.Scene.mcow_scene_json_char = bpy.props.EnumProperty(
        name = "Indent Character",
        description = "The character to be used to indent in the generated JSON files.",
        items = [
            ("SPACE", "Space", "Space character (' ')"),
            ("TAB", "Tab", "Tab character ('\\t')")
        ],
        default = "SPACE"
    )

    # NOTE : A list of benefits of storing all of the export config within the scene panel rather than the export menu:
    # - The settings are saved across sessions (extremely useful for the base folder path, it used to be extremely fucking annoying for it to disappear all the time when reopening a Blender project...)
    # - The settings are tied to a specific blend file within a single session rather than being carried over across scenes (if you have multiple scenes, and some are maps and others are assets, it can become a fucking pain in the ass to constantly have to change the export settings and fine tune them, when you could just do it once and be done with it...)
    # Note that having to reconfigure the export each time you make a new project is an extremely minor inconvenience compared to the crap one had to put up with before... not to mention that this is how Valve does it in their source tools for blender...
    # In short, it is far more benefitial to associate these settings on a per project basis than on a global basis for the entire editor...
    bpy.types.Scene.mcow_scene_base_path = bpy.props.StringProperty(
        name = "Base Directory Path",
        description = "Select the path in which the exporter will look for the base directory. This directory contains JSON files which correspond to effects (materials) that will be applied to the surfaces that have a material with the name of the corresponding effect file to be used.",
        default = "C:\\"
    )

    # TODO : Improve the description string so that it is more generic and also applies to all other forms of exportable object types / scene types rather than being specific to level (map) export.
    bpy.types.Scene.mcow_scene_animation = bpy.props.BoolProperty(
        name = "Export Animation Data",
        description = "Determines whether the animation data of the current scene will be exported or not.\n - If True : The animated level parts will be exported, including all of the child objects and animation data.\n - If False : The animated level parts will be completely ignored and not exported. All children components, including geometry, lights, and any other type of object, that is attached to animated level parts, will also be ignored.\n - Note : The animated level parts root still needs to be present for the exporter to properly generate the level data.",
        default = False
    )

    bpy.types.Scene.mcow_scene_display_tags = bpy.props.BoolProperty(
        name = "Display Object Tags",
        description = "Display name tags for point data objects such as locators and triggers.",
        default = True,
        update = update_properties_scene
    )

    bpy.types.Scene.mcow_scene_display_sync = bpy.props.BoolProperty(
        name = "Synchronize Displayed State",
        description = "Synchronize the displayed state with the internal state of MagickCow object configuration. Useful for visualization purposes.",
        default = True,
        update = update_properties_scene
    )

    # Register the scene panel itself
    bpy.utils.register_class(MagickCowScenePanel)

def unregister_properties_scene():
    
    # Unregister properties for the scene panel
    del bpy.types.Scene.mcow_scene_mode
    del bpy.types.Scene.mcow_scene_json_pretty
    del bpy.types.Scene.mcow_scene_json_indent
    del bpy.types.Scene.mcow_scene_base_path
    del bpy.types.Scene.mcow_scene_animation
    del bpy.types.Scene.mcow_scene_display_tags
    del bpy.types.Scene.mcow_scene_display_sync

    # Unregister the scene panel
    bpy.utils.unregister_class(MagickCowScenePanel)

# endregion
