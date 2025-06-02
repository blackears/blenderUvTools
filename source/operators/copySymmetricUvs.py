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
import math

    
#--------------------------------------

class CopySymmetricUvSettings(bpy.types.PropertyGroup):
    axis : bpy.props.EnumProperty(
        items=(
            ('X', "X Axis", "Copy to faces across X axis"),
            ('Y', "Y Axis", "Copy to faces across Y axis"),
            ('Z', "Z Axis", "Copy to faces across Z axis")
        ),
        default='X'
    )
    
    epsilon : bpy.props.FloatProperty(
        name="Epsilon", description="How far away vertices can be and still be considered overlapping.", default = .001, min=0, soft_max = .01
    )
    
    different_islands_only : bpy.props.BoolProperty(
        name="Different Islands Only", description="Only copy the face if it belongs to a different uv island than the current face.", default = True
    )


#--------------------------------------

class CopySymmetricUvsOperator(bpy.types.Operator):
    """Copy UVs to faces that are symmetrically opposite of selected faces"""
    bl_idname = "kitfox.copy_symmetric_uvs"
    bl_label = "Copy Symmetric UVs"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
            

    def __del__(self):
        super().__del__()
        
    def findLoopMap(self, f0, f1, xform, epsilon):
        #Compare vertex positions
        if len(f0.loops) != len(f1.loops):
            return None

        indices = []

        for loop0 in f0.loops:
            pos0 = xform @ loop0.vert.co
            foundMatch = False
            
            
            for loop1 in f1.loops:
                pos1 = loop1.vert.co
            
                dist = pos0 - pos1
                if dist.magnitude < epsilon:
                    foundMatch = True
                    break
            
            if not foundMatch:
                return None
                
            indices.append(loop1)

        return indices
        
            
    def execute(self, context):
        props = context.scene.kitfox_copy_symmetric_uvs
        epsilon = props.epsilon
        axis = props.axis
        
        
        
        if axis == 'X':
            mMirror = mathutils.Matrix.Diagonal((-1, 1, 1))
            axisVec = mathutils.Vector((1, 0, 0))
        elif axis == 'Y':
            mMirror = mathutils.Matrix.Diagonal((1, -1, 1))
            axisVec = mathutils.Vector((0, 1, 0))
        elif axis == 'Z':
            mMirror = mathutils.Matrix.Diagonal((1, 1, -1))
            axisVec = mathutils.Vector((0, 0, 1))
    
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            l2w = obj.matrix_world
            
            mesh = obj.data
            
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)
    
            uv_layer = bm.loops.layers.uv.verify()
            
            selectedFaces = []
    
            for f in bm.faces:
                if f.select:
                    selectedFaces.append(f)

            for f0 in selectedFaces:
                for f1 in bm.faces:
                    if f0 == f1.loops:
                        continue
                        
                    center0 = f0.calc_center_bounds()
                    center1 = f1.calc_center_bounds()
                    
                    center1m = mMirror @ center1
                    
                    if (center0 - center1m).magnitude > epsilon:
                        continue
                        
                    if f1.select:
                        if axisVec.dot(center1) > 0:
                            #If both source face and reflection are selected, copy from positive side of axis to negative
                            continue
                     
                    loopMap = self.findLoopMap(f0, f1, mMirror, epsilon)
                    if loopMap == None:
                        continue

                    #Copy uv
                    for i in range(len(loopMap)):
                        loop0 = f0.loops[i]
                        loop1 = loopMap[i]
                        loop1[uv_layer].uv = loop0[uv_layer].uv
            

            if obj.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
    
        
        
        return {'FINISHED'}

#---------------------------


def register():
    bpy.utils.register_class(CopySymmetricUvSettings)
    bpy.utils.register_class(CopySymmetricUvsOperator)

    bpy.types.Scene.kitfox_copy_symmetric_uvs = bpy.props.PointerProperty(type=CopySymmetricUvSettings)


def unregister():
    
    bpy.utils.unregister_class(CopySymmetricUvSettings)
    bpy.utils.unregister_class(CopySymmetricUvsOperator)
    
    del bpy.types.Scene.kitfox_copy_symmetric_uvs


if __name__ == "__main__":
    register()


