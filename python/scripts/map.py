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

# shared scale so dots and paths match visually
SCENE_SCALE = 1.0
DOT_RADIUS = 0.01 * SCENE_SCALE
PATH_THICKNESS = DOT_RADIUS
DOT_X = 0.2
PATH_X = 0.1

def make_dot(colour):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=DOT_RADIUS,
        align='WORLD',
        location=(0, 0, 0),
    )
    obj = bpy.context.active_object
    # Assign a red material for visibility
    mat = bpy.data.materials.get("DotRed")
    if mat is None:
        mat = bpy.data.materials.new(name="DotColour")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = colour  # Base Coluor
            bsdf.inputs[1].default_value # Specular
            bsdf.inputs[2].default_value # Roughness
        obj.data.materials.append(mat)
    return obj

def make_path(name, yz_points):
    # local X-plane for path placement
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'
    # make the path visible with thickness matching dots
    curve.bevel_depth = PATH_THICKNESS
    curve.bevel_resolution = 3
    curve.resolution_u = 12
    spline = curve.splines.new(type='NURBS')
    spline.points.add(len(yz_points) - 1)
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(yz_points))

    for p, (y, z) in zip(spline.points, yz_points):
        p.co = (PATH_X * SCENE_SCALE, y * SCENE_SCALE, z * SCENE_SCALE, 1.0)

    obj = bpy.data.objects.new(name + "_curve", curve)
    bpy.context.scene.collection.objects.link(obj)
    # Hide path in final renders but keep it in viewport
    #obj.hide_render = True
    return obj

def attach_and_animate_on_path(obj, path_obj, start_frame=None, end_frame=None):
    """Attach object to curve and animate along it using Follow Path constraint."""
    scene = bpy.context.scene
    if start_frame is None:
        start_frame = scene.frame_start
    if end_frame is None:
        end_frame = scene.frame_end

    # Ensure the curve acts as a path
    path_obj.data.use_path = True

    c = obj.constraints.new(type='FOLLOW_PATH')
    c.target = path_obj
    c.use_curve_follow = True
    # Use normalized progression along the curve independent of eval_time
    c.use_fixed_location = True
    c.offset_factor = 0.0
    c.keyframe_insert(data_path="offset_factor", frame=start_frame)
    c.offset_factor = 1.0
    c.keyframe_insert(data_path="offset_factor", frame=end_frame)

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
camera.location[0] = 3.0
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

dot1 = make_dot((1.0, 0.0, 0.0, 1.0))
dot2 = make_dot((0.0, 1.0, 0.0, 1.0))
dot3 = make_dot((0.0, 0.0, 1.0, 1.0))

path1 = make_path("path1", [[0.1, 0.1], [0.2, 0.1], [0.18, 0.2], [0.3, 0.3]]) 
path2 = make_path("path2", [[0.2, 0.1], [0.2, 0.2], [0.3, 0.4], [0.5, 0.3]]) 
path3 = make_path("path3", [[0.43, 0.42], [0.25, 0.47], [0.34, 0.5], [0.3, -0.4]]) 

# Attach dots to the path and animate along it over the scene duration
attach_and_animate_on_path(dot1, path1)
attach_and_animate_on_path(dot2, path2)
attach_and_animate_on_path(dot3, path3)

# this is how an object iṡ attached to path
# bpy.ops.object.parent_set(type='FOLLOW')

# pack all outputs into the file and save output
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath="./outputs/map.blend")
