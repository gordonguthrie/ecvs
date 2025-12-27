import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.object.text_add(enter_editmode=False, location=(0, 0, 0))
text_obj = bpy.context.object

text_obj.data.body = "Hello World"

text_obj.data.extrude = 0.05
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'

text_obj.rotation_euler[0] = 1.5708

bpy.ops.wm.save_as_mainfile(filepath="./outputs/text.blend")
