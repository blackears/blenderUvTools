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
from .handles import *
from .blenderUtil import *

class UvPlaneLayoutSettings(bpy.types.PropertyGroup):
    selected_faces_only : bpy.props.BoolProperty(
        name="Seleccted Faces Only", 
        description="Only change uvs of selected faces", 
        default = True
    )


#---------------------------

class UvPlaneControl:
    
    def __init__(self, context):
        self.controlMtx = None
    
        self.setFromMeshes(context)

        
        self.handle00 = HandleCorner(self, mathutils.Matrix.Translation(-vecX - vecY), vecZ, -vecX - vecY)
        self.handle02 = HandleCorner(self, mathutils.Matrix.Translation(-vecX + vecY), vecZ, -vecX + vecY)
        self.handle20 = HandleCorner(self, mathutils.Matrix.Translation(vecX - vecY), vecZ, vecX - vecY)
        self.handle22 = HandleCorner(self, mathutils.Matrix.Translation(vecX + vecY), vecZ, vecX + vecY)

        self.handle10 = HandleEdge(self, mathutils.Matrix.Translation(-vecY), -vecY, -vecY)
        self.handle01 = HandleEdge(self, mathutils.Matrix.Translation(-vecX), -vecX, -vecX)
        self.handle12 = HandleEdge(self, mathutils.Matrix.Translation(vecY), vecY, vecY)
        self.handle21 = HandleEdge(self, mathutils.Matrix.Translation(vecX), vecX, vecX)

        self.handle11 = HandleTranslate(self, mathutils.Matrix(), HandleConstraintOmni(), vecZero)

        self.handleRotX = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecX, vecX)
        self.handleRotY = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecY, vecY)
        self.handleRotZ = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecZ, vecZ)

        
        self.handle00.body.color = (0, 0, 1, 1)
        self.handle02.body.color = (0, 1, 1, 1)
        self.handle20.body.color = (1, 0, 1, 1)
        self.handle22.body.color = (1, 1, 1, 1)

        self.handleRotX.body.color = (1, 0, 0, 1)
        self.handleRotY.body.color = (0, 1, 0, 1)
        self.handleRotZ.body.color = (0, 0, 1, 1)
        
        self.handles = [self.handle00, self.handle02, self.handle20, self.handle22, self.handle10, self.handle01, self.handle12, self.handle21, self.handle11, self.handleRotX, self.handleRotY, self.handleRotZ]
        
        self.layoutHandles()

        
    def __del__(self):
#        print("UvPlaneControl DESTRUCT")
        for h in self.handles:
            del h
        
            
    def mouse_move(self, context, event):
        consumed = False
        for handle in self.handles:
            if handle.mouse_move(context, event):
                consumed = True
                break
                
        #update uvs
        w2uv = self.controlMtx.inverted()
        
        props = context.scene.kitfox_uv_plane_layout_props
        selected_faces_only = props.selected_faces_only
#        print("self.controlMtx %s" % (str(self.controlMtx)))
#        print("w2uv %s" % (str(w2uv)))
        
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            mesh = obj.data
            l2w = obj.matrix_world
            
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)
                

            uv_layer = bm.loops.layers.uv.verify()
            
            for face in bm.faces:
                if not selected_faces_only or face.select:
                    for loop in face.loops:
                        loop_uv = loop[uv_layer]
                        
                        uvPos = w2uv @ loop.vert.co
                        
                        #print("worldPos %s" % (str(uvPos)))
                        loop_uv.uv = uvPos.xy

            if obj.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
                
                
        return consumed

    def mouse_click(self, context, event):
        consumed = False
        for handle in self.handles:
            if handle.mouse_click(context, event):
                consumed = True
                redraw_all_viewports(context)
                break
            
        return consumed

    def layoutHandles(self):
        i = self.controlMtx.col[0].to_3d()
        j = self.controlMtx.col[1].to_3d()
        k = self.controlMtx.col[2].to_3d()
        
        self.handle00.transform = self.controlMtx @ mathutils.Matrix.Translation((-1, -1, 0))
        self.handle00.constraint.planeNormal = k
        
        self.handle02.transform = self.controlMtx @ mathutils.Matrix.Translation((-1, 1, 0))
        self.handle02.constraint.planeNormal = k
        
        self.handle20.transform = self.controlMtx @ mathutils.Matrix.Translation((1, -1, 0))
        self.handle20.constraint.planeNormal = k
        
        self.handle22.transform = self.controlMtx @ mathutils.Matrix.Translation((1, 1, 0))
        self.handle22.constraint.planeNormal = k
        
        
        self.handle01.transform = self.controlMtx @ mathutils.Matrix.Translation(-vecX)
        self.handle01.constraint.vector = -i
        
        self.handle21.transform = self.controlMtx @ mathutils.Matrix.Translation(vecX)
        self.handle21.constraint.vector = i
        
        self.handle10.transform = self.controlMtx @ mathutils.Matrix.Translation(-vecY)
        self.handle10.constraint.vector = -j
        
        self.handle12.transform = self.controlMtx @ mathutils.Matrix.Translation(vecY)
        self.handle12.constraint.vector = j

        self.handle11.transform = self.controlMtx @ mathutils.Matrix.Translation(vecZero)
        
        self.handleRotX.transform = self.controlMtx @ mathutils.Matrix.Translation(vecZero) @ mathutils.Matrix.Rotation(math.radians(90), 4, 'Y')
        self.handleRotX.constraint.planeNormal = i
        
        self.handleRotY.transform = self.controlMtx @ mathutils.Matrix.Translation(vecZero) @ mathutils.Matrix.Rotation(math.radians(90), 4, 'X')
        self.handleRotY.constraint.planeNormal = j
        
        self.handleRotZ.transform = self.controlMtx @ mathutils.Matrix.Translation(vecZero)
        self.handleRotZ.constraint.planeNormal = k
        
    def updateProjectionMatrix(self, context, matrix):
        self.controlMtx = matrix
        self.layoutHandles()
        redraw_all_viewports(context)
        

    def findTangent(self, norm):
        if 1 - norm.normalized().dot(vecZ) < .0001:
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
            
        #print("bestNorm %s  bestCenter %s " % (str(bestNormal), str(bestCenter)))
            
        #Build matrix from world space to face space
        tangent = self.findTangent(bestNormal)
        binormal = bestNormal.cross(tangent)

        #print("tangent %s  binormal %s " % (str(tangent), str(binormal)))

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

        #print("poly2w %s\n" % (str(poly2w)))
        #print("w2poly %s\n" % (str(w2poly)))

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
                    

        #print("minX %s  maxX %s  minY %s  maxY %s " % (str(minX), str(maxX), str(minY), str(maxY)))

        dx = maxX - minX
        dy = maxY - minY
        cx = (maxX + minX) / 2
        cy = (maxY + minY) / 2
        ctrlCenter = cx * tangent + cy * binormal + center
#        ctrlCenter.w = 1
        #print("dx %s  dy %s  cx %s  cy %s " % (str(dx), str(dy), str(cx), str(cy)))
        #print("cx tan %s  cy tan %s" % (str(cx * tangent), str(cy * binormal)))

        self.controlMtx = mathutils.Matrix((tangent * dx / 2, binormal * dy / 2, bestNormal, ctrlCenter))
        self.controlMtx.transpose()

        #print("controlMtx %s" % (str(self.controlMtx)))
            

    

    
    def draw(self, context):
        #print("draign control")
    
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
#        batchCube = batch_for_shader(shader, 'LINES', {"pos": coordsCube})
        batchCube = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsSquare2_strip})
            
        
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


