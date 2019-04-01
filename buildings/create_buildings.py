import psycopg2
import os, sys
import bpy, bmesh
from math import *
from mathutils import Vector
import numpy as np

C = bpy.context
D = bpy.data

dir = os.path.dirname(D.filepath)
if dir not in sys.path:
    sys.path.append(dir)
# import django
# from landscapelab.settings.local_settings import GDAL_LIBRARY_PATH
# from buildings.models import BuildingLayout

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
    vertices = np.pad(np.asarray(vertices), (0, 1), 'constant')[:-1]

    clear_scene()
    building = createBaseMesh(name, vertices)

    if texture is not None:
        building_mat = create_material(texture)
        building.data.materials.append(building_mat)
        set_uvs(building)

    bpy.ops.wm.collada_export(filepath=os.path.join(out_path, name+'.dae'), use_texture_copies=False)
    # bpy.ops.wm.collada_export(filepath=os.path.join(out_path, name+'.dae'))


def clear_scene():
    for m in D.meshes:
        D.meshes.remove(m)
    for o in D.objects:
        D.objects.remove(o)
    for l in D.lights:
        D.lights.remove(l)
    for i in D.images:
        D.images.remove(i)
    for m in D.materials:
        D.materials.remove(m)
    for t in D.textures:
        D.textures.remove(t)
    for c in D.cameras:
        D.cameras.remove(c)


def createBaseMesh(name, vertices):
    # instantiate mesh
    mesh = D.meshes.new('mesh')
    building = D.objects.new(name, mesh)
    C.scene.collection.objects.link(building)

    mesh = building.data
    bm = bmesh.new()

    # add vertices to create bottom face
    vert = []
    for v in vertices:
        vert.append(bm.verts.new(v))

    layout = bm.faces.new(vert) # create bottom face
    roof = bmesh.ops.extrude_face_region(bm, geom=[layout]) # extrude face to get roof
    bmesh.ops.translate(bm, vec=Vector((0, 0, 5)), verts=[v for v in roof["geom"] if isinstance(v,bmesh.types.BMVert)]) # move roof up
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces) # correct face normals

    # finish mesh
    bm.to_mesh(mesh)
    bm.free()

    return building


def set_uvs(object):
    C.view_layer.objects.active = object
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = object.data
    bm = bmesh.from_edit_mesh(mesh)

    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        if face_is_wall(f):
            l = f.loops
            [mx, my, mz] = face_mean(f)
            [upper, lower] = [[],[]]

            # split in upper and lower parts
            for v in l:
                if v.vert.co.z > mz:
                    upper.append(v)
                else:
                    lower.append(v)

            # decide how often the texture should repeat itself horizontally
            columns = max(1, vertex_distance(upper[0].vert,lower[0].vert)//3)

            # find vertex below upper[0] and assign UVs accordingly
            if vertex_distance(upper[0].vert,lower[0].vert) < vertex_distance(upper[0].vert,lower[1].vert):
                upper[0][uv_layer].uv = Vector((0,1))
                lower[0][uv_layer].uv = Vector((0,0))
                upper[1][uv_layer].uv = Vector((columns,1))
                lower[1][uv_layer].uv = Vector((columns,0))
            else:
                upper[0][uv_layer].uv = Vector((0,1))
                lower[1][uv_layer].uv = Vector((0,0))
                upper[1][uv_layer].uv = Vector((columns,1))
                lower[0][uv_layer].uv = Vector((columns,0))

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


def create_material(texture):

    mat = D.materials.new(name=texture)
    mat.use_nodes = True
    tImg =  mat.node_tree.nodes.new('ShaderNodeTexImage')
    tImg.image = D.images.load(os.path.join(tex_dir, texture))
    diff = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(diff.inputs['Base Color'], tImg.outputs['Color'])

    return mat


def face_is_wall(f):
    if len(f.loops) is 4:
        mean_z = face_mean(f)[2]
        if abs(f.loops[0].vert.co.z - mean_z) > 0.1:
            return True
    return False


def face_mean(f):
    mean = np.zeros(3)
    if len(f.loops) > 0:
        for l in f.loops:
            c = l.vert.co
            mean = np.add(mean,np.array([c.x,c.y,c.z]))
        mean = np.divide(mean, len(f.loops))
    return mean.tolist()


def vertex_distance(v1, v2):
    c1 = v1.co
    c2 = v2.co
    return sqrt(pow(c1.x - c2.x, 2) + pow(c1.y - c2.y, 2) + pow(c1.z - c2.z, 2))


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
