"""Try the material in Blender: every part as a flat plane in front of a camera, the far boat bobbing.

Usage: blender -b --python tries/bob-blender.py [-- exact]

With `exact`, it renders at the still's own size with no filtering, to see whether Blender
gives the still back.

Reads out/parts/ and parts.toml. Writes out/tries/kanagawa-parts.blend and two renders, the boat
at rest and at the top of its bob.
"""

import math
import sys
import tomllib
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "tries"
WIDTH = 960
SECONDS, FPS = 6, 24
LIFT, TILT = 0.007, 0.7  # share of the picture's height, and degrees
MOVING = "boat-far"
EXACT = "exact" in sys.argv

OUT.mkdir(parents=True, exist_ok=True)
names = [part["name"] for part in tomllib.loads((HERE / "parts.toml").read_text())["part"]]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, SECONDS * FPS
scene.world = bpy.data.worlds.new("World")
scene.world.color = (1, 0, 1)  # anything that shows through is easy to see

planes = {}
for index, name in enumerate(names):
  image = bpy.data.images.load(str(HERE / "out" / "parts" / f"{index + 1:02d}-{name}.png"))
  aspect = image.size[0] / image.size[1]
  bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, index * 0.01))
  plane = bpy.context.active_object
  plane.name = name
  plane.scale = (aspect, 1, 1)
  material = bpy.data.materials.new(name)
  material.use_nodes = True
  material.surface_render_method = "BLENDED"
  nodes, links = material.node_tree.nodes, material.node_tree.links
  nodes.clear()
  texture = nodes.new("ShaderNodeTexImage")
  texture.image = image
  texture.extension = "CLIP"
  if EXACT:
    texture.interpolation = "Closest"
  emission = nodes.new("ShaderNodeEmission")
  clear = nodes.new("ShaderNodeBsdfTransparent")
  mix = nodes.new("ShaderNodeMixShader")
  output = nodes.new("ShaderNodeOutputMaterial")
  links.new(texture.outputs["Color"], emission.inputs["Color"])
  links.new(texture.outputs["Alpha"], mix.inputs["Fac"])
  links.new(clear.outputs["BSDF"], mix.inputs[1])
  links.new(emission.outputs["Emission"], mix.inputs[2])
  links.new(mix.outputs["Shader"], output.inputs["Surface"])
  plane.data.materials.append(material)
  planes[name] = plane

camera_data = bpy.data.cameras.new("Camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = aspect
camera = bpy.data.objects.new("Camera", camera_data)
camera.location = (0, 0, 10)
scene.collection.objects.link(camera)
scene.camera = camera
if EXACT:
  scene.render.resolution_x, scene.render.resolution_y = image.size
  scene.render.filter_size = 0.01
  scene.render.dither_intensity = 0
else:
  scene.render.resolution_x = WIDTH
  scene.render.resolution_y = round(WIDTH / aspect / 2) * 2
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

boat = planes[MOVING]
for frame in range(1, SECONDS * FPS + 1):
  phase = 2 * math.pi * (frame - 1) / (SECONDS * FPS)
  boat.location.y = LIFT * math.sin(phase)
  boat.rotation_euler.z = math.radians(TILT) * (math.sin(phase + 0.9) - math.sin(0.9))
  boat.keyframe_insert("location", frame=frame)
  boat.keyframe_insert("rotation_euler", frame=frame)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "kanagawa-parts.blend"), relative_remap=True)
for label, frame in (("rest", 1), ("peak", 1 + SECONDS * FPS // 4)):
  scene.frame_set(frame)
  scene.render.filepath = str(OUT / f"bob-blender-{'exact-' if EXACT else ''}{label}.png")
  bpy.ops.render.render(write_still=True)
print("blender try done")
