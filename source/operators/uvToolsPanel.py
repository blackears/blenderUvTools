import bpy
import bpy.utils.previews
import os

preview_collections = {}

#---------------------------


class UvToolsPanel(bpy.types.Panel):

    """Properties Panel for the Uv Tools"""
    bl_label = "Uv Tools"
    bl_idname = "OBJECT_PT_uv_tools_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "Kitfox"

        

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        settings = scene.uv_brush_props
        
        pcoll = preview_collections["main"]
        
        
        col = layout.column();
        col.operator("kitfox.uv_brush_operator", text="Uv Brush", icon_value = pcoll["uvBrush"].icon_id)
        
        col.prop(settings, "radius")
        col.prop(settings, "strength")
        col.prop(settings, "use_pressure")

        
#---------------------------



def register():
    
    #Load icons
    icon_path = "../icons"
    if __name__ == "__main__":
        icon_path = "../../source/icons"
        
    icons_dir = os.path.join(os.path.dirname(__file__), icon_path)
    
#    print("icons dir: " + str(icons_dir))
    
    pcoll = bpy.utils.previews.new()
    pcoll.load("uvBrush", os.path.join(icons_dir, "uvBrush.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    #Register tools
    bpy.utils.register_class(UvToolsPanel)


def unregister():
    bpy.utils.unregister_class(UvToolsPanel)

    
    #Unload icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    register()