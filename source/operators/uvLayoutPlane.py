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
#import bgl
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
    init_layout : bpy.props.EnumProperty(
        items=(
            ('BOUNDS', "Bounds", "Fit to bounds of selected faces"),
            ('FACE', "Face", "Start with same UVs as active face"),
            ('GRID', "Grid", "Align UVs using grid of closest axis")
        ),
        default='BOUNDS'
    )

    selected_faces_only : bpy.props.BoolProperty(
        name="Selected Faces Only", 
        description="Only change uvs of selected faces", 
        default = True
    )

    clamp_to_basis : bpy.props.BoolProperty(
        name="Step by UVs", 
        description="When you translate the control, snap to a multiple of the length of the UV vectors.", 
        default = False
    )
    
    clamp_scalar : bpy.props.FloatProperty(
        name="Step UV scalar", 
        description="Step size when using step mode.  1 will step by the entire texture width, .5 by half the texture, etc.", 
        default = 1
    )

    relocate_origin : bpy.props.BoolProperty(
        name="Relocate Origin", 
        description="If true, when you start in Face mode, the origin will be relocated to be close to the center of the active face.", 
        default = True
    )


#---------------------------

class UvPlaneControl:
    
    def __init__(self, context):
        self.controlMtx = None

        props = context.scene.kitfox_uv_plane_layout_props
        init_layout = props.init_layout
    
        if init_layout == 'FACE':
            self.setProjFromActiveFace(context)
        elif init_layout == 'BOUNDS':
            self.setFromMeshes(context)
        elif init_layout == 'GRID':
            self.setFromGrid(context)

        
        self.handle00 = HandleCorner(self, mathutils.Matrix.Translation(-vecX - vecY), vecZ, mathutils.Vector((0, 0, 0)))
        self.handle02 = HandleCorner(self, mathutils.Matrix.Translation(-vecX + vecY), vecZ, mathutils.Vector((0, 1, 0)))
        self.handle20 = HandleCorner(self, mathutils.Matrix.Translation(vecX - vecY), vecZ, mathutils.Vector((1, 0, 0)))
        self.handle22 = HandleCorner(self, mathutils.Matrix.Translation(vecX + vecY), vecZ, mathutils.Vector((1, 1, 0)))

        self.handle10 = HandleEdge(self, mathutils.Matrix.Translation(-vecY), -vecY, mathutils.Vector((.5, 0, 0)))
        self.handle01 = HandleEdge(self, mathutils.Matrix.Translation(-vecX), -vecX, mathutils.Vector((0, .5, 0)))
        self.handle12 = HandleEdge(self, mathutils.Matrix.Translation(vecY), vecY, mathutils.Vector((.5, 1, 0)))
        self.handle21 = HandleEdge(self, mathutils.Matrix.Translation(vecX), vecX, mathutils.Vector((1, .5, 0)))

        self.handle11 = HandleTranslateOmni(self, mathutils.Matrix(), mathutils.Vector((.5, .5, 0)))

        self.handleTransX = HandleTranslateVector(self, mathutils.Matrix(), vecX, mathutils.Vector((1.3, .5, 0)))
        self.handleTransY = HandleTranslateVector(self, mathutils.Matrix(), vecY, mathutils.Vector((.5, 1.3, 0)))
        self.handleTransZ = HandleTranslateVector(self, mathutils.Matrix(), vecZ, mathutils.Vector((.5, .5, 1.3)))

        self.handleRotX = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecX, vecX)
        self.handleRotY = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecY, vecY)
        self.handleRotZ = HandleRotateAxis(self, mathutils.Matrix.Translation(vecZero), vecZ, vecZ)

        
        self.handle00.body.setColor((0, 0, 1, 1))
        self.handle02.body.setColor((0, 1, 1, 1))
        self.handle20.body.setColor((1, 0, 1, 1))
        self.handle22.body.setColor((1, 1, 1, 1))

        self.handleRotX.body.setColor((1, 0, 0, 1))
        self.handleRotY.body.setColor((0, 1, 0, 1))
        self.handleRotZ.body.setColor((0, 0, 1, 1))

        self.handleTransX.body.setColor((1, 0, 0, 1))
        self.handleTransY.body.setColor((0, 1, 0, 1))
        self.handleTransZ.body.setColor((0, 0, 1, 1))
        
        self.handles = [self.handle00, self.handle02, self.handle20, self.handle22, self.handle10, self.handle01, self.handle12, self.handle21, self.handle11, self.handleTransX, self.handleTransY, self.handleTransZ, self.handleRotX, self.handleRotY, self.handleRotZ]
        
        
        self.layoutHandles()
        self.updateUvs(context)

        
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

        return consumed
                
    def updateUvs(self, context):
        #update uvs
        w2uv = self.controlMtx.inverted()
        
        props = context.scene.kitfox_uv_plane_layout_props
        selected_faces_only = props.selected_faces_only
#        print("self.controlMtx %s" % (str(self.controlMtx)))
#        print("w2uv %s" % (str(w2uv)))
        
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
            
            for face in bm.faces:
                if not selected_faces_only or face.select:
                    for loop in face.loops:
                        loop_uv = loop[uv_layer]
                        
                        uvPos = w2uv @ l2w @ loop.vert.co
                        
                        #print("worldPos %s" % (str(uvPos)))
                        #print("worldPos %s" % (str(uvPos)))
                        loop_uv.uv = uvPos.xy

            if obj.mode == 'EDIT':
                bmesh.update_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm.to_mesh(mesh)
                bm.free()
                
                

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
        h = self.controlMtx.col[3].to_3d()
        
        # print("layout Handles " + str(self.controlMtx))
        # print("layout Handles i " + str(i))
        # print("layout Handles j " + str(j))
        # print("layout Handles k " + str(k))
        
        self.handle00.transform = self.controlMtx @ mathutils.Matrix.Translation((0, 0, 0))
        self.handle00.constraint.planeNormal = k
        
        self.handle02.transform = self.controlMtx @ mathutils.Matrix.Translation((0, 1, 0))
        self.handle02.constraint.planeNormal = k
        
        self.handle20.transform = self.controlMtx @ mathutils.Matrix.Translation((1, 0, 0))
        self.handle20.constraint.planeNormal = k
        
        self.handle22.transform = self.controlMtx @ mathutils.Matrix.Translation((1, 1, 0))
        self.handle22.constraint.planeNormal = k
        
        
        self.handle01.transform = self.controlMtx @ mathutils.Matrix.Translation(mathutils.Vector((0, .5, 0)))
        self.handle01.constraint.vector = -i
        
        self.handle21.transform = self.controlMtx @ mathutils.Matrix.Translation(mathutils.Vector((1, .5, 0)))
        self.handle21.constraint.vector = i
        
        self.handle10.transform = self.controlMtx @ mathutils.Matrix.Translation(mathutils.Vector((.5, 0, 0)))
        self.handle10.constraint.vector = -j
        
        self.handle12.transform = self.controlMtx @ mathutils.Matrix.Translation(mathutils.Vector((.5, 1, 0)))
        self.handle12.constraint.vector = j

        self.handle11.transform = self.controlMtx @ mathutils.Matrix.Translation(self.handle11.posControl)

        self.handleTransX.transform = self.controlMtx @ mathutils.Matrix.Translation(self.handleTransX.posControl)
        self.handleTransX.constraint.vector = i

        self.handleTransY.transform = self.controlMtx @ mathutils.Matrix.Translation(self.handleTransY.posControl)
        self.handleTransY.constraint.vector = j

        self.handleTransZ.transform = self.controlMtx @ mathutils.Matrix.Translation(self.handleTransZ.posControl)
        self.handleTransZ.constraint.vector = k
        
        center = mathutils.Vector((.5, .5, 0))
        self.handleRotX.transform = self.controlMtx @ mathutils.Matrix.Translation(center) @ mathutils.Matrix.Rotation(math.radians(90), 4, 'Y')
        self.handleRotX.constraint.planeNormal = i
        self.handleRotX.constraint.planeOrigin = self.controlMtx @ self.handleRotX.pivot
        
        self.handleRotY.transform = self.controlMtx @ mathutils.Matrix.Translation(center) @ mathutils.Matrix.Rotation(math.radians(90), 4, 'X')
        self.handleRotY.constraint.planeNormal = j
        self.handleRotY.constraint.planeOrigin = self.controlMtx @ self.handleRotY.pivot
        
        self.handleRotZ.transform = self.controlMtx @ mathutils.Matrix.Translation(center)
        self.handleRotZ.constraint.planeNormal = k
        self.handleRotZ.constraint.planeOrigin = self.controlMtx @ self.handleRotZ.pivot
        
        
    def updateProjectionMatrix(self, context, matrix):
        self.controlMtx = matrix
        self.layoutHandles()
        self.updateUvs(context)
        redraw_all_viewports(context)
        

    def findTangent(self, norm):
        if 1 - abs(norm.normalized().dot(vecZ)) < .0001:
            return vecX.copy()
            
        tan = norm.cross(vecZ)
        tan.normalize()
        return tan


    def setProjFromActiveFace(self, context):
        obj = context.active_object
        if obj == None or obj.type != 'MESH':
            self.controlMtx = None        
            return

        props = context.scene.kitfox_uv_plane_layout_props
        relocate_origin = props.relocate_origin

        bm = None
        
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        elif obj.mode == 'OBJECT':
            bm = bmesh.new()
            bm.from_mesh(obj.data)

#            print("active face idx " + str(bm.faces.active))
        face = bm.faces.active
        if face == None:
            bm.faces.ensure_lookup_table()
            face = bm.faces[0]

        l2w = obj.matrix_world
        n2w = l2w.copy()
        n2w.invert()
        n2w.transpose()
            
        bestNormal = n2w @ face.normal
        bestCenter = l2w @ face.calc_center_median()

        uv_layer = bm.loops.layers.uv.active

        l0 = face.loops[0]
        l1 = face.loops[1]
        l2 = face.loops[2]

        p0 = l2w @ face.verts[0].co
        p1 = l2w @ face.verts[1].co
        p2 = l2w @ face.verts[2].co
        
        # print("p0 " + str(p0))
        # print("p1 " + str(p1))
        # print("p2 " + str(p2))
        
        p3 = p0 - bestNormal
        
        uv0 = l0[uv_layer].uv
        uv1 = l1[uv_layer].uv
        uv2 = l2[uv_layer].uv

        #if uvs don't form the basis of a plane, artificially create one
        duv1 = uv1 - uv0
        duv2 = uv2 - uv0
        if duv1.magnitude < .0001 and duv2.magnitude < .0001:
            uv1 = uv0 + mathutils.Vector((1, 0, 0))
            uv2 = uv0 + mathutils.Vector((0, 1, 0))

        elif duv1.magnitude < .0001:
            uv1.x = -duv2.y
            uv1.y = duv2.x
            uv1 += uv0

        elif duv2.magnitude < .0001 or (uv2 - uv1).magnitude < .0001:
            uv2.x = duv1.y
            uv2.y = -duv1.x
            uv2 += uv0


        # print("uv0 " + str(uv0))
        # print("uv1 " + str(uv1))
        # print("uv2 " + str(uv2))
        # print("duv1 " + str(duv1))
        # print("duv2 " + str(duv2))
        
        U = mathutils.Matrix((
            (uv0.x, uv0.y, 0, 1),
            (uv1.x, uv1.y, 0, 1),
            (uv2.x, uv2.y, 0, 1),
            (uv0.x, uv0.y, 1, 1)
            ))
        U.transpose()
#        print("mtx U " + str(U))
        U.invert()
#        print("mtx U-1 " + str(U))

        P = mathutils.Matrix((
            (p0.x, p0.y, p0.z, 1),
            (p1.x, p1.y, p1.z, 1),
            (p2.x, p2.y, p2.z, 1),
            (p3.x, p3.y, p3.z, 1)
            ))
        P.transpose()

#        print("mtx P " + str(P))

        C = P @ U
        
        #Center UVs on face by subtracting out integer multiples of u, v vectors
        if relocate_origin:
            CI = C.inverted()
            
            bestCenterUv = CI @ bestCenter
#            bestCenterUvFloor = floor_vector(bestCenterUv + mathutils.Vector((.5, .5, .5)))
            bestCenterUvFloor = floor_vector(bestCenterUv)
            
            C = C @ mathutils.Matrix.Translation(bestCenterUvFloor)
            
        
        self.controlMtx = C

#        print("mtx C " + str(C))
        
        # CI = C.copy()
        # CI.invert()
#        print("mtx C-1 " + str(CI))

        if obj.mode == 'OBJECT':
            bm.free()
        

    def setFromGrid(self, context):
        obj = context.active_object
        if obj == None or obj.type != 'MESH':
            self.controlMtx = None        
            return

        #Find active face
        bm = None
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        elif obj.mode == 'OBJECT':
            bm = bmesh.new()
            bm.from_mesh(obj.data)

#            print("active face idx " + str(bm.faces.active))
        face = bm.faces.active
        if face == None:
            bm.faces.ensure_lookup_table()
            face = bm.faces[0]

        l2w = obj.matrix_world
        n2w = l2w.copy()
        n2w.invert()
        n2w.transpose()
            
        activeNormal = n2w @ face.normal
        activeCenter = l2w @ face.calc_center_median()

        if obj.mode == 'OBJECT':
            bm.free()
            
        #Grid projection
        scale = context.space_data.overlay.grid_scale
        center = snap_to_grid(activeCenter, scale)
        
        axis = closest_axis(activeNormal)
        if axis == Axis.X:
            i = vecY * scale
            j = vecZ * scale
            k = vecX * scale
            center.x = activeCenter.x
        elif axis == Axis.Y:
            i = vecX * scale
            j = vecZ * scale
            k = vecY * scale
            center.y = activeCenter.y
        elif axis == Axis.Z:
            i = vecX * scale
            j = vecY * scale
            k = vecZ * scale
            center.z = activeCenter.z

        i = i.to_4d()
        i.w = 0
        j = j.to_4d()
        j.w = 0
        k = k.to_4d()
        k.w = 0
        h = center.to_4d()
        
        self.controlMtx = mathutils.Matrix((i, j, k, h))
        self.controlMtx.transpose()
        

    def setFromMeshes(self, context):
    
        obj = context.active_object
        if obj == None or obj.type != 'MESH':
            self.controlMtx = None        
            return

        props = context.scene.kitfox_uv_plane_layout_props
        selected_faces_only = props.selected_faces_only

        mesh = obj.data
        l2w = obj.matrix_world
        n2w = l2w.copy()
        n2w.invert()
        n2w.transpose()

        mesh = obj.data
        bestNormal = None
        bestCenter = None
        
        bm = None
        
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
            print("active face idx " + str(bm.faces.active))
            face = bm.faces.active
            if face == None:
                face = bm.faces[0]
            bestNormal = n2w @ face.normal
            bestCenter = l2w @ face.calc_center_median()
        elif obj.mode == 'OBJECT':
            print("active poly idx " + str(mesh.polygons.active))
            bestPoly = mesh.polygons[mesh.polygons.active]
                
            bestNormal = n2w @ bestPoly.normal
            bestCenter = l2w @ bestPoly.center
            
            bm = bmesh.new()
            bm.from_mesh(mesh)
            
            
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
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            elif obj.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(mesh)
            
            
            l2w = obj.matrix_world
            l2poly = w2poly @ l2w
            
            for f in bm.faces:
                if not selected_faces_only or f.select:
                    for v in f.verts:
#                        v = mesh.vertices[vIdx]
                        
                        faceV = l2poly @ v.co
                        
    #                    print("mapping v %s -> %s " % (str(v.co), str(faceV)))
               
                        minX = faceV.x if minX == None else min(faceV.x, minX)
                        maxX = faceV.x if maxX == None else max(faceV.x, maxX)
                        minY = faceV.y if minY == None else min(faceV.y, minY)
                        maxY = faceV.y if maxY == None else max(faceV.y, maxY)
                    
            if obj.mode == 'OBJECT':
                bm.free()

        if minX == None:
            return

        #print("minX %s  maxX %s  minY %s  maxY %s " % (str(minX), str(maxX), str(minY), str(maxY)))

        dx = maxX - minX
        dy = maxY - minY
        # cx = (maxX + minX) / 2
        # cy = (maxY + minY) / 2
        cx = minX
        cy = minY
        ctrlCenter = cx * tangent + cy * binormal + center
        #print("dx %s  dy %s  cx %s  cy %s " % (str(dx), str(dy), str(cx), str(cy)))
        #print("cx tan %s  cy tan %s" % (str(cx * tangent), str(cy * binormal)))

#        self.controlMtx = mathutils.Matrix((tangent * dx / 2, binormal * dy / 2, bestNormal, ctrlCenter))
        self.controlMtx = mathutils.Matrix((tangent * dx, binormal * dy, bestNormal, ctrlCenter))
        self.controlMtx.transpose()

        #print("controlMtx %s" % (str(self.controlMtx)))
            

    

    
    def draw(self, context):
        #print("draign control")
        
#        rv3d = context.space_data.region_3d
#        w2v = rv3d.view_matrix
#        v2w = w2v.inverted()
#        print("view_matrix " + str(w2v))
#        print("view_matrix I " + str(v2w))
        
#        win2v = rv3d.window_matrix
#        print("window_matrix " + str(win2v))
#        print("window_matrix I " + str(win2v.inverted()))
        
        # rv3d.view_perspective
        # rv3d.is_perspective
#        persp = rv3d.perspective_matrix
#        print("perspective_matrix " + str(persp))
#        print("perspective_matrix I " + str(persp.inverted()))
    
        #---------------------------
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
#        batchCube = batch_for_shader(shader, 'LINES', {"pos": coordsCube})
        batchCube = batch_for_shader(shader, 'LINE_STRIP', {"pos": coordsSquare_strip})
            
        
        if self.controlMtx == None:
            return
        
        shader.bind();
        #bgl.glEnable(bgl.GL_DEPTH_TEST)
        
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(self.controlMtx)
        shader.uniform_float("color", (1, 0, 1, 1))
        batchCube.draw(shader)
        
        gpu.matrix.pop()
    
        #bgl.glDisable(bgl.GL_DEPTH_TEST)
        
#        print("  DRAW HANDLESs")
        for handle in self.handles:
#            print("  Drawing handle " + str(handle))
            handle.draw(context)

#---------------------------



def draw_callback(self, context):
    
    ctx = bpy.context

    if self.control != None:
        self.control.draw(context)


#---------------------------

class UvLayoutPlaneOperator(bpy.types.Operator):
    """Plane projection for UVs"""
    bl_idname = "kitfox.uv_plane_layout_op"
    bl_label = "Uv Layout"
    bl_options = {"REGISTER", "UNDO"}


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.control = None
        

    def __del__(self):
        super().__del__()

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

        elif event.type == 'UP_ARROW':
            if event.value == 'PRESS':
                m = mathutils.Matrix.Diagonal(mathutils.Vector((1, 2, 1, 1)))
                self.control.updateProjectionMatrix(context, self.control.controlMtx @ m)
            return {'RUNNING_MODAL'}

        elif event.type == 'DOWN_ARROW':
            if event.value == 'PRESS':
                m = mathutils.Matrix.Diagonal(mathutils.Vector((1, .5, 1, 1)))
                self.control.updateProjectionMatrix(context, self.control.controlMtx @ m)
            return {'RUNNING_MODAL'}

        elif event.type == 'RIGHT_ARROW':
            if event.value == 'PRESS':
                m = mathutils.Matrix.Diagonal(mathutils.Vector((2, 1, 1, 1)))
                self.control.updateProjectionMatrix(context, self.control.controlMtx @ m)
            return {'RUNNING_MODAL'}

        elif event.type == 'LEFT_ARROW':
            if event.value == 'PRESS':
                m = mathutils.Matrix.Diagonal(mathutils.Vector((.5, 1, 1, 1)))
                self.control.updateProjectionMatrix(context, self.control.controlMtx @ m)
            return {'RUNNING_MODAL'}

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

    def isEmpty(self, context):
        props = context.scene.kitfox_uv_plane_layout_props
        selected_faces_only = props.selected_faces_only
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                mesh = obj.data
                
                if selected_faces_only:
                    if obj.mode == 'EDIT':
                        bm = bmesh.from_edit_mesh(mesh)
                        for f in bm.faces:
                            if f.select:
                                return False
                        
                    else:
                            
                        for p in mesh.polygons:
                            if p.select:
                                return False
                        
                else:
                    return False
                    
        return True

    def invoke(self, context, event):
        
        if context.area.type == 'VIEW_3D':
            if self.isEmpty(context):
                self.report({'WARNING'}, "Nothing selected to apply projection to")
                return {'CANCELLED'}
                
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


