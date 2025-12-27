import bpy
import math
import mathutils

# delete the cube
bpy.ops.object.select_all(action="DESELECT")
bpy.data.objects["Cube"].select_set(True)
bpy.ops.object.delete()

# insert the sentinel
bpy.ops.import_scene.fbx(filepath="./imports/Salute.fbx")

# set up camera
camera = bpy.data.objects["Camera"]
# position first
camera.location[0] =  0.0
camera.location[1] = -0.298
camera.location[2] =  0.0
# then angle
camera.rotation_euler[0]=math.radians(90)
camera.rotation_euler[1]=0
camera.rotation_euler[2]=0

# set up light source
bpy.data.lights["Light"].type="SUN"
bpy.data.lights["Light"].color=mathutils.Color((1.0, 0.866, 0.301))

# set up output
bpy.data.scenes["Scene"].render.resolution_x=3840
bpy.data.scenes["Scene"].render.resolution_y=2160
bpy.data.scenes["Scene"].frame_end=368
bpy.data.scenes["Scene"].render.image_settings.media_type='VIDEO'
bpy.data.scenes["Scene"].render.filepath = "/tmp/sentinel.blend"

# general parameters
animation = range(0,368)
starting_angle=90
diff=0.172078312

for i in animation:
    camera.keyframe_insert("rotation_euler", index=0, frame=i)
    camera.rotation_euler[0] = math.radians(starting_angle+i*diff)

# save output
bpy.ops.wm.save_as_mainfile(filepath="./outputs/tilt_render.blend")
