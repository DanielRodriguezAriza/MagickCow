# region Import Data Pipeline class - LevelModel / Map

# TODO : Solve the vertex winding issues on all of the mesh imports... except collisions, which actually have the correct winding as of now.
# TODO : Implement material caching (or maybe I implemented this in the past, but I cannot recall right now).

# TODO : Implement all import functions...
class MCow_ImportPipeline_Map(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        self._cached_lights = {} # Cache object that stores the lights that have been generated so that they can be referenced on the animated level parts import side of the code. Remember that in Magicka's file format, lights are stored on the static level data, but the animated level data can move lights by referencing them through their ID.
        return
    
    def exec(self, data, path):
        self._cached_import_path = path
        level_model = data["XnbFileData"]["PrimaryObject"]
        self.import_level_model(level_model)
    
    def import_level_model(self, level_model):
        # Get the data entries from the level model JSON dict object.
        level_model_mesh = level_model["model"]
        animated_parts = level_model["animatedParts"]
        lights = level_model["lights"]
        effects = level_model["effects"]
        physics_entities = level_model["physicsEntities"]
        liquids = level_model["liquids"]
        force_fields = level_model["forceFields"]
        model_collision = level_model["collisionDataLevel"]
        camera_collision = level_model["collisionDataCamera"]
        triggers = level_model["triggers"]
        locators = level_model["locators"]
        nav_mesh = level_model["navMesh"]
        
        # Import level lights and cache them so that they can be referenced and parented when importing the animated level data.
        lights_objs = self.import_lights(lights)
        for light_obj in lights_objs:
            self._cached_lights[light_obj.name] = light_obj

        # Execute the import functions for each of the types of data found within the level model JSON dict.
        self.import_level_model_mesh(level_model_mesh)
        self.import_animated_parts(animated_parts)
        # NOTE : We used to import the lights here before, just as they were ordered within the JSON file, but the truth is that Magicka's file format for maps requires referencing lights
        # When importing the animated level parts, so we import the lights first and then everything else.
        self.import_effects(effects)
        self.import_physics_entities(physics_entities)
        self.import_liquids(liquids)
        self.import_force_fields(force_fields)
        self.import_model_collision(model_collision)
        self.import_camera_collision(camera_collision)
        self.import_triggers(triggers)
        self.import_locators(locators)
        self.import_nav_mesh(nav_mesh)

    # region Import Methods - Top Level

    def import_level_model_mesh(self, model):
        root_nodes = model["RootNodes"]
        for idx, root_node in enumerate(root_nodes):
            self.import_root_node(idx, root_node)
    
    def import_animated_parts(self, animated_parts):
        for part in animated_parts:
            self.import_animated_part(part, None)
    
    def import_lights(self, lights):
        ans = [self.import_light(light) for light in lights]
        return ans
    
    def import_effects(self, effects):
        ans = [self.import_effect(effect) for effect in effects]
        return ans
    
    def import_physics_entities(self, physics_entities):
        for idx, physics_entity in enumerate(physics_entities):
            self.import_physics_entity(idx, physics_entity)
    
    def import_liquids(self, liquids):
        ans = [self.import_liquid(idx, liquid) for idx, liquid in enumerate(liquids)]
        return ans
    
    def import_force_fields(self, force_fields):
        for idx, force_field in enumerate(force_fields):
            self.import_force_field(idx, force_field)
    
    def import_model_collision(self, collision_data):
        for idx, collision_channel in enumerate(collision_data):
            self.import_collision_mesh_level(collision_channel, idx)
    
    def import_camera_collision(self, collision_data):
        self.import_collision_mesh_camera(collision_data)
    
    def import_triggers(self, triggers):
        for trigger in triggers:
            self.import_trigger(trigger)
    
    def import_locators(self, locators):
        ans = [self.import_locator(locator) for locator in locators]
        return ans
    
    def import_nav_mesh(self, nav_mesh):
        self.import_nav_mesh_internal(nav_mesh, "nav_mesh_static")
    
    # endregion

    # region Import Methods - Internal

    def import_light(self, light):
        # Read the light data
        name = light["LightName"]
        position = self.read_point(light["Position"])
        direction = self.read_point(light["Direction"]) # We use the read_point function, but that's because the translation for any spatial 3D vector, both those that represent points and directions, is the same when transforming from Z-up to Y-up and viceversa.
        light_type = find_light_type_name(light["LightType"])
        variation_type = find_light_variation_type_name(light["LightVariationType"])
        reach = light["Reach"]
        use_attenuation = light["UseAttenuation"]
        cutoff_angle = light["CutoffAngle"]
        sharpness = light["Sharpness"]
        color_diffuse_raw = self.read_color_rgb(light["DiffuseColor"])
        color_ambient_raw = self.read_color_rgb(light["AmbientColor"])
        specular = light["SpecularAmount"]
        variation_speed = light["VariationSpeed"]
        variation_amount = light["VariationAmount"]
        shadow_map_size = light["ShadowMapSize"]
        casts_shadows = light["CastsShadows"]

        # Calculate normalized color RGB values
        color_diffuse = color_diffuse_raw.normalized()
        color_ambient = color_ambient_raw.normalized()
        
        # Calculate light intensity values for the new normalized RGB values
        # region Comment - intensity value calculation
        # NOTE : The results obtained may not be 100% correct. This is the best approximation I could come up with. An input color may have an intensity of a different magnitude for each of the color channels.
        # This code is built on the assumption that the intensity is assumed to be the same multiplier for all channels, even tho it can be manually set to anything by hand. Obviously this assumption is made
        # Because of the intensity property found on the leftover fbx map file within the Magicka game files, which points to the direction that devs deliberatedly made all maps to respect this constraint.
        # Users could edit this by hand if they wanted tho. The best solution in the future would be to actually add support for individual intensity values for each channel. 
        # endregion
        color_diffuse_intensity = color_diffuse_raw.length
        color_ambient_intensity = color_ambient_raw.length

        # Create the light data and modify its properties
        light_data = bpy.data.lights.new(name=name, type=light_type)

        # Create the light object
        light_object = bpy.data.objects.new(name=name, object_data=light_data)

        # Add the light object to the scene (link object to collection)
        bpy.context.collection.objects.link(light_object)

        # Modify light object properties
        light_object.location = position
        light_object.rotation_mode = "QUATERNION" # Set rotation mode to quaternion for the light object.
        light_object.rotation_quaternion = mathutils.Vector((0, 0, -1)).rotation_difference(direction)

        # Modify light mcow properties
        light_data.magickcow_light_type = light_type
        light_data.magickcow_light_variation_type = variation_type
        light_data.magickcow_light_variation_speed = variation_speed
        light_data.magickcow_light_variation_amount = variation_amount
        light_data.magickcow_light_reach = reach
        light_data.magickcow_light_use_attenuation = use_attenuation
        light_data.magickcow_light_cutoffangle = cutoff_angle
        light_data.magickcow_light_sharpness = sharpness
        light_data.magickcow_light_color_diffuse = color_diffuse
        light_data.magickcow_light_color_ambient = color_ambient
        light_data.magickcow_light_intensity_specular = specular
        light_data.magickcow_light_intensity_diffuse = color_diffuse_intensity
        light_data.magickcow_light_intensity_ambient = color_ambient_intensity
        light_data.magickcow_light_shadow_map_size = shadow_map_size
        light_data.magickcow_light_casts_shadows = casts_shadows

        # Return the generated object
        return light_object

    def import_collision_mesh_generic_internal(self, name, json_has_collision, json_vertices, json_triangles):
        has_collision, vertices, triangles = self.read_collision_mesh(json_has_collision, json_vertices, json_triangles)
        if has_collision:
            mesh = bpy.data.meshes.new(name=name)
            obj = bpy.data.objects.new(name=name, object_data=mesh)
            bpy.context.collection.objects.link(obj)
            mesh.from_pydata(vertices, [], triangles)
            mesh.update()
            return (True, obj, mesh)
        else:
            return (False, None, None)

    def import_static_collision_mesh(self, collision, name):
        json_has_collision = collision["hasCollision"]
        json_vertices = collision["vertices"]
        json_triangles = collision["triangles"]
        return self.import_collision_mesh_generic_internal(name, json_has_collision, json_vertices, json_triangles)

    def import_collision_mesh_level(self, collision, channel_index = 0):
        channel_name = find_collision_material_name(channel_index)
        name = f"collision_mesh_model_{channel_index}_{channel_name}"

        has_collision, obj, mesh = self.import_static_collision_mesh(collision, name)

        if has_collision:
            mesh.magickcow_mesh_type = "COLLISION"
            obj.magickcow_collision_material = channel_name

    def import_collision_mesh_camera(self, collision):
        name = "collision_mesh_camera"

        has_collision, obj, mesh = self.import_static_collision_mesh(collision, name)

        if has_collision:
            mesh.magickcow_mesh_type = "CAMERA"

    def import_locator(self, locator):
        # Get the properties of the locator from the json data
        name = locator["Name"]
        transform = self.read_mat4x4(locator["Transform"])
        radius = locator["Radius"]

        # region Comment - empty display explanation
        # NOTE : The display type is updated automatically when we change the property empty.magickcow_empty_type, since it is linked to an update function,
        # so we don't need to call this ourselves by hand. I'm leaving this code behind so that you can remember why we don't do it.
        # empty.empty_display_type = "PLAIN_AXES"
        # endregion
        # Create empty object and add it to the scene and modify its properties
        empty = bpy.data.objects.new(name = name, object_data = None)
        empty.matrix_world = transform

        # Link the object to the current scene collection
        bpy.context.collection.objects.link(empty)

        # Update the mcow properties
        empty.magickcow_empty_type = "LOCATOR"
        empty.magickcow_locator_radius = radius

        # Return the generated object
        return empty

    def import_trigger(self, trigger):
        # Extract the data from the json object
        name = trigger["Name"]
        position = self.read_point(trigger["Position"])
        scale = self.read_scale(trigger["SideLengths"])
        rotation = self.read_quat(trigger["Rotation"])

        # Create the empty object trigger on the Blender scene and assign the properties
        empty = bpy.data.objects.new(name = name, object_data = None)
        
        # Link the object to the scene
        bpy.context.collection.objects.link(empty)

        # Assign the properties to the created empty object
        # NOTE : These values that we are assigning here are the ones used by Magicka's engine in-game.
        # After this, we apply some corrections so that the values are exactly the ones that Blender needs to use.
        empty.location = position
        empty.rotation_mode = "QUATERNION" # Change the rotation mode to quaternion so that we can apply quaternion rotations. Yes, in blender, if you don't change the rotation mode from "XYZ" to "QUATERNION", the rotation_quaternion property will literally do fucking nothing at all...
        empty.rotation_quaternion = rotation
        empty.scale = scale / 2.0 # Set the scale to half of the side of the in-game trigger side lengths because the trigger origin in Magicka is on a corner, but in Blender it's on the center of the trigger's volume.

        # Update the context view layer after changing the location, rotation and scale, so that we can access the most updated values for the transform matrix.
        # Blender does not update this value until it finishes evaluating everything for the next frame, which means that we need to force blender to perform an extra evaluation here
        # so that accessing obj.matrix_world returns the expected value rather than an outdated value.
        bpy.context.view_layer.update()
        
        # Get the relative transform vectors (forward vector, up vector and right vector) of the object on the Blender scene.
        # These will be used to apply some relative translations.
        x_vec = empty.matrix_world.col[0].xyz.normalized()
        y_vec = empty.matrix_world.col[1].xyz.normalized()
        z_vec = empty.matrix_world.col[2].xyz.normalized()

        # Apply corrections to trigger location.
        # Apply a relative transform by half of the in-game scale (which is 100% of the in-Blender scale, since we already divided the scale by half in a previous step)
        # so that the origin point is now aligned with the center of the trigger's volume rather than the corner of the trigger's volume.
        empty.location += x_vec * empty.scale[0]
        empty.location -= y_vec * empty.scale[1]
        empty.location += z_vec * empty.scale[2]

        # Change the mcow empty type. This also updates the empty display type automatically.
        empty.magickcow_empty_type = "TRIGGER"

    def import_effect(self, effect):
        effect_name = effect["id"]
        effect_position = self.read_point(effect["vector1"])
        effect_orientation = self.read_point(effect["vector2"])
        effect_range = effect["range"]
        effect_name = effect["name"]

        obj = bpy.data.objects.new(name = effect_name, object_data = None)
        
        obj.location = effect_position
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = mathutils.Vector((0, -1, 0)).rotation_difference(effect_orientation)

        bpy.context.collection.objects.link(obj)

        obj.magickcow_empty_type = "PARTICLE"
        obj.magickcow_particle_name = effect_name
        obj.magickcow_particle_range = effect_range

        return obj

    def import_physics_entity(self, idx, physics_entity):
        template = physics_entity["template"]
        transform = self.read_mat4x4(physics_entity["transform"])

        obj = bpy.data.objects.new(name=f"physics_entity_{idx}", object_data = None)

        obj.matrix_world = transform

        bpy.context.collection.objects.link(obj)

        obj.magickcow_empty_type = "PHYSICS_ENTITY"
        obj.magickcow_physics_entity_name = template

    def import_root_node(self, idx, root_node):
        # Read root node properties
        is_visible = root_node["isVisible"]
        casts_shadows = root_node["castsShadows"]
        sway = root_node["sway"] # Now that we know what these 3 properties are, we can assign them without any issues!
        entity_influence = root_node["entityInfluence"] # same
        ground_level = root_node["groundLevel"] # same
        vertex_stride = root_node["vertexStride"]
        vertex_declaration = root_node["vertexDeclaration"]
        vertex_buffer = root_node["vertexBuffer"]
        index_buffer = root_node["indexBuffer"]
        effect = root_node["effect"]
        primitive_count = root_node["primitiveCount"]
        # start_index = root_node["startIndex"] # We always read all of the geometry, so for us, the start index is always 0. This is because we just merge all of the contents of child nodes into the same object, since they share the same vertex buffer anwyways. Keeping child nodes as individual objects is more work than it's worth, and it's pretty pointless for 99% of cases anyway...
        # bounding_box = root_node["boundingBox"] # We auto generate a new AABB on export anyways, so this value is not really required.
        
        # region Comment - Child nodes support
        
        # NOTE : Child node support is not required. Children nodes do not have any way of moving geometry around, so they cannot be used to reuse parent geometry at a different location without generating a new vertex buffer.
        # Tbh, I don't really know what the fuck they are for, seeing the code, they are pretty much useless, and I have no clue what the Magicka devs were smoking when they conjured up this idea.
        # All we do in this importer addon is read the entire vertex buffer data and generate a single mesh, which effectively does the same as merging all of the child nodes with their parent nodes into a single mesh.
        # I mean, after all, that IS exactly how they are organized in memory within the vertex buffer data itself. The only purpose that child nodes have is to give different bounding boxes to different segments of
        # the mesh, which is pretty useless in 99% of usecases, and we auto generate those anyway, so yeah. Pretty much, just a premature optimization that actually just bloats memory use unnecessarily and fucks up cache alignment for no reason...
        # has_child_a = ["hasChildA"]
        # has_child_b = ["hasChildB"]
        # child_a = ["childA"]
        # child_b = ["childB"]
        
        # endregion

        # Read the vertex and index buffer data
        obj, mesh = self.import_buffer_mesh(vertex_stride, vertex_declaration, vertex_buffer, index_buffer, f"mesh_{idx}")

        # Asign the mcow mesh properties to the generated mesh data
        mesh.magickcow_mesh_is_visible = is_visible
        mesh.magickcow_mesh_casts_shadows = casts_shadows
        mesh.magickcow_mesh_advanced_settings_enabled = True # We can't really compare equality between the float values of the advanced settings due to precission errors, so we might as well just enable these... besides, these default values were picked by me, so 90% of maps will not have them like that anyway.
        mesh.magickcow_mesh_sway = sway
        mesh.magickcow_mesh_entity_influence = entity_influence
        mesh.magickcow_mesh_ground_level = ground_level
        
        # Asign the mcow object properties to the generated object
        obj.magickcow_collision_enabled = False # We disable the complex collision generation for thei mported mesh since the imported scene already has all of the collision meshes baked into the collision channel meshes, and since we don't want to accidentally add extra collisions on export, we might as well just disable it and assume that the collision channels are what the user expects to get / see on import.

        # Set the mcow mesh type
        mesh.magickcow_mesh_type = "GEOMETRY" # NOTE : This is already the default anyways, so we don't need the statement, but it's here for correctness, just in case the default changes in the future.

        # Read material data and append it to the generated mesh
        material_name = f"material_mesh_{idx}"
        mat = self.read_effect(material_name, root_node["effect"])
        mesh.materials.append(mat)

    def import_liquid(self, idx, liquid):
        # Read the properties from the JSON object
        liquid_type = liquid["$type"]
        vertex_buffer = liquid["vertices"]
        index_buffer = liquid["indices"]
        vertex_declaration = liquid["declaration"]
        vertex_stride = liquid["vertexStride"]
        primitive_count = liquid["primitiveCount"]

        can_drown = liquid["flag"]
        can_freeze = liquid["freezable"]
        can_auto_freeze = liquid["autofreeze"]

        effect = liquid["effect"]

        # Read vertex buffer data and index buffer data
        obj, mesh = self.import_buffer_mesh(vertex_stride, vertex_declaration, vertex_buffer, index_buffer, f"liquid_{idx}_{liquid_type}")

        # Get mcow mesh type from input liquid type.
        # NOTE : In the future, this may be modified / removed, IF / when the WATER / LAVA system is deprecated / modified (if it ever happens)
        if liquid_type == "liquid_water":
            mesh_type = "WATER"
        elif liquid_type == "liquid_lava":
            mesh_type = "LAVA"
        else:
            raise MagickCowImportException(f"Imported liquid has unknown liquid type: \"{liquid_type}\"")
        
        # Assign mcow properties
        mesh.magickcow_mesh_type = mesh_type
        mesh.magickcow_mesh_can_drown = can_drown
        mesh.magickcow_mesh_freezable = can_freeze
        mesh.magickcow_mesh_autofreeze = can_auto_freeze

        # Create material and assign it to the mesh
        mat_name = f"liquid_material_{idx}_{liquid_type}"
        mat = self.read_effect(mat_name, effect)
        mesh.materials.append(mat)

        # Return the generated object for further use
        return obj

    def import_force_field(self, idx, force_field):
        # Get data from the input json object
        vertex_buffer = force_field["vertices"]
        index_buffer = force_field["indices"]
        vertex_declaration = force_field["declaration"]
        vertex_stride = force_field["vertexStride"]

        # Generate object and mesh data
        obj, mesh = self.import_buffer_mesh(vertex_stride, vertex_declaration, vertex_buffer, index_buffer, f"force_field_{idx}")

        # Assign mcow properties to mesh
        mesh.magickcow_mesh_type = "FORCE_FIELD"

        # Create material data and assign it to the mesh
        mat_name = f"force_field_material_{idx}"
        mat = self.read_effect(mat_name, force_field) # NOTE : The material effect data is embedded within the force field object itself.
        mesh.materials.append(mat)

    def import_animated_part(self, part, parent):
        # region Comments - Stuff to figure out about the animated level part import implementation

        # TODO : Figure out how to deal with animated level parts from the base game which contain more than one bone... I just found one like that on wc_s4, and it sure will make things a bit harder to deal with.
        # Note that for my exporter implementation, I settled for every single part having a single bone, and any child bones being a separate part, which is what the vs boat map does, so yeah... this is gonna be
        # a bit complicated to deal with, I suppose...
        # NOTE : Considering how only the root bone of an animated level part can be moved (it's the one used to describe the motion), we have 2 possible solutions here:
        # 1) Modify the exporter so that child bones with no motion and identical collision channel as their parents are not added to separate animated level part on export, but rather they are added as child bones of the same XNA model hierarchy.
        # 2) Accept that the importer will translate things to the way mcow does it, just add a different child animated level part on import and have it exist so that we don't break pois. On export, it will be a separate animated level part, but theoretically, the outcome should be the same, so we just compile to an slightly different form hierarchy-wise.
        # Option 1 may be a bit more elegant, but option 2 requires far less work in the long run, and is probably just as valid. Also note that this would never even be a problem if the magicka devs hadn't made maps that contain for some fucking stupid reason multiple bones on the same animated level part, when only the root matters... which means that they just exist as a way to add different identifiers to pois but for the same fucking object, like wtf?
        # iirc, pois are identified with part_name.child_part_name.child_bone_name etc... which means that this does lead to different pois with different names, but they point to the same fucking visual object, so wtf?
        # This also means that we can't really get away with option 2, since that means that objects with geometry that must glow when pointing at a poi will no longer do so on recompilation... wtf... artificial problems...

        # NOTE : All of this may not matter at all if in the base game, these sort of "leaf" bones are never really used for anything and just exist for some fucking weird reason...
        # If that's the case, then we can just ignore them and import them as new bones, and go with route 1), which is what I'm gonna be implementing for now.
        # Also, as a warning, note that maybe the impl will change, but I'm sure I will forget to update this comment, so just be aware of the issue for future reference and look at the code to know what impl
        # is actually on the code right now...

        # NOTE : The "extra" bone names could correspond to the mesh names, no? iirc that's the way it works, I don't remember how I implemented it on the exporter, but now that I think about it, it very well could be...
        # TODO : Figure this part out again and then properly implement the fucking importer ffs...

        # endregion

        # TODO : Finish implementing

        # Get properties for the animated level part
        name = part["name"] # NOTE : For now, we're taking the bone name from the part name. From what I've seen, these should always match (the name of this part and the name of the root bone of this part), but if in the future I find any examples on the base game that don't match, then it would be important to revise this implementation and change it.
        affects_shields = part["affectShields"]

        model = part["model"]
        mesh_settings = part["meshSettings"] # TODO : Implement mesh settings handling
        
        liquids = part["liquids"]
        locators = part["locators"]
        effects = part["effects"]

        lights = part["lights"]

        animation_duration = part["animationDuration"]
        animation = part["animation"]

        has_collision = part["hasCollision"]
        collision_material = part["collisionMaterial"]
        collision_vertices = part["collisionVertices"]
        collision_triangles = part["collisionTriangles"]

        has_nav_mesh = part["hasNavMesh"]
        nav_mesh = part["navMesh"]

        children = part["children"]

        # Internal import process

        # Import animated level part model mesh
        root_bone_obj = self.import_animated_model(model, parent)

        # Import Animation
        self.import_animation_data(animation, root_bone_obj)

        # Import Liquids
        self.import_animated_liquids(liquids, root_bone_obj)

        # Import Locators
        self.import_animated_locators(locators, root_bone_obj)

        # Import Effects
        self.import_animated_effects(effects, root_bone_obj)

        # Import lights
        self.import_animated_lights(lights, root_bone_obj)

        # Import collision
        self.import_animated_collision_mesh(has_collision, collision_material, collision_vertices, collision_triangles, root_bone_obj)

        # Import nav mesh
        self.import_animated_nav_mesh(has_nav_mesh, nav_mesh, root_bone_obj)

        # Import child animated parts
        for child_part in children:
            self.import_animated_part(child_part, root_bone_obj)

        # TODO : Implement property assignment, etc...

    def import_nav_mesh_internal(self, nav_mesh, name):
        # region Comment - Inverted Normals Problem
        # NOTE : The generated nav mesh has inverted normals, and I have no idea as of now if that has any negative impact on the AI's behaviour.
        # So for now, this is ok I suppose, since I have not seen anything within Magicka's code that would point to the face orientation of the nav mesh
        # being taken into account... so this should be ok, but it would be ideal to solve this issue so that people who import maps don't have to deal with the ugly
        # inverted normals, or maybe it's ok, idk.
        # TODO : Fix Me!!!
        # endregion

        json_vertices = nav_mesh["Vertices"]
        json_triangles = nav_mesh["Triangles"]

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["VertexA"], tri["VertexB"], tri["VertexC"]) for tri in json_triangles]

        mesh = bpy.data.meshes.new(name = name)
        obj = bpy.data.objects.new(name = name, object_data = mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        mesh.magickcow_mesh_type = "NAV"

        return obj

    def import_buffer_mesh(self, vertex_stride, vertex_declaration, vertex_buffer, index_buffer, name):
        
        # Read the vertex and index buffer data
        mesh_vertices, mesh_triangles, mesh_normals = self.read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

        # Create mesh data and mesh object
        mesh = bpy.data.meshes.new(name = name)
        obj = bpy.data.objects.new(name = name, object_data = mesh)

        # Link the object to the scene
        bpy.context.collection.objects.link(obj)

        # Generate the mesh data from the vertex buffer and index buffer
        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

        # Select the object so that we can use bpy.ops over this mesh
        obj.select_set(state=True)
        bpy.context.view_layer.objects.active = obj

        # Apply smooth shading to get some default normal groups going
        bpy.ops.object.shade_smooth()

        # region Unused Content

        # Set the vertex normals from the imported data
        # Option 1: Calculate loop normals
        # loop_normals = []
        # for poly in mesh.polygons:
        #     for loop_index in poly.loop_indices:
        #         vertex_index = mesh.loops[loop_index].vertex_index
        #         loop_normals.append(mesh_normals[vertex_index].normalized())
        # mesh.normals_split_custom_set(loop_normals)
        # mesh.update()
        # Option 2: Use the per-vertex normals directly
        # mesh.normals_split_custom_set_from_vertices(mesh_normals)
        # mesh.update()
        # NOTE : This code is disabled for now, since after today's Blender update, importing normals is pretty much broken AFAIK and will lead to geometry that simply crashes on edit.
        # I guess we'll just have to wait for them to patch this out and get their shit together before we can use custom normals...
        # For now, the split faces generate some pretty nice normals automatically, so I guess we'll live with those for now and that's it...

        # Flip the normals so that their direction matches the one expected by Blender
        # bpy.ops.object.mode_set(mode="EDIT")
        # bpy.ops.mesh.flip_normals()
        # bpy.ops.object.mode_set(mode="OBJECT")
        # NOTE : This code is disabled for now, because since 4.2, flipping normals crashes the editor, so we can't fix this either unless I manually flip them myself on import!!!
        # WOW BLENDER IS SO GOOD!!!!

        # endregion

        # Return the generated object and mesh data block
        return obj, mesh

    # endregion

    # region Import Methods - Internal - Animated

    # TODO : Maybe in the future, make it so that these read functions become members of the base Importer Pipeline class so that the PhysicsEntity Importer can use it as well.
    
    def import_animated_model(self, model, parent_bone_obj):
        # Get model properties
        bones = model["bones"]
        vertex_declarations = model["vertexDeclarations"]
        model_meshes = model["modelMeshes"]

        # Import the root bone of the model
        root_bone_obj = self.import_bone(bones[0], parent_bone_obj)

        # Import the child meshes of this animated level part
        self.import_model_meshes(root_bone_obj, bones, vertex_declarations, model_meshes)

        return root_bone_obj

    # region Comment
    # TODO : Maybe make this function a generic importer pipeline function so that Physics Entities and other such objects can import bones as well?
    # Or at least part of its logic, since the empty object type is Map and PE specific, and when the skinned character mesh export / import support is added, we'll use armatures for that, so only the JSON
    # parsing side of things could be considered generic, everything else requires some specific treatment regarding the object creation process itself and the properties that must be added to properly
    # handle importing and object creation / generation.
    # endregion
    def import_bone(self, bone_data, parent_bone_obj):
        # Get bone properties
        bone_name = bone_data["name"]
        bone_transform = self.read_mat4x4(bone_data["transform"]) # NOTE : This transform is relative to the parent bone of this part. If no parent exists, then obviously it's in global coordinates, since it is relative to the parent, which is the world origin.

        # Create bone object
        bone_obj = bpy.data.objects.new(name=bone_name, object_data=None)
        
        # Set bone transform and attach to parent if there's a parent bone object
        if parent_bone_obj is None:
            bone_obj.matrix_world = bone_transform # Set the matrix world transform matrix
        else:
            bone_obj.parent = parent_bone_obj # Attach the generate bone to the existing parent bone
            bone_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4) # Clear the parent inverse matrix that Blender calculates.
            bone_obj.matrix_basis = bone_transform # Set the relative transform
            # region Comment - Clearing out parent inverse matrix
            
            # We clear the parent inverse matrix that Blender calculates.
            # This way, the relative offset behaviour we get is what we would expect in literally any other 3D software on planet Earth.
            # Note that I'm NOT saying that Blender's parent inverse is useless... no, it's pretty nice... sometimes... but in this case? it's a fucking pain in the ass. So we clear it out.
            # We also could clear it with bpy.ops, but that's a pain in the butt, so easier to just do what bpy.ops does under the hood, which is setting the inverse matrix to the identity,
            # which is the same as having no inverse parent matrix.
            # For more information regarding the parent inverse matrix, read: https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Parenting#Clear_Parent_Inverse_Clarified
            # It will all make sense...
            
            # NOTE : Quote from the article (copy-pasted here just in case the link goes dead at some point in the future):
            # Normally, when a parent relationship is set up, if the parent has already had an object transformation applied, the child does not immediately inherit that.
            # Instead, it only picks up subsequent changes to the parent’s object transformation. What happens is that, at the time the parent relationship is set up, the inverse of the current parent
            # object transformation is calculated and henceforth applied before passing the parent transformation onto the child.
            # This cancels out the initial transformation, leaving the child where it is to start with.
            # This inverse is not recomputed when the parent object is subsequently moved or subject to other object transformations, so the child follows along thereafter.
            # The "Clear Parent Inverse" function sets this inverse transformation to the identity transformation, so the child picks up the full parent object transformation.

            # endregion
        
        # Link the object to the scene
        bpy.context.collection.objects.link(bone_obj)

        # Set mcow properties
        bone_obj.magickcow_empty_type = "BONE"

        # TODO : Refine the handling of the bounding sphere, maybe fully figure out what it does and maybe even auto-generate it like the bounding box for static mesh level parts.

        return bone_obj

    def import_model_meshes(self, root_bone_obj, bones, vertex_declarations, model_meshes):
        for model_mesh in model_meshes:
            
            parent_bone_index = model_mesh["parentBone"]
            parent_bone_data = bones[parent_bone_index]

            json_vertex_buffer = model_mesh["vertexBuffer"]
            json_index_buffer = model_mesh["indexBuffer"]
            
            mesh_parts = model_mesh["meshParts"]

            total_vertices = 0
            for mesh_part in mesh_parts:
                total_vertices += mesh_part["numVertices"]
            vertex_stride = len(json_vertex_buffer["Buffer"]) // total_vertices

            for mesh_part in mesh_parts:
                
                # region Comment - Mesh Parts Handling

                # TODO : Add proper mesh part handling in the future in the event that any of the vanilla maps have model meshes with multiple mesh parts rather than just 1.
                # Note that all mesh parts share the same vertex and index buffers, but they allow assigning different share resource indices (different material effects) to a segment of the mesh,
                # as well as different vertex declarations.

                # endregion
                
                vertex_declaration_index = mesh_part["vertexDeclarationIndex"]
                json_vertex_declaration = vertex_declarations[vertex_declaration_index]

                self.import_model_mesh(root_bone_obj, parent_bone_data, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer)

                share_resource_index = mesh_part["sharedResourceIndex"] # TODO : Add shared resource handling

    def import_model_mesh(self, obj_root_bone, json_parent_bone, vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer):
        # Generate mesh data, create mesh data block and create Blender mesh object
        obj, mesh = self.import_buffer_mesh(vertex_stride, json_vertex_declaration, json_vertex_buffer, json_index_buffer, json_parent_bone["name"])

        # Assign mcow properties
        mesh.magickcow_mesh_type = "GEOMETRY"

        # Attach to parent bone object and set relative object transform
        transform = self.read_mat4x4(json_parent_bone["transform"])
        obj.parent = obj_root_bone
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        obj.matrix_basis = transform

        # Create material data
        # TODO : Implement material handling

    def import_animated_liquids(self, liquids_data, parent_obj):
        liquids_objs = self.import_liquids(liquids_data)
        if parent_obj is not None: # NOTE : Parent should never be None here, since we always generate a bone obj for each animated level part, but we add the None check just in case...
            for liquid_obj in liquids_objs:
                liquid_obj.parent = parent_obj
                liquid_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                liquid_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_locators(self, locators_data, parent_obj):
        locators_objs = self.import_locators(locators_data)
        if parent_obj is not None:
            for locator_obj in locators_objs:
                locator_obj.parent = parent_obj
                locator_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                locator_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_effects(self, effects_data, parent_obj):
        effects_objs = self.import_effects(effects_data)
        if parent_obj is not None:
            for effect_obj in effects_objs:
                effect_obj.parent = parent_obj
                effect_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                effect_obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_lights(self, lights, parent_obj):
        if parent_obj is not None:
            for light in lights:
                name = light["name"]
                transform = self.read_mat4x4(light["position"])
                if name in self._cached_lights:
                    obj = self._cached_lights[name]
                    obj.parent = parent_obj
                    obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                    obj.matrix_basis = transform

    def import_animated_collision_mesh(self, json_has_collision, json_collision_material, json_vertices, json_triangles, parent_obj):
        # Get generic collision properties
        name = "animated_collision_mesh"
        collision_material = find_collision_material_name(json_collision_material)
        
        # Generate collision blender mesh data and blender object
        has_collision, obj, mesh = self.import_collision_mesh_generic_internal(name, json_has_collision, json_vertices, json_triangles)

        # If a collision mesh object was generated, set the mcow properties and attach to parent bone object
        if has_collision:
            mesh.magickcow_mesh_type = "COLLISION"
            obj.magickcow_collision_material = collision_material
        
            # Attach the collision mesh to the parent bone object and set the relative transform to the identity matrix
            if parent_obj is not None:
                obj.parent = parent_obj
                obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                obj.matrix_basis = mathutils.Matrix.Identity(4)

    def import_animated_nav_mesh(self, has_nav_mesh, nav_mesh, root_bone_obj):
        if has_nav_mesh:
            obj = self.import_nav_mesh_internal(nav_mesh, "nav_mesh_animated")
            obj.parent = root_bone_obj
            obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
            obj.matrix_basis = mathutils.Matrix.Identity(4)
    
    def import_animation_data(self, animation, root_bone_obj):
        # Set the bone rotation mode to quaternion so that we can assign directly the rotation data
        root_bone_obj.rotation_mode = "QUATERNION"

        # Hack to set the default pose of the bone to the same as the first animation keyframe
        # This can be removed later on, but for now it's ok to keep this around
        # Note that this should never have any issues since in theory, an animated level part must have at least 1 single keyframe with its default pose for Magicka to not crash on level load.
        # All this hack does is set the default pose of the mesh to the same as the first keyframe for visualization in Blender, since the "wrong" pose would be seen until after playing the first anim keyframe.
        # Not a big deal, but just a bit of quality of life for people who care I guess.
        first_keyframe_pose_hack_enabled = True
        if first_keyframe_pose_hack_enabled:
            first_anim_frame = animation["frames"][0]["pose"]
            faf_pos = self.read_point(first_anim_frame["translation"])
            faf_rot = self.read_quat(first_anim_frame["orientation"])
            faf_scale = self.read_scale(first_anim_frame["scale"])
            root_bone_obj.location = faf_pos
            root_bone_obj.rotation_mode = "QUATERNION" # NOTE : Important to ensure that this is the rotation mode so that we can assign rotation quaternions...
            root_bone_obj.rotation_quaternion = faf_rot
            root_bone_obj.scale = faf_scale
        
        # Select a framerate for the translation from Magicka's time-based keyframes format to Blender's keyframe format.
        # For now, the FPS is fixed to Blender's default 24 fps, but this can be configured later on to use whatever the user has defined on the render output FPS config window.
        # It could also be configured with a custom import FPS option for mcow or something like that.
        fps = 24

        # Read the animation data keyframes and assign the properties to the Blender root bone object
        frames = animation["frames"]
        for frame in frames:
            # Read the keyframe data
            time = frame["time"] # The time in seconds at which the frame takes place within Magicka's animation format
            pose = frame["pose"]
            location = self.read_point(pose["translation"])
            rotation = self.read_quat(pose["orientation"])
            scale = self.read_scale(pose["scale"])
            keyframe = int(round(time * fps)) # The Blender integer keyframe value

            # Assign the data
            root_bone_obj.location = location
            root_bone_obj.rotation_quaternion = rotation
            root_bone_obj.scale = scale

            # Store the keyframe
            root_bone_obj.keyframe_insert(data_path="location", frame=keyframe)
            root_bone_obj.keyframe_insert(data_path="rotation_quaternion", frame=keyframe)
            root_bone_obj.keyframe_insert(data_path="scale", frame=keyframe)

            # Update the start and end frame times
            # region Comment - Set timeline start and end frame times to fit imported animation
            # NOTE : We need to find the smallest and largest keyframes within the imported animation so that we can extend the Blender animation start and end frame times.
            # This way, we can play the whole animation without any imported keyframes being left out of the bounds of the time timeline.
            # It also prevents any possible confusions where users will miss some keyframe that is way out of sight, letting them know that at most there's a frame present at the end frame time if it
            # is larger than the default Blender value of 250, or whatever value they had already configured.
            # endregion
            bpy.context.scene.frame_start = min(bpy.context.scene.frame_start, keyframe)
            bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, keyframe)

    # endregion

# endregion
