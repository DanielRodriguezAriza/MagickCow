# Base import
import bpy
from bpy.props import StringProperty

# Node-Editor imports
from bpy.types import Space, Panel, Operator

# Node imports
from bpy.types import Node, NodeSocket

# Define addon info
bl_info = {
    "name" : "MagickCow Experimental Features Addon - Nodes",
    "blender" : (3, 0, 0),
    "category" : "Export",
    "description" : "Adds some experimental stuff to MagickCow",
    "author" : "potatoes",
    "version" : (1, 0, 0)
}

# Create custom editor space class
class MyCustomNodeEditor(Space):
    bl_idname = "SpaceNodeEditorCustom"
    bl_label = "My Custom Node Editor"

# Register the custom editor
def register_editor():
    bpy.utils.register_class(MyCustomNodeEditor)

def unregister_editor():
    bpy.utils.unregister_class(MyCustomNodeEditor)


# Define a custom socket
class MyCustomSocket(NodeSocket):
    bl_idname = "MyCustomSocket"
    bl_label = "Custom Socket"
    
    value: StringProperty(name="Value")

    def draw(self, context, layout, node, text):
        layout.label(text=self.value)

# Define a custom node
class MyCustomNode(Node):
    bl_idname = "MyCustomNode"
    bl_label = "My Custom Node"

    def init(self, context):
        self.inputs.new("MyCustomSocket", "Input")
        self.outputs.new("NodeSocket", "Output")

    def execute(self, context):
        # Here you can collect data from the scene
        print("Collecting data from the scene...")
        scene_data = "Some scene data"  # Replace with actual logic

        # Output the data
        self.outputs["Output"].value = scene_data

# Register custom node and socket
def register_nodes():
    bpy.utils.register_class(MyCustomSocket)
    bpy.utils.register_class(MyCustomNode)

def unregister_nodes():
    bpy.utils.unregister_class(MyCustomSocket)
    bpy.utils.unregister_class(MyCustomNode)


# Top-Level register and unregister functions
def register():
    register_editor()
    register_nodes()

def unregister():
    unregister_editor()
    unregister_nodes()

# Entry point
if __name__ == "__main__":
    register()
