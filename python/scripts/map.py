import bpy
import bpy_extras
import json
import math
import mathutils
import os
import sys

from bpy_extras import image_utils

# set the output path after config/shot are loaded

# Color management and material helpers
def set_vivid_color_management(view_transform='Standard', look='Medium High Contrast', exposure=0.25):
    scene = bpy.context.scene
    scene.display_settings.display_device = 'sRGB'
    vs = scene.view_settings
    try:
        vs.view_transform = view_transform
    except Exception:
        # Fallback to Filmic if Standard isn't available
        vs.view_transform = 'Filmic'
    vs.look = look
    vs.exposure = exposure
    if hasattr(vs, "gamma"):
        vs.gamma = 1.0

def make_image_plane_vivid(image_name, emission_strength=1.5):
    # Rebuild the imported plane material as emission-only so lighting cannot dull the image
    target_img = bpy.data.images.get(image_name)
    if not target_img:
        return
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nodes = mat.node_tree.nodes
        img_nodes = [n for n in nodes if n.type == 'TEX_IMAGE' and n.image == target_img]
        if not img_nodes:
            continue
        try:
            target_img.colorspace_settings.name = 'sRGB'
        except Exception:
            pass

        nodes.clear()
        links = mat.node_tree.links

        tex = nodes.new('ShaderNodeTexImage')
        tex.image = target_img
        tex.interpolation = 'Linear'

        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Strength'].default_value = emission_strength

        out = nodes.new('ShaderNodeOutputMaterial')

        links.new(tex.outputs['Color'], emission.inputs['Color'])
        links.new(emission.outputs['Emission'], out.inputs['Surface'])

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
_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "master.json")
with open(_config_path, "r") as _f:
    _cfg = json.load(_f)

SCENE_SCALE             = _cfg["SCENE_SCALE"]
PATH_THICKNESS          = 0.003 * SCENE_SCALE
DOT_X                   = _cfg["DOT_X"]
PATH_X                  = _cfg["PATH_X"]

# ---- Render/preview tuning (simple parameters) ----
# Color management (forced)
VIEW_TRANSFORM          = "Standard"
VIEW_LOOK               = "None"
VIEW_EXPOSURE           = 0.0

MAP_EMISSION_STRENGTH   = _cfg["MAP_EMISSION_STRENGTH"]   # raise for brighter unlit colors (e.g., 1.8–2.2)
RENDER_OUTPUT_DIR       = _cfg["RENDER_OUTPUT_DIR"]


# Shot config — name passed after '--' on the Blender command line, e.g.:
#   blender --background --python map.py -- shot_1
_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
try:
    _argv = sys.argv[sys.argv.index("--") + 1:]
except ValueError:
    _argv = []
if not _argv:
    raise SystemExit("Usage: blender --background --python map.py -- <shot_name>  (e.g. shot_1)")
_shot_name = _argv[0]
_shot_config_path = os.path.join(_config_dir, f"{_shot_name}.json")
with open(_shot_config_path, "r") as _f:
    _shot = json.load(_f)

TIME_OF_DAY = _shot.get("TIME_OF_DAY", "day").lower()
if TIME_OF_DAY not in {"day", "night"}:
    raise ValueError(f"Shot config TIME_OF_DAY must be 'day' or 'night'; got {TIME_OF_DAY!r}")

GROUND_DRONE_COLOUR = tuple(_cfg[f"{TIME_OF_DAY.upper()}_GROUND_DRONE_COLOUR"])
HELICOPTER_DRONE_COLOUR = tuple(_cfg[f"{TIME_OF_DAY.upper()}_HELICOPTER_DRONE_COLOUR"])


def build_entities_from_config(shot_config):
    if "entities" in shot_config:
        return shot_config["entities"]

    devices = shot_config.get("devices", [])
    paths = shot_config.get("paths", [])

    if len(devices) != len(paths):
        raise ValueError(
            f"Shot config has {len(devices)} devices but {len(paths)} paths; they must match"
        )

    entities = []
    for device, path_entry in zip(devices, paths):
        if not isinstance(path_entry, dict) or len(path_entry) != 1:
            raise ValueError(
                f"Each path entry must be a single-key object like {{\"path_1\": [[...]]}}; got {path_entry}"
            )
        _, yz_points = next(iter(path_entry.items()))
        entity = dict(device)
        entity["path"] = yz_points
        entities.append(entity)

    return entities

_render_base = os.path.abspath(RENDER_OUTPUT_DIR)
bpy.data.scenes["Scene"].render.filepath = os.path.join(_render_base, _shot_name + "_2")

MAP_IMAGE_NAME = _shot["MAP_IMAGE_NAME"]
CLIP_LENGTH    = _shot["CLIP_LENGTH"]
ENTITIES       = build_entities_from_config(_shot)

_colour_map = {
    "GROUND_DRONE_COLOUR":     GROUND_DRONE_COLOUR,
    "HELICOPTER_DRONE_COLOUR": HELICOPTER_DRONE_COLOUR,
}

PATH_COLOUR = (1.0, 0.45, 0.08, 1.0)

def make_text(name, body, colour, emission_strength=2.0):
    bpy.ops.object.text_add(location=(0, 0, 0), rotation=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = body
    obj.data.size = 0.002 * SCENE_SCALE
    obj.data.extrude = PATH_THICKNESS*0.01
    obj.rotation_euler[0] = n090
    obj.rotation_euler[1] = n000
    obj.rotation_euler[2] = n090

    # Create a unique material per text so colours are independent
    mat_name = f"{name}_mat"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for link in list(links):
        links.remove(link)
    # Ensure output node exists
    out = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        out = nodes.new('ShaderNodeOutputMaterial')
    emission = next((n for n in nodes if n.type == 'EMISSION'), None)
    if emission is None:
        emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = colour
    emission.inputs['Strength'].default_value = emission_strength
    links.new(emission.outputs['Emission'], out.inputs['Surface'])
    mat.blend_method = 'OPAQUE'
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
    curve.bevel_depth = PATH_THICKNESS*0.1
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
    obj.color = PATH_COLOUR

    mat_name = f"{name}_mat"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for link in list(links):
        links.remove(link)

    out = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        out = nodes.new('ShaderNodeOutputMaterial')

    emission = next((node for node in nodes if node.type == 'EMISSION'), None)
    if emission is None:
        emission = nodes.new('ShaderNodeEmission')

    emission.inputs['Color'].default_value = PATH_COLOUR
    emission.inputs['Strength'].default_value = 1.6
    links.new(emission.outputs['Emission'], out.inputs['Surface'])

    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

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
    edit_prefs = bpy.context.preferences.edit
    previous_interpolation = edit_prefs.keyframe_new_interpolation_type
    try:
        edit_prefs.keyframe_new_interpolation_type = 'LINEAR'
        c.offset_factor = 0.0
        c.keyframe_insert(data_path="offset_factor", frame=start_frame)
        c.offset_factor = 1.0
        c.keyframe_insert(data_path="offset_factor", frame=end_frame)
    finally:
        edit_prefs.keyframe_new_interpolation_type = previous_interpolation

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
scene = bpy.data.scenes["Scene"]
# scene.render.engine = 'CYCLES'
# scene.cycles.device = 'CPU'
scene.render.resolution_x=3840
scene.render.resolution_y=2160
scene.frame_end=CLIP_LENGTH
scene.render.image_settings.media_type='VIDEO'
scene.render.use_overwrite = True

# general parameters
animation = range(0,CLIP_LENGTH)
starting_angle=90
diff=0.172078312

# create number text and paths from shot config, then animate
for i, entity in enumerate(ENTITIES, start=1):
    colour = _colour_map[entity["colour"]]
    num_text = make_text(f"text_{i}", entity["label"], colour)
    path_obj = make_path(f"path text{i}", entity["path"])
    attach_and_animate_on_path(num_text, path_obj, follow_orientation=False)

# this is how an object iṡ attached to path
# bpy.ops.object.parent_set(type='FOLLOW')

# pack all outputs into the file and save output
bpy.ops.file.pack_all()
_blend_path = os.path.join("./outputs", f"map_{_shot_name}_2.blend")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=_blend_path, check_existing=False)
