# region Blender Panel Classes for N-Key Panel

# region Internal logic classes

# NOTE : This is a dummy class that exists to draw empty panels
class MagickCowPanelObjectPropertiesNone:
    def draw(self, layout, obj):
        layout.label(text = "No available properties:")
        layout.label(text = " - Export mode is \"None\"!")

class MagickCowPanelObjectPropertiesGeneric:
    # Properties that must be displayed for all objects no matter their type
    def draw(self, layout, obj):
        # NOTE : For information stored within an Ojbect, we use obj directly. For information stored within a specific type, we must access obj.data
        layout.prop(obj, "magickcow_allow_export")
        return

class MagickCowPanelObjectPropertiesMap:
    
    # Base draw function. Calls the specific drawing functions based on the type of the selected object.
    def draw(self, layout, obj):
        
        # If the object exists (the user is currently selecting an object), draw the properties in the panel
        # The displayed properties are changed depending on the type of the selected object
        # This "if obj" thing could be an early return with "if not obj" or whatever, but all examples I've seen do it like this, so there must be a pythonic reason to do this...
        if obj:
            if obj.type == "LIGHT":
                self.draw_light(layout, obj)
            elif obj.type == "MESH":
                self.draw_mesh(layout, obj)
            elif obj.type == "EMPTY":
                self.draw_empty(layout, obj)
    
    # Properties that must be displayed for empties
    def draw_empty(self, layout, obj):
        layout.prop(obj, "magickcow_empty_type")
        
        if obj.magickcow_empty_type == "LOCATOR":
            layout.prop(obj, "magickcow_locator_radius")
        elif obj.magickcow_empty_type == "PARTICLE":
            layout.prop(obj, "magickcow_particle_name")
            layout.prop(obj, "magickcow_particle_range")
        elif obj.magickcow_empty_type == "PHYSICS_ENTITY":
            layout.prop(obj, "magickcow_physics_entity_name")
        elif obj.magickcow_empty_type == "BONE":
            layout.prop(obj, "magickcow_locator_radius")
            layout.prop(obj, "magickcow_bone_affects_shields")
            layout.prop(obj, "magickcow_collision_enabled")
            if obj.magickcow_collision_enabled:
                layout.prop(obj, "magickcow_collision_material")
    
    
    # Properties that must be displayed for lights
    def draw_light(self, layout, obj):
        layout.prop(obj.data, "magickcow_light_type")
        layout.prop(obj.data, "magickcow_light_color_diffuse")
        layout.prop(obj.data, "magickcow_light_color_ambient")
        layout.prop(obj.data, "magickcow_light_variation_type")
        layout.prop(obj.data, "magickcow_light_variation_speed")
        layout.prop(obj.data, "magickcow_light_variation_amount")
        layout.prop(obj.data, "magickcow_light_reach")
        layout.prop(obj.data, "magickcow_light_use_attenuation")
        layout.prop(obj.data, "magickcow_light_sharpness")
        layout.prop(obj.data, "magickcow_light_cutoffangle")
        layout.prop(obj.data, "magickcow_light_intensity_diffuse")
        layout.prop(obj.data, "magickcow_light_intensity_ambient")
        layout.prop(obj.data, "magickcow_light_intensity_specular")
        layout.prop(obj.data, "magickcow_light_shadow_map_size")
        layout.prop(obj.data, "magickcow_light_casts_shadows")
    
    
    # README : The collision layer / material appears under 2 if blocks in this code, not that it's bad, but important to remember when editing in the future.
    # Properties that must be displayed for meshes
    def draw_mesh(self, layout, obj):
        layout.prop(obj.data, "magickcow_mesh_type")
        
        if obj.data.magickcow_mesh_type == "GEOMETRY":
            self.draw_mesh_geometry(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        elif obj.data.magickcow_mesh_type in ["WATER", "LAVA"]:
            self.draw_mesh_liquid(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        elif obj.data.magickcow_mesh_type == "COLLISION":
            self.draw_mesh_collision(layout, obj)
        elif obj.data.magickcow_mesh_type == "FORCE_FIELD":
            self.draw_mesh_force_field(layout, obj)
            # self.draw_mesh_vertex_properties(layout, obj)
        return
    
    def draw_mesh_geometry(self, layout, obj):
        layout.prop(obj, "magickcow_collision_enabled")
        if(obj.magickcow_collision_enabled):
            layout.prop(obj, "magickcow_collision_material") # 1
        
        layout.prop(obj.data, "magickcow_mesh_sway")
        layout.prop(obj.data, "magickcow_mesh_entity_influence")
        layout.prop(obj.data, "magickcow_mesh_ground_level")
    
    def draw_mesh_liquid(self, layout, obj):
        layout.prop(obj.data, "magickcow_mesh_can_drown")
        layout.prop(obj.data, "magickcow_mesh_freezable")
        layout.prop(obj.data, "magickcow_mesh_autofreeze")
    
    def draw_mesh_collision(self, layout, obj):
        layout.prop(obj, "magickcow_collision_material") # 2

    def draw_mesh_force_field(self, layout, obj):
        # layout.prop(obj.data, "magickcow_force_field_ripple_color")
        return
    
    # def draw_mesh_vertex_properties(self, layout, obj):
    #     layout.prop(obj.data, "magickcow_vertex_color_enabled")

class MagickCowPanelObjectPropertiesPhysicsEntity:
    
    def draw(self, layout, obj):
        if obj:
            if obj.type == "EMPTY":
                self.draw_empty(layout, obj)
            elif obj.type == "MESH":
                self.draw_mesh(layout, obj)
    
    def draw_empty(self, layout, obj):
        obj_type = obj.mcow_physics_entity_empty_type
        layout.prop(obj, "mcow_physics_entity_empty_type")
        if obj_type == "ROOT":
            self.draw_empty_root(layout, obj)
        elif obj_type == "BONE":
            self.draw_empty_bone(layout, obj)
    
    def draw_empty_root(self, layout, obj):
        # Simple properties
        layout.prop(obj, "mcow_physics_entity_is_movable")
        layout.prop(obj, "mcow_physics_entity_is_pushable")
        layout.prop(obj, "mcow_physics_entity_is_solid")
        layout.prop(obj, "mcow_physics_entity_mass")
        layout.prop(obj, "mcow_physics_entity_can_have_status")
        layout.prop(obj, "mcow_physics_entity_hitpoints")

        # NOTE : Using the layout.prop(obj, "mcow_physics_entity_resistances") method does not work for lists of properties ("collection properties"). You must use a box instead.

        # Resistances list
        layout.label(text="Resistances")
        layout.operator("magickcow.resistance_add_item")
        for index, item in enumerate(obj.mcow_physics_entity_resistances):
            box = layout.box()
            box.prop(item, "element")
            box.prop(item, "multiplier")
            box.prop(item, "modifier")
            remove_op = box.operator("magickcow.resistance_remove_item")
            remove_op.index = index
        
        # Gibs list
        layout.label(text="Gibs")
        layout.operator("magickcow.gibs_add_item")
        for index, item in enumerate(obj.mcow_physics_entity_gibs):
            box = layout.box()
            box.prop(item, "model")
            box.prop(item, "mass")
            box.prop(item, "scale")
            remove_op = box.operator("magickcow.gibs_remove_item")
            remove_op.index = index
    
    def draw_empty_bone(self, layout, obj):
        # TODO : Implement
        return

    def draw_mesh(self, layout, obj):
        mesh_type = obj.data.mcow_physics_entity_mesh_type
        layout.prop(obj.data, "mcow_physics_entity_mesh_type")
        if mesh_type == "GEOMETRY":
            self.draw_mesh_geometry(layout, obj)
        elif mesh_type == "COLLISION":
            self.draw_mesh_collision(layout, obj)
    
    # NOTE : Collision meshes for physics entities don't have specific collision materials / "channels", so we don't display them, unlike for level part collisions, which do have specific collision materials support.
    def draw_mesh_geometry(self, layout, obj):
        layout.prop(obj, "magickcow_collision_enabled") # Determines if complex collision is enabled or not for this visual mesh.
    
    def draw_mesh_collision(self, layout, obj):
        # NOTE : In the case of physics entities, draw nothing else, because they don't have collision material support, so we don't need to specify it.
        # layout.prop(obj, "magickcow_collision_material")
        return

# endregion

# This class is the one that controls the N-Key panel for selected object configuration.
class OBJECT_PT_MagickCowPropertiesPanel(bpy.types.Panel):

    bl_label = "MagickCow Properties"
    bl_idname = "OBJECT_PT_MagickCowProperties_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MagickCow"

    mcow_panel_none = MagickCowPanelObjectPropertiesNone()
    mcow_panel_generic = MagickCowPanelObjectPropertiesGeneric()
    mcow_panel_map = MagickCowPanelObjectPropertiesMap()
    mcow_panel_physics_entity = MagickCowPanelObjectPropertiesPhysicsEntity()

    # Base draw function. Calls the specific drawing functions based on the type of the selected object.
    def draw(self, context):
        # Get the panel's layout and the currently selected object
        layout = self.layout
        obj = context.object
        
        # Get the scene config to check what scene mode we're in
        mode = context.scene.mcow_scene_mode

        # Draw selected object properties
        # Calls the specific draw functions according to the selected scene mode
        if obj:
            if mode == "MAP":
                self.draw_panel(layout, obj, self.mcow_panel_map)
            elif mode == "PHYSICS_ENTITY":
                self.draw_panel(layout, obj, self.mcow_panel_physics_entity)
            else:
                self.draw_none(layout, obj) # Object panel draw call for case "NONE" or any other invalid value

    # NOTE : The reason I've implemented it like this is because I don't want the generic object properties to be displayed when working with the NONE scene export mode, that way we can quickly signal to the users that they forgot to configure their scene and avoid confusion when they look for settings on a panel and don't find it...
    def draw_panel(self, layout, obj, mcow_panel_type):
        self.mcow_panel_generic.draw(layout, obj) # Draw all of the properties that are common to all object types.
        mcow_panel_type.draw(layout, obj) # Draw all of the properties that are specific to the selected object type.

    def draw_none(self, layout, obj):
        self.mcow_panel_none.draw(layout, obj)

# endregion

# region Blender Object Properties Register, Unregister and Update

# region Object Properties - Map / Level

# NOTE : The name of these parameters is important, as Blender internally calls them using "self = ..." and "context = ...".
# If the names are different, the function will not properly allow objects to be modified.
def update_properties_map_empty(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return

    show_tags_true = bpy.context.scene.mcow_scene_display_tags
    show_tags_false = False

    if self.magickcow_empty_original_setting_must_update:
        # Restore the original settings and mark as updated / restored
        self.magickcow_empty_original_setting_must_update = False
        self.empty_display_type = self.magickcow_empty_original_setting_display_type
        self.show_name = self.magickcow_empty_original_setting_display_name
    
    else:
        # Save / Back Up the original settings
        self.magickcow_empty_original_setting_display_type = self.empty_display_type
        self.magickcow_empty_original_setting_display_name = self.show_name
    
    if self.magickcow_empty_type != "NONE":
        # Mark for restoration so that it will restore its original settings when returning to the default empty type ("NONE")
        self.magickcow_empty_original_setting_must_update = True
        
        # Perform the corresponding updates for each empty type
        if self.magickcow_empty_type == "LOCATOR":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
                
        elif self.magickcow_empty_type == "TRIGGER":
            self.empty_display_type = "CUBE"
            self.show_name = show_tags_true
        
        elif self.magickcow_empty_type == "PARTICLE":
            self.empty_display_type = "SPHERE"
            self.show_name = show_tags_false
        
        elif self.magickcow_empty_type == "BONE":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
        
        elif self.magickcow_empty_type == "PHYSICS_ENTITY":
            self.empty_display_type = "ARROWS"
            self.show_name = show_tags_false

def register_properties_map_empty():
    empty = bpy.types.Object
    
    # Object type for empty objects
    empty.magickcow_empty_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object",
        items = [
            ("NONE", "None", "This object will be treated as a regular empty object and will be ignored by the exporter"),
            ("ROOT", "Root", "This object will be exported as the root of the level scene"),
            ("LOCATOR", "Locator", "This object will be exported as a locator"),
            ("TRIGGER", "Trigger", "This object will be exported as a trigger"),
            ("PARTICLE", "Particle", "This object will be exported as a particle effect"),
            ("BONE", "Bone", "This object will be exported as a model bone for animated level parts"),
            ("PHYSICS_ENTITY", "Physics Entity", "This object will be exported as a physics entity"),
            # ("HIERARCHY_NODE", "Hierarchy Node", "This object will be used to structure the hierarchy of the scene. Allows the exporter to organize the objects in the scene.")
        ],
        default = "NONE", # By default, it will be marked as none, so you need to manually select whether you want the empty to be a locator or a trigger
        update = update_properties_map_empty
    )
    
    # Locator Properties
    empty.magickcow_locator_radius = bpy.props.FloatProperty(
        name = "Radius",
        description = "Radius of the locator",
        default = 2.0
    )
    
    # Particle Properties
    empty.magickcow_particle_name = bpy.props.StringProperty(
        name = "Particle",
        description = "Name of the effect XML file to use for this particle",
        default = "ambient_fire_torch"
    )
    
    empty.magickcow_particle_range = bpy.props.FloatProperty(
        name = "Range",
        description = "Range of the particle effect",
        default = 0.0
    )
    
    # Properties to save original settings of the empty (this is used in case we go back from a locator / trigger to a "none" default empty)
    empty.magickcow_empty_original_setting_display_type = bpy.props.StringProperty(
        name = "__original_display_type__",
        description = "Determines the original display type of the selected empty. Used to return to the original display config when selecting type None",
        default = "__none__",
        maxlen = 1024
    )
    empty.magickcow_empty_original_setting_display_name = bpy.props.BoolProperty(
        name = "__original_display_name__",
        description = "Determines the original display name of the selected empty. Used to return to the original display config when selecting type None",
        default = False
    )
    empty.magickcow_empty_original_setting_must_update = bpy.props.BoolProperty(
        name = "__original_display_must_update__",
        description = "Determines if the original display settings must be restored",
        default = False
    )
    
    # Bone Properties
    empty.magickcow_bone_affects_shields = bpy.props.BoolProperty(
        name = "Affects Shields",
        description = "Determines whether this animated level part will affect shields (wards) or not.",
        default = True
    )
    
    # Collision Properties
    empty.magickcow_collision_enabled = bpy.props.BoolProperty(
        name = "Has Collision",
        description = "Determines whether this object will have a collision mesh when exported or not.",
        default = True
    )
    empty.magickcow_collision_material = bpy.props.EnumProperty(
        name = "Collision Material",
        description = "Determine the collision material used by this object's collision",
        items = [
            ("GENERIC", "Generic", "The material will be marked as generic"),
            ("GRAVEL", "Gravel", "The material will be marked as gravel"),
            ("GRASS", "Grass", "The material will be marked as grass"),
            ("WOOD", "Wood", "The material will be marked as wood"),
            ("SNOW", "Snow", "The material will be marked as snow"),
            ("STONE", "Stone", "The material will be marked as stone"),
            ("MUD", "Mud", "The material will be marked as mud"),
            ("REFLECT", "Reflect", "The material will be marked as reflective. Allows beams (arcane and healing) to reflect from this surface. Used for objects like mirrors from R'lyeh."),
            ("WATER", "Water", "The material will be marked as water"),
            ("LAVA", "Lava", "The material will be marked as lava")
        ],
        default = "GENERIC"
    )

    # Physics Entity Properties
    empty.magickcow_physics_entity_name = bpy.props.StringProperty(
        name = "Template",
        description = "Name of the physics entity template XNB file to use for this physics entity",
        default = "barrel_explosive"
    )

def unregister_properties_map_empty():
    empty = bpy.types.Object
    
    del empty.magickcow_empty_type
    del empty.magickcow_locator_radius
    del empty.magickcow_empty_original_setting_display_type
    del empty.magickcow_empty_original_setting_display_name
    del empty.magickcow_empty_original_setting_must_update
    del empty.magickcow_particle_name
    del empty.magickcow_particle_range
    del empty.magickcow_bone_affects_shields
    del empty.magickcow_collision_enabled
    del empty.magickcow_collision_material
    del empty.magickcow_physics_entity_name

def register_properties_map_mesh():
    mesh = bpy.types.Mesh
    
    # region Object type for mesh objects:
    
    mesh.magickcow_mesh_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object",
        items = [
            ("GEOMETRY", "Geometry", "This object will be exported as a piece of level geometry"),
            ("COLLISION", "Collision", "This object will be exported as a piece of level collision"),
            ("WATER", "Water", "This object will be exported as a liquid of type \"Water\""),
            ("LAVA", "Lava", "This object will be exported as a liquid of type \"Lava\""),
            ("NAV", "Nav", "This object will be exported as a nav mesh"),
            ("FORCE_FIELD", "Force Field", "This object will be exported as a force field")
        ],
        default = "GEOMETRY"
    )

    # endregion
    
    # region Liquid properties (for both water and lava):
    
    mesh.magickcow_mesh_can_drown = bpy.props.BoolProperty(
        name = "Can Drown Entities",
        description = "Determines whether the entities that collide with this liquid's surface will die by drowning in the liquid or not. Useful for maps with shallow water like \"Eye Sockey Rink\", where entities can contact the liquid but will not instantly drown. Entities will drown both in water and lava when this setting is enabled for the selected liquid.",
        default = False
    )
    mesh.magickcow_mesh_freezable = bpy.props.BoolProperty(
        name = "Freezable",
        description = "Determines whether the liquid can be frozen or not. Note that liquid freezing works on a per vertex manner, meaning that a freezable surface needs to be subdivided to have enough vertices to allow for proper freezing behaviour.", # This is probably because it uses vertex painting / weights for freezing (makes sense if you think about how water sort of freezes in square patches in Magicka and Magicka 2). This means that a somewhat evenly distributed grid of vertices is the best way to go to make freezable liquids.
        default = False
    )
    mesh.magickcow_mesh_autofreeze = bpy.props.BoolProperty(
        name = "Auto Freeze",
        description = "Determines whether the liquid will freeze automatically or not. Useful for cold maps and areas like \"Frostjord\" where the environment is cold and water would logically freeze automatically into ice as time passes.",
        default = False
    )

    # endregion

    # region Force Field Properties

    # NOTE : Disabled because this property is now controlled via material JSON files.
    """
    mesh.magickcow_force_field_ripple_color = bpy.props.FloatVectorProperty(
        name = "Ripple Color",
        description = "Color used for the ripple effect displayed when an entity collides with the force field.\nThe lower the values, the more transparent they will appear. This means that color < 0.0, 0.0, 0.0 >, which corresponds to black, is displayed as a transparent ripple effect with no color tint.",
        subtype = "COLOR",
        default = (0.0, 0.0, 0.0),
        min = 0.0,
        max = 1.0,
        size = 3 # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
    )
    """

    # endregion

    # region Vertex Properties
    
    # NOTE : Some day in the future we may allow adding custom properties at will to the vertices, for now we're just going to roll with the same config for all meshes except for vertex color,
    # cause that's the only special case there is for now tbh. Something something ease of use etc etc...
    """
    mesh.magickcow_vertex_normal_enabled = bpy.props.BoolProperty(
        name = "Use Vertex Normals",
        description = "Allow vertex normals to be exported for this mesh",
        default = True
    )
    mesh.magickcow_vertex_tangent_enabled = bpy.props.BoolProperty(
        name = "Use Vertex Tangents",
        description = "Allow vertex tangents to be exported for this mesh",
        default = True
    )
    mesh.magickcow_vertex_color_enabled = bpy.props.BoolProperty(
        name = "Vertex Color Enabled",
        description = "Export the vertex color property for this mesh",
        default = True
    )
    """
    # endregion

    # region Extra Deferred Effect Instance Properties

    # NOTE : These values properties describe values that correspond to parameters of the deferred effect's shader.
    # These values are ONLY applied by Magicka to static root node mesh parts of the level model, and they are applied to the RenderDeferredEffect instance (keyword INSTANCE!!!) used by said mesh part, which means
    # that this is a property that is not stored on the effect "material" file, but rather applied during runtime to specific instances of the material, and altough theoretically one could inject these values
    # into memory on effect instances that are assigned to animated level parts, these properties are actually only loaded by the game when reading them from root nodes, so they can only be used on static level parts.
    # The reader code for render deferred effects does NOT read these properties directly, so that means that the only way to modify them in vanilla Magicka executables is through the BiTreeRootNode's properties, which
    # set these values and then apply them to their material / effect instance.

    mesh.magickcow_mesh_sway = bpy.props.FloatProperty(
        name = "Sway",
        description = "Set the value of the \"sway\" property of the Deferred Effect instance used by this mesh. Determines how much sway the vertices of this mesh will have. Used to simulate swaying motions such as that of plants like grass and leaves.",
        default = 0.0
    )

    mesh.magickcow_mesh_entity_influence = bpy.props.FloatProperty(
        name = "Entity Influence",
        description = "Set the value of the \"EntityInfluence\" property of the Deferred Effect instance used by this mesh.",
        default = 0.0
    )

    mesh.magickcow_mesh_ground_level = bpy.props.FloatProperty(
        name = "Ground Level",
        description = "Set the value of the \"GroundLevel\" property of the Deferred Effect instance used by this mesh.",
        default = -10.0 # NOTE : We used to hard code this to -10 on the make stage, and it has worked pretty well as a default value for a long time up until now, so that's literally the only reason why -10 is the default value now that ground level is an editable property, because it's battle tested, and because of legacy reasons, lol... in short: It's -10 because history, no other objective reason. The first value I saw on the first map I decompiled was something close to this, so I just rounded the value and called it a day, and it's been like that ever since. Literally just that.
    )

    # endregion

def unregister_properties_map_mesh():
    mesh = bpy.types.Mesh
    
    del mesh.magickcow_mesh_type
    del mesh.magickcow_mesh_can_drown
    del mesh.magickcow_mesh_freezable
    del mesh.magickcow_mesh_autofreeze
    # del mesh.magickcow_force_field_ripple_color

    # del mesh.magickcow_vertex_normal_enabled
    # del mesh.magickcow_vertex_tangent_enabled
    # del mesh.magickcow_vertex_color_enabled

def update_properties_map_light(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return
    
    self.type = self.magickcow_light_type # The enum literally has the same strings under the hood, so we can just assign it directly.
    self.color = self.magickcow_light_color_diffuse # The color is normalized, so they are identical values.
    
    # Approximation for light radius and intensity because there is no way in modern Blender to set exact light radius for some reason.
    if self.type == "SUN":
        self.energy = 10 * self.magickcow_light_intensity_diffuse
    else:
        self.energy = 100 * self.magickcow_light_intensity_diffuse * self.magickcow_light_reach
        self.use_custom_distance = True
        self.cutoff_distance = self.magickcow_light_reach

def register_properties_map_light():
    light = bpy.types.Light

    # NOTE : If the values from the props synced with blender props are changed from the Blender UI panel, the sync breaks.
    # The syncing is performed only for visual reasons "in-editor" (aka for visualization within Blender to be prettier with lights using the right color and stuff...), the real final
    # values used should be extracted from the mcow properties, so this desync should not matter, as it is only visual, and will only last until the mcow prop is modified once more, syncing them again. 

    # Light type settings:
    # NOTE : The enum values are literally the same as Blender's base lights so that the update function can update the light types automatically.
    light.magickcow_light_type = bpy.props.EnumProperty(
        name = "",
        description = "",
        items = [
            ("POINT", "Point", "This light will be treated as a point light."),
            ("SUN", "Directional", "This light will be treated as a directional light (Sun)."),
            ("SPOT", "Spot", "This light will be treated as a spotlight.")
        ],
        default = "POINT",
        update = update_properties_map_light
    )

    # Light Variation Settings:
    light.magickcow_light_variation_type = bpy.props.EnumProperty(
        name = "Variation Type",
        description = "Determine the type of light variation to be used by this light source when exported.",
        items = [
            ("NONE", "None", "This light will have no variation"),
            ("SINE", "Sine", "This light will have the variation determined by a sine wave"),
            ("FLICKER", "Flicker", "This light will flicker"),
            ("CANDLE", "Candle", "This light will behave like a candle"),
            ("STROBE", "Strobe", "This light will behave like a strobe")
        ],
        default = "NONE"
    )
    
    light.magickcow_light_variation_speed = bpy.props.FloatProperty(
        name = "Variation Speed",
        description = "The speed of light variation",
        default = 0.0
    )
    
    light.magickcow_light_variation_amount = bpy.props.FloatProperty(
        name = "Variation Amount",
        description = "The amount of light variation",
        default = 0.0
    )
    
    # Light radius settings
    light.magickcow_light_reach = bpy.props.FloatProperty(
        name = "Reach",
        description = "The \"distance\" or \"radius\" of effect of the light.\n - For point lights, it defines the radius.\n - For spot lights, it defines the length of the light.\n - For directional lights, it is ignored.",
        default = 5.0,
        update = update_properties_map_light
    )
    
    # Light attenuation and cutoff settings
    light.magickcow_light_use_attenuation = bpy.props.BoolProperty(
        name = "Use Attenuation",
        description = "Determines if the light should use attenuation or not",
        default = False
    )
    
    light.magickcow_light_cutoffangle = bpy.props.FloatProperty(
        name = "Cutoff Angle",
        description = "Angle at which the light is cut off",
        default = 0.0
    )
    
    light.magickcow_light_sharpness = bpy.props.FloatProperty(
        name = "Sharpness",
        description = "Sharpness of the light",
        default = 0.0
    )
    
    # Light color properties
    light.magickcow_light_color_diffuse = bpy.props.FloatVectorProperty(
        name = "Diffuse Color",
        description = "Difuse color of the light",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3, # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
        update = update_properties_map_light
    )
    
    light.magickcow_light_color_ambient = bpy.props.FloatVectorProperty(
        name = "Ambient Color",
        description = "Ambient color of the light",
        subtype = "COLOR",
        default = (1.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        size = 3 # RGB has 3 values. Magicka lights are Vec3, so no alpha channel.
    )
    
    # Intensity settings:
    light.magickcow_light_intensity_specular = bpy.props.FloatProperty(
        name = "Specular Intensity",
        description = "Specular intensity of the light",
        default = 0.0
    )
    
    light.magickcow_light_intensity_diffuse = bpy.props.FloatProperty(
        name = "Diffuse Intensity",
        description = "Intensity of the light's diffuse color emission. Acts as a multiplier over the diffuse color value. The result is NOT clamped to the [0,1] interval.",
        default = 1.0,
        update = update_properties_map_light
    )
    
    light.magickcow_light_intensity_ambient = bpy.props.FloatProperty(
        name = "Ambient Intensity",
        description = "Intensity of the light's ambient color. Acts as a multiplier over the ambient color value. The result is NOT clamped to the [0,1] interval.",
        default = 1.0
    )
    
    # Other light settings:
    light.magickcow_light_shadow_map_size = bpy.props.IntProperty(
        name = "Shadow Map Size",
        description = "Size of the shadow map used for the light",
        default = 64,
        min = 0
    )
    
    light.magickcow_light_casts_shadows = bpy.props.BoolProperty(
        name = "Casts Shadows",
        description = "Determine whether the light should cast shadows or not",
        default = True
    )

def unregister_properties_map_light():
    light = bpy.types.Light
    
    del light.magickcow_light_type
    del light.magickcow_light_variation_type
    del light.magickcow_light_variation_speed
    del light.magickcow_light_variation_amount
    del light.magickcow_light_reach
    del light.magickcow_light_use_attenuation
    del light.magickcow_light_cutoffangle
    del light.magickcow_light_sharpness
    del light.magickcow_light_color_diffuse
    del light.magickcow_light_color_ambient
    del light.magickcow_light_intensity_specular
    del light.magickcow_light_intensity_diffuse
    del light.magickcow_light_intensity_ambient
    del light.magickcow_light_shadow_map_size
    del light.magickcow_light_casts_shadows

def register_properties_map():
    # Register the properties for each object type
    register_properties_map_empty()
    register_properties_map_mesh()
    register_properties_map_light()

def unregister_properties_map():
    # Unregister the properties for each object type
    unregister_properties_map_empty()
    unregister_properties_map_mesh()
    unregister_properties_map_light()

# endregion

# region Object Properties - Physics Entity

# TODO : Implement
# TODO : In the future maybe rework the system so that custom properties are stored within dicts so that we can actually have a better organization and just delete the dict rather than each prop one by one?

def update_properties_physics_entity_empty(self, context):
    
    # Only update the display if the display sync is enabled.
    if not bpy.context.scene.mcow_scene_display_sync:
        return

    show_tags_true = bpy.context.scene.mcow_scene_display_tags
    show_tags_false = False

    if self.magickcow_empty_original_setting_must_update:
        # Restore the original settings and mark as updated / restored
        self.magickcow_empty_original_setting_must_update = False
        self.empty_display_type = self.magickcow_empty_original_setting_display_type
        self.show_name = self.magickcow_empty_original_setting_display_name
    
    else:
        # Save / Back Up the original settings
        self.magickcow_empty_original_setting_display_type = self.empty_display_type
        self.magickcow_empty_original_setting_display_name = self.show_name
    
    if self.mcow_physics_entity_empty_type != "NONE":
        # Mark for restoration so that it will restore its original settings when returning to the default empty type ("NONE")
        self.magickcow_empty_original_setting_must_update = True
        
        # Perform the corresponding updates for each empty type
        if self.mcow_physics_entity_empty_type == "BONE":
            self.empty_display_type = "PLAIN_AXES"
            self.show_name = show_tags_true
        
        elif self.mcow_physics_entity_empty_type == "ROOT":
            self.empty_display_type = "SPHERE"
            self.show_name = show_tags_false
        
        elif self.mcow_physics_entity_empty_type == "BOUNDING_BOX":
            self.empty_display_type = "CUBE"
            self.show_name = show_tags_true

def register_properties_physics_entity_empty():
    
    empty = bpy.types.Object
    
    # region Properties - Generic

    # Object type for empty objects
    empty.mcow_physics_entity_empty_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determine the type of this object.",
        items = [
            ("NONE", "None", "This object will be treated as a regular empty object and will be ignored by the exporter."),
            ("ROOT", "Root", "This object will be exported as the root of a physics entity."),
            ("BONE", "Bone", "This object will be exported as a model bone for a physics entity."),
            ("BOUNDING_BOX", "Bounding Box", "This Object will be exported as a bounding box for the physics entity.")
        ],
        default = "NONE", # By default, it will be marked as none, so you need to manually select what type of point data object you want this to be
        update = update_properties_physics_entity_empty
    )

    # endregion

    # region Properties - Root

    # region Deprecated
    
    # NOTE : Discarded for now because I'm actually going to get the name / ID from the name of the root object in the inspector panel.
    # empty.mcow_physics_entity_id = bpy.props.StringProperty(
    #     name = "ID", # NOTE : The ID must be unique!!! each physics entity asset must have its own unique name within the game's data!!!
    #     description = "Determine the ID of this physics entity",
    #     default = "root"
    # )

    # endregion

    empty.mcow_physics_entity_is_movable = bpy.props.BoolProperty(
        name = "Is Movable", # This hurts me... movable is the "correct" modern spelling used nowadays, moveable is my preferred spelling, altough it is an archaism and nobody really uses it anymore... fuck me, but yeah, I'll pick whatever people use the most so as to make it more user friendly I guess...
        description = "Determines whether this physics entity can be moved or not.",
        default = False
    )

    empty.mcow_physics_entity_is_pushable = bpy.props.BoolProperty(
        name = "Is Pushable",
        description = "Determines whether this physics entity can be pushed or not.",
        default = False
    )

    empty.mcow_physics_entity_is_solid = bpy.props.BoolProperty(
        name = "Is Solid",
        description = "Determines whether this physics entity is solid or not.",
        default = True
    )

    empty.mcow_physics_entity_mass = bpy.props.FloatProperty(
        name = "Mass",
        description = "Determines the mass of this physics object.",
        default = 200
    )

    empty.mcow_physics_entity_hitpoints = bpy.props.IntProperty(
        name = "Health",
        description = "Determines the number of hit points for this physics object.",
        default = 300
    )

    empty.mcow_physics_entity_can_have_status = bpy.props.BoolProperty(
        name = "Can Have Status",
        description = "Determines whether the physics entity can have a status or not.",
        default = True
    )

    empty.mcow_physics_entity_resistances = bpy.props.CollectionProperty(
        type = MagickCowProperty_Resistance,
        name = "Resistances",
        description = "Determines the elemental resistances and weaknesses of this physics entity."
    )

    empty.mcow_physics_entity_gibs = bpy.props.CollectionProperty(
        type = MagickCowProperty_Gib,
        name = "Gibs",
        description = "List of the gibs spawned by this physics entity when destroyed."
    )

    # endregion
    
    return

def unregister_properties_physics_entity_empty():
    empty = bpy.types.Object

    del empty.mcow_physics_entity_empty_type

    del empty.mcow_physics_entity_is_movable
    del empty.mcow_physics_entity_is_pushable
    del empty.mcow_physics_entity_is_solid
    del empty.mcow_physics_entity_mass
    del empty.mcow_physics_entity_hitpoints
    del empty.mcow_physics_entity_can_have_status

    del empty.mcow_physics_entity_resistances
    del empty.mcow_physics_entity_gibs

    return

def register_properties_physics_entity_mesh():
    mesh = bpy.types.Mesh

    mesh.mcow_physics_entity_mesh_type = bpy.props.EnumProperty(
        name = "Type",
        description = "Determines the type of object this piece of geometry will be exported as.",
        items = [
            ("GEOMETRY", "Geometry", "This mesh will be exported as a piece of visual geometry for the physics entity."),
            ("COLLISION", "Collision", "This mesh will be exported as a collision mesh for the physics entity.")
        ],
        default = "GEOMETRY"
    )

def unregister_properties_physics_entity_mesh():
    mesh = bpy.types.Mesh

    del mesh.mcow_physics_entity_mesh_type

def register_properties_physics_entity():
    register_properties_physics_entity_empty()
    register_properties_physics_entity_mesh()

def unregister_properties_physics_entity():
    unregister_properties_physics_entity_empty()
    unregister_properties_physics_entity_mesh()

# endregion

# region Object Properties - Generic

# Generic properties are properties that all objects share no matter their type.

def register_properties_generic():
    obj = bpy.types.Object

    # Allow export option for all objects:
    obj.magickcow_allow_export = bpy.props.BoolProperty(
        name = "Export",
        description = "Determines whether this object will be exported or not. If set to false, the object will be ignored by the exporter, as well as all of its children objects.",
        default = True
    )

def unregister_properties_generic():
    obj = bpy.types.Object
    
    del obj.magickcow_allow_export

# endregion

# region Global Register and Unregister functions for objects

def register_properties_object():

    # Register the properties that all objects should have
    register_properties_generic()

    # Register the properties for each object type and for each scene mode type
    register_properties_map()
    register_properties_physics_entity()

    # Register the class for the properties panel itself
    bpy.utils.register_class(OBJECT_PT_MagickCowPropertiesPanel)

def unregister_properties_object():

    # Unregister the properties that all objects should have
    unregister_properties_generic()

    # Unregister the properties for each object type and for each scene mode type
    unregister_properties_map()
    unregister_properties_physics_entity()

    # Unregister the class for the properties panel itself
    bpy.utils.unregister_class(OBJECT_PT_MagickCowPropertiesPanel)

# endregion

# endregion
