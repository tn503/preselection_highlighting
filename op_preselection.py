import bpy
import bmesh

import gpu
from gpu_extras.batch import batch_for_shader

bl_info = {"name": "Preselection highlighting Add-on", "version": (1, 0),}

def update_mybool(self, context):
    bpy.ops.object.preselection_operator('INVOKE_DEFAULT')

class PreselectionOperatorSettings(bpy.types.PropertyGroup):
    my_bool: bpy.props.BoolProperty(default = False, update=update_mybool)
    
    my_selection: bpy.props.StringProperty(default = 'none')
    
    my_vector1: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector2: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector3: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector4: bpy.props.FloatVectorProperty(subtype='XYZ')
    
    my_vector5: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector6: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector7: bpy.props.FloatVectorProperty(subtype='XYZ')
    my_vector8: bpy.props.FloatVectorProperty(subtype='XYZ')

def draw_callback(context):
    ss = context.window_manager.PreselectionOperatorSettings
    if ss.my_selection != 'none':
        if ss.my_selection == 'vert':
            shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR')
            
            coords = [ss.my_vector1,]
            batch = batch_for_shader(shader, 'POINTS', {"pos": coords})
            
            shader.uniform_float("color", (0, 1, 0, 1))
            gpu.state.point_size_set(4.5)
        elif ss.my_selection == 'edge':
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            
            coords = [ss.my_vector1, ss.my_vector2,]
            batch = batch_for_shader(shader, 'LINES', {"pos": coords})
            
            shader.uniform_float("color", (0, 1, 0, 1))
            shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
            shader.uniform_float("lineWidth", 1.0)
        elif ss.my_selection == 'triangle' or ss.my_selection == 'face':
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            
            coords = [ ss.my_vector1, ss.my_vector2, ss.my_vector3, ss.my_vector4, ss.my_vector5, ss.my_vector6]
            
            if ss.my_selection == 'face':
                coords.extend([ss.my_vector7, ss.my_vector8])
            
            batch = batch_for_shader(shader, 'LINES', {"pos": coords})
            
            shader.uniform_float("color", (0, 1, 0, 1))
            shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
            shader.uniform_float("lineWidth", 1.0)
            
        batch.draw(shader)

def cursor_callback(context, xy):
    xy = xy[0] - bpy.context.area.x, xy[1] - bpy.context.area.y
    
    if bpy.context.mode=='EDIT_MESH':
        obj = bpy.context.object
        bm = bmesh.from_edit_mesh(obj.data)
        
        #store selection
        selection = []
        for v in bm.verts:
            if v.select:
                selection.append(v)
        for e in bm.edges:
            if e.select:
                selection.append(e)
        for f in bm.faces:
            if f.select:
                selection.append(f)
        #store active
        active = bm.select_history.active
        active_face = bm.faces.active
        
        #(pre)select at mouse position        
        bpy.ops.view3d.select(location=xy, deselect_all=True)
        
        ss = context.window_manager.PreselectionOperatorSettings
        #store (pre)selection coordinates and deselct
        for f in bm.faces:
            if f.select:
                ss.my_selection = 'triangle'
                
                ss.my_vector1 = f.edges[0].verts[0].co
                ss.my_vector2 = f.edges[0].verts[1].co
                
                ss.my_vector3 = f.edges[1].verts[0].co
                ss.my_vector4 = f.edges[1].verts[1].co
                
                ss.my_vector5 = f.edges[2].verts[0].co
                ss.my_vector6 = f.edges[2].verts[1].co
                
                #print(len(f.verts))
                if len(f.verts) == 4:
                    ss.my_selection = 'face'
                    ss.my_vector7 = f.edges[3].verts[0].co
                    ss.my_vector8 = f.edges[3].verts[1].co
                
                f.select = False
                bm.select_history.remove(f)
                break
        else:
            for e in bm.edges:
                if e.select:
                    ss.my_selection = 'edge'
                    
                    ss.my_vector1 = e.verts[0].co
                    ss.my_vector2 = e.verts[1].co
                    
                    e.select = False
                    bm.select_history.remove(e)
                    break
            else:
                for v in bm.verts:
                    if v.select:
                        
                        ss.my_selection = 'vert'
                        ss.my_vector1 = v.co
                        
                        v.select = False
                        bm.select_history.remove(v)
                        
                        break
                else:
                    ss.my_selection = 'none'
                    
        #recovery selection
        for i in selection:
            i.select = True
        #recovery active
        if active:
            bm.select_history.add(active)
        if active_face:
            bm.faces.active = active_face

        bmesh.update_edit_mesh(obj.data)
        
    
class PreselectionOperator(bpy.types.Operator):
    """Preselction Highlighting Operator"""
    bl_idname = "object.preselection_operator"
    bl_label = "Object Preselection Operator"

    added_handler = False
    added_draw_handler = False
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        WindowManager = bpy.types.WindowManager
        
        if type(self).added_handler:
            context.window_manager.draw_cursor_remove(type(self).added_handler)
            bpy.types.SpaceView3D.draw_handler_remove(type(self).added_draw_handler, 'WINDOW')
            
            type(self).added_handler = False
            type(self).added_draw_handler = False
                        
            self.report({'INFO'}, "Preselection highlighting add-on handlers remove")
        else:
            args = (context, )

            type(self).added_handler = context.window_manager.draw_cursor_add(cursor_callback, args, 'VIEW_3D', 'WINDOW')
            type(self).added_draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback, args, 'WINDOW', 'POST_VIEW')
            
            bpy.context.area.tag_redraw()
            self.report({'INFO'}, "Preselection highlighting add-on handlers add")
        
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.prop(context.window_manager.PreselectionOperatorSettings, 'my_bool', text = 'Preselection', toggle=1)

def register():    
    for f in bpy.types.VIEW3D_HT_header._dyn_ui_initialize():
        if f.__name__ == menu_func.__name__:
            bpy.types.VIEW3D_HT_header.remove(f)
    
    bpy.utils.register_class(PreselectionOperator)
    bpy.utils.register_class(PreselectionOperatorSettings)
    
    bpy.types.WindowManager.PreselectionOperatorSettings = bpy.props.PointerProperty(type=PreselectionOperatorSettings)
        
    bpy.types.VIEW3D_HT_header.append(menu_func)
    
    
def unregister():
    bpy.utils.unregister_class(PreselectionOperator)
    bpy.utils.unregister_class(PreselectionOperatorSettings)
    
    bpy.types.VIEW3D_HT_header.remove(menu_func)


if __name__ == "__main__":
    register()
