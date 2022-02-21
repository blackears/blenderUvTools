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
from enum import Enum
from mathutils import *

class FaceUvsToGridProperties(bpy.types.PropertyGroup):
    
    grid_cells_x : bpy.props.IntProperty(
        name="Grid U", 
        description="Number of cells wide UV grid is along U axis.", 
        default = 1, 
        min=0, 
        soft_max = 4
    )

    grid_cells_y : bpy.props.IntProperty(
        name="Grid V", 
        description="Number of cells wide UV grid is along U axis.", 
        default = 1, 
        min=0, 
        soft_max = 4
    )

    winding : bpy.props.EnumProperty(
        items=(
            ('KEEP', "Keep", "Keep current winding."),
            ('CW', "CW", "UVs travel clockwise around face."),
            ('CCW', "CCW", "UVs travel counter-clockwise around face."),
        ),
        default='KEEP'
    )

    uv_align_direction : bpy.props.FloatVectorProperty(
        name="Align Direction", 
        description="Direction used by Align UVs.", 
        default = (0, 0, 1), 
        subtype='DIRECTION'
    )


class ShiftType(Enum):
    REVERSE = 1
    CW = 2
    CCW = 3

def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()


    
def align_face_uvs(context):
    props = context.scene.faces_to_grid_props
    uv_align_direction = props.uv_align_direction.to_3d()

    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue

    
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
#                print("---face")
                uvs = []
                weights = []
            
                num_uvs = len(face.loops)
                for i in range(num_uvs):
                    loop = face.loops[i]
                    uvs.append(loop[uv_layer].uv.copy())
                    weights.append(uv_align_direction.dot(loop.vert.co))

                #Find best weighted sum of Vs for all possible sequences of uvs
                best_offset = -1
                best_offset_sum = 0
                for offset in range(num_uvs):
                    sum = 0
                    for i in range(num_uvs):
                        sum += uvs[(i + offset) % num_uvs].y * weights[i]

#                    print("offset " + str(offset) + " sum " + str(sum))
                    
                    if best_offset == -1 or sum > best_offset_sum:
                        best_offset = offset
                        best_offset_sum = sum

#                print("best_offset " + str(best_offset) + " best_sum " + str(best_offset_sum))

                for i in range(num_uvs):
                    loop = face.loops[i]
                    loop[uv_layer].uv = uvs[(i + best_offset) % num_uvs]
    

        if obj.mode == 'EDIT':
            bmesh.update_edit_mesh(mesh)
        elif obj.mode == 'OBJECT':
            bm.to_mesh(mesh)
            bm.free()
        
    redraw_all_viewports(context)    

def shift_face_uvs(context, shift_type):
    props = context.scene.faces_to_grid_props
    grid_cells_x = props.grid_cells_x
    grid_cells_y = props.grid_cells_y
    winding = props.winding

    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue

    
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
                uvs = []
                num_uvs = len(face.loops)
                for i in range(num_uvs):
                    loop = face.loops[i]
                    uvs.append(loop[uv_layer].uv.copy())

                for i in range(num_uvs):
                    loop = face.loops[i]
                    if shift_type == ShiftType.CW:
                        iNext = i + 1 if i < num_uvs - 1 else 0
                    elif shift_type == ShiftType.CCW:
                        iNext = i - 1 if i > 0 else num_uvs - 1
                    else:
                        iNext = num_uvs - 1 - i
                        
                    loop[uv_layer].uv = uvs[iNext]


        if obj.mode == 'EDIT':
            bmesh.update_edit_mesh(mesh)
        elif obj.mode == 'OBJECT':
            bm.to_mesh(mesh)
            bm.free()
        
    redraw_all_viewports(context)    

#-------------------------------------

class RotUvsCwOperator(bpy.types.Operator):
    """Rotate face UVs clockwise."""
    bl_idname = "kitfox.rot_uvs_cw"
    bl_label = "Rotate Uvs Clockwise"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')


    def execute(self, context):
        shift_face_uvs(context, ShiftType.CW)
        return {'FINISHED'}

#-------------------------------------

class RotUvsCcwOperator(bpy.types.Operator):
    """Rotate face UVs counter-clockwise."""
    bl_idname = "kitfox.rot_uvs_ccw"
    bl_label = "Rotate Uvs Clockwise"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')


    def execute(self, context):
        shift_face_uvs(context, ShiftType.CCW)
        return {'FINISHED'}

#-------------------------------------

class ReverseFaceUvsOperator(bpy.types.Operator):
    """Reverse winding of face UVs."""
    bl_idname = "kitfox.reverse_face_uvs"
    bl_label = "Reverse Face UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')


    def execute(self, context):
        shift_face_uvs(context, ShiftType.REVERSE)
        return {'FINISHED'}

#-------------------------------------

class CopyFaceUvsOperator(bpy.types.Operator):
    """Set UVs of selected faces to match that of the active face."""
    bl_idname = "kitfox.copy_face_uvs_unwrap"
    bl_label = "Copy Face Uvs"
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
        winding = props.winding

#        print("faceToGrid exec")

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

        
            mesh = obj.data
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)


            uv_layer = bm.loops.layers.uv.verify()

#            print("obj " + obj.name)

            active = bm.faces.active
            if active == None:
                continue
                

            # adjust uv coordinates
            for face in bm.faces:
                if face.select and face != active:

                    for i in range(len(face.loops)):
                        loop = face.loops[i]
                        activeI = i if i < len(active.loops) else len(active.loops) - 1
                        
                        loop[uv_layer].uv = active.loops[activeI][uv_layer].uv.copy()


            if obj.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
            
        redraw_all_viewports(context)    
            
        return {'FINISHED'}


#-------------------------------------

class AlignFaceUvsOperator(bpy.types.Operator):
    """Rotate UVs so that their V axis is pointing along the Align Direction as much as is possible."""
    bl_idname = "kitfox.align_face_uvs"
    bl_label = "Align Face UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')

    def execute(self, context):
        align_face_uvs(context)
        return {'FINISHED'}

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
        winding = props.winding

#        print("--faceToGrid exec")

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

        
            mesh = obj.data
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)

            uv_layer = bm.loops.layers.uv.verify()

#            print("obj " + obj.name)

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
                        uvCenter = Vector((0, 0))
                        
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

                        ccw = (winding == 'KEEP' and area >= 0) or winding == 'CCW'
                        if ccw:
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

    """Properties Panel for Trim Sheet Tools"""
    bl_label = "Trim Sheet Tools"
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
        col.operator("kitfox.face_uvs_to_grid_unwrap")

        col.prop(props, "grid_cells_x")
        col.prop(props, "grid_cells_y")
        col.prop(props, "winding", text = "Winding")

        col.operator("kitfox.copy_face_uvs_unwrap")
        col.operator("kitfox.rot_uvs_cw", text="Rotate CW")
        col.operator("kitfox.rot_uvs_ccw", text="Rotate CCW")
        col.operator("kitfox.reverse_face_uvs", text="Reverse Face Winding")
        col.operator("kitfox.align_face_uvs", text="Align UVs")

        col.prop(props, "uv_align_direction", expand = True)
        
#-------------------------------------


def menu_start_faceUvsToGrid(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator("kitfox.uv_brush_operator")


def register():
    bpy.utils.register_class(FaceUvsToGridProperties)
    bpy.utils.register_class(FaceUvsToGridOperator)
    bpy.utils.register_class(CopyFaceUvsOperator)
    bpy.utils.register_class(RotUvsCwOperator)
    bpy.utils.register_class(RotUvsCcwOperator)
    bpy.utils.register_class(ReverseFaceUvsOperator)
    bpy.utils.register_class(AlignFaceUvsOperator)
    
    bpy.utils.register_class(FaceUvsToGridPanel)


    bpy.types.VIEW3D_MT_uv_map.prepend(menu_start_faceUvsToGrid)

    bpy.types.Scene.faces_to_grid_props = bpy.props.PointerProperty(type=FaceUvsToGridProperties)


def unregister():
    bpy.utils.unregister_class(FaceUvsToGridProperties)
    bpy.utils.unregister_class(FaceUvsToGridOperator)
    bpy.utils.unregister_class(CopyFaceUvsOperator)
    bpy.utils.unregister_class(RotUvsCwOperator)
    bpy.utils.unregister_class(RotUvsCcwOperator)
    bpy.utils.unregister_class(ReverseFaceUvsOperator)
    bpy.utils.unregister_class(AlignFaceUvsOperator)
    bpy.utils.unregister_class(FaceUvsToGridPanel)
    bpy.types.VIEW3D_MT_uv_map.remove(menu_start_faceUvsToGrid)
    
    del bpy.types.Scene.faces_to_grid_props


if __name__ == "__main__":
    register()



