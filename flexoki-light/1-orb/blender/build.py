# Builds orb.blend from nothing: a dark egg-shaped orb on a cream backdrop,
# drawn in 4-pixel dots, with a light that circles the orb once in 8 seconds.
#
# Run it from this folder with:
#   blender --background --python build.py
#
# Every number you might want to play with sits in the block of constants
# below. Change one, run the line above again, and open orb.blend.

import math
import os

import bpy
from mathutils import Vector


# --- Picture -----------------------------------------------------------------

WIDTH = 3840                # the still is 3840 x 2160 pixels
HEIGHT = 2160
DOT = 4                     # each dot is a 4 x 4 pixel square
FPS = 24
LOOP_SECONDS = 8            # the light goes round once in this time

CREAM = "#FFFCF0"           # Flexoki paper
INK = "#100F0F"             # Flexoki black

# --- Scene, in Blender units ------------------------------------------------
#
# The camera is orthographic (no perspective) and 38.4 units wide, so one
# unit is exactly 100 pixels of the 3840-pixel picture. The camera looks
# along +Y, so X is left-right on screen and Z is up-down.

PIXELS_PER_UNIT = 100

# Where the orb sits and how big it is, measured from the still
# (pixel position of its centre, half-widths in pixels, tilt in degrees).
ORB_CENTRE_PX = (1873.7, 985.7)
ORB_HALF_WIDTH_PX = 313.6      # along its long axis
ORB_HALF_HEIGHT_PX = 279.6     # along its short axis
ORB_HALF_DEPTH_PX = 120.8      # towards the camera
ORB_TILT_DEG = 48.0            # positive tilts the long axis up to the right
# The still's orb is an egg, not a perfect oval: one end is fatter than the
# other. A Simple Deform modifier set to Taper makes the sphere thicker
# towards one end. 0 is no taper; negative makes the left end the fat one.
ORB_TAPER = -0.335

# Where the light comes from at frame 1, as a direction seen from the orb,
# in Blender's axes: X is right, Y is depth (negative is towards the camera)
# and Z is up. The still is lit from below and a little to the right.
LIGHT_DIRECTION = (1.053, -1.0, -3.696)

# How shading turns into darkness. Brightness 0 (facing away from the light)
# becomes DARK_MAX, brightness 1 (facing the light) becomes DARK_MIN.
DARK_MAX = 0.759
DARK_MIN = -0.375


# --- Small helpers -----------------------------------------------------------

def hex_to_linear(hex_colour):
  # Blender's colour values are "scene linear", not the sRGB numbers in a hex
  # code, so convert, or the cream would come out the wrong shade.
  values = []
  for i in (1, 3, 5):
    c = int(hex_colour[i:i + 2], 16) / 255
    if c <= 0.04045:
      values.append(c / 12.92)
    else:
      values.append(((c + 0.055) / 1.055) ** 2.4)
  return (*values, 1.0)


def pixels_to_world(px, py):
  # Picture pixels (from the top-left corner) to a point on the X-Z plane.
  x = (px - WIDTH / 2) / PIXELS_PER_UNIT
  z = (HEIGHT / 2 - py) / PIXELS_PER_UNIT
  return Vector((x, 0.0, z))


def loop_frames():
  return FPS * LOOP_SECONDS


# --- Steps ---------------------------------------------------------------------

def empty_the_file():
  # Start from a truly empty file: no default cube, camera or light.
  bpy.ops.wm.read_factory_settings(use_empty=True)


def set_up_scene():
  scene = bpy.context.scene
  scene.name = "Orb"

  render = scene.render
  # EEVEE draws with the graphics chip and is quick for a scene this simple.
  render.engine = "BLENDER_EEVEE"
  render.resolution_x = WIDTH
  render.resolution_y = HEIGHT
  render.resolution_percentage = 100
  # One sample per pixel and the narrowest pixel filter, so every pixel is
  # exactly cream or exactly ink and the dots keep hard edges.
  scene.eevee.taa_render_samples = 1
  scene.eevee.taa_samples = 1
  render.filter_size = 0.0
  # Blender adds faint noise to every picture it saves to hide colour banding.
  # Turn it off so the cream stays one exact colour.
  render.dither_intensity = 0.0

  # "Standard" shows colours as they are. The default (AgX) is made for
  # photos and would turn the cream grey and the ink lighter.
  scene.view_settings.view_transform = "Standard"
  scene.view_settings.look = "None"

  scene.frame_start = 1
  scene.frame_end = loop_frames()
  render.fps = FPS
  scene.frame_set(1)
  return scene


def make_world(scene):
  # The world is what you would see behind everything. The backdrop hides it,
  # and it is black so it adds no light of its own to the orb.
  world = bpy.data.worlds.new("Empty Sky")
  background = world.node_tree.nodes["Background"]
  background.inputs["Color"].default_value = (0, 0, 0, 1)
  background.inputs["Strength"].default_value = 0.0
  scene.world = world


def make_camera(scene):
  data = bpy.data.cameras.new("Camera")
  data.type = "ORTHO"
  data.ortho_scale = WIDTH / PIXELS_PER_UNIT
  data.clip_start = 0.1
  data.clip_end = 100.0
  camera = bpy.data.objects.new("Camera", data)
  camera.location = (0.0, -30.0, 0.0)
  # Turn the camera from looking down (its resting pose) to looking along +Y.
  camera.rotation_euler = (math.radians(90), 0.0, 0.0)
  scene.collection.objects.link(camera)
  scene.camera = camera
  return camera


def make_flat_material(name, hex_colour):
  # Emission only: the surface shows this colour exactly, whatever the light.
  material = bpy.data.materials.new(name)
  nodes = material.node_tree.nodes
  nodes.clear()
  emission = nodes.new("ShaderNodeEmission")
  emission.name = emission.label = "Flat Colour"
  emission.inputs["Color"].default_value = hex_to_linear(hex_colour)
  output = nodes.new("ShaderNodeOutputMaterial")
  output.name = output.label = "Material Output"
  output.location = (250, 0)
  material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
  return material


def make_backdrop(scene):
  bpy.ops.mesh.primitive_plane_add(size=1.0)
  backdrop = bpy.context.active_object
  backdrop.name = "Backdrop"
  backdrop.data.name = "Backdrop"
  # Stand the plane up behind the orb and make it larger than the frame.
  backdrop.location = (0.0, 10.0, 0.0)
  backdrop.rotation_euler = (math.radians(90), 0.0, 0.0)
  backdrop.scale = (WIDTH / PIXELS_PER_UNIT * 1.5, HEIGHT / PIXELS_PER_UNIT * 1.5, 1.0)
  backdrop.data.materials.append(make_flat_material("Cream Paper", CREAM))
  backdrop.visible_shadow = False
  return backdrop


def make_bayer_image():
  # The dot pattern: a 4 x 4 "ordered dither" (Bayer) matrix. Each of the 16
  # cells holds a threshold between 0 and 1. A spot of the orb turns to ink
  # when its darkness is above the threshold of the cell it falls on, so
  # darker spots switch on more of the 16 cells.
  bayer = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
  ]
  image = bpy.data.images.new("Bayer 4x4", width=4, height=4, alpha=False, float_buffer=True)
  image.colorspace_settings.name = "Non-Color"
  pixels = []
  for row in range(4):           # Blender stores image rows bottom first
    for column in range(4):
      # The columns are shifted by two so the pattern lines up with the still.
      value = (bayer[row][(column + 2) % 4] + 0.5) / 16
      pixels += [value, value, value, 1.0]
  image.pixels = pixels
  image.pack()                   # keep the image inside orb.blend
  return image


def add_node(nodes, kind, name, location, frame=None):
  node = nodes.new(kind)
  node.name = node.label = name
  node.location = location
  if frame is not None:
    node.parent = frame
  return node


def add_frame(nodes, name):
  frame = nodes.new("NodeFrame")
  frame.name = frame.label = name
  frame.label_size = 24
  return frame


def make_dot_material():
  material = bpy.data.materials.new("Orb Dots")
  tree = material.node_tree
  nodes = tree.nodes
  links = tree.links
  nodes.clear()

  # 1. How lit is each spot? A plain white Diffuse surface lit by the sun,
  #    turned into a number by Shader to RGB (EEVEE only), then flipped into
  #    a darkness value: 1 is full ink, 0 is bare paper.
  lighting = add_frame(nodes, "1. Light becomes darkness")
  diffuse = add_node(nodes, "ShaderNodeBsdfDiffuse", "Lit Surface", (-900, 300), lighting)
  diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
  to_rgb = add_node(nodes, "ShaderNodeShaderToRGB", "Shading As Colour", (-700, 300), lighting)
  darkness = add_node(nodes, "ShaderNodeMapRange", "Darkness", (-500, 300), lighting)
  darkness.inputs["From Min"].default_value = 0.0
  darkness.inputs["From Max"].default_value = 1.0
  darkness.inputs["To Min"].default_value = DARK_MAX
  darkness.inputs["To Max"].default_value = DARK_MIN
  darkness.clamp = True

  # 2. Which dot cell is this pixel in? "Window" gives the position on the
  #    rendered picture from 0 to 1. The Mapping node scales that so one
  #    repeat of the 4 x 4 Bayer image covers 16 x 16 pixels, giving 4-pixel
  #    cells. Closest interpolation keeps each cell one solid value.
  pattern = add_frame(nodes, "2. Dot pattern on the screen")
  coords = add_node(nodes, "ShaderNodeTexCoord", "Screen Position", (-1100, -100), pattern)
  grid = add_node(nodes, "ShaderNodeMapping", "Dot Grid", (-900, -100), pattern)
  grid.vector_type = "POINT"
  repeat = DOT * 4
  grid.inputs["Scale"].default_value = (WIDTH / repeat, HEIGHT / repeat, 1.0)
  # Shift the grid down two pixels so the cells land where the still has them.
  grid.inputs["Location"].default_value = (0.0, -2.0 / repeat, 0.0)
  bayer = add_node(nodes, "ShaderNodeTexImage", "Bayer Thresholds", (-700, -100), pattern)
  bayer.image = make_bayer_image()
  bayer.interpolation = "Closest"
  bayer.extension = "REPEAT"

  # 3. Ink or paper? Ink where the darkness beats the cell's threshold.
  colours = add_frame(nodes, "3. Two colours")
  compare = add_node(nodes, "ShaderNodeMath", "Ink Or Paper", (-250, 150), colours)
  compare.operation = "GREATER_THAN"
  mix = add_node(nodes, "ShaderNodeMix", "Paper And Ink", (-50, 150), colours)
  mix.data_type = "RGBA"
  mix.inputs["A"].default_value = hex_to_linear(CREAM)
  mix.inputs["B"].default_value = hex_to_linear(INK)
  # Emission shows the chosen colour as is, so the sun never tints it.
  emit = add_node(nodes, "ShaderNodeEmission", "Flat Colour", (150, 150), colours)
  output = add_node(nodes, "ShaderNodeOutputMaterial", "Material Output", (350, 150))

  links.new(diffuse.outputs["BSDF"], to_rgb.inputs["Shader"])
  links.new(to_rgb.outputs["Color"], darkness.inputs["Value"])
  links.new(coords.outputs["Window"], grid.inputs["Vector"])
  links.new(grid.outputs["Vector"], bayer.inputs["Vector"])
  links.new(darkness.outputs["Result"], compare.inputs[0])
  links.new(bayer.outputs["Color"], compare.inputs[1])
  links.new(compare.outputs["Value"], mix.inputs["Factor"])
  links.new(mix.outputs["Result"], emit.inputs["Color"])
  links.new(emit.outputs["Emission"], output.inputs["Surface"])
  return material


def make_orb(scene):
  # A UV sphere of radius 1, then stretched into an egg with Scale and tilted
  # with Rotation. Smooth shading hides the facets.
  bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
  orb = bpy.context.active_object
  orb.name = "Orb"
  orb.data.name = "Orb"
  bpy.ops.object.shade_smooth()
  # Modifiers change a shape without touching its saved vertices, and can be
  # switched off or edited later in the Properties editor (the wrench tab).
  egg = orb.modifiers.new("Egg Shape", "SIMPLE_DEFORM")
  egg.deform_method = "TAPER"
  egg.deform_axis = "X"
  egg.factor = ORB_TAPER
  orb.location = pixels_to_world(*ORB_CENTRE_PX)
  orb.scale = (
    ORB_HALF_WIDTH_PX / PIXELS_PER_UNIT,
    ORB_HALF_DEPTH_PX / PIXELS_PER_UNIT,
    ORB_HALF_HEIGHT_PX / PIXELS_PER_UNIT,
  )
  # Turning about Y (the camera's line of sight) tilts it on screen.
  # Negative Y rotation raises the right-hand end as seen by the camera.
  orb.rotation_euler = (0.0, math.radians(-ORB_TILT_DEG), 0.0)
  orb.data.materials.append(make_dot_material())
  return orb


def make_light(scene, orb):
  # The light hangs off an empty at the orb's centre. Turning the empty turns
  # the light around the orb, which is how the animation works.
  pivot = bpy.data.objects.new("Light Pivot", None)
  pivot.empty_display_type = "SPHERE"
  pivot.empty_display_size = 0.5
  pivot.location = orb.location
  scene.collection.objects.link(pivot)

  data = bpy.data.lights.new("Sun", type="SUN")
  # Blender divides a sun's strength by pi for a plain diffuse surface, so a
  # strength of pi makes a surface facing the light exactly 1.0 bright.
  data.energy = math.pi
  data.use_shadow = False        # the orb is convex, so shadows add nothing
  sun = bpy.data.objects.new("Sun", data)
  direction = Vector(LIGHT_DIRECTION).normalized()
  # A sun shines along its own -Z axis, so point its +Z back at where the
  # light comes from. Its position does not matter to a sun; it is placed
  # out along that direction only so you can see it in the viewport.
  sun.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
  sun.location = direction * 6.0
  sun.parent = pivot
  scene.collection.objects.link(sun)
  return pivot, sun


def animate_light(pivot):
  # Two keyframes: turned 0 degrees at frame 1 and a full turn one loop later.
  # Frame (loop + 1) is not rendered; it equals frame 1, so the loop is seamless.
  frames = loop_frames()
  pivot.rotation_euler = (0.0, 0.0, 0.0)
  pivot.keyframe_insert("rotation_euler", index=1, frame=1)
  pivot.rotation_euler = (0.0, math.radians(-360), 0.0)
  pivot.keyframe_insert("rotation_euler", index=1, frame=frames + 1)
  pivot.rotation_euler = (0.0, 0.0, 0.0)

  action = pivot.animation_data.action
  action.name = "Light Goes Round"
  # Even speed all the way round instead of easing in and out.
  for fcurve in action_fcurves(action):
    for key in fcurve.keyframe_points:
      key.interpolation = "LINEAR"


def action_fcurves(action):
  # Since Blender 4.4 an action keeps its curves in layers, strips and
  # "channelbags", one per slot (the thing it animates).
  curves = []
  for layer in action.layers:
    for strip in layer.strips:
      for channelbag in strip.channelbags:
        curves.extend(channelbag.fcurves)
  return curves


def open_in_camera_view():
  # When the file opens in Blender's window, look through the camera. The
  # window layout (the "screens") comes from Blender's start-up file and is
  # saved with orb.blend. Rendered shading is asked for too, but Blender may
  # reset it to Solid on opening; press Z and pick Rendered if it does.
  for screen in bpy.data.screens:
    for area in screen.areas:
      if area.type == "VIEW_3D":
        for space in area.spaces:
          if space.type == "VIEW_3D":
            space.region_3d.view_perspective = "CAMERA"
            space.shading.type = "RENDERED"


def main():
  empty_the_file()
  scene = set_up_scene()
  make_world(scene)
  make_camera(scene)
  make_backdrop(scene)
  orb = make_orb(scene)
  pivot, _sun = make_light(scene, orb)
  animate_light(pivot)
  open_in_camera_view()
  scene.frame_set(1)

  here = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(here, "orb.blend")
  bpy.ops.wm.save_as_mainfile(filepath=path)
  print(f"Saved {path}")


main()
