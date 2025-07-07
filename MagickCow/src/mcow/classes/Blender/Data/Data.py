# region Custom Blender Property types and related Blender Operator classes

# This region contains classes that describe custom property types for Blender.
# Note that these properties can be used on any place in Blender, such as object properties or scene properties.

# region Resistances

# TODO : Maybe make the elements enum into some kind of function that returns the result of the bpy.props.EnumProperty() call so that we can make element enums anywhere we want?
# Also, think about adding support for all of the possible values for elements, including stuff like "Beams" and whatnot...
class MagickCowProperty_Resistance(bpy.types.PropertyGroup):
    element : bpy.props.EnumProperty(
        name = "Element",
        description = "Magical element described by this entry",
        items = [
            ("Water", "Water", "Water Element"),
            ("Life", "Life", "Life Element"),
            ("Shield", "Shield", "Shield Element"),
            ("Cold", "Cold", "Cold Element"),
            ("Lighting", "Lighting", "Electricity Element"),
            ("Arcane", "Arcane", "Arcane Element"),
            ("Earth", "Earth", "Earth Element"),
            ("Fire", "Fire", "Fire Element"),
            ("Steam", "Steam", "Steam Element"),
            ("Ice", "Ice", "Ice Element"),
            ("Poison", "Poison", "Poison Element")
        ],
        default = "Earth"
    )
    multiplier : bpy.props.FloatProperty(
        name = "Multiplier",
        description = "Multiplies the effects applied by the selected element. If set to 1, the value will be unchanged and the default damage will be applied. If set to a negative value, the effects of the spell will be inverted. If set to 0, the spell will have no effect unless specified on the modifier property.",
        default = 1
    )
    modifier : bpy.props.FloatProperty(
        name = "Modifier",
        description = "Modifies the effects applied by the selected element. If set to 0, the value will be unchaged.",
        default = 0
    )

class MAGICKCOW_OT_Operator_Resistance_AddItem(bpy.types.Operator):
    bl_label = "Add"
    bl_idname = "magickcow.resistance_add_item"
    def execute(self, context):
        obj = context.object
        obj.mcow_physics_entity_resistances.add()
        return {"FINISHED"}

class MAGICKCOW_OT_Operator_Resistance_RemoveItem(bpy.types.Operator):
    bl_label = "Remove"
    bl_idname = "magickcow.resistance_remove_item"
    index : bpy.props.IntProperty() # NOTE : For this property to be accessible from the outside without errors, we need to use ":" rather than "=" on assignment, for some reason...
    def execute(self, context):
        obj = context.object
        if self.index >= 0 and self.index < len(obj.mcow_physics_entity_resistances): # NOTE : This check is not really necessary considering how we're assured that the index should theoretically always be correct when iterating on the collection.
            obj.mcow_physics_entity_resistances.remove(self.index)
        return {"FINISHED"}

def register_property_class_resistance():
    bpy.utils.register_class(MagickCowProperty_Resistance)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

def unregister_property_class_resistance():
    bpy.utils.unregister_class(MagickCowProperty_Resistance)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Resistance_RemoveItem)

# endregion

# region Gibs

class MagickCowProperty_Gib(bpy.types.PropertyGroup):
    model : bpy.props.StringProperty(
        name = "Model",
        description = "Path to the file that contains the model used for this gib",
        default = "..\\..\\Models\\AnimatedProps\\Dungeons\\gib_slime01_0"
    )

    mass : bpy.props.FloatProperty(
        name = "Mass",
        description = "The mass of this gib",
        default = 20
    )

    scale : bpy.props.FloatProperty(
        name = "Scale",
        description = "The scale of this gib",
        default = 1
    )

class MAGICKCOW_OT_Operator_Gib_AddItem(bpy.types.Operator):
    bl_label = "Add"
    bl_idname = "magickcow.gibs_add_item"
    def execute(self, context):
        obj = context.object
        obj.mcow_physics_entity_gibs.add()
        return {"FINISHED"}

class MAGICKCOW_OT_Operator_Gib_RemoveItem(bpy.types.Operator):
    bl_label = "Remove"
    bl_idname = "magickcow.gibs_remove_item"
    index : bpy.props.IntProperty()
    def execute(self, context):
        obj = context.object
        if self.index >= 0 and self.index < len(obj.mcow_physics_entity_gibs):
            obj.mcow_physics_entity_gibs.remove(self.index)
        return {"FINISHED"}

def register_property_class_gib():
    bpy.utils.register_class(MagickCowProperty_Gib)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.register_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

def unregister_property_class_gib():
    bpy.utils.unregister_class(MagickCowProperty_Gib)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_AddItem)
    bpy.utils.unregister_class(MAGICKCOW_OT_Operator_Gib_RemoveItem)

# endregion

# region Global Property Register and Unregister functions

def register_properties_classes():
    register_property_class_resistance() # Resistances
    register_property_class_gib() # Gibs
    

def unregister_properties_classes():
    unregister_property_class_resistance() # Resistances
    unregister_property_class_gib() # Gibs

# endregion

# endregion
