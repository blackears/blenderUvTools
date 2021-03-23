import bpy
import bmesh
import mathutils


class TriplanarSettings(bpy.types.PropertyGroup):
    scale_u : bpy.props.FloatProperty(
        name="U Scale", description="Scale of texture along horizon", default = 1, min=0, soft_max = 4
    )

    scale_v : bpy.props.FloatProperty(
        name="V Scale", description="Scale of texture along vertical", default = 1, min=0, soft_max = 4
    )

def redraw_all_viewports(context):
    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if area.type == 'VIEW_3D':
            area.tag_redraw()

def map_editmode(context):
    settings = context.scene.triplanar_settings_props
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
    
        l2w = obj.matrix_world
        
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
#        bm = bmesh.new()
#        bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()


        # adjust uv coordinates
        for face in bm.faces:
            if face.select:
                xAbs = abs(face.normal.x)
                yAbs = abs(face.normal.y)
                zAbs = abs(face.normal.z)

                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    
                    wco = l2w @ loop.vert.co
                    
                    # use xy position of the vertex as a uv coordinate
                    uv = None
                    if (xAbs > yAbs and xAbs > zAbs):
                        uv = mathutils.Vector(wco.yz)
                    elif (yAbs > zAbs):
                        uv = mathutils.Vector(wco.xz)
                    else:
                        uv = mathutils.Vector(wco.xy)
                    
                    uv.x /= settings.scale_u
                    uv.y /= settings.scale_v
                    loop_uv.uv = uv

        bmesh.update_edit_mesh(me)
#        bm.to_mesh(me)
#        bm.free()
        
    redraw_all_viewports(context)    


def map_objectmode(context):
    settings = context.scene.triplanar_settings_props
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
    
        l2w = obj.matrix_world
        
        me = obj.data
#        bm = bmesh.from_edit_mesh(me)
        bm = bmesh.new()
        bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()


        # adjust uv coordinates
        for face in bm.faces:
            xAbs = abs(face.normal.x)
            yAbs = abs(face.normal.y)
            zAbs = abs(face.normal.z)

            for loop in face.loops:
                loop_uv = loop[uv_layer]
                
                wco = l2w @ loop.vert.co
                
                # use xy position of the vertex as a uv coordinate
                uv = None
                if (xAbs > yAbs and xAbs > zAbs):
                    uv = mathutils.Vector(wco.yz)
                elif (yAbs > zAbs):
                    uv = mathutils.Vector(wco.xz)
                else:
                    uv = mathutils.Vector(wco.xy)
                
                uv.x /= settings.scale_u
                uv.y /= settings.scale_v
                loop_uv.uv = uv

#        bmesh.update_edit_mesh(me)
        bm.to_mesh(me)
        bm.free()
        
    redraw_all_viewports(context)    
        

class TriplanarUvUnwrapOperator(bpy.types.Operator):
    """Vertex Pos as UVs"""
    bl_idname = "kitfox.triplanar_uv_unwrap"
    bl_label = "Vertex Pos as UVs"
    bl_options = {'REGISTER', 'UNDO'}

    # scale: FloatProperty(
        # name="Scale",
        # description="Scale UVs by this",
        # soft_min=0.1, soft_max=10.0,
        # default=0.5,
    # )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and (obj.mode == 'EDIT' or obj.mode == 'OBJECT')
#        return obj and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def execute(self, context):
        obj = context.active_object
        if obj.mode == 'EDIT':
            map_editmode(context)
        elif obj.mode == 'OBJECT':
            map_objectmode(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator("kitfox.triplanar_uv_unwrap")
    # bl_idname should be in form of "something.something"
    # or YourClass.bl_idname


def register():
    bpy.utils.register_class(TriplanarSettings)
    bpy.utils.register_class(TriplanarUvUnwrapOperator)
    bpy.types.VIEW3D_MT_uv_map.prepend(menu_func)

    bpy.types.Scene.triplanar_settings_props = bpy.props.PointerProperty(type=TriplanarSettings)


def unregister():
    bpy.utils.register_class(TriplanarSettings)
    bpy.utils.unregister_class(TriplanarUvUnwrapOperator)
    bpy.types.VIEW3D_MT_uv_map.remove(menu_func)
    
    del bpy.types.Scene.triplanar_settings_props


if __name__ == "__main__":
    register()