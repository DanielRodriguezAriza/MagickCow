# region Import Data Pipeline class - LevelModel / Map

# TODO : Implement all import functions...
class MCow_ImportPipeline_Map(MCow_ImportPipeline):
    def __init__(self):
        super().__init__()
        return
    
    def exec(self, data):
        level_model = data["XnbFileData"]["PrimaryObject"]
        self.import_level_model(level_model)
    
    def import_level_model(self, level_model):
        # Get the data entries from the level model JSON dict object.
        model_mesh = level_model["model"]
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
        
        # Execute the import functions for each of the types of data found within the level model JSON dict.
        self.import_model_mesh(model_mesh)
        self.import_animated_parts(animated_parts)
        self.import_lights(lights)
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

    def import_model_mesh(self, model):
        root_nodes = model["RootNodes"]
        for idx, root_node in enumerate(root_nodes):
            self.import_root_node(f"mesh_{idx}", root_node)
    
    def import_animated_parts(self, animated_parts):
        pass
    
    def import_lights(self, lights):
        for light in lights:
            self.import_light(light)
    
    def import_effects(self, effects):
        for effect in effects:
            self.import_effect(effect)
    
    def import_physics_entities(self, physics_entities):
        for idx, physics_entity in enumerate(physics_entities):
            self.import_physics_entity(idx, physics_entity)
    
    def import_liquids(self, liquids):
        pass
    
    def import_force_fields(self, force_fields):
        pass
    
    def import_model_collision(self, collision_data): # TODO : Add support to specify the type of collision channel that we're importing, as of now we're only going to be importing the mesh and that's it.
        for idx, collision_channel in enumerate(collision_data):
            self.import_collision_channel(f"collision_mesh_model_{idx}", collision_channel) # This would need an extra param to specify the collision channel index, but what happens then to the import camera collision function? those are the details we need to polish.
    
    def import_camera_collision(self, collision_data):
        self.import_collision_channel("collision_mesh_camera", collision_data)
    
    def import_triggers(self, triggers):
        for trigger in triggers:
            self.import_trigger(trigger)
    
    def import_locators(self, locators):
        for locator in locators:
            self.import_locator(locator)
    
    def import_nav_mesh(self, nav_mesh):
        # NOTE : The generated nav mesh has inverted normals, and I have no idea as of now if that has any negative impact on the AI's behaviour.
        # So for now, this is ok I suppose, since I have not seen anything within Magicka's code that would point to the face orientation of the nav mesh
        # being taken into account... so this should be ok, but it would be ideal to solve this issue so that people who import maps don't have to deal with the ugly
        # inverted normals, or maybe it's ok, idk.
        name = "nav_mesh_static"

        json_vertices = nav_mesh["Vertices"]
        json_triangles = nav_mesh["Triangles"]

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["VertexA"], tri["VertexB"], tri["VertexC"]) for tri in json_triangles]

        mesh = bpy.data.meshes.new(name = name)
        obj = bpy.data.objects.new(name = name, object_data = mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()
    
    # endregion

    # region Import Methods - Internal

    # TODO : Finish implementing (what's left as of now is modifying the properties of the spawned in light so that it uses the values that it has read from the JSON data)
    # TODO : Handle translating ALL vectors from Y up to Z up...
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

    def import_collision_channel(self, name, collision):
        has_collision = collision["hasCollision"]

        if not has_collision:
            return
        
        json_vertices = collision["vertices"]
        json_triangles = collision["triangles"]

        mesh_vertices = [self.read_point(vert) for vert in json_vertices]
        mesh_triangles = [(tri["index0"], tri["index1"], tri["index2"]) for tri in json_triangles]

        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

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

    def import_physics_entity(self, idx, physics_entity):
        template = physics_entity["template"]
        transform = self.read_mat4x4(physics_entity["transform"])

        obj = bpy.data.objects.new(name=f"physics_entity_{idx}", object_data = None)

        obj.matrix_world = transform

        bpy.context.collection.objects.link(obj)

        obj.magickcow_empty_type = "PHYSICS_ENTITY"
        obj.magickcow_physics_entity_name = template

    def import_root_node(self, name, root_node):
        # Read root node properties
        is_visible = root_nodes["isVisible"] # Ignored for now because we don't want meshes to be hidden on the scene on import. We'll maybe have an option that says "hide meshes that are set to invisible" or whatever on the mcow scene panel or some shit like that. Or maybe just import and hide the object and call it a day. Users can easily look for hidden objects and that's it.
        casts_shadows = root_nodes["castsShadows"]
        sway = root_nodes["sway"] # Not supported yet because we don't know wtf sway is yet...
        entity_influence = root_nodes["entityInfluence"] # Not supported yet because we don't know wtf this does yet...
        ground_level = root_nodes["groundLevel"] # Not supported yet because the exporter hardcodes this anyway, and we don't really know wtf this is yet so yeah...
        vertex_stride = root_nodes["vertexStride"]
        vertex_declaration = root_nodes["vertexDeclaration"]
        vertex_buffer = root_nodes["vertexBuffer"]
        index_buffer = root_nodes["indexBuffer"]
        effect = root_nodes["effect"]
        primitive_count = root_nodes["primitiveCount"]
        start_index = root_nodes["startIndex"]
        bounding_box = root_nodes["boundingBox"]
        
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
        mesh_vertices, mesh_triangles = self.read_mesh_buffer_data(vertex_stride, vertex_declaration, vertex_buffer, index_buffer)

        # Create mesh data and mesh object
        mesh = bpy.data.meshes.new(name=name)
        obj = bpy.data.objects.new(name=name, object_data=mesh)

        bpy.context.collection.objects.link(obj)

        mesh.from_pydata(mesh_vertices, [], mesh_triangles)
        mesh.update()

    # endregion

# endregion
