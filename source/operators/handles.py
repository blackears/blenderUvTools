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
    def __init__(self, planeNormal):
        super().__init__()
        self.planeNormal = planeNormal
        
    def constrain(self, offset, viewDir):
        s = isect_line_plane(offset, viewDir, vecZero, self.planeNormal)
        return offset + s * viewDir
        
        # planeOff = offset.project(self.planeNormal)
        # return offset - planeOff


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
        self.viewportScale = .2
        
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

       
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(l2w)
        
        
        if dragging:
            self.shader.uniform_float("color", self.colorDrag)
        else:
            self.shader.uniform_float("color", self.color)
        self.batchShape.draw(self.shader)

        gpu.matrix.pop()
            
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        

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
        
    

class HandleScaleAroundOrigin(Handle):
    def __init__(self, control, transform, constraint, posControl):
        
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

            print("offset %s" % (str(offset)))

            projOrigin = self.startControlProj.col[3].to_3d()

            print("projOrigin %s" % (str(projOrigin)))
            
            startPos = self.startControlProj @ self.posControl
            fixedPos = self.startControlProj @ -self.posControl
            startOrigin = self.startControlProj.col[3].to_3d()

            print("startPos %s" % (str(startPos)))
            print("fixedPos %s" % (str(fixedPos)))
            print("startOrigin %s" % (str(startOrigin)))

            newPos = startPos + offset

            print("newPos %s" % (str(newPos)))
            
            newControlOrigin = (newPos + fixedPos) / 2

            print("newControlOrigin %s" % (str(newControlOrigin)))
            
            newPosOffset = newPos - newControlOrigin
            w2Proj = self.startControlProj.copy()
            w2Proj.invert()
            newPosOffsetProj = w2Proj @ (newPosOffset + startOrigin)

            print("newPosOffsetProj %s" % (str(newPosOffsetProj)))
            
            
            i = self.startControlProj.col[0].to_3d()
            j = self.startControlProj.col[1].to_3d()
            k = self.startControlProj.col[2].to_3d()

            print("i %s" % (str(i)))
            print("j %s" % (str(j)))
            print("k %s" % (str(k)))

            
            newI = i.copy() if self.posControl.x == 0 else i * newPosOffsetProj.x / self.posControl.x
            newJ = j.copy() if self.posControl.y == 0 else j * newPosOffsetProj.y / self.posControl.y
            newK = k.copy() if self.posControl.z == 0 else j * newPosOffsetProj.z / self.posControl.z


            newI = newI.to_4d()
            newI.w = 0
            newJ = newJ.to_4d()
            newJ.w = 0
            newK = newK.to_4d()
            newK.w = 0
            newControlOrigin = newControlOrigin.to_4d()
            
            newProjMatrix = mathutils.Matrix((newI, newJ, newK, newControlOrigin))
            newProjMatrix.transpose()

            print("newProjMatrix %s" % (str(newProjMatrix)))

            self.control.updateProjectionMatrix(context, newProjMatrix)

            return True
        return False


class HandleCorner(HandleScaleAroundOrigin):
    def __init__(self, control, transform, normal, posControl):
        
        constraint = HandleConstraintPlane(normal)

        super().__init__(control, transform, constraint, posControl)


class HandleEdge(HandleScaleAroundOrigin):
    def __init__(self, control, transform, direction, posControl):
        
        constraint = HandleConstraintVector(direction)

        super().__init__(control, transform, constraint, posControl)


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
            q = mathutils.Quaternion(axis, -angle)
            mR = q.to_matrix().to_4x4()
            
            xform = mR @ xform
            
        body = HandleBodyCone(self, xform, (1, 0, 1, 1), (1, 1, 0, 1))
        
        super().__init__(control, transform, body, HandleConstraintVector(constraintVector), posControl)


class HandleRotateAxis(Handle):
    def __init__(self, control, transform, axis, axisLocal):
        
        constraint = HandleConstraintPlane(axis)
        
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
            offsetPerpToView = startPointOffset.project(mouse_ray) - startPointOffset

            # print("posControl %s" % (str(self.posControl)))
            # print("offsetPerpToView %s" % (str(offsetPerpToView)))

            offset = self.constraint.constrain(offsetPerpToView, mouse_ray)

            # print("offset %s" % (str(offset)))
            origin = self.startControlProj.col[3].xyz

            v0 = self.drag_start_pos - origin
            v1 = (self.drag_start_pos + offset) - origin

#            print("v0 %s" % (str(v0)))
#            print("v1 %s" % (str(v1)))
            
            v0.normalize()
            v1.normalize()

#            print("v0 norm %s" % (str(v0)))
#            print("v1 norm %s" % (str(v1)))

            angle = math.acos(v0.dot(v1))
            vc = v0.cross(v1)

            #Find angle relative to normal of axis
            axisWorld = self.constraint.planeNormal
            if vc.dot(axisWorld) < 0:
                angle = -angle
            
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
            
            mRot = mathutils.Matrix.Rotation(angle, 4, self.axisLocal)

            trans, rot, scale = self.startControlProj.decompose()
#            newProjMatrix = self.startControlProj @ mRot
            newProjMatrix = mathutils.Matrix.Translation(trans).to_4x4() @ rot.to_matrix().to_4x4() @ mRot @ mathutils.Matrix.Diagonal(scale).to_4x4()

            # print("newProjMatrix %s" % (str(newProjMatrix)))

            self.control.updateProjectionMatrix(context, newProjMatrix)

            return True
        return False
