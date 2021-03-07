import bpy
import bpy.utils.previews
import os
import bgl
import blf
import gpu
import mathutils
import math
import bmesh

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from enum import Enum

from .vecmath import *
from .blenderUtil import *

class UvPlaneLayoutSettings(bpy.types.PropertyGroup):
    brush_type : bpy.props.EnumProperty(
        items=(
            ('FIXED', "Fixed", "Normals are in a fixed direction"),
            ('ATTRACT', "Attract", "Normals point toward target object"),
            ('REPEL', "Repel", "Normals point away from target object"),
            ('VERTEX', "Vertex", "Get normal values from mesh vertices")
        ),
        default='FIXED'
    )



#---------------------------

class UvPlaneControl:
#    handles = []
#    bmesh_start = None
    
    def __init__(self, context):
        self.controlMtx = None
    
        self.setFromMeshes(context)

    
        # self.obj = obj
        # mesh = obj.data
        
        self.handles = []
        
        # self.bmesh_start = bmesh.new()
        # self.bmesh_start.from_mesh(mesh)
        
        # (self.minCo, self.maxCo) = self.mesh_bounds_world(obj)
        
        # span = self.maxCo - self.minCo
        
        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((.5, .5, 0)), -vecZ, Face.Z_NEG))
        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((.5, .5, 1)), vecZ, Face.Z_POS))

        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((.5, 0, .5)), -vecY, Face.Y_NEG))
        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((.5, 1, .5)), vecY, Face.Y_POS))

        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((0, .5, .5)), -vecX, Face.X_NEG))
        # self.handles.append(HandleDirectionial(self, self.minCo + span * mathutils.Vector((1, .5, .5)), vecX, Face.X_POS))

    def findTangent(self, norm):
        if 1 - norm.normalized().dot(vecZ) < .0001:
#        if norm.x == 0 and norm.y == 0:
            return vecX.copy()
            
        tan = norm.cross(vecZ)
        tan.normalize()
        return tan

    def setFromMeshes(self, context):
    
        #find polygon with largest area
        bestArea = 0
        bestNormal = None
        bestCenter = None
        
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            mesh = obj.data
            l2w = obj.matrix_world
            n2w = l2w.copy()
            n2w.invert()
            n2w.transpose()
            
            bestPoly = None
            
            for p in mesh.polygons:
                if bestArea < p.area:
                    bestArea = p.area
                    bestNormal = n2w @ p.normal
                    bestCenter = l2w @ p.center
                    
            
        if bestNormal == None:
            self.controlMtx = None        
            return 
            
        print("bestNorm %s  bestCenter %s " % (str(bestNormal), str(bestCenter)))
            
        #Build matrix from world space to face space
        tangent = self.findTangent(bestNormal)
        binormal = bestNormal.cross(tangent)

        print("tangent %s  binormal %s " % (str(tangent), str(binormal)))

        tangent = tangent.to_4d()
        tangent.w = 0
        binormal = binormal.to_4d()
        binormal.w = 0
        bestNormal = bestNormal.to_4d()
        bestNormal.w = 0
        center = bestCenter.to_4d()
        center.w = 1
        poly2w = mathutils.Matrix((tangent.to_4d(), binormal.to_4d(), bestNormal.to_4d(), center))
        poly2w.transpose()
        w2poly = poly2w.inverted()

        print("poly2w %s\n" % (str(poly2w)))
        print("w2poly %s\n" % (str(w2poly)))

        #find bounds of mesh projected along normal of chosen polygon
        minX = None
        maxX = None
        minY = None
        maxY = None
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            mesh = obj.data
            
            l2w = obj.matrix_world
            l2poly = w2poly @ l2w
            
            for p in mesh.polygons:
                for vIdx in p.vertices:
                    v = mesh.vertices[vIdx]
                    
                    faceV = l2poly @ v.co
                    
                    print("mapping v %s -> %s " % (str(v.co), str(faceV)))
           
                    minX = faceV.x if minX == None else min(faceV.x, minX)
                    maxX = faceV.x if maxX == None else max(faceV.x, maxX)
                    minY = faceV.y if minY == None else min(faceV.y, minY)
                    maxY = faceV.y if maxY == None else max(faceV.y, maxY)
                    

        print("minX %s  maxX %s  minY %s  maxY %s " % (str(minX), str(maxX), str(minY), str(maxY)))

        dx = maxX - minX
        dy = maxY - minY
        cx = (maxX + minX) / 2
        cy = (maxY + minY) / 2
        ctrlCenter = cx * tangent + cy * binormal + center
#        ctrlCenter.w = 1
        print("dx %s  dy %s  cx %s  cy %s " % (str(dx), str(dy), str(cx), str(cy)))
        print("cx tan %s  cy tan %s" % (str(cx * tangent), str(cy * binormal)))

        self.controlMtx = mathutils.Matrix((tangent * dx / 2, binormal * dy / 2, bestNormal, ctrlCenter))
        self.controlMtx.transpose()

        print("controlMtx %s" % (str(self.controlMtx)))
            

    
        
    def __del__(self):
#        print("MeshTracker DESTRUCT")
        for h in self.handles:
            del h
        
        # if self.bmesh_start != None:
            # self.bmesh_start.free()

    
    def draw(self, context):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
#        batchCube = batch_for_shader(shader, 'LINES', {"pos": coordsCube})
        batchCube = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsSquare2_strip})
            
        #self.controlMtx = 
        
#        (minCo, maxCo) = self.mesh_bounds_world(self.obj)
        
        if self.controlMtx == None:
            return
        
        shader.bind();
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(self.controlMtx)
        shader.uniform_float("color", (1, 0, 1, 1))
        batchCube.draw(shader)
        
        gpu.matrix.pop()
    
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        
#        print("  DRAW HANDLESs")
        for handle in self.handles:
#            print("  Drawing handle " + str(handle))
            handle.draw(context)
            
    def mouse_move(self, context, event):
        consumed = False
        for handle in self.handles:
            if handle.mouse_move(context, event):
                consumed = True
                break
        return consumed

    def mouse_click(self, context, event):
        consumed = False
        for handle in self.handles:
            if handle.mouse_button(context, event):
                consumed = True
                break
            
        return consumed

#---------------------------



def draw_callback(self, context):
    
    ctx = bpy.context

    if self.control != None:
        self.control.draw(context)
    
    # region = context.region
    # rv3d = context.region_data

    # viewport_center = (region.x + region.width / 2, region.y + region.height / 2)
    # view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, viewport_center)
    # ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, viewport_center)


    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    # batchCube = batch_for_shader(shader, 'LINES', {"pos": coordsCube})
    # batchSquare = batch_for_shader(shader, 'TRI_FAN', {"pos": coordsSquare})
    # batchCircle = batch_for_shader(shader, 'TRI_FAN', {"pos": coordsCircle})


# #    print("DRAW MTs")
    # for mesh_tracker in self.mesh_trackers:
# #        print("Drawing mt " + str(mesh_tracker))
        # mesh_tracker.draw(context)


#---------------------------

class UvLayoutPlaneOperator(bpy.types.Operator):
    """Plane projection for UVs"""
    bl_idname = "kitfox.uv_plane_layout_op"
    bl_label = "Uv Layout"
    bl_options = {"REGISTER", "UNDO"}


    def __init__(self):
        #self.mesh_trackers = []
        self.control = None
        


    def mouse_move(self, context, event):
    
        consumed = False
        
        if self.control:
            self.control.mouse_move(context, event)
            consumed = True
        
        # for mesh_tracker in self.mesh_trackers:
            # if mesh_tracker.mouse_move(context, event):
                # consumed = True

    
        if consumed:
            return {'RUNNING_MODAL'}
        else:
            return {'PASS_THROUGH'}
        

    def mouse_click(self, context, event):
    
        consumed = False
        
        if self.control:
            self.control.mouse_click(context, event)
            consumed = True
            
        
        # for mesh_tracker in self.mesh_trackers:
            # if mesh_tracker.mouse_button(context, event):
                # consumed = True
                # break
            
        if consumed:
            return {'RUNNING_MODAL'}
        else:
            return {'PASS_THROUGH'}
            

    def modal(self, context, event):
        
#        context.area.tag_redraw()
        redraw_all_viewports(context)

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        elif event.type == 'MOUSEMOVE':
            return self.mouse_move(context, event)
            
        elif event.type == 'LEFTMOUSE':
            return self.mouse_click(context, event)
#            return {'PASS_THROUGH'}
#            return {'RUNNING_MODAL'}
        
        elif event.type in {'RET'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
            
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}
#        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._context = context
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')

#            context.area.tag_redraw()
            redraw_all_viewports(context)

            context.window_manager.modal_handler_add(self)

            if self.control:
                del self.control
            # for mt in self.mesh_trackers:
                # del mt            

            self.control = UvPlaneControl(context)

            # self.mesh_trackers = []
            # for obj in context.selected_objects:
                # if obj.type != "MESH":
                    # continue
                # self.mesh_trackers.append(MeshTracker(obj))
#            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


#---------------------------


def register():
    bpy.utils.register_class(UvPlaneLayoutSettings)
    bpy.utils.register_class(UvLayoutPlaneOperator)

    bpy.types.Scene.kitfox_uv_plane_layout_props = bpy.props.PointerProperty(type=UvPlaneLayoutSettings)


def unregister():
    
    bpy.utils.unregister_class(UvPlaneLayoutSettings)
    bpy.utils.unregister_class(UvLayoutPlaneOperator)
    
    del bpy.types.Scene.kitfox_uv_plane_layout_props


if __name__ == "__main__":
    register()


