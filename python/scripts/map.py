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
DOT_RADIUS = 0.001 * SCENE_SCALE
PATH_THICKNESS = 0.001 * SCENE_SCALE
DOT_X = 0.2
PATH_X = 0.1
CLIP_LENGTH = 48

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

def make_text(name, body, colour=(1.0, 1.0, 1.0, 1.0)):
    bpy.ops.object.text_add(location=(0, 0, 0), rotation=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = body
    obj.data.size = 0.001 * SCENE_SCALE
    obj.data.extrude = PATH_THICKNESS
    obj.rotation_euler[0] = n090
    obj.rotation_euler[1] = n000
    obj.rotation_euler[2] = -n090

    mat = bpy.data.materials.get("TextColour")
    if mat is None:
        mat = bpy.data.materials.new(name="TextColour")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = colour
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat
    return obj

def make_path(name, yz_points):
    # validate input points are pairs (y, z)
    for i, pt in enumerate(yz_points):
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            raise ValueError(f"Each path point must be a pair (y, z); got {pt} at index {i}")
    # local X-plane for path placement
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'
    # make the path visible with thickness matching dots
    curve.bevel_depth = PATH_THICKNESS
    curve.bevel_resolution = 3
    curve.resolution_u = 12
    spline = curve.splines.new(type='BEZIER')
    spline.bezier_points.add(len(yz_points) - 1)
    
    # make them all straight lines
    for bp in spline.bezier_points:
        bp.handle_left_type="VECTOR"
        bp.handle_right_type="VECTOR"

    for p, (y, z) in zip(spline.bezier_points, yz_points):
        p.co = (PATH_X * SCENE_SCALE, y * SCENE_SCALE, z * SCENE_SCALE)

    obj = bpy.data.objects.new(name + "_curve", curve)
    bpy.context.scene.collection.objects.link(obj)
    # Hide curve from final render but keep it in viewport
    obj.hide_render = True
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
bpy.ops.image.import_as_mesh_planes(files=[{"name": "edinburgh_midnight_blue_800_130_90.png"}],size_mode='DPI', directory="./imports/")

# set up camera
camera = bpy.data.objects["Camera"]
# position first
camera.location[0] = 0.22
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
bpy.data.scenes["Scene"].frame_end=CLIP_LENGTH
bpy.data.scenes["Scene"].render.image_settings.media_type='VIDEO'

# general parameters
animation = range(0,CLIP_LENGTH)
starting_angle=90
diff=0.172078312

dot1a = make_dot((1.0, 0.0, 0.0, 1.0))
# dot1b = make_dot((1.0, 0.0, 0.0, 1.0))
# dot1c = make_dot((1.0, 0.0, 0.0, 1.0))
# dot2a = make_dot((0.0, 1.0, 0.0, 1.0))
# dot2b = make_dot((0.0, 1.0, 0.0, 1.0))
# dot2c = make_dot((0.0, 1.0, 0.0, 1.0))
# dot3a = make_dot((0.0, 0.0, 1.0, 1.0))
# dot3b = make_dot((0.0, 0.0, 1.0, 1.0))
# dot3c = make_dot((0.0, 0.0, 1.0, 1.0))

# create number text and animate along path_text
num_text = make_text("text_5498", "5498", (1.0, 0.0, 0.0, 1.0))

path1a = make_path("path1a", [[-0.03, -0.03], [-0.015, -0.03], [-0.015, -0.015], [0.0, -0.015], [0.0, 0.0], [0.015, 0.0], [0.015, 0.015], [0.03, 0.015], [0.03, 0.03]]) 

path_text = make_path("path text", [[0.024, -0.02], [0.017, -0.028], [0.0, -0.02], [0.01, -0.01], [0.015, -0.017], [-0.024, -0.026]]) 

# path1b = make_path("path1b", [[0.2, -0.38], [0.35, -0.19], [0.47, -0.01], [0.54, 0.3], [0.67, 0.37], [0.87, 0.44]]) 
# path1c = make_path("path1c", [[-0.1, -0.29], [0.0, -0.19], [0.27, 0.0], [0.41, 0.2], [0.66, 0.4], [0.87, 0.42]]) 

# path2a = make_path("path2a", [[-0.76, -0.1], [-0.71, 0.2], [-0.61, 0.4], [0.3, 0.41], [0.82, 0.42]]) 
# path2b = make_path("path2b", [[-0.75, -0.2], [-0.68, -0.1], [-0.54, 0.0], [-0.1, 0.2], [0.42, 0.25], [0.65, 0.37], [0.88, 0.41]]) 
# path2c = make_path("path2c", [[-0.83, -0.26], [-0.63, -0.15], [-0.32, -0.05], [0.2, 0.1], [0.42, 0.15], [0.65, 0.27], [0.88, 0.41]])

# path3a = make_path("path3a", [[-0.43, -0.42], [-0.25, -0.32], [0.09, -0.025], [-0.3, 0.02], [0.39, 0.30], [0.8, 0.455]]) 
# path3b = make_path("path3b", [[-0.43, -0.41], [-0.35, -0.39], [-0.13, -0.04], [0.35, 0.3], [0.47, 0.38], [0.82, 0.43]]) 
# path3c = make_path("path3c", [[-0.47, -0.42], [-0.37, -0.32], [-0.02, -0.26], [0.23, 0.2], [0.55, 0.35], [0.85, 0.45]]) 

# Attach dots to the path and animate along it over the scene duration
attach_and_animate_on_path(dot1a, path1a)
# attach_and_animate_on_path(dot1b, path1b)
# attach_and_animate_on_path(dot1c, path1c)
# attach_and_animate_on_path(dot2a, path2a)
# attach_and_animate_on_path(dot2b, path2b)
# attach_and_animate_on_path(dot2c, path2c)
# attach_and_animate_on_path(dot3a, path3a)
# attach_and_animate_on_path(dot3b, path3b)
# attach_and_animate_on_path(dot3c, path3c)

attach_and_animate_on_path(num_text, path_text)

# this is how an object iṡ attached to path
# bpy.ops.object.parent_set(type='FOLLOW')

# pack all outputs into the file and save output
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath="./outputs/map.blend")
