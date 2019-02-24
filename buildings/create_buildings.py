import psycopg2
import os, sys
import bpy, bmesh
from math import *
from mathutils import Vector
import numpy as np

# TODO get db connection data from django server somehow
db = {
    'NAME': 'buildingTest2',
    'USER': 'postgres',
    'PASSWORD': 'retour4321',
    'HOST': 'localhost',
    'PORT': '5432'
}

# TODO get out path from django server somehow
out_path = os.path.join(os.getcwd(), 'buildings', 'out')

def create_building(name, vertices):
    # clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # reformat vertices
    vertices = np.pad(np.asarray(vertices), (0,1),'constant')[:-1]

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


    # export scene
    bpy.ops.wm.collada_export(filepath=os.path.join(out_path, name+'.dae'))


if __name__ == '__main__':
    arg = sys.argv
    arg = arg[arg.index('--') + 1:]

    conn = psycopg2.connect(host=db['HOST'], database=db['NAME'], user=db['USER'], password=db['PASSWORD'], port=db['PORT'])
    cur = conn.cursor()

    for a in arg:
        # get building name TODO maybe get building height as well if it is stored in db
        # FIXME table name is subject to change, do not hardcode, maybe get data in different, more reliable way
        cur.execute('SELECT name FROM public.buildings_buildinglayout where id = {};'.format(a))
        name = cur.fetchone()[0]

        # get building vertices
        cur.execute('SELECT ST_x(geom), ST_y(geom) FROM (SELECT (St_DumpPoints(vertices)).geom FROM public.buildings_buildinglayout where id = {}) as foo;'.format(a))
        vertices = cur.fetchall()
        del vertices[-1]

        # create and export the building
        create_building(name, vertices)


    cur.close()
    conn.close()
