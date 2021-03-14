import mathutils
import math
from bpy_extras import view3d_utils
from enum import Enum


vecX = mathutils.Vector((1, 0, 0))
vecY = mathutils.Vector((0, 1, 0))
vecZ = mathutils.Vector((0, 0, 1))
vecZero = mathutils.Vector((0, 0, 0))

circleSegs = 64
coordsCircle = [(math.sin(((2 * math.pi * i) / circleSegs)), math.cos((math.pi * 2 * i) / circleSegs), 0) for i in range(circleSegs + 1)]

coordsSquare = [(0, 0, 0), (1, 0, 0), 
(1, 1, 0), (0, 1, 0)
]

coordsSquare2_strip = [(-1, -1, 0), (1, -1, 0), 
(1, 1, 0), (-1, 1, 0), 
(-1, -1, 0)
]


coordsCube = [(0, 0, 0), (1, 0, 0), 
(1, 0, 0), (1, 1, 0), 
(1, 1, 0), (0, 1, 0), 
(0, 1, 0), (0, 0, 0), 

(0, 0, 0), (0, 0, 1), 
(1, 0, 0), (1, 0, 1), 
(1, 1, 0), (1, 1, 1), 
(0, 1, 0), (0, 1, 1), 

(0, 0, 1), (1, 0, 1), 
(1, 0, 1), (1, 1, 1), 
(1, 1, 1), (0, 1, 1), 
(0, 1, 1), (0, 0, 1), 
]

cubeVerts = [(0, 0, 0),
(1, 0, 0),
(0, 1, 0),
(1, 1, 0),
(0, 0, 1),
(1, 0, 1),
(0, 1, 1),
(1, 1, 1),
]

cubeFaces = [(2, 3, 1, 0),
(4, 5, 7, 6),
(0, 1, 5, 4),
(6, 7, 3, 2),
(1, 3, 7, 5),
(2, 0, 4, 6),
]

cubeUvs = [
((0, 0), (1, 0), (1, 1), (0, 1)),
((0, 0), (1, 0), (1, 1), (0, 1)),
((0, 0), (1, 0), (1, 1), (0, 1)),
((0, 0), (1, 0), (1, 1), (0, 1)),
((0, 0), (1, 0), (1, 1), (0, 1)),
((0, 0), (1, 0), (1, 1), (0, 1))
]

def unitCube():
    coords = []
    normals = []
    uvs = []

    v000 = mathutils.Vector((-1, -1, -1))
    v100 = mathutils.Vector((1, -1, -1))
    v010 = mathutils.Vector((-1, 1, -1))
    v110 = mathutils.Vector((1, 1, -1))
    v001 = mathutils.Vector((-1, -1, 1))
    v101 = mathutils.Vector((1, -1, 1))
    v011 = mathutils.Vector((-1, 1, 1))
    v111 = mathutils.Vector((1, 1, 1))

    nx0 = mathutils.Vector((-1, 0, 0))
    nx1 = mathutils.Vector((1, 0, 0))
    ny0 = mathutils.Vector((0, -1, 0))
    ny1 = mathutils.Vector((0, 1, 0))
    nz0 = mathutils.Vector((0, 0, -1))
    nz1 = mathutils.Vector((0, 0, 1))

    uv00 = mathutils.Vector((0, 0))
    uv10 = mathutils.Vector((1, 0))
    uv01 = mathutils.Vector((0, 1))
    uv11 = mathutils.Vector((1, 1))
    
    #Face -x
    coords.append(v010)
    coords.append(v000)
    coords.append(v001)
    
    coords.append(v010)
    coords.append(v001)
    coords.append(v011)

    for i in range(6):
        normals.append(nx0)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
    
    
    #Face +x
    coords.append(v100)
    coords.append(v110)
    coords.append(v111)
    
    coords.append(v100)
    coords.append(v111)
    coords.append(v101)

    for i in range(6):
        normals.append(nx1)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
    
    #Face -y
    coords.append(v000)
    coords.append(v100)
    coords.append(v101)
    
    coords.append(v000)
    coords.append(v101)
    coords.append(v001)

    for i in range(6):
        normals.append(ny0)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
    
    
    #Face +y
    coords.append(v110)
    coords.append(v010)
    coords.append(v011)
    
    coords.append(v110)
    coords.append(v011)
    coords.append(v111)

    for i in range(6):
        normals.append(ny1)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
    

    #Face -z
    coords.append(v010)
    coords.append(v110)
    coords.append(v100)
    
    coords.append(v010)
    coords.append(v100)
    coords.append(v000)

    for i in range(6):
        normals.append(nz0)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
    
    
    #Face +z
    coords.append(v001)
    coords.append(v101)
    coords.append(v111)
    
    coords.append(v001)
    coords.append(v111)
    coords.append(v011)

    for i in range(6):
        normals.append(nz1)
    
    uvs.append(uv00)
    uvs.append(uv10)
    uvs.append(uv11)
    uvs.append(uv00)
    uvs.append(uv11)
    uvs.append(uv01)
        
    return (coords, normals, uvs)

def unitCylinder(segs = 16, radius0 = 1, radius1 = 1, bottom_cap = False, top_cap = False):
    coords = []
    normals = []
    uvs = []
    
    vc0 = mathutils.Vertex((0, 0, -1))
    vc1 = mathutils.Vertex((0, 0, 1))
    uvc = mathutils.Vertex((.5, .5))
    
    for s in range(segs):
        sin0 = math.sin(math.radians(360 * s / segs))
        sin1 = math.sin(math.radians(360 * (s + 1) / segs))
        cos0 = math.cos(math.radians(360 * lo / segs_long))
        cos1 = math.cos(math.radians(360 * (lo + 1) / segs_long))
        
        v00 = mathutils.Vector((sin0 * radius0, cos0 * radius0, -1))
        v10 = mathutils.Vector((sin1 * radius0, cos1 * radius0, -1))
        v01 = mathutils.Vector((sin0 * radius1, cos0 * radius1, 1))
        v11 = mathutils.Vector((sin1 * radius1, cos1 * radius, 1))
        
        tan0 = mathutils.Vector((cos0, sin0, 0))
        n00 = (v01 - v00).cross(tan0)
        n00.normalize()
        n01 = n00
        tan1 = mathutils.Vector((cos1, sin1, 0))
        n10 = (v11 - v10).cross(tan1)
        n10.normalize()
        n11 = n10
        
        uv00 = mathutils.Vector((s / segs, 0))
        uv10 = mathutils.Vector(((s + 1) / segs, 0))
        uv01 = mathutils.Vector((s / segs, 1))
        uv11 = mathutils.Vector(((s + 1) / segs, 1))
        
        coords.append(v00)
        coords.append(v10)
        coords.append(v11)

        coords.append(v00)
        coords.append(v11)
        coords.append(v01)
            
        normals.append(n00)
        normals.append(n10)
        normals.append(n11)
        
        normals.append(n00)
        normals.append(n11)
        normals.append(n01)
        
        uvs.append(uv00)
        uvs.append(uv10)
        uvs.append(uv11)
        
        uvs.append(uv00)
        uvs.append(uv11)
        uvs.append(uv01)
        
        if top_cap:
            coords.append(v01)
            coords.append(v11)
            coords.append(vc1)
            
            normals.append(vecZ)
            normals.append(vecZ)
            normals.append(vecZ)
            
            uvs.append(matutils.Vector((sin0, cos0)))
            uvs.append(matutils.Vector((sin1, cos1)))
            uv.append(uvc)
        
        if bottom_cap:
            coords.append(v00)
            coords.append(v10)
            coords.append(vc0)
            
            normals.append(-vecZ)
            normals.append(-vecZ)
            normals.append(-vecZ)
            
            uvs.append(matutils.Vector((sin0, cos0)))
            uvs.append(matutils.Vector((sin1, cos1)))
            uv.append(uvc)
            
        
    return (coords, normals, uvs)

        
def unitCone(segs = 16, radius = 1, cap = False):
    return unitCylinder(segs, radius, 0, cap, False)


def unitSphere(segs_lat, segs_long):
    coords = []
    normals = []
    uvs = []
    

    for la in range(segs_lat):
        z0 = math.sin(math.radians(90 - 180 * la / segs_lat))
        z1 = math.sin(math.radians(90 - 180 * (la + 1) / segs_lat))
        r0 = math.cos(math.radians(90 - 180 * la / segs_lat))
        r1 = math.cos(math.radians(90 - 180 * (la + 1) / segs_lat))
        
        for lo in range(segs_long):
            cx0 = math.sin(math.radians(360 * lo / segs_long))
            cx1 = math.sin(math.radians(360 * (lo + 1) / segs_long))
            cy0 = math.cos(math.radians(360 * lo / segs_long))
            cy1 = math.cos(math.radians(360 * (lo + 1) / segs_long))
            
            v00 = mathutils.Vector((cx0 * r0, cy0 * r0, z0))
            v10 = mathutils.Vector((cx1 * r0, cy1 * r0, z0))
            v01 = mathutils.Vector((cx0 * r1, cy0 * r1, z1))
            v11 = mathutils.Vector((cx1 * r1, cy1 * r1, z1))
            
            coords.append(v00)
            coords.append(v10)
            coords.append(v11)
            
            coords.append(v00)
            coords.append(v11)
            coords.append(v01)
            
            normals.append(v00)
            normals.append(v10)
            normals.append(v11)
            
            normals.append(v00)
            normals.append(v11)
            normals.append(v01)
            
            uvs.append((lo / segs_long, la / segs_lat))
            uvs.append(((lo + 1) / segs_long, la / segs_lat))
            uvs.append(((lo + 1) / segs_long, (la + 1) / segs_lat))
            
            uvs.append((lo / segs_long, la / segs_lat))
            uvs.append(((lo + 1) / segs_long, (la + 1) / segs_lat))
            uvs.append((lo / segs_long, (la + 1) / segs_lat))
            
    return (coords, normals, uvs)
    

def unitTorus(radius = 1, ring_radius = .2, segs_u = 16, segs_v = 8):
    coords = []
    normals = []
    uvs = []

#    print("--Build torus")

    for i in range(segs_u):
        cx0 = math.sin(math.radians(360 * i / segs_u)) * radius
        cy0 = math.cos(math.radians(360 * i / segs_u)) * radius
        cx1 = math.sin(math.radians(360 * (i + 1) / segs_u)) * radius
        cy1 = math.cos(math.radians(360 * (i + 1) / segs_u)) * radius

        c0 = mathutils.Vector((cx0, cy0, 0))
        c1 = mathutils.Vector((cx1, cy1, 0))

#        print("c0 %s" % (str(c0)))

        for j in range(segs_v):
            dir0 = c0 * ring_radius / c0.magnitude
            dir1 = c1 * ring_radius / c1.magnitude
            
            tan0 = dir0.cross(vecZ)
            tan1 = dir1.cross(vecZ)

#            print("dir0 %s" % (str(dir0)))
#            print("tan0 %s" % (str(tan0)))

            q00 = mathutils.Quaternion(tan0, math.radians(360 * j / segs_v))
            q01 = mathutils.Quaternion(tan0, math.radians(360 * (j + 1) / segs_v))
            q10 = mathutils.Quaternion(tan1, math.radians(360 * j / segs_v))
            q11 = mathutils.Quaternion(tan1, math.radians(360 * (j + 1) / segs_v))
            
            # m00 = q00.to_matrix()
            # m01 = q01.to_matrix()
            # m10 = q10.to_matrix()
            # m11 = q11.to_matrix()

#            print("m00 %s" % (str(m00)))
            
            # p00 = m00 @ dir0 + c0
            # p01 = m01 @ dir0 + c0
            # p10 = m10 @ dir1 + c1
            # p11 = m11 @ dir1 + c1

#            print("p00 %s" % (str(p00)))
            
            # p00 = q00 @ dir0 @ q00.conjugated() + c0
            # p01 = q01 @ dir0 @ q01.conjugated() + c0
            # p10 = q10 @ dir1 @ q10.conjugated() + c1
            # p11 = q11 @ dir1 @ q11.conjugated() + c1

            p00 = q00 @ dir0 + c0
            p01 = q01 @ dir0 + c0
            p10 = q10 @ dir1 + c1
            p11 = q11 @ dir1 + c1
            
            vu = p10 - p00
            vv = p01 - p00
            norm = vu.cross(vv)
            norm.normalize()
            
            uv00 = mathutils.Vector((i / segs_u, j / segs_v))
            uv10 = mathutils.Vector(((i + 1) / segs_u, j / segs_v))
            uv01 = mathutils.Vector((i / segs_u, (j + 1) / segs_v))
            uv11 = mathutils.Vector(((i + 1) / segs_u, (j + 1) / segs_v))
        
            coords.append(p00)
            coords.append(p10)
            coords.append(p11)

            coords.append(p00)
            coords.append(p11)
            coords.append(p01)
            
            for k in range(6):
                normals.append(norm)
            
            uvs.append(uv00)
            uvs.append(uv10)
            uvs.append(uv11)
            
            uvs.append(uv00)
            uvs.append(uv11)
            uvs.append(uv01)

    return (coords, normals, uvs)


class Axis(Enum):
    X = 1
    Y = 2
    Z = 3


class Face(Enum):
    X_POS = 0
    X_NEG = 1
    Y_POS = 2
    Y_NEG = 3
    Z_POS = 4
    Z_NEG = 5
    
    
#Scale to apply so that a sphere of diameter 1 at position pos appears to be 1 unit high in the viewport
def calc_unit_scale(pos, region, rv3d):
    viewport_pos = view3d_utils.location_3d_to_region_2d(region, rv3d, pos)
    viewport_pos_near = view3d_utils.region_2d_to_origin_3d(region, rv3d, viewport_pos)
    
    pos_dir = pos - viewport_pos_near
    
#    print("pos " + str(pos))        

    perp = vecZ.cross(pos_dir)
    perp.normalize()
#    print("perp " + str(perp))
    
#    print ("viewport_pos " + str(viewport_pos))
    
    viewport_perp = view3d_utils.location_3d_to_region_2d(region, rv3d, pos + perp)
    
#    print ("viewport_perp " + str(viewport_perp))
    viewport_offset = viewport_perp - viewport_pos
#        print ("viewport_offset " + str(viewport_offset))
    
    return 1 / viewport_offset.magnitude


#Returns scalar s to multiply line_dir by so that line_point + s * line_dir lies on plane
# note that plane_norm does not need to be normalized
def isect_line_plane(line_point, line_dir, plane_point, plane_norm):
    to_plane = (plane_point - line_point).project(plane_norm)
    dir_par_to_norm = line_dir.project(plane_norm)
    
    if dir_par_to_norm.magnitude == 0:
        return None
        
    scalar = to_plane.magnitude / dir_par_to_norm.magnitude
    if to_plane.dot(dir_par_to_norm) < 0:
        scalar = -scalar
    return scalar


#Returns scalar s to multiply line_dir0 by so that line_point0 + s * line_dir0 is as close as possible to the other line
def closest_point_to_line(line_point0, line_dir0, line_point1, line_dir1):
    #vector perpendicular to both line 0 and line 1
    r = line_dir0.cross(line_dir1)
    norm = r.cross(line_dir1)
    return isect_line_plane(line_point0, line_dir0, line_point1, norm)


#Returns the ray of the intersection of two planes
def isect_planes(point0, normal0, point1, normal1):
    ray_normal = normal0.cross(normal1)
    ray_normal.normalize()
    
    perp = ray_normal.cross(normal0)
    
    s = isect_line_plane(point0, perp, point1, normal1)
    ray_point = point0 + s * perp
    
    return ray_point, ray_normal


#Finds the best s such that v1 = s * v0.  Presumes vectors are parallel
def findVectorScalar(v0, v1):
    xx = abs(v1.x - v0.x)
    yy = abs(v1.y - v0.y)
    zz = abs(v1.z - v0.z)
    
    if xx > yy and xx > zz:
        return v1.x / v0.x
    elif yy > zz:
        return v1.y / v0.y
    else:
        return z1.y / v0.z
    

def abs_vector(vector):
    return mathutils.Vector((abs(vector.x), abs(vector.y), abs(vector.z)))

def mult_vector(matrix, vector):
    v = vector.copy()
    v.resize_4d()
    v.w = 0
    v = matrix @ v
    v.resize_3d()
    return v

def mult_normal(matrix, normal):
    m = matrix.copy()
    m.invert()
    m.transpose()
    return mult_vector(m, normal)
    
def closest_axis(vector):
    xx = abs(vector.x)
    yy = abs(vector.y)
    zz = abs(vector.z)
    
    if xx > yy and xx > zz:
        return Axis.X
    elif yy > zz:
        return Axis.Y
    else:
        return Axis.Z
    

def project_point_onto_plane(point, plane_pt, plane_norm):
    proj = (point - plane_pt).project(plane_norm)
    return point - proj

#return vector of coefficients [a, b, c] such that vec = a * v0 + b * v1 + c * v2
def express_in_basis(vec, v0, v1, v2):
    v = mathutils.Matrix((v0, v1, v2)) #row order
    if v.determinant() == 0:
        return mathutils.Vector((0, 0, 0))
        
    vI = v.copy()
    vI.transpose()
    vI.invert()
    return vI @ vec
    
def snap_to_grid(pos, unit):
    p = mathutils.Vector(pos)
    p /= unit
    p += mathutils.Vector((.5, .5, .5))
    
    p.x = math.floor(p.x)
    p.y = math.floor(p.y)
    p.z = math.floor(p.z)
    
    p *= unit
    
    return p
    
def snap_to_grid_plane(pos, unit, plane_point, plane_normal):
    sp = snap_to_grid(pos, unit)

    axis = closest_axis(plane_normal)
    
    if axis == Axis.X:
        s = isect_line_plane(sp, vecX, plane_point, plane_normal)
        return sp + s * vecX
    elif axis == Axis.Y:
        s = isect_line_plane(sp, vecY, plane_point, plane_normal)
        return sp + s * vecY
    else:
        s = isect_line_plane(sp, vecZ, plane_point, plane_normal)
        return sp + s * vecZ

def intersect_triangle(p0, p1, p2, pickOrigin, pickRay):
    v10 = p1 - p0
    v20 = p2 - p0
    v21 = p2 - p1
    norm = v10.cross(v20)
    norm.normalize()
    
    scalar = isect_line_plane(pickOrigin, pickRay, p0, norm)
    if scalar == None:
        return None
        
    hitPoint = pickOrigin + scalar * pickRay
    
    vh0 = hitPoint - p0
    vh1 = hitPoint - p1
    v01 = -v10
    
    if vh0.cross(v20).dot(v10.cross(v20)) < 0:
        return None
    if vh0.cross(v10).dot(v20.cross(v10)) < 0:
        return None
    if vh1.cross(v21).dot(v01.cross(v21)) < 0:
        return None
    
    return hitPoint

    


class Bounds:
    def __init__(self, point):
        self.minBound = point.copy()
        self.maxBound = point.copy()
        
    def include_point(self, point):
        self.minBound.x = min(self.minBound.x, point.x)
        self.maxBound.x = max(self.maxBound.x, point.x)
        self.minBound.y = min(self.minBound.y, point.y)
        self.maxBound.y = max(self.maxBound.y, point.y)
        self.minBound.z = min(self.minBound.z, point.z)
        self.maxBound.z = max(self.maxBound.z, point.z)
    
    def include_bounds(self, bounds):
        include_point(bounds.minBound)
        include_point(bounds.maxBound)
    
    
def mesh_bounds(obj, world = True):
    
    bounds = None

    # minCo = None
    # maxCo = None
    mesh = obj.data
    
    for v in mesh.vertices:
        pos = mathutils.Vector(v.co)
        if world:
            pos = obj.matrix_world @ pos
    
#            print("pos " + str(pos))

        if bounds == None:
            bounds = Bounds(pos)
        else:
            bounds.include_point(pos)
    
        # if minCo == None:
            # minCo = mathutils.Vector(pos)
            # maxCo = mathutils.Vector(pos)
        # else:
            # minCo.x = min(minCo.x, pos.x)
            # minCo.y = min(minCo.y, pos.y)
            # minCo.z = min(minCo.z, pos.z)
            # maxCo.x = max(maxCo.x, pos.x)
            # maxCo.y = max(maxCo.y, pos.y)
            # maxCo.z = max(maxCo.z, pos.z)
            
    return bounds

    
    
def bmesh_bounds(obj, bmesh, world = True):

    bounds = None
    
    for v in bmesh.verts:
        pos = mathutils.Vector(v.co)
        if world:
            pos = obj.matrix_world @ pos
    
#            print("pos " + str(pos))

        if bounds == None:
            bounds = Bounds(pos)
        else:
            bounds.include_point(pos)
     
    return bounds


    # minCo = None
    # maxCo = None
    
    # for v in bmesh.verts:
        # pos = mathutils.Vector(v.co)
        # pos = obj.matrix_world @ pos
    
# #            print("pos " + str(pos))
    
        # if minCo == None:
            # minCo = mathutils.Vector(pos)
            # maxCo = mathutils.Vector(pos)
        # else:
            # minCo.x = min(minCo.x, pos.x)
            # minCo.y = min(minCo.y, pos.y)
            # minCo.z = min(minCo.z, pos.z)
            # maxCo.x = max(maxCo.x, pos.x)
            # maxCo.y = max(maxCo.y, pos.y)
            # maxCo.z = max(maxCo.z, pos.z)
            
    # return (minCo, maxCo)
    
    
    
