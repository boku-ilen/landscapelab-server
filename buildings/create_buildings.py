import psycopg2
import os, sys
import bpy, bmesh
from math import *
from mathutils import Vector
import numpy as np

dir = os.path.dirname(bpy.data.filepath)
if dir not in sys.path:
    sys.path.append(dir)
#import django
#from landscapelab.settings.local_settings import GDAL_LIBRARY_PATH
#from buildings.models import BuildingLayout

# TODO get db connection data from django server somehow
db = {
    'NAME': 'retour',
    'USER': 'postgres',
    'PASSWORD': 'retour4321',
    'HOST': 'localhost',
    'PORT': '5432'
}

tex_dir = os.path.join(os.getcwd(), 'landscapelab', 'resources', 'buildings', 'textures', 'no_rights')
if not os.path.exists(tex_dir):
    os.makedirs(tex_dir)

# TODO get out path from django server somehow
out_path = os.path.join(os.getcwd(), 'buildings', 'out')
if not os.path.exists(str(out_path)):
    os.makedirs(out_path)


def create_building(name, vertices, texture=None):
    # clear scene
    bpy.ops.wm.read_factory_settings()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # reformat vertices
    vertices = np.pad(np.asarray(vertices), (0, 1), 'constant')[:-1]

    # setup scene
    mesh = bpy.data.meshes.new('mesh')
    building = bpy.data.objects.new(name, mesh)
    scene = bpy.context.scene
    scene.objects.link(building)
    scene.objects.active = building
    building.select = True

    mesh = bpy.context.object.data
    bm = bmesh.new()

    # add vertices to create bottom face
    vert = []
    for v in vertices:
        vert.append(bm.verts.new(v))

    layout = bm.faces.new(vert) # create bottom face
    roof = bmesh.ops.extrude_face_region(bm, geom=[layout]) # extrude face to get roof
    bmesh.ops.translate(bm, vec=Vector((0,0,10)), verts=[v for v in roof["geom"] if isinstance(v,bmesh.types.BMVert)]) # move roof up
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces) # correct face normals

    # finish mesh
    bm.to_mesh(mesh)
    bm.free()

    if texture is not None:
        building.data.materials.append(create_material(texture))
        set_material(building.data)

    # export scene
    bpy.ops.wm.collada_export(filepath=os.path.join(out_path, name+'.dae'), use_texture_copies=False, include_uv_textures=True, include_material_textures=True)
    # NOTE: parameter include_uv_textures and include_material_textures might be subject to change in future versions of blender and could cause issues when upgrading


def set_material(mesh):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)

    bm.faces.ensure_lookup_table()
    for f in range(len(bm.faces)):
        ph = bm.faces[f].verts[0].co.z
        for v in bm.faces[f].verts:
            if v.co.z != ph:
                bm.faces[f].select = True
                break

    bpy.ops.uv.reset()
    bpy.ops.object.mode_set(mode='OBJECT')


def create_material(texture):
    mat = bpy.data.materials.new(name=texture)
    tex = bpy.data.textures.new(texture, type='IMAGE')
    print(os.path.join(tex_dir, texture))
    tex.image = bpy.data.images.load(os.path.join(tex_dir, texture))
    mat.texture_slots.add()
    ts = mat.texture_slots[0]
    ts.texture = tex
    # ts.texture_coords = 'UV'
    # ts.uv_layer = 'default'

    return mat


def get_images():
    img_ext = 'jpg'

    images = []
    files = os.listdir(tex_dir)

    for file_id in range(len(files)):
        if files[file_id].endswith(img_ext):
            images.append(files[file_id])

    return images


def main(arguments):
    images = get_images()

    conn = psycopg2.connect(host=db['HOST'], database=db['NAME'], user=db['USER'], password=db['PASSWORD'], port=db['PORT'])
    cur = conn.cursor()

    for a in arguments:
        # get building name TODO maybe get building height as well if it is stored in db
        # FIXME table name is subject to change, do not hardcode, maybe get data in different, more reliable way
        cur.execute('SELECT name FROM public.assetpos_asset WHERE id IN (SELECT asset_id FROM public.assetpos_assetpositions WHERE id IN (SELECT asset_id FROM public.buildings_buildingfootprint WHERE id = {}));'.format(a))
        name = cur.fetchone()[0]

        # get building vertices
        cur.execute('SELECT ST_x(geom), ST_y(geom) FROM (SELECT (St_DumpPoints(vertices)).geom FROM public.buildings_buildingfootprint where id = {}) as foo;'.format(a))
        vertices = cur.fetchall()
        del vertices[-1]

        # create and export the building
        if len(images) > 0:
            create_building(name, vertices, images[int(a) % len(images)])
        else:
            create_building(name, vertices, None)

    cur.close()
    conn.close()


if __name__ == '__main__':
    arg = sys.argv
    arg = arg[arg.index('--') + 1:]
    main(arg)
