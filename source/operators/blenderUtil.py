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
import mathutils

def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    
#Wrap Blender's ray_cast, since the way the method was called changed in verison 2.91
def ray_cast_scene(context, viewlayer, ray_origin, view_vector):
    if bpy.app.version >= (2, 91, 0):
        return context.scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)
    else:
        return context.scene.ray_cast(viewlayer, ray_origin, view_vector)
    
        
def mesh_bounds_world(obj):

    minCo = None
    maxCo = None
    mesh = obj.data
    
    for v in mesh.vertices:
        pos = mathutils.Vector(v.co)
        pos = obj.matrix_world @ pos
    
#            print("pos " + str(pos))
    
        if minCo == None:
            minCo = mathutils.Vector(pos)
            maxCo = mathutils.Vector(pos)
        else:
            minCo.x = min(minCo.x, pos.x)
            minCo.y = min(minCo.y, pos.y)
            minCo.z = min(minCo.z, pos.z)
            maxCo.x = max(maxCo.x, pos.x)
            maxCo.y = max(maxCo.y, pos.y)
            maxCo.z = max(maxCo.z, pos.z)
            
    return (minCo, maxCo)
