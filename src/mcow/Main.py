# region Main Addon Entry Point

def register():
    # Register custom property classes
    register_properties_classes()

    # Register the Import and Export Panels
    register_exporters()
    register_importers()

    # Register the Object Properties and Object Properties Panel
    register_properties_object()

    # Register the Scene Properties and Scene Properties Panel
    register_properties_scene()

def unregister():
    # Register custom property classes
    unregister_properties_classes()

    # Unregister the Import and Export Panels
    unregister_exporters()
    unregister_importers()

    # Unregister the Object Properties and Object Properties Panel
    unregister_properties_object()

    # Unregister the Scene Properties and Scene Properties Panel
    unregister_properties_scene()

if __name__ == "__main__":
    register()

# endregion
