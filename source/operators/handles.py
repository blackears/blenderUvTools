import bpy
import mathutils
import math
import gpu
import bgl

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from .vecmath import *

#---------------------------

class HandleContraint:
    def __init__(self):
        pass

    def constrain(self, offset, viewDir):
        #By default just pass back offset
        return offset

class HandleConstraintVector(HandleContraint):
    def __init__(self, vector):
        super().__init__()
        self.vector = vector
        
    def constrain(self, offset, viewDir):
#        print("---Constrain ")
#        print("vector " + str(self.vector))
#        print("offset " + str(offset))
#        print("viewDir " + str(viewDir))
        scalar = closest_point_to_line(vecZero, self.vector, offset, viewDir)
#        print("scalar " + str(scalar))
#        print("scalar * self.vector " + str(scalar * self.vector))
#        print("---")
        return scalar * self.vector
    
#        return offset.project(self.vector)

class HandleConstraintPlane(HandleContraint):
    def __init__(self, planeOrigin, planeNormal):
        super().__init__()
        self.planeOrigin = planeOrigin
        self.planeNormal = planeNormal
        
    def constrain(self, offset, viewDir):
        s = isect_line_plane(offset, viewDir, self.planeOrigin, self.planeNormal)
        return offset + s * viewDir
        
    def copy(self):
        return HandleConstraintPlane(self.planeOrigin.copy(), self.planeNormal.copy())


class HandleConstraintOmni(HandleContraint):
    def __init__(self):
        super().__init__()
        
    def constrain(self, offset, viewDir):
        return offset
    

#---------------------------
    
    
class HandleBody:
    def __init__(self, handle, transform, color, colorDrag):
        self.handle = handle
        self.transform = transform
        self.color = color
        self.colorDrag = colorDrag        
        self.dragging = False
        self.viewportScale = .3
        
    def setColor(self, color):
        self.color = color

    def draw(self, context, dragging):

        #Replace scaling component from handle transform
        trans, rot, scale = self.handle.transform.decompose()
        
        region = context.region
        rv3d = context.region_data
        #unitScale = calc_unit_scale2(trans, region, rv3d)
        unitScale = dist_from_viewport_center(trans, region, rv3d)
        #unitScale = unitScale * unitScale
        unitScale = 1 / unitScale
#        print("unitScale " + str(unitScale))
        viewport_scale = self.viewportScale / unitScale
        mS = mathutils.Matrix.Diagonal((viewport_scale, viewport_scale, viewport_scale, 1))

        hM = mathutils.Matrix.Translation(trans) @ rot.to_matrix().to_4x4() @ mS
        l2w = hM @ self.transform

       
#        bgl.glEnable(bgl.GL_DEPTH_TEST)
        
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(l2w)
        
        
        if dragging:
            self.shader.uniform_float("color", self.colorDrag)
        else:
            self.shader.uniform_float("color", self.color)
        self.batchShape.draw(self.shader)

        gpu.matrix.pop()
            
#        bgl.glDisable(bgl.GL_DEPTH_TEST)
        

    def intersect(self, context, pickOrigin, pickRay):

        trans, rot, scale = self.handle.transform.decompose()
        
        region = context.region
        rv3d = context.region_data
        unitScale = dist_from_viewport_center(trans, region, rv3d)
        unitScale = 1 / unitScale
#        print("unitScale " + str(unitScale))
        viewport_scale = self.viewportScale / unitScale
        mS = mathutils.Matrix.Diagonal((viewport_scale, viewport_scale, viewport_scale, 1))
    
        # print("view Mtx " + str(rv3d.view_matrix))
        # print("window Mtx " + str(rv3d.window_matrix))
        # print("perspective_matrix " + str(rv3d.perspective_matrix))
        
    
        hM = mathutils.Matrix.Translation(trans) @ rot.to_matrix().to_4x4() @ mS
        l2w = hM @ self.transform
        
        for i in range(len(self.coords) // 3):
            p0 = self.coords[i * 3]
            p1 = self.coords[i * 3 + 1]
            p2 = self.coords[i * 3 + 2]
            
            p0w = l2w @ p0
            p1w = l2w @ p1
            p2w = l2w @ p2
            
            hit = intersect_triangle(p0w, p1w, p2w, pickOrigin, pickRay)
            if hit != None:
                # print("hit p0:%s p1:%s p2:%s " % (str(p0w), str(p1w), str(p2w)))
                # print("hit pickOrigin:%s pickRay:%s" % (str(pickOrigin), str(pickRay)))
            
                return hit
            
        return None
        

class HandleBodyCube(HandleBody):
    def __init__(self, handle, transform, color, colorDrag):
        super().__init__(handle, transform, color, colorDrag)
    
        self.coords, normals, uvs = unitCube()
        
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": self.coords})
        
        

class HandleBodySphere(HandleBody):
    def __init__(self, handle, transform, color, colorDrag):
        super().__init__(handle, transform, color, colorDrag)
    
        self.coords, normals, uvs = unitSphere()
        
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": self.coords})


class HandleBodyCone(HandleBody):
    def __init__(self, handle, transform, color, colorDrag):
        super().__init__(handle, transform, color, colorDrag)
    
        self.coords, normals, uvs = unitCone(cap = True)
        
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": self.coords})


class HandleBodyTorus(HandleBody):
    def __init__(self, handle, transform, color, colorDrag):
        super().__init__(handle, transform, color, colorDrag)
    
        self.coords, normals, uvs = unitTorus(8)
        
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": self.coords})

        
#---------------------------


class Handle:
    def __init__(self, transform, body, constraint):
        #Location in world space
        self.transform = transform
        self.body = body
        self.constraint = constraint
        
        self.dragging = False

    def draw(self, context):
#        gpu.matrix.push()        
        #gpu.matrix.multiply_matrix(self.transform)

        self.body.draw(context, self.dragging)
        
#        gpu.matrix.pop()
        
    

class HandleScaleAroundPivot(Handle):
    #posControl is position within uv square that this control point represents
    def __init__(self, control, transform, pivot, constraint, posControl):
        
        self.pivot = pivot
        self.control = control
        xform = mathutils.Matrix.Diagonal(mathutils.Vector((.02, .02, .02, 1)))
        body = HandleBodyCube(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
        
        #Location of handle in i, j, k coords of control's projection matrix
        self.posControl = posControl

        super().__init__(transform, body, constraint)
        
    
    def mouse_click(self, context, event):
        if event.value == "PRESS":
            if not self.dragging:
                region = context.region
                rv3d = context.region_data

                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
                mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

                hit = self.body.intersect(context, mouse_near_origin, mouse_ray)
                if hit != None:
                    self.dragging = True
                    self.drag_start_pos = hit
                    
                    #Structure of original projection matrix
                    self.startControlProj = self.control.controlMtx.copy()

                    # print("--starting drag")
                    # print("startControlProj %s" % (str(self.startControlProj)))
                    
                    return True
            
        else:
            if self.dragging:
                self.dragging = False
                # self.drag_offset = None

                #self.mesh_tracker.stretch(self.move_amount, self.dir, self.face, True)
                return True
                
        return False
            
    def mouse_move(self, context, event):
        if self.dragging:
            region = context.region
            rv3d = context.region_data

            mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
            mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
            mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

            #calc offset in 3d space perpendicular to view direction
            startPointOffset = self.drag_start_pos - mouse_near_origin
            offsetPerpToView = startPointOffset.project(mouse_ray) - startPointOffset

            print("posControl %s" % (str(self.posControl)))
            print("offsetPerpToView %s" % (str(offsetPerpToView)))

            offset = self.constraint.constrain(offsetPerpToView, mouse_ray)

            pos2Uv = self.startControlProj.inverted()
            tmp = offset.to_4d()
            tmp.w = 0
            offsetUv = pos2Uv @ tmp
            offsetUv = offsetUv.to_3d()

            # print("offsetUv %s" % (str(offsetUv)))

            fixedPosUv = self.pivot * 2 - self.posControl
            spanNewUv = self.posControl + offsetUv - fixedPosUv
            spanUv = self.posControl - fixedPosUv

            # print("fixedPosUv %s" % (str(fixedPosUv)))
            # print("spanUv %s" % (str(spanUv)))
            # print("spanNewUv %s" % (str(spanNewUv)))

            sx = 1 if spanUv.x == 0 else spanNewUv.x / spanUv.x
            sy = 1 if spanUv.y == 0 else spanNewUv.y / spanUv.y
            
            #This is the transform in UV space that moves the starting uv point to its new position
            T = mathutils.Matrix.Translation((fixedPosUv)) @ mathutils.Matrix.Diagonal((sx, sy, 1, 1)) @ mathutils.Matrix.Translation((-fixedPosUv))

#            print("T %s" % (str(T)))

            newProjMatrix = self.startControlProj @ T

            self.control.updateProjectionMatrix(context, newProjMatrix)

            return True
        return False


class HandleCorner(HandleScaleAroundPivot):
    def __init__(self, control, transform, normal, posControl):
        
        constraint = HandleConstraintPlane(vecZero, normal)

        super().__init__(control, transform, mathutils.Vector((.5, .5, 0)), constraint, posControl)


class HandleEdge(HandleScaleAroundPivot):
    def __init__(self, control, transform, direction, posControl):
        
        constraint = HandleConstraintVector(direction)

        super().__init__(control, transform, mathutils.Vector((.5, .5, 0)), constraint, posControl)


class HandleTranslate(Handle):
    def __init__(self, control, transform, body, constraint, posControl):
        
        self.control = control
        # xform = mathutils.Matrix.Diagonal(mathutils.Vector((.02, .02, .02, 1)))
        # body = HandleBodyCone(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
#        body = HandleBodySphere(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
#        body = HandleBodyCube(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
        
        #Location of handle in i, j, k coords of control's projection matrix
        self.posControl = posControl

        super().__init__(transform, body, constraint)

    
    def mouse_click(self, context, event):
        if event.value == "PRESS":
            if not self.dragging:
                region = context.region
                rv3d = context.region_data

                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
                mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

                hit = self.body.intersect(context, mouse_near_origin, mouse_ray)
                if hit != None:
                    self.dragging = True
                    self.drag_start_pos = hit
                    
                    #Structure of original projection matrix
                    self.startControlProj = self.control.controlMtx.copy()
                    
                    return True
        else:
            if self.dragging:
                self.dragging = False
                return True
                
        return False
        
    def mouse_move(self, context, event):
        if self.dragging:
        
            props = context.scene.kitfox_uv_plane_layout_props
            clamp_to_basis = props.clamp_to_basis
            clamp_scalar = props.clamp_scalar
        
            region = context.region
            rv3d = context.region_data

            mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
            mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
            mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

            #calc offset in 3d space perpendicular to view direction
            startPointOffset = self.drag_start_pos - mouse_near_origin
            offsetPerpToView = startPointOffset.project(mouse_ray) - startPointOffset

            # print("posControl %s" % (str(self.posControl)))
            # print("offsetPerpToView %s" % (str(offsetPerpToView)))

            offset = self.constraint.constrain(offsetPerpToView, mouse_ray)

#            print("offset %s" % (str(offset)))

            if clamp_to_basis:
                uv2w = self.startControlProj
                w2uv = uv2w.inverted()
                
                off = offset.to_4d()
                off.w = 0
                uvOff = w2uv @ off
                uvOff /= clamp_scalar
                
                uvOff.x = math.floor(uvOff.x)
                uvOff.y = math.floor(uvOff.y)
                uvOff.z = math.floor(uvOff.z)
                
                uvOff *= clamp_scalar
                offset = uv2w @ uvOff
                offset = offset.to_3d()
                


            newProjMatrix = mathutils.Matrix.Translation(offset) @ self.startControlProj

            #print("newProjMatrix %s" % (str(newProjMatrix)))

            self.control.updateProjectionMatrix(context, newProjMatrix)

            return True
        return False


class HandleTranslateOmni(HandleTranslate):
    def __init__(self, control, transform, posControl):
        xform = mathutils.Matrix.Diagonal(mathutils.Vector((.04, .04, .04, 1)))
        body = HandleBodySphere(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))

        super().__init__(control, transform, body, HandleConstraintOmni(), posControl)


class HandleTranslateVector(HandleTranslate):
    def __init__(self, control, transform, constraintVector, posControl):
        xform = mathutils.Matrix.Diagonal(mathutils.Vector((.04, .04, .04, 1)))
        
        #Rotate body to point along vector
        axis = constraintVector.cross(vecZ)
        if axis.magnitude > 0:
            i = constraintVector.normalized()
            angle = math.acos(i.z)
            q = mathutils.Quaternion(axis, angle)
            mR = q.to_matrix().to_4x4()
            
            xform = mR @ xform
        elif constraintVector.dot(vecZ) > 0:
            mR = mathutils.Matrix.Rotation(math.pi, 4, vecX)
            
            xform = mR @ xform
            
        body = HandleBodyCone(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
        
        super().__init__(control, transform, body, HandleConstraintVector(constraintVector), posControl)


class HandleRotateAxis(Handle):
    def __init__(self, control, transform, axis, axisLocal):
        
#        constraint = HandleConstraintPlane(axis)
        
        self.pivot = mathutils.Vector((.5, .5, 0))
        pivotWorld = control.controlMtx @ self.pivot
        constraint = HandleConstraintPlane(pivotWorld, axis)
        
        self.axisLocal = axisLocal
        self.control = control
        xform = mathutils.Matrix.Diagonal(mathutils.Vector((.05, .05, .05, 1)))
        body = HandleBodyTorus(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
        
        super().__init__(transform, body, constraint)

    def draw(self, context):
        super().draw(context)
        
        # gpu.matrix.push()
        # gpu.matrix.multiply_matrix(self.transform)

        # self.body.draw(context, self.dragging)
        
        # gpu.matrix.pop()
    
    def mouse_click(self, context, event):
        if event.value == "PRESS":
            if not self.dragging:
                region = context.region
                rv3d = context.region_data

                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
                mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

                hit = self.body.intersect(context, mouse_near_origin, mouse_ray)
                if hit != None:
                    self.dragging = True
                    self.drag_start_pos = hit
                    self.start_constraint = self.constraint.copy()
                    
                    #Structure of original projection matrix
                    self.startControlProj = self.control.controlMtx.copy()
                    
                    return True
        else:
            if self.dragging:
                self.dragging = False
                return True
                
        return False

    def mouse_move(self, context, event):
        if self.dragging:
            region = context.region
            rv3d = context.region_data

            mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
            mouse_ray = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos_2d)
            mouse_near_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos_2d)

            #calc offset in 3d space perpendicular to view direction
            startPointOffset = self.drag_start_pos - mouse_near_origin
            offsetPerpendicularToViewDir = startPointOffset.project(mouse_ray) - startPointOffset

            print("self.drag_start_pos %s" % (str(self.drag_start_pos)))

            # print("posControl %s" % (str(self.posControl)))
            # print("offsetPerpToView %s" % (str(offsetPerpToView)))
            p0 = self.drag_start_pos
            p1 = self.drag_start_pos + offsetPerpendicularToViewDir

            print("p0 %s" % (str(p0)))
            print("p1 %s" % (str(p1)))

            # p0 = self.constraint.constrain(p0, mouse_ray)
            # p1 = self.constraint.constrain(p1, mouse_ray)
            p0 = self.start_constraint.constrain(p0, mouse_ray)
            p1 = self.start_constraint.constrain(p1, mouse_ray)

            print("p0 const %s" % (str(p0)))
            print("p1 const %s" % (str(p1)))

            # offset = self.constraint.constrain(offsetPerpToView, mouse_ray)

            # print("offset %s" % (str(offset)))
            
#            origin = self.startControlProj.col[3].xyz
            origin = self.startControlProj @ self.pivot

            print("origin %s" % (str(origin)))

            # v0 = self.drag_start_pos - origin
            # v1 = (self.drag_start_pos + offset) - origin
            v0 = p0 - origin
            v1 = p1 - origin

            print("v0 %s" % (str(v0)))
            print("v1 %s" % (str(v1)))

            v0.normalize()
            v1.normalize()

            

            print("v0 norm %s" % (str(v0)))
            print("v1 norm %s" % (str(v1)))

            angle = math.acos(v0.dot(v1))
            vc = v0.cross(v1)
            
            print("vc %s" % (str(vc)))

            #Find angle relative to normal of axis
            axisWorld = self.start_constraint.planeNormal
            if vc.dot(axisWorld) < 0:
                angle = -angle

            print("angle %s" % (str(angle * 180 / math.pi)))
            
            if event.ctrl:
#                print ("snapping angle " + str(math.degrees(angle)))
                snapAngle = (15 / 360) * (2 * math.pi)
                angle = math.floor(angle / snapAngle) * snapAngle
#                print ("snapping after angle " + str(math.degrees(angle)))

#            print("vc %s" % (str(vc)))
            
#            print("vc mag %s" % (vc.magnitude))
            
#            angle = math.asin(vc.magnitude)

#            print("angle %s" % (str(angle)))
            
#            print("vc %s" % (str(vc)))
#            print("axisWorld %s" % (str(axisWorld)))
            

#            print("vc.dot(axisWorld)) %s" % (str(vc.dot(axisWorld))))

#            mRot = mathutils.Matrix.Rotation(angle, 4, self.axisLocal)
            mRot = mathutils.Matrix.Rotation(angle, 4, axisWorld)
            
            pivotPos = self.startControlProj @ self.pivot
            mPivot = mathutils.Matrix.Translation(pivotPos)
            mPivotNeg = mathutils.Matrix.Translation(-pivotPos)

            trans, rot, scale = self.startControlProj.decompose()
#            newProjMatrix = self.startControlProj @ mRot
            # newProjMatrix = mPivot @ mRot @ mPivotNeg @ mathutils.Matrix.Translation(trans).to_4x4() @ rot.to_matrix().to_4x4() @ mathutils.Matrix.Diagonal(scale).to_4x4()
            newProjMatrix = mPivot @ mRot @ mPivotNeg @ self.startControlProj

            # print("newProjMatrix %s" % (str(newProjMatrix)))

            self.control.updateProjectionMatrix(context, newProjMatrix)

            return True
        return False
