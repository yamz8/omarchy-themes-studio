"""Build the Blender base for 1-on-pole: every layer cut.py made, as a flat plane in front of a camera.

Usage: blender -b --python build.py [-- render]

Reads parts.toml and out/parts/. Writes out/base.blend. With `render`, it also renders the scene at
rest to out/rest.png, which check.py compares with the still.

The scene is set up so that at rest it draws the still exactly: the camera sees the picture at its
own size, textures are read pixel for pixel, nothing is filtered, dithered or tone mapped. Keep
those settings when animating, or the first frame of a loop stops being the still.

One Blender unit is 100 pixels of the still, so a plane moved 0.05 along x moves 5 pixels.
The layers are 1 unit apart in depth, back to front, so a perspective camera could be added later
for a parallax move without reordering anything.
"""

import sys
import tomllib
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PIXELS_PER_UNIT = 100
RENDER = "render" in sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else False


def main():
  parts = tomllib.loads((HERE / "parts.toml").read_text())["part"]
  bpy.ops.wm.read_factory_settings(use_empty=True)
  scene = bpy.context.scene
  scene.name = "Base"

  first = None
  for index, part in enumerate(parts):
    path = OUT / "parts" / f"{index + 1:02d}-{part['name']}.png"
    if not path.is_file():
      sys.exit(f"{path} is missing: run cut.py first.")
    plane = add_layer(scene, part["name"], path, depth=index)
    first = first or plane
  width, height = first["pixels"]

  set_up_render(scene, width, height)
  add_camera(scene, width, height, depth=len(parts) + 10)
  open_through_camera()

  bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "base.blend"), relative_remap=True)
  if RENDER:
    scene.frame_set(1)
    scene.render.filepath = str(OUT / "rest.png")
    bpy.ops.render.render(write_still=True)
  print(f"base.blend: {len(parts)} layers, {width} x {height}")


def add_layer(scene, name, path, depth):
  """A plane the size of the picture showing one layer, its own colour with no lighting."""
  image = bpy.data.images.load(str(path))
  image.name = name
  image.colorspace_settings.name = "sRGB"
  image.alpha_mode = "STRAIGHT"
  width, height = image.size

  mesh = bpy.data.meshes.new(name)
  half_w, half_h = width / PIXELS_PER_UNIT / 2, height / PIXELS_PER_UNIT / 2
  mesh.from_pydata([(-half_w, -half_h, 0), (half_w, -half_h, 0), (half_w, half_h, 0), (-half_w, half_h, 0)], [], [(0, 1, 2, 3)])
  uv = mesh.uv_layers.new(name="UVMap")
  for loop, coords in zip(mesh.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    uv.data[loop.index].uv = coords
  plane = bpy.data.objects.new(name, mesh)
  plane.location.z = depth
  plane["pixels"] = (width, height)
  scene.collection.objects.link(plane)

  material = bpy.data.materials.new(name)
  material.use_nodes = True
  material.surface_render_method = "BLENDED"
  material.use_backface_culling = True
  nodes, links = material.node_tree.nodes, material.node_tree.links
  nodes.clear()
  texture = nodes.new("ShaderNodeTexImage")
  texture.name = texture.label = "Layer"
  texture.image = image
  texture.interpolation = "Closest"
  texture.extension = "CLIP"
  emission = nodes.new("ShaderNodeEmission")
  clear = nodes.new("ShaderNodeBsdfTransparent")
  mix = nodes.new("ShaderNodeMixShader")
  output = nodes.new("ShaderNodeOutputMaterial")
  links.new(texture.outputs["Color"], emission.inputs["Color"])
  links.new(texture.outputs["Alpha"], mix.inputs["Fac"])
  links.new(clear.outputs["BSDF"], mix.inputs[1])
  links.new(emission.outputs["Emission"], mix.inputs[2])
  links.new(mix.outputs["Shader"], output.inputs["Surface"])
  for node, x in zip((texture, emission, clear, mix, output), (-600, -250, -250, 0, 250)):
    node.location = (x, -150 if node is clear else 0)
  mesh.materials.append(material)
  return plane


def set_up_render(scene, width, height):
  scene.render.engine = "BLENDER_EEVEE"
  scene.render.resolution_x, scene.render.resolution_y = width, height
  scene.render.resolution_percentage = 100
  scene.render.filter_size = 0.01
  scene.render.dither_intensity = 0
  scene.render.fps = 24
  scene.frame_start = scene.frame_end = 1
  scene.view_settings.view_transform = "Standard"
  scene.view_settings.look = "None"
  scene.view_settings.exposure = 0
  scene.view_settings.gamma = 1
  scene.render.image_settings.file_format = "PNG"
  scene.render.image_settings.color_mode = "RGB"
  scene.render.image_settings.color_depth = "8"
  scene.world = bpy.data.worlds.new("World")
  scene.world.color = (1, 0, 1)  # magenta: anything that shows through is easy to see


def add_camera(scene, width, height, depth):
  data = bpy.data.cameras.new("Camera")
  data.type = "ORTHO"
  data.ortho_scale = max(width, height) / PIXELS_PER_UNIT
  data.clip_end = depth + 10
  camera = bpy.data.objects.new("Camera", data)
  camera.location = (0, 0, depth)
  scene.collection.objects.link(camera)
  scene.camera = camera


def open_through_camera():
  """Have every 3D view open looking through the camera, showing the pictures, not grey planes."""
  for screen in bpy.data.screens:
    for area in screen.areas:
      if area.type != "VIEW_3D":
        continue
      for space in area.spaces:
        if space.type == "VIEW_3D":
          space.shading.type = "MATERIAL"
          space.overlay.show_floor = False
          space.overlay.show_axis_x = space.overlay.show_axis_y = False
          space.region_3d.view_perspective = "CAMERA"
          space.region_3d.view_camera_zoom = 0  # the camera's frame fitted to the view


main()
