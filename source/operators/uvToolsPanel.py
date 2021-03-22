import bpy
import bpy.utils.previews
import os

preview_collections = {}

#---------------------------


# class UvToolsObjectPanel(bpy.types.Panel):

    # """Properties Panel for the Uv Tools"""
    # bl_label = "Uv Tools"
    # bl_idname = "OBJECT_PT_uv_object_tools_props"
    # bl_space_type = 'VIEW_3D'
    # bl_region_type = 'UI'
    # bl_context = "objectmode"
# #    bl_context = "mesh_edit"
    # bl_category = "Kitfox"

        

    # def draw(self, context):
        # layout = self.layout

        # scene = context.scene
        # settings = scene.uv_brush_props
        
        # pcoll = preview_collections["main"]
        
        
        # col = layout.column();
        # col.operator("kitfox.uv_brush_operator", text="Uv Brush", icon_value = pcoll["uvBrush"].icon_id)
        
        # col.prop(settings, "radius")
        # col.prop(settings, "strength")
        # col.prop(settings, "use_pressure")
        
        # layout.separator()

        # col = layout.column();
        # col.operator("kitfox.uv_plane_layout_op", text="Uv Plane Project", icon_value = pcoll["uvBrush"].icon_id)
        
#---------------------------


class UvToolsEditPanel(bpy.types.Panel):

    """Properties Panel for the Uv Tools"""
    bl_label = "Uv Tools"
    bl_idname = "OBJECT_PT_uv_edit_tools_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
#    bl_context = "objectmode"
#    bl_context = "mesh_edit"
    bl_category = "Kitfox - UV"

        

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj != None and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')
        
    def draw(self, context):
        layout = self.layout

        scene = context.scene
        settings = scene.uv_brush_props
        
        pcoll = preview_collections["main"]
        
        #--------------------------------
        
        col = layout.column();
        col.operator("kitfox.uv_brush_operator", text="Uv Brush", icon_value = pcoll["uvBrush"].icon_id)
        
        col.prop(settings, "radius")
        col.prop(settings, "strength")
        col.prop(settings, "use_pressure")

        #--------------------------------
        layout.separator()

        planeLayout_props = scene.kitfox_uv_plane_layout_props

        col = layout.column();
        col.operator("kitfox.uv_plane_layout_op", text="Uv Plane Project", icon_value = pcoll["uvBrush"].icon_id)
        col.prop(planeLayout_props, "selected_faces_only")
        col.prop(planeLayout_props, "clamp_to_basis")
        col.prop(planeLayout_props, "clamp_scalar")        
        col.prop(planeLayout_props, "init_layout", expand = True)
        
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
#    bpy.utils.register_class(UvToolsObjectPanel)
    bpy.utils.register_class(UvToolsEditPanel)


def unregister():
#    bpy.utils.unregister_class(UvToolsObjectPanel)
    bpy.utils.unregister_class(UvToolsEditPanel)

    
    #Unload icons
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    register()