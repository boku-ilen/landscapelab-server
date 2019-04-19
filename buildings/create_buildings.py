import psycopg2
import os, sys
import bpy, bmesh
from math import *
from mathutils import Vector, Matrix
import numpy as np
# import django
# from landscapelab.settings.local_settings import GDAL_LIBRARY_PATH
# from buildings.models import BuildingLayout

C = bpy.context
D = bpy.data

ASSET_TABLE_NAME = "public.assetpos_asset"
ASSET_POSITIONS_TABLE_NAME = "public.assetpos_assetpositions"
BUILDING_FOOTPRINT_TABLE_NAME = "public.buildings_buildingfootprint"

BUILDING_TEXTURE_FOLDER = 'facade'
ROOF_TEXTURE_FOLDER = 'roof'

dir = os.path.dirname(D.filepath)
if dir not in sys.path:
    sys.path.append(dir)

# TODO get db connection data from django server somehow
db = {
    'NAME': 'retour',
    'USER': 'postgres',
    'PASSWORD': 'retour4321',
    'HOST': 'localhost',
    'PORT': '5432'
}

TEXTURE_DIRECTORY = os.path.join(os.getcwd(), 'landscapelab', 'resources', 'buildings', 'textures', 'no_rights')
if not os.path.exists(TEXTURE_DIRECTORY):
    os.makedirs(TEXTURE_DIRECTORY)

# TODO get out path from django server somehow
OUTPUT_DIRECTORY = os.path.join(os.getcwd(), 'buildings', 'out')
if not os.path.exists(str(OUTPUT_DIRECTORY)):
    os.makedirs(OUTPUT_DIRECTORY)


# takes name footprint-vertices, building-height and texture name (optional)
# to create a new building and export it
def create_building(name, vertices, height, textures):

    # clear the scene and add z component to the received 2d vertices
    clear_scene()
    vertices = np.pad(np.asarray(vertices), (0, 1), 'constant')[:-1]

    # crate the base of the building and the roof
    building = create_base_building_mesh(name, vertices, height, textures)
    roof = create_roof(name, vertices, height, textures)

    # export the scene to a collada file
    bpy.ops.wm.collada_export(filepath=os.path.join(OUTPUT_DIRECTORY, name + '.dae'), use_texture_copies=False)
    # bpy.ops.wm.collada_export(filepath=os.path.join(out_path, name+'.dae'))


# clears unwanted elements from the default scene
# and the leftovers from previous building exports
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


# creates a footprint and extrudes it upwards to get a cylindrical base of the building
def create_base_building_mesh(name, vertices, height, textures):

    # create the building footprint
    [building, mesh, bm, footprint] = create_footprint(name, vertices)

    # extrude face to get roof
    roof = bmesh.ops.extrude_face_region(bm, geom=[footprint])

    # move the roof upwards, recalculate the face normals and finish edit
    bmesh.ops.translate(bm, vec=Vector((0, 0, height)), verts=[v for v in roof["geom"] if isinstance(v, bmesh.types.BMVert)]) # move roof up
    bmesh.ops.recalc_face_normals(bm, faces = bm.faces)
    finish_edit(bm, mesh)

    # add textures if possible
    if BUILDING_TEXTURE_FOLDER in textures:
        # create and add material
        building_mat = create_material(textures[BUILDING_TEXTURE_FOLDER])
        building.data.materials.append(building_mat)

        # set wall UVs
        set_wall_uvs(building)

    return building


# creates a decently looking roof on any building
# uses neat_roof() on buildings with 4 vertex footprint
def create_roof(name, vertices, height, textures):

    # create base face
    [roof, mesh, bm, footprint] = create_footprint(name+"_roof", vertices)

    # if footprint has 4 vertices use neat_roof()
    # otherwise use inset operator and push resulting face up
    if len(bm.verts) is 4:
        neat_roof(footprint, bm)
    else:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        bmesh.ops.inset_individual(bm, faces=[footprint], thickness = shortest_edge(bm.verts) // 2)

        # adjust lookup-table and find new top face
        bm.faces.ensure_lookup_table()
        top = bm.faces[0]

        # move top face up
        bmesh.ops.translate(bm, vec=Vector([0, 0, 2]), verts=[v for v in top.verts])

    # translate the roof to the top of the base building and finish edit
    bmesh.ops.translate(bm, vec=Vector([0, 0, height]), verts=bm.verts)
    finish_edit(bm, mesh)

    # add textures if possible
    if ROOF_TEXTURE_FOLDER in textures:
        # create and add material
        roof_mat = create_material(textures[ROOF_TEXTURE_FOLDER])
        roof.data.materials.append(roof_mat)

        # set wall UVs
        # NOTE: for buildings with 4 vertices this will work perfectly
        # for other buildings this will distort the UVs
        # for pattern textures this is hardly noticable
        # but if for example a window is on the image, it will be noticably distorted
        # TODO create suitable function for buildings with more than 4 vertices
        set_wall_uvs(roof)

    return roof


# creates a new object and adds the footprint of a building as a face
# returns all necessary elements to continue editing the object
# NOTE: when caller is finished editing the footprint they should call finish_edit(bm, mesh)
def create_footprint(name, vertices):

    # instantiate mesh
    mesh = D.meshes.new('mesh')
    generated_object = D.objects.new(name, mesh)
    C.scene.collection.objects.link(generated_object)

    # set footprint active and enable edit mode
    C.view_layer.objects.active = generated_object
    bpy.ops.object.mode_set(mode='EDIT')

    # setup mesh and bm
    mesh = generated_object.data
    bm = bmesh.new()

    # add vertices to create footprint
    vert = []
    for v in vertices:
        vert.append(bm.verts.new(v))

    footprint = bm.faces.new(vert)

    return [generated_object, mesh, bm, footprint]


# updates mesh, frees bm and returns to object mode
def finish_edit(bm ,mesh):

    bpy.ops.object.mode_set(mode='OBJECT')
    bm.to_mesh(mesh)
    bm.free()


# code from https://blender.stackexchange.com/questions/14136/trying-to-create-a-script-that-makes-roofs-on-selected-boxes
# only works on buildings with 4 vertex footprint
# sets a neat looking roof on top of the building
def neat_roof(face, bm):

    if len(face.verts) == 4:
        ret = bmesh.ops.extrude_face_region(bm, geom=[face])
        vertices = [element for element in ret['geom'] if isinstance(element, bmesh.types.BMVert)]
        faces = [element for element in ret['geom'] if isinstance(element, bmesh.types.BMFace)]
        bmesh.ops.translate(bm, vec=face.normal * 0.7, verts=vertices)

        e1, e2, e3, e4 = faces[0].edges
        if (e1.calc_length() + e3.calc_length()) < (e2.calc_length() + e4.calc_length()):
            edges = [e1, e3]
        else:
            edges = [e2, e4]
        bmesh.ops.collapse(bm, edges=edges)


# sets the uv coordinates for the wall faces of any general cylinder
def set_wall_uvs(object):

    # scene setup
    C.view_layer.objects.active = object
    bpy.ops.object.mode_set(mode='EDIT')

    # mesh setup
    mesh = object.data
    bm = bmesh.from_edit_mesh(mesh)

    # convenience variable
    uv_layer = bm.loops.layers.uv.verify()

    # iterates through all faces of the object
    # and sets the uv-coordinates for all wall faces
    for f in bm.faces:
        if face_is_wall(f):
            mean_z_value = face_mean(f)[2]
            upper, lower = [], []

            # split vertices in upper and lower parts
            for v in f.loops:
                if v.vert.co.z > mean_z_value:
                    upper.append(v)
                else:
                    lower.append(v)

            # decide how often the texture should repeat itself horizontally
            columns = max(float(1), vertex_distance(upper[0].vert, upper[1].vert) // 3)

            # find vertex below upper[0] and assign UVs accordingly
            if vertex_distance(upper[0].vert, lower[0].vert) < vertex_distance(upper[0].vert, lower[1].vert):
                upper[0][uv_layer].uv = Vector((0, 1))
                lower[0][uv_layer].uv = Vector((0, 0))
                upper[1][uv_layer].uv = Vector((columns, 1))
                lower[1][uv_layer].uv = Vector((columns, 0))
            else:
                upper[0][uv_layer].uv = Vector((0, 1))
                lower[1][uv_layer].uv = Vector((0, 0))
                upper[1][uv_layer].uv = Vector((columns, 1))
                lower[0][uv_layer].uv = Vector((columns, 0))

    # update mesh and return to object mode
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


# creates a new material with defined texture and returns it
def create_material(texture_name: str):

    # create material
    mat = D.materials.new(name=texture_name)
    mat.use_nodes = True

    # create and set texture_image with
    texture_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture_image.image = D.images.load(os.path.join(TEXTURE_DIRECTORY, texture_name))

    # get shader node of material and link texture to it's color property
    diff = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(diff.inputs['Base Color'], texture_image.outputs['Color'])

    return mat


# returns true if the specified face is a wall with 4 vertices
def face_is_wall(f):

    if len(f.loops) is 4:
        mean_z = face_mean(f)[2]

        # determines if a face is a wall by checking
        # if the z distance of the first vertex to the face mean
        if abs(f.loops[0].vert.co.z - mean_z) > 0.1:
            return True

    return False


# calculates the mean point of
def face_mean(f):

    mean = np.zeros(3)
    if len(f.loops) > 0:
        for l in f.loops:
            c = l.vert.co
            mean = np.add(mean, np.array([c.x,c.y,c.z]))
        mean = np.divide(mean, len(f.loops))

    return mean.tolist()


# calculates the euclidean distance between two vertices
def vertex_distance(v1, v2):
    c1 = v1.co
    c2 = v2.co
    return sqrt(pow(c1.x - c2.x, 2) + pow(c1.y - c2.y, 2) + pow(c1.z - c2.z, 2))


# takes the vertices of a polygon in a list, computes the shortest edge and returns it's length
def shortest_edge(vertices):
    min_edge = float("inf")

    # iterates through all the vertices
    # calculates the distance to the next vertex
    # uses % operator in order to loop around and also consider the edge from last to first vertex
    for i in range(len(vertices)):
        d = vertex_distance(vertices[i], vertices[(i + 1) % len(vertices)])
        if d < min_edge:
            min_edge = d

    return d


# scans the texture folder
# creates a dictionary of lists where each subdirectory is a key
# each list contains all jpg image names of the corresponding direcotry
def get_images():

    img_ext = 'jpg'
    images = {}
    dirs = os.listdir(TEXTURE_DIRECTORY)

    # iterate through all directories
    for dir in dirs:
        dir_path = os.path.join(TEXTURE_DIRECTORY, dir)
        if os.path.isdir(dir_path):

            # add directory name as key to images
            images[dir] = []

            # add all files with correct extension to images[dir]
            files = os.listdir(dir_path)
            for file in files:
                if file.endswith(img_ext):
                    images[dir].append(file)

    return images


def main(arguments):

    images = get_images()
    conn = psycopg2.connect(host=db['HOST'], database=db['NAME'], user=db['USER'],
                            password=db['PASSWORD'], port=db['PORT'])
    cur = conn.cursor()

    # goes through each argument
    # fetches the data for specified building
    # creates and exports it
    for a in arguments:

        # get building name TODO maybe get building height as well if it is stored in db
        # FIXME table name is subject to change, do not hardcode, maybe get data in different, more reliable way
        cur.execute('SELECT name FROM {} WHERE id IN '
                    '(SELECT asset_id FROM {} WHERE id IN '
                    '(SELECT asset_id FROM {} WHERE id = {}));'
                    .format(
                        ASSET_TABLE_NAME,
                        ASSET_POSITIONS_TABLE_NAME,
                        BUILDING_FOOTPRINT_TABLE_NAME,
                        a
                        )
                    )

        name = cur.fetchone()[0]

        # get building vertices
        cur.execute('SELECT ST_x(geom), ST_y(geom) FROM'
                    '(SELECT (St_DumpPoints(vertices)).geom FROM {} where id = {}) as foo;'
                    .format(BUILDING_FOOTPRINT_TABLE_NAME, a)
                    )

        vertices = cur.fetchall()

        # delete last vertex since it is duplicate of first
        del vertices[-1]

        # select textures from the image pool
        textures = {}
        for key, value in images.items():
            if len(value) > 0:
                textures[key] = os.path.join(key, value[int(a) % len(value)])

        # create and export the building
        create_building(name, vertices, 5, textures)

    cur.close()
    conn.close()


if __name__ == '__main__':
    arg = sys.argv
    arg = arg[arg.index('--') + 1:]
    main(arg)
