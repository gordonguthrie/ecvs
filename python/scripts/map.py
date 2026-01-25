import bpy
import bpy_extras
import math
import mathutils

from bpy_extras import image_utils

# Color management and material helpers
def set_vivid_color_management(view_transform='Standard', look='Medium High Contrast', exposure=0.25):
    scene = bpy.context.scene
    vs = scene.view_settings
    try:
        vs.view_transform = view_transform
    except Exception:
        # Fallback to Filmic if Standard isn't available
        vs.view_transform = 'Filmic'
    vs.look = look
    vs.exposure = exposure

def make_image_plane_vivid(image_name, emission_strength=1.5):
    # Find the material that uses the given image, then drive Emission for unlit vivid colors
    target_img = bpy.data.images.get(image_name)
    if not target_img:
        return
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        img_nodes = [n for n in nodes if n.type == 'TEX_IMAGE' and n.image == target_img]
        if not img_nodes:
            continue
        img_node = img_nodes[0]
        # Ensure we have an output and an emission shader
        out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out is None:
            out = nodes.new('ShaderNodeOutputMaterial')
        emission = next((n for n in nodes if n.type == 'EMISSION'), None)
        if emission is None:
            emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Strength'].default_value = emission_strength
        # Link image color -> emission color, emission -> output
        try:
            links.new(img_node.outputs['Color'], emission.inputs['Color'])
        except Exception:
            pass
        # If there's an existing BSDF, we can bypass it for a pure unlit look
        links.new(emission.outputs['Emission'], out.inputs['Surface'])
        # Optional: set blend mode to opaque to avoid unintended alpha darkening
        mat.blend_method = 'OPAQUE'
        break

# set up shading type
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL' #'MATERIAL', 'SOLID' or 'RENDERED'


# define some angles
n000 = math.radians(0)
n090 = math.radians(90)
n180 = math.radians(180)

# define some helper fns

# shared scale so text and paths match visually
SCENE_SCALE = 1.0
PATH_THICKNESS = 0.001 * SCENE_SCALE
DOT_X = 0.2
PATH_X = 0.1
CLIP_LENGTH = 144

# ---- Render/preview tuning (simple parameters) ----
# Color management
VIEW_TRANSFORM = 'Standard'   # fallback to 'Filmic' if unavailable
VIEW_LOOK      = 'Medium High Contrast'
VIEW_EXPOSURE  = 0.25

# Map material vividness
MAP_IMAGE_NAME          = 'edinburgh_midnight_blue_800_130_90.png'
# MAP_IMAGE_NAME        = 'edinburgh_forest_800_130_90.png''
# MAP_IMAGE_NAME        = 'edinburgh_contrast_zones_2400_130_90.png'
MAP_EMISSION_STRENGTH   = 1.3   # raise for brighter unlit colors (e.g., 1.8–2.2)

GROUND_DRONE_COLOUR     = (1.0, 0.0, 0.0, 1.0)
HELICOPTER_DRONE_COLOUR = (0.0, 0.0, 1.0, 1.0)

def make_text(name, body, colour, emission_strength=2.0):
    bpy.ops.object.text_add(location=(0, 0, 0), rotation=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = body
    obj.data.size = 0.002 * SCENE_SCALE
    obj.data.extrude = PATH_THICKNESS*0.1
    obj.rotation_euler[0] = n090
    obj.rotation_euler[1] = n000
    obj.rotation_euler[2] = n090

    # Create a unique material per text so colours are independent
    mat_name = f"{name}_mat"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs[0].default_value = colour
    # Add Emission shader and combine with BSDF for vivid text
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # Ensure output node exists
    out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        out = nodes.new('ShaderNodeOutputMaterial')
    emission = next((n for n in nodes if n.type == 'EMISSION'), None)
    if emission is None:
        emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = colour
    emission.inputs['Strength'].default_value = emission_strength
    add_shader = next((n for n in nodes if n.type == 'ADD_SHADER'), None)
    if add_shader is None:
        add_shader = nodes.new('ShaderNodeAddShader')
    if bsdf:
        try:
            links.new(bsdf.outputs['BSDF'], add_shader.inputs[0])
        except Exception:
            pass
    try:
        links.new(emission.outputs['Emission'], add_shader.inputs[1])
    except Exception:
        pass
    links.new(add_shader.outputs['Shader'], out.inputs['Surface'])
    # Assign/replace material slot 0
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

def attach_and_animate_on_path(obj, path_obj, start_frame=None, end_frame=None, follow_orientation=True):
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
    c.use_curve_follow = follow_orientation
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
bpy.ops.image.import_as_mesh_planes(files=[{"name": MAP_IMAGE_NAME}], size_mode='DPI', directory="./imports/")

# Boost map vividness: unlit emission + color management
set_vivid_color_management(VIEW_TRANSFORM, VIEW_LOOK, VIEW_EXPOSURE)
make_image_plane_vivid(MAP_IMAGE_NAME, emission_strength=MAP_EMISSION_STRENGTH)

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
lightsource.color=mathutils.Color((1.0, 1.0, 1.0))
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

# create number text and animate along path_text
num_text1 = make_text("text_1", "🚚5498", GROUND_DRONE_COLOUR)
num_text2 = make_text("text_2", "🚚3341", GROUND_DRONE_COLOUR)
num_text3 = make_text("text_3", "🚚0440", GROUND_DRONE_COLOUR)
num_text4 = make_text("text_4", "🚁198", HELICOPTER_DRONE_COLOUR)
num_text5 = make_text("text_5", "🚁379", HELICOPTER_DRONE_COLOUR)

path_text1 = make_path("path text1", [[0.01,    0.00], [0.01,   -0.008], [0.0,    -0.009]]) 
path_text2 = make_path("path text2", [[0.03,    0.01], [0.032,   0.006], [0.034,   0.012]]) 
path_text3 = make_path("path text3", [[-0.01,  -0.00], [-0.012, -0.002], [-0.018, -0.003]]) 
path_text4 = make_path("path text4", [[0.02,    0.01], [0.0,    -0.003]]) 
path_text5 = make_path("path text5", [[-0.01,  -0.02], [-0.04,  -0.009]]) 

# attach to paths
attach_and_animate_on_path(num_text1, path_text1, follow_orientation=False)
attach_and_animate_on_path(num_text2, path_text2, follow_orientation=False)
attach_and_animate_on_path(num_text3, path_text3, follow_orientation=False)
attach_and_animate_on_path(num_text4, path_text4, follow_orientation=False)
attach_and_animate_on_path(num_text5, path_text5, follow_orientation=False)

# this is how an object iṡ attached to path
# bpy.ops.object.parent_set(type='FOLLOW')

# pack all outputs into the file and save output
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath="./outputs/map.blend")
