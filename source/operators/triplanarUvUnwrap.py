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
import bmesh
import mathutils


class TriplanarSettings(bpy.types.PropertyGroup):

    scale_uniform : bpy.props.BoolProperty(
        name="Scale Uniform", description="If true, both axes will be scaled by the same amount.  Otherwise u and v scaling can be specified separately.", default = True
    )
    
    scale_u : bpy.props.FloatProperty(
        name="U Scale", description="Scale of texture along horizon", default = 1, min=0, soft_max = 4
    )

    scale_v : bpy.props.FloatProperty(
        name="V Scale", description="Scale of texture along vertical", default = 1, min=0, soft_max = 4
    )

    use_grid_scale : bpy.props.BoolProperty(
        name="Use Grid Scale", description="If true, multiply coords by current grid size.", default = False
    )

def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()

def map_editmode(context):
    settings = context.scene.triplanar_settings_props

    scale = context.space_data.overlay.grid_scale
    use_grid_scale = settings.use_grid_scale
    print("scale %s" % (str(scale)))
    print("use_grid_scale %s" % (str(use_grid_scale)))
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
    
        l2w = obj.matrix_world
        
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
#        bm = bmesh.new()
#        bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()


        # adjust uv coordinates
        for face in bm.faces:
            if face.select:
                xAbs = abs(face.normal.x)
                yAbs = abs(face.normal.y)
                zAbs = abs(face.normal.z)

                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    
                    wco = l2w @ loop.vert.co
                    
                    # use xy position of the vertex as a uv coordinate
                    uv = None
                    if (xAbs > yAbs and xAbs > zAbs):
                        uv = mathutils.Vector(wco.yz)
                    elif (yAbs > zAbs):
                        uv = mathutils.Vector(wco.xz)
                    else:
                        uv = mathutils.Vector(wco.xy)
                    
                    if settings.scale_uniform:
                        uv.x /= settings.scale_u
                        uv.y /= settings.scale_u
                    else:
                        uv.x /= settings.scale_u
                        uv.y /= settings.scale_v
                    
                    if use_grid_scale:
                        uv /= scale
                        
                    loop_uv.uv = uv

        bmesh.update_edit_mesh(me)
#        bm.to_mesh(me)
#        bm.free()
        
    redraw_all_viewports(context)    


def map_objectmode(context):
    settings = context.scene.triplanar_settings_props
    scale = context.space_data.overlay.grid_scale
    use_grid_scale = settings.use_grid_scale
    print("scale %s" % (str(scale)))
    print("use_grid_scale %s" % (str(use_grid_scale)))
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
    
        l2w = obj.matrix_world
        
        me = obj.data
#        bm = bmesh.from_edit_mesh(me)
        bm = bmesh.new()
        bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()


        # adjust uv coordinates
        for face in bm.faces:
            xAbs = abs(face.normal.x)
            yAbs = abs(face.normal.y)
            zAbs = abs(face.normal.z)

            for loop in face.loops:
                loop_uv = loop[uv_layer]
                
                wco = l2w @ loop.vert.co
                
                # use xy position of the vertex as a uv coordinate
                uv = None
                if (xAbs > yAbs and xAbs > zAbs):
                    uv = mathutils.Vector(wco.yz)
                elif (yAbs > zAbs):
                    uv = mathutils.Vector(wco.xz)
                else:
                    uv = mathutils.Vector(wco.xy)
                
                if settings.scale_uniform:
                    uv.x /= settings.scale_u
                    uv.y /= settings.scale_u
                else:
                    uv.x /= settings.scale_u
                    uv.y /= settings.scale_v
                    
                if use_grid_scale:
                    uv /= scale
                        
                loop_uv.uv = uv

#        bmesh.update_edit_mesh(me)
        bm.to_mesh(me)
        bm.free()
        
    redraw_all_viewports(context)    
        

class TriplanarUvUnwrapOperator(bpy.types.Operator):
    """Vertex Pos as UVs"""
    bl_idname = "kitfox.triplanar_uv_unwrap"
    bl_label = "Vertex Pos as UVs"
    bl_options = {'REGISTER', 'UNDO'}

    # scale: FloatProperty(
        # name="Scale",
        # description="Scale UVs by this",
        # soft_min=0.1, soft_max=10.0,
        # default=0.5,
    # )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')
#        return obj and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def execute(self, context):
        obj = context.active_object
        if obj.mode == 'EDIT':
            map_editmode(context)
        elif obj.mode == 'OBJECT':
            map_objectmode(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator("kitfox.triplanar_uv_unwrap")
    # bl_idname should be in form of "something.something"
    # or YourClass.bl_idname


def register():
    bpy.utils.register_class(TriplanarSettings)
    bpy.utils.register_class(TriplanarUvUnwrapOperator)
    bpy.types.VIEW3D_MT_uv_map.prepend(menu_func)

    bpy.types.Scene.triplanar_settings_props = bpy.props.PointerProperty(type=TriplanarSettings)


def unregister():
    bpy.utils.unregister_class(TriplanarSettings)
    bpy.utils.unregister_class(TriplanarUvUnwrapOperator)
    bpy.types.VIEW3D_MT_uv_map.remove(menu_func)
    
    del bpy.types.Scene.triplanar_settings_props


if __name__ == "__main__":
    register()