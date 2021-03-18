import bpy
import random
import logging
import os

random.seed(1337)
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')


def load_curve_svg(file_name, name, x=0, y=0, z=0, material=None):
    bpy.ops.import_curve.svg(filepath=file_name)
    collection = bpy.data.collections.get(file_name)
    if collection is None:
        return
    bevel = bpy.data.objects["Circle"]
    collection.name = name
    for i, curve in enumerate(collection.objects):
        curve.name = f"{name}_{i}"
        curve.location = [x, y, z]
        curve.data.bevel_object = bevel
        if material:
            curve.data.materials.pop()
            curve.data.materials.append(material)
    bevel.select_set(False)


def load_and_merge_svg(file_name, name="Curve", x=0, y=0, z=0, depth=0, material=None):
    bpy.ops.import_curve.svg(filepath=file_name)
    collection = bpy.data.collections.get(file_name)
    if collection is None:
        return
    collection.name = name
    main_body = None
    for i, star in enumerate(collection.objects):
        star.select_set(True)
        bpy.context.view_layer.objects.active = star
        bpy.ops.object.convert(target="MESH")
        bpy.ops.object.mode_set(mode="OBJECT")
        star.location = [x, y, z]
        star.modifiers.new(name="solid", type="SOLIDIFY")
        star.modifiers["solid"].thickness = depth
        star.modifiers["solid"].material_offset_rim = 0
        if material:
            star.data.materials.pop()
            star.data.materials.append(material)
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=f"solid")
        star.select_set(False)
        if i == 0 or not main_body:
            main_body = star
            main_body.name = name
            continue
        bpy.context.view_layer.objects.active = main_body
        main_body.select_set(True)
        main_body.modifiers.new(name="boolean", type="BOOLEAN")
        main_body.modifiers["boolean"].operation = "UNION"
        main_body.modifiers["boolean"].object = star
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier=f"boolean")
        main_body.select_set(False)
        star.select_set(True)
        bpy.context.view_layer.objects.active = star
        bpy.ops.object.delete()


def object_difference(main_body, stars):
    bpy.context.view_layer.objects.active = main_body
    main_body.select_set(True)
    main_body.modifiers.new(name="boolean", type="BOOLEAN")
    main_body.modifiers["boolean"].operation = "DIFFERENCE"
    main_body.modifiers["boolean"].object = stars
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier=f"boolean")
    main_body.select_set(False)
    stars.select_set(True)
    bpy.context.view_layer.objects.active = stars
    bpy.ops.object.delete()


log.info('Started script')

#bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.realpath(__file__)), f"starlink.blend"))
body_wood = bpy.data.materials['BodyWood']
back_wood = bpy.data.materials['BackWood']
metal_button = bpy.data.materials['MetalButton']

svg_settings = {
    'border.svg': {
        'x': -2.2, 'y': 0, 'z': -0.1, 'depth': -0.03, 'material': body_wood},
    'stars.svg': {
        'x': -2, 'y': 0, 'z': -0.01, 'depth': -0.05, 'material': metal_button},
    'constellation_stars.svg': {
        'x': -2, 'y': 0, 'z': 0, 'depth': -0.10, 'material': metal_button},
    'constellation_names.svg': {
        'x': -2, 'y': 0, 'z': 0.03, 'depth': -0.01, 'material': metal_button},
    'planets.svg': {
        'x': -2, 'y': 0, 'z': 0.03, 'depth': -0.01, 'material': metal_button},
    'moon.svg': {
        'x': -2, 'y': 0, 'z': 0.03, 'depth': -0.01, 'material': metal_button},
}

file_name = 'border.svg'
load_and_merge_svg(file_name, 'backing_plate', -2, 0, 0, -svg_settings[file_name]['depth'], back_wood)
for file_name in svg_settings:
    log.info(f"Opening {file_name}")
    settings = svg_settings[file_name]
    load_and_merge_svg(file_name, file_name.replace('.svg', ''), **settings)

file_name = 'constellation_lines.svg'
load_curve_svg(file_name, file_name.split(".")[0], -2, 0, 0.01, metal_button)
main_body = bpy.data.objects["border"]
stars = bpy.data.objects["stars"]
object_difference(main_body, stars)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'GPU'
bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

res = 1000
bpy.context.scene.render.resolution_x = int(res)
bpy.context.scene.render.resolution_y = int(res)
bpy.context.scene.render.tile_x = 500
bpy.context.scene.render.tile_y = 500

samples = 20
bpy.context.scene.cycles.seed = 1337
bpy.context.view_layer.cycles.use_denoising = True
bpy.context.scene.cycles.samples = int(samples)

render_path = './render.png'
bpy.context.scene.render.filepath = render_path
# bpy.ops.wm.save_as_mainfile(filepath="Starlink.blend")

bpy.context.scene.render.use_freestyle = True
bpy.context.scene.render.line_thickness = 0.001

log.info("Starting Render")
# bpy.ops.render.render(write_still=True)
log.info("Finished Render")
