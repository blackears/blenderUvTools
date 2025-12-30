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
import blf
import gpu
import mathutils
import math
import bmesh
from .vecmath import *
from .blenderUtil import *

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils


circleSegs = 64
coordsCircle = [(math.sin(((2 * math.pi * i) / circleSegs)), math.cos((math.pi * 2 * i) / circleSegs), 0) for i in range(circleSegs + 1)]

coordsNormal = [(0, 0, 0), (0, 0, 1)]

vecZ = mathutils.Vector((0, 0, 1))
vecX = mathutils.Vector((1, 0, 0))

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
batchLine = batch_for_shader(shader, 'LINES', {"pos": coordsNormal})
batchCircle = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsCircle})

#--------------------------------------

class UvBrushToolSettings(bpy.types.PropertyGroup):
    
    radius : bpy.props.FloatProperty(
        name="Radius", description="Radius of brush", default = 1, min=0, soft_max = 4
    )

    strength : bpy.props.FloatProperty(
        name="Strength", description="Strength of brush", default = 1, min=0, soft_max = 4
    )

    use_pressure : bpy.props.BoolProperty(
        name="Pen Pressure", description="If true, pen pressure is used to adjust strength", default = False
    )

#--------------------------------------


#Find matrix that maps onto vertex UV space with Z along normal
#coord - point in world space
#normal - normal in world space
def calc_vertex_transform_world(pos, norm):
    axis = norm.cross(vecZ)
    if axis.length_squared < .0001:
        axis = mathutils.Vector(vecX)
    else:
        axis.normalize()
    angle = -math.acos(norm.dot(vecZ))
    
    quat = mathutils.Quaternion(axis, angle)
    mR = quat.to_matrix()
    mR.resize_4x4()
    
    mT = mathutils.Matrix.Translation(pos)

    m = mT @ mR
    return m


def draw_callback(self, context):
#    if True:
#        return

    ctx = bpy.context

    region = context.region
    rv3d = context.region_data

    viewport_center = (region.x + region.width / 2, region.y + region.height / 2)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, viewport_center)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, viewport_center)


    shader.bind();

    #Draw cursor
    if self.show_cursor:
        brush_radius = context.scene.uv_brush_props.radius
    
        m = calc_vertex_transform_world(self.cursor_pos, self.cursor_normal);
        mS = mathutils.Matrix.Scale(brush_radius, 4)
        m = m @ mS
    
        #Tangent to mesh
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(m)

        shader.uniform_float("color", (1, 0, 1, 1))
        batchCircle.draw(shader)
        
        gpu.matrix.pop()


class UvTracker:
    def __init__(self, uv, dist, newUv):
        self.uv = uv
        self.dist = dist
        self.newUv = newUv
        
    def toString(self):
        print("        uv %s  dist %s  newUv %s"  % (str(self.uv), str(self.dist), str(self.newUv)))
    
class VertexTracker:

    def __init__(self, vert):
        self.vert = vert
        self.uvInfo = []
        
    def considerUv(self, uv_in, dist_in, newUv_in):
#        print("Adding uv %s  dist %s  newUv %s" % (str(uv_in), str(dist_in), str(newUv_in)))
    
        for i in range(len(self.uvInfo)):
            map = self.uvInfo[i]
            
            #Check if uv_in already has an entry for this vertex
            if map.uv == uv_in:
#                print("found in map")
                if map.dist > dist_in:
#                    print("adding to map")
                    map.dist = dist_in
                    map.newUv = newUv_in
                
                return
 
        #Uv for this vertex not encountered yet.  Create new entry
        map = UvTracker(uv_in, dist_in, newUv_in)
        self.uvInfo.append(map)
                    
    def getNewUv(self, uv):
#        print("Looking up uv %s  " % (str(uv)))
        for map in self.uvInfo:
#            print("Checking against uv %s  " % (str(map.uv)))
            if map.uv == uv:
#                print("Matched!")
                return map.newUv
        
        return None
         
    def toString(self):
        print("    vert_index %d"  % (self.vert_index))
        for map in self.uvInfo:
            map.toString()
    
    
#-------------------------------------

class UvBrushToolOperator(bpy.types.Operator):
    """Move uvs on your mesh by stroking a brush."""
    bl_idname = "kitfox.uv_brush_operator"
    bl_label = "UV Brush"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dragging = False
        
        self.cursor_pos = None
        self.show_cursor = False
        self.edit_object = None
        self.stroke_trail = []
        
        self.history = []
        self.history_idx = -1
        self.history_limit = 10
        self.history_bookmarks = {}
        
#        print("construct UvBrushToolOperator")

    def __del__(self):
        super().__del__()
        
    def free_snapshot(self, map):
        for obj in map:
            bm = map[obj]
            bm.free()

    #if bookmark is other than -1, snapshot added to bookmark library rather than undo stack
    def history_snapshot(self, context, bookmark = -1):
        if True:
            #Disabling history for now
            return
    
        map = {}
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = bmesh.new()
                
                mesh = obj.data
                bm.from_mesh(mesh)
                map[obj] = bm
                
        if bookmark != -1:
            self.history_bookmarks[bookmark] = map
                
        else:
            #Remove first element if history queue is maxed out
            if self.history_idx == self.history_limit:
                self.free_snapshot(self.history[0])
                self.history.pop(0)
            
                self.history_idx += 1

            #Remove all history past current pointer
            while self.history_idx < len(self.history) - 1:
                self.free_snapshot(self.history[-1])
                self.history.pop()
                    
            self.history.append(map)
            self.history_idx += 1
        
    def history_undo(self, context):
        if True:
            #Disabling history for now
            return
    
        if (self.history_idx == 0):
            return
            
        self.history_undo_to_snapshot(context, self.history_idx - 1)
                
    def history_redo(self, context):
        if True:
            #Disabling history for now
            return
    
        if (self.history_idx == len(self.history) - 1):
            return

        self.history_undo_to_snapshot(context, self.history_idx + 1)
            
        
    def history_restore_bookmark(self, context, bookmark):
        if True:
            #Disabling history for now
            return
    
        map = self.history[bookmark]
    
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = map[obj]
                
                if obj.mode == 'OBJECT':
                #self.edit_object
                    mesh = obj.data
                    bm.to_mesh(mesh)
                    mesh.update()
                elif obj.mode == 'EDIT':
                    objBm = bmesh.from_edit_mesh(obj.data)
                    #TODO: Somehow copy bm data to objBm
                    
                    #bm.clear()
                    #bmesh.update_edit_mesh(obj.data)
        
    def history_undo_to_snapshot(self, context, idx):
        if True:
            #Disabling history for now
            return
    
        if idx < 0 or idx >= len(self.history):
            return
            
        self.history_idx = idx
       
        map = self.history[self.history_idx]
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bm = map[obj]
                
                mesh = obj.data
                if obj.mode == 'OBJECT':
                    bm.to_mesh(mesh)
                    mesh.update()
                elif obj.mode == 'EDIT':
                    bm.update_edit_mesh(mesh)
        
    def history_clear(self, context):
        for key in self.history_bookmarks:
            map = self.history_bookmarks[key]
            self.free_snapshot(map)
    
        for map in self.history:
            self.free_snapshot(map)
                
        self.history = []
        self.history_idx = -1


    def dab_brush(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        
        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        
        hit_object = None
        location = None
        normal = None
        index = None
        
        if self.edit_object == None:
            hit_object, location, normal, face_index, object, matrix = ray_cast_scene(context, viewlayer, ray_origin, view_vector)
        else:
            l2w = self.edit_object.matrix_world
            w2l = l2w.inverted()
            local_ray_origin = w2l @ ray_origin
            local_view_vector = mul_vector(w2l, view_vector)
            
            if self.edit_object.mode == 'OBJECT':
                hit_object, location, normal, index = self.edit_object.ray_cast(local_ray_origin, local_view_vector)
                object = self.edit_object

                location = l2w @ location
                
            if self.edit_object.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(self.edit_object.data)
                tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)
                location, normal, index, distance = tree.ray_cast(local_ray_origin, local_view_vector)
                hit_object = location != None
                object = self.edit_object
            
                location = l2w @ location
            
            
#        print("hit obj:%s" % (str(hit_object)))
        
        center = None
        center_count = 0

        brush_radius = context.scene.uv_brush_props.radius
        strength = context.scene.uv_brush_props.strength
        use_pressure = context.scene.uv_brush_props.use_pressure
        
        if hit_object and len(self.stroke_trail) > 0:
            
            if self.edit_object == None:
                self.edit_object = object
#            print("--------Edit object uvs") 
            
            l2w = object.matrix_world
            n2w = l2w.copy()
            n2w.invert()
            n2w.transpose()
            
            mesh = object.data
            if self.edit_object.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif self.edit_object.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)
            
#            uvLayer = mesh.uv_layers.active.data
            uv_layer = bm.loops.layers.uv.active
            
            vert_trackers = [VertexTracker(v) for v in bm.verts]
            
            for face in bm.faces:
                l0 = face.loops[0]
                l1 = face.loops[1]
                l2 = face.loops[2]
            
                v0pos = l2w @ l0.vert.co
                v1pos = l2w @ l1.vert.co
                v2pos = l2w @ l2.vert.co
                
#                print("v0pos: %s  v1pos: %s  v2pos: %s  " % (str(v0pos), str(v1pos), str(v2pos)))

                v1 = v1pos - v0pos
                v2 = v2pos - v0pos

#                print("v1: %s  v2: %s  norm: %s  " % (str(v1), str(v2), str(p.normal)))

                faceNormal = mul_vector(n2w, face.normal)
                
                dragP0 = project_point_onto_plane(self.stroke_trail[-1], v0pos, faceNormal)
                dragP1 = project_point_onto_plane(location, v0pos, faceNormal)

#                print("dragP0: %s  dragP1: %s" % (str(dragP0), str(dragP1)))

                uv0 = l0[uv_layer].uv
                uv1 = l1[uv_layer].uv
                uv2 = l2[uv_layer].uv
                # uv0 = uvLayer[p.loop_indices[0]].uv
                # uv1 = uvLayer[p.loop_indices[1]].uv
                # uv2 = uvLayer[p.loop_indices[2]].uv

#                print("uv0: %s  uv1: %s  uv2: %s" % (str(uv0), str(uv1), str(uv2)))
                
            
                locCo0 = express_in_basis(dragP0 - v0pos, v1, v2, faceNormal)
                locCo1 = express_in_basis(dragP1 - v0pos, v1, v2, faceNormal)

#                print("locCo0: %s  locCo1: %s" % (str(locCo0), str(locCo1)))
            
                dragUv0 = (uv1 - uv0) * locCo0.x + (uv2 - uv0) * locCo0.y + uv0
                dragUv1 = (uv1 - uv0) * locCo1.x + (uv2 - uv0) * locCo1.y + uv0
                dUv = dragUv1 - dragUv0

#                print("dragUv0: %s  dragUv1: %s  dUv: %s" % (str(dragUv0), str(dragUv1), str(dUv)))
                    
#                print ("dUv.magnitude " + str(dUv.magnitude))
            
#                print("loop total:%d" % (p.loop_total))
            
                for loop in face.loops:
                    
                    loop_uv = loop[uv_layer].uv
                    v = loop.vert
                    pos = l2w @ v.co
                    dist = (pos - location).magnitude
#                    print ("dist " + str(dist))
                    if dist < brush_radius:
                        atten = 1 - dist / brush_radius
                        atten *= strength
                        if use_pressure:
                            atten *= event.pressure
                        vert_trackers[v.index].considerUv(loop_uv.copy(), dist, loop_uv - atten * dUv)

            #Write new uvs back to mesh
            
            for face in bm.faces:
                for loop in face.loops:
#                    loop = mesh.loops[loop_idx]
#                    print("lookup vertidx %s  uv %s " % (str(loop.vertex_index), str(uvLayer[loop_idx].uv)))
                    
                    loop_uv = loop[uv_layer].uv
                    tracker = vert_trackers[loop.vert.index]
                    newUv = tracker.getNewUv(loop_uv)
                    if newUv != None:
                        loop[uv_layer].uv = newUv
                    

            if self.edit_object.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif self.edit_object.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
        
        if hit_object:        
            self.stroke_trail.append(location)
            
        else:
            self.stroke_trail = []
            self.edit_object = None
        
    def mouse_move(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        ctx = bpy.context

        region = context.region
        rv3d = context.region_data

        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

        viewlayer = bpy.context.view_layer
        result, location, normal, index, object, matrix = ray_cast_scene(context, viewlayer, ray_origin, view_vector)
        
        #Brush cursor display
        if result:
            self.show_cursor = True
            self.cursor_pos = location
            self.cursor_normal = normal
            self.cursor_object = object
            self.cursor_matrix = matrix
        else:
            self.show_cursor = False

        if self.dragging:
            self.dab_brush(context, event)
            pass


    def mouse_click(self, context, event):
        if event.value == "PRESS":
            
            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            region = context.region
            rv3d = context.region_data

            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

            viewlayer = bpy.context.view_layer
            result, location, normal, index, object, matrix = ray_cast_scene(context, viewlayer, ray_origin, view_vector)

            if result == False or object.select_get() == False or object.type != 'MESH':
                return {'PASS_THROUGH'}
                            
            self.dragging = True
            self.stroke_trail = []
            
            self.edit_object = object
            
            self.dab_brush(context, event)
            
            
            # self.init_mesh = bmesh.new()
            # self.init_mesh.copyFrom(object)
            
        elif event.value == "RELEASE":
            self.dragging = False
            self.edit_object = None
            
            self.history_snapshot(context)


        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def modal(self, context, event):
#        print("modal evTyp:%s evVal:%s" % (str(event.type), str(event.value)))
        context.area.tag_redraw()

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        
        elif event.type == 'MOUSEMOVE':
            context.window.cursor_set("PAINT_BRUSH")
        
            self.mouse_move(context, event)
            
            if self.dragging:
                return {'RUNNING_MODAL'}
            else:
                return {'PASS_THROUGH'}
            
        elif event.type == 'LEFTMOUSE':
            return self.mouse_click(context, event)

        # elif event.type == 'RIGHTMOUSE':
            # mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            # print("  pos %s" % str(mouse_pos))
            
            # bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            # self.show_cursor = False
    
            # return {'FINISHED'}
            
        elif event.type in {'Z'}:
            if event.ctrl:
                if event.shift:
                    if event.value == "RELEASE":
                        self.history_redo(context)
                    return {'RUNNING_MODAL'}
                else:
                    if event.value == "RELEASE":
                        self.history_undo(context)

                    return {'RUNNING_MODAL'}
                
            return {'RUNNING_MODAL'}
            
        elif event.type in {'RET'}:
            if event.value == 'RELEASE':
                context.window.cursor_set("DEFAULT")
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.history_clear(context)
                return {'FINISHED'}
            return {'RUNNING_MODAL'}

        elif event.type in {'PAGE_UP', 'RIGHT_BRACKET'}:
            if event.value == "PRESS":
                brush_radius = context.scene.uv_brush_props.radius
                brush_radius = brush_radius + .1
                context.scene.uv_brush_props.radius = brush_radius
            return {'RUNNING_MODAL'}

        elif event.type in {'PAGE_DOWN', 'LEFT_BRACKET'}:
            if event.value == "PRESS":
                brush_radius = context.scene.uv_brush_props.radius
                brush_radius = max(brush_radius - .1, .1)
                context.scene.uv_brush_props.radius = brush_radius
            return {'RUNNING_MODAL'}
            
        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.window.cursor_set("DEFAULT")
                self.history_restore_bookmark(context, 0)
                self.history_clear(context)            
                return {'CANCELLED'}
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

#    def execute(self, context):
#        print("execute SimpleOperator")
#        return {'FINISHED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
    #        print("invoke evTyp:%s evVal:%s" % (str(event.type), str(event.value)))

            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')

            redraw_all_viewports(context)
            self.history_clear(context)
            self.history_snapshot(context)
            self.history_snapshot(context, 0)

            context.window_manager.modal_handler_add(self)

            context.window.cursor_set("PAINT_BRUSH")
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}



#---------------------------



def register():

    #Register tools
    bpy.utils.register_class(UvBrushToolSettings)
    bpy.utils.register_class(UvBrushToolOperator)

    bpy.types.Scene.uv_brush_props = bpy.props.PointerProperty(type=UvBrushToolSettings)

def unregister():
    bpy.utils.unregister_class(UvBrushToolSettings)
    bpy.utils.unregister_class(UvBrushToolOperator)
    
    del bpy.types.Scene.uv_brush_props


if __name__ == "__main__":
    register()