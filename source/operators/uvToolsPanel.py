# This file is part of the Kitfox Normal Brush distribution (https://github.com/blackears/blenderUvTools).
# Copyright (c) 2021 Mark McKay
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
        
        #--------------------------------
        layout.separator()
        settings_copy_sym = context.scene.kitfox_copy_symmetric_uvs
        
        col = layout.column();
        col.operator("kitfox.copy_symmetric_uvs", text="Copy Symmetric UVs")

        col.prop(settings_copy_sym, "axis")
        col.prop(settings_copy_sym, "epsilon")
        
        #--------------------------------
        layout.separator()
        settings_tri = context.scene.triplanar_settings_props
        
        col = layout.column();
        col.operator("kitfox.triplanar_uv_unwrap", text="Triplanar Unwrap")

        row = layout.row()
        row.prop(settings_tri, "scale_u")
        row.prop(settings_tri, "scale_v")
        col.prop(settings_tri, "use_grid_scale")
        
        #--------------------------------
        layout.separator()
        col = layout.column();
        col.prop(bpy.context.scene.tool_settings, "use_transform_correct_face_attributes")
        
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