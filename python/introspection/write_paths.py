import bpy
import json

OUTPUT_PATH = "C:\\tmp\\paths.json"

all_paths = {}

for obj in bpy.data.objects:
    if obj.type != 'CURVE':
        continue
    curve = obj.data
    path_points = []
    for spline in curve.splines:
        if spline.type == 'BEZIER':
            pts = [[round(bp.co.y, 6), round(bp.co.z, 6)] for bp in spline.bezier_points]
        elif spline.type in ('POLY', 'NURBS'):
            pts = [[round(p.co.y, 6), round(p.co.z, 6)] for p in spline.points]
        else:
            continue
        path_points.extend(pts)
    if path_points:
        all_paths[obj.name] = path_points

with open(OUTPUT_PATH, 'w') as f:
    json.dump(all_paths, f, indent=2)

print(f"Written {len(all_paths)} paths to {OUTPUT_PATH}")
