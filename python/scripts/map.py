import bpy
import bpy_extras
import math
import mathutils

from bpy_extras import image_utils

# define some angles
n000 = math.radians(0)
n090 = math.radians(90)
n180 = math.radians(180)

# define some helper fns

def make_dot(x, y):
    bpy.ops.mesh.primitive_circle_add(radius=0.01, align='WORLD', location=(x, y, 0.1), scale=(1, 1, 1), rotation=(n000, n090, n000))

def make_path(x, y):
    bpy.ops.curve.primitive_bezier_curve_add(radius=1, align='WORLD', location=(x, y, 0.02), scale=(1, 1, 1))

# Start the procedural stuff

# delete the cube
bpy.ops.object.select_all(action="DESELECT")
bpy.data.objects["Cube"].select_set(True)
bpy.ops.object.delete()

# insert the map
bpy.ops.image.import_as_mesh_planes(files=[{"name": "example_map.png"}], directory="./imports/")

# set up camera
camera = bpy.data.objects["Camera"]
# position first
camera.location[0] = 2.0
camera.location[1] = 0.0
camera.location[2] = 0.0
# then angle
camera.rotation_euler[0] = n090
camera.rotation_euler[1] = n000
camera.rotation_euler[2] = n090

# set up light source
light = bpy.data.objects["Light"]
lightsource = bpy.data.lights["Light"]

lightsource.type="SUN"
lightsource.color=mathutils.Color((1.0, 0.866, 0.301))
lightsource.energy = 1.0

light.location[0] = 3.0
light.location[1] = 0.0
light.location[2] = 0.0

light.rotation_euler[0] = 0.0
light.rotation_euler[1] = n090
light.rotation_euler[2] = 0.0

# set up output
bpy.data.scenes["Scene"].render.resolution_x=3840
bpy.data.scenes["Scene"].render.resolution_y=2160
bpy.data.scenes["Scene"].frame_end=368
bpy.data.scenes["Scene"].render.image_settings.media_type='VIDEO'

# general parameters
animation = range(0,368)
starting_angle=90
diff=0.172078312

make_dot(0.2, 0.2)
make_dot(0.2, 0.3)
make_dot(0.2, 0.4)

make_path(-0.2, -0.2)

#for i in animation:
#    camera.keyframe_insert("rotation_euler", index=0, frame=i)
#    camera.rotation_euler[0] = math.radians(starting_angle+i*diff)

# pack all outputs into the file and save output
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath="./outputs/map.blend")
