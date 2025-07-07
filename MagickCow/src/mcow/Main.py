# region Main Addon Entry Point

def register():
    # Register custom property classes
    register_properties_classes()

    # Register the Import and Export Panels
    register_exporters()
    register_importers()

    # Register the Material, Object and Scene Properties and Property Panels
    register_properties_material()
    register_properties_object()
    register_properties_scene()

def unregister():
    # Register custom property classes
    unregister_properties_classes()

    # Unregister the Import and Export Panels
    unregister_exporters()
    unregister_importers()

    # Unregister the Material, Object and Scene Properties and Property Panels
    unregister_properties_material()
    unregister_properties_object()
    unregister_properties_scene()

if __name__ == "__main__":
    register()

# endregion
