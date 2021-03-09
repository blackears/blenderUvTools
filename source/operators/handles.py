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

class HandleContraintVector(HandleContraint):
    def __init__(self, vector):
        super().__init__()
        self.vector = vector
        
    def constrain(self, offset, viewDir):
        scalar = closest_point_to_line(vecZero, self.vector, offset, viewDir)
        return scalar * self.vector
    
#        return offset.project(self.vector)

class HandleContraintPlane(HandleContraint):
    def __init__(self, planeNormal):
        super().__init__()
        self.planeNormal = planeNormal
        
    def constrain(self, offset, viewDir):
        s = isect_line_plane(offset, viewDir, vecZero, self.planeNormal)
        return offset + s * viewDir
        
        # planeOff = offset.project(self.planeNormal)
        # return offset - planeOff


class HandleContraintOmni(HandleContraint):
    def __init__(self):
        super().__init__()
        
    def constrain(self, offset, viewDir):
        return offset
    

#---------------------------
    
    
class HandleBody:
    def __init__(self, handle, transform):
        self.handle = handle
        self.transform = transform
        self.dragging = False

    def draw(self, context):
        pass

    def intersects(self, handle, pickOrigin, pickRay):
        return False

class HandleBodyCube(HandleBody):
    def __init__(self, handle, transform):
        super(HandleBodyCube, self).__init__(handle, transform)
    
        self.coords, normals, uvs = unitCube()
        
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": self.coords})

        # self.shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        # colors = [mathutils.Vector((1, 1, .5, 1)) for i in range(len(coords))]
        # self.batchShape = batch_for_shader(self.shader, 'TRIS', {"pos": coords, "color": colors})
        
        
    def draw(self, context):
#        print("  Drawing cube h body")
        
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        
        gpu.matrix.push()
        
        gpu.matrix.multiply_matrix(self.transform)
        if self.dragging:
            self.shader.uniform_float("color", (1, 1, 0, 1))
        else:
            self.shader.uniform_float("color", (1, 0, 1, 1))
        self.batchShape.draw(self.shader)

        gpu.matrix.pop()
            
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        
        
    def intersect(self, pickOrigin, pickRay):
        l2w = self.handle.transform @ self.transform
        
        for i in range(len(self.coords) // 3):
            p0 = self.coords[i * 3]
            p1 = self.coords[i * 3 + 1]
            p2 = self.coords[i * 3 + 2]
            
            p0w = l2w @ p0
            p1w = l2w @ p1
            p2w = l2w @ p2
            
            hit = intersect_triangle(p0w, p1w, p2w, pickOrigin, pickRay)
            if hit != None:
                return hit
            
        return None

#---------------------------


class Handle:
    def __init__(self, transform, body, constraint):
        #Location in world space
        self.transform = transform
        self.body = body
        self.constraint = constraint
        
        self.dragging = False

    def draw(self, context):
        gpu.matrix.push()
        gpu.matrix.multiply_matrix(self.transform)

#        print("Drawing h body  %s" % (str(self.posControl)))
        self.body.draw(context)
        
        gpu.matrix.pop()
        
    

class HandleCorner(Handle):
    def __init__(self, control, transform, normal, posControl):
        
        self.control = control
        xform = mathutils.Matrix.Diagonal(mathutils.Vector((.05, .05, .05, 1)))
        body = HandleBodyCube(self, xform)
        constraint = HandleContraintPlane(normal)
        
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

                hit = self.body.intersect(mouse_near_origin, mouse_ray)
                if hit != None:
                    self.dragging = True
                    self.drag_start_pos = hit
                    #self.drag_start_pos_viewport = mouse_pos_2d
                    # self.drag_offset = None
                    # self.move_amount = 0
                    
                    #Structure of original projection matrix
                    self.startControlProj = self.control.controlMtx.copy()
                    # self.startControlOrigin = self.control.controlMtx.col[4].to_3d()
                    # self.startOffsetFromOrigin = self.offsetFromOrigin.copy()
#                    self.origProj = self.control.controlMtx.copy()
                    # self.i = self.control.controlMtx.transform.col[0]
                    # self.j = self.transform.col[1]
                    # self.k = self.transform.col[2]
                    # self.origin = self.transform.col[4]
                    
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

            offset = self.constraint.constrain(offsetPerpToView, mouse_ray)
            #self.applyOffset(offset)

#            self.controlOrigin
            projOrigin = self.startControlProj.col[3].to_3d()
            # projI = self.startControlProj.col[0].to_3d()
            # projJ = self.startControlProj.col[1].to_3d()
            
            #startPos = self.posControl.x * projI + self.posControl.y * projJ + projOrigin
            startPos = self.startControlProj @ self.posControl
            fixedPos = self.startControlProj @ -self.posControl

            # newPos = self.startControlOrigin + self.startOffsetFromOrigin + offset
            # fixedPos = self.startControlOrigin - self.startOffsetFromOrigin
            newPos = startPos + offset
            
            newControlOrigin = (newPos + fixedPos) / 2
            originOffset = newControlOrigin - projOrigin
            
            i = self.startControlProj.col[0].to_3d()
            j = self.startControlProj.col[1].to_3d()
            k = self.startControlProj.col[2].to_3d()
            
            newI = i - originOffset.project(i)
            newJ = j - originOffset.project(j)
            newK = k - originOffset.project(k)

            newI = newI.to_4d()
            newI.w = 0
            newJ = newJ.to_4d()
            newJ.w = 0
            newK = newK.to_4d()
            newK.w = 0
            newControlOrigin = newControlOrigin.to_4d()
            
            newProjMatrix = mathutils.Matrix((newI, newJ, newK, newControlOrigin))
            newProjMatrix.transpose()

            self.control.updateProjectionMatrix(context, newProjMatrix)



            # print ("drag_Start_pos: " + str(self.drag_start_pos))
# #            print("<1> self.pos "  + str(self.pos))
            # self.move_amount = closest_point_to_line(self.pos, self.dir, mouse_near_origin, mouse_ray)
            # drag_to_pos = self.pos + self.move_amount * self.dir
            # self.drag_offset = drag_to_pos - self.drag_start_pos
            # print ("drag_offset: " + str(self.drag_offset))
            # print ("move_amount: " + str(self.move_amount))
# #            print("<2> self.pos "  + str(self.pos))
            
# #            print("drag to " + str(drag_to_pos))
# #            print("drag offset " + str(self.drag_offset))

# #            self.mesh_tracker.stretch(self.drag_start_pos, self.drag_offset - self.drag_start_pos, self.face)
            # self.mesh_tracker.stretch(self.move_amount, self.dir, self.face, False)

            return True
        return False

    # def applyOffset(self):
        # self.controlOrigin
        # self.startOffsetFromOrigin
        # self.
        # pass



# class HandleGroup:
    # def __init__(self, transform):
        # #Location in world space
        # self.transform = transform
        # self.handles = []

    # def addChild(self, handle):
        # self.handles,append(handle)

    # def draw(self, context):
        # gpu.matrix.push()
        # gpu.matrix.multiply_matrix(self.transform)

        # self.body.draw(context)
        
        # gpu.matrix.pop()
        
    # def intersects(self, pickOrigin, pickRay):
        # return self.body.intersects(pickOrigin, pickRay)
