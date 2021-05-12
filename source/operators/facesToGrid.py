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
import math
from mathutils import *

class FaceUvsToGridProperties(bpy.types.PropertyGroup):
    
    grid_cells_x : bpy.props.IntProperty(
        name="Grid U", description="Number of cells wide UV grid is along U axis.", default = 1, min=0, soft_max = 4
    )

    grid_cells_y : bpy.props.IntProperty(
        name="Grid V", description="Number of cells wide UV grid is along U axis.", default = 1, min=0, soft_max = 4
    )


def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()


#-------------------------------------


class FaceUvsToGridOperator(bpy.types.Operator):
    """Set UVs per face so that they fit a grid square."""
    bl_idname = "kitfox.face_uvs_to_grid_unwrap"
    bl_label = "Face Uvs to Grid"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')
#        return obj and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def execute(self, context):
        props = context.scene.faces_to_grid_props
        grid_cells_x = props.grid_cells_x
        grid_cells_y = props.grid_cells_y

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            l2w = obj.matrix_world
            
        
            mesh = obj.data
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)

            uv_layer = bm.loops.layers.uv.verify()


            # adjust uv coordinates
            for face in bm.faces:
                if face.select:

                    uvCenter = None
                    
                    for loop in face.loops:
                        if uvCenter == None:
                            uvCenter = Vector(loop[uv_layer].uv)
                        else:
                            uvCenter += Vector(loop[uv_layer].uv)
                            
                    if uvCenter == None:
                        continue
                        
                    uvCenter *= 1.0 / len(face.loops)

#                    print ("Uv center " + str(uvCenter))
                    
                    cell_x = int((uvCenter.x - math.floor(uvCenter.x)) * grid_cells_x)
                    cell_y = int((uvCenter.y - math.floor(uvCenter.y)) * grid_cells_y)
                        
#                    print ("cell_x " + str(cell_x))
#                    print ("cell_y " + str(cell_y))
                    
#                    print ("face.loops[0][uv_layer].uv " + str(face.loops[0][uv_layer].uv))
                        
                    uvDir = face.loops[0][uv_layer].uv - uvCenter
                    uvDirSign = Vector((-1 if uvDir.x < 0 else 1, -1 if uvDir.y < 0 else 1))

#                    print ("uvDir " + str(uvDir))
#                    print ("uvDirSign " + str(uvDirSign))
                    
                    area = 0
                    for i in range(len(face.loops)):
                        loop0 = face.loops[i]
                        loop1 = face.loops[0 if i == len(face.loops) - 1 else i + 1]
                        
                        uv0 = loop0[uv_layer].uv
                        uv1 = loop1[uv_layer].uv
                        area += uv0.x * uv1.y - uv0.y * uv1.x
                    
                    
                    mT = Matrix.Translation((1, 1, 0))
                    mS = Matrix.Diagonal((1.0 / (grid_cells_x * 2), 1.0 / (grid_cells_y * 2), 1, 1))
                    mT2 = Matrix.Translation((cell_x / grid_cells_x, cell_y / grid_cells_y, 0))
                    mUvXlate = mT2 @ mS @ mT
                        
                    for i in range(len(face.loops)):
                        uvPos = mUvXlate @ uvDirSign.to_4d()
#                        print ("- uvDirSign " + str(uvDirSign))
#                        print ("- uvPos " + str(uvPos))
                        
                        face.loops[i][uv_layer].uv = uvPos.to_2d()

                        if area >= 0:
                            #CCW
                            tmp = uvDirSign.y
                            uvDirSign.y = uvDirSign.x
                            uvDirSign.x = -tmp
                        else:
                            tmp = uvDirSign.x
                            uvDirSign.x = uvDirSign.y
                            uvDirSign.y = -tmp
                        

                    
            if obj.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
            
        redraw_all_viewports(context)    
            
        return {'FINISHED'}


#-------------------------------------



class FaceUvsToGridPanel(bpy.types.Panel):

    """Properties Panel for Triplanar Unwrap"""
    bl_label = "Face Uvs to Grid Panel"
    bl_idname = "OBJECT_PT_kitfox_face_uvs_to_grid"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kitfox - UV"

        

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj != None and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')
        
    def draw(self, context):
        layout = self.layout

        scene = context.scene
        settings = scene.uv_brush_props
        
        #--------------------------------

        props = context.scene.faces_to_grid_props
        
        col = layout.column();
        col.operator("kitfox.face_uvs_to_grid_unwrap", text="Face Uvs to Grid")

        col.prop(props, "grid_cells_x")
        col.prop(props, "grid_cells_y")

#-------------------------------------


def menu_start_faceUvsToGrid(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator("kitfox.uv_brush_operator")


def register():
    bpy.utils.register_class(FaceUvsToGridProperties)
    bpy.utils.register_class(FaceUvsToGridOperator)
    bpy.utils.register_class(FaceUvsToGridPanel)
    bpy.types.VIEW3D_MT_uv_map.prepend(menu_start_faceUvsToGrid)

    bpy.types.Scene.faces_to_grid_props = bpy.props.PointerProperty(type=FaceUvsToGridProperties)


def unregister():
    bpy.utils.unregister_class(FaceUvsToGridProperties)
    bpy.utils.unregister_class(FaceUvsToGridOperator)
    bpy.utils.unregister_class(FaceUvsToGridPanel)
    bpy.types.VIEW3D_MT_uv_map.remove(menu_start_faceUvsToGrid)
    
    del bpy.types.Scene.faces_to_grid_props


if __name__ == "__main__":
    register()



