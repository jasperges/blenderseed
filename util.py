#
# This source file is part of appleseed.
# Visit http://appleseedhq.net/ for additional information and resources.
#
# This software is released under the MIT license.
#
# Copyright (c) 2013 Franz Beaune, Joel Daniels, Esteban Tovagliari.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import bpy
import os
import multiprocessing
from extensions_framework import util as efutil
from shutil import copyfile
from math import tan, atan, degrees
from . import bl_info

#------------------------------------
# Generic utilities and settings.
#------------------------------------
sep = os.sep

thread_count = multiprocessing.cpu_count()

EnableDebug = True

# Addon directory.
addon_paths = bpy.utils.script_paths( "addons")
if 'blenderseed' in os.listdir( addon_paths[0]):
    addon_dir = os.path.join( addon_paths[0], 'blenderseed')
else:
    addon_dir = os.path.join( addon_paths[1], 'blenderseed')

version = str(bl_info['version'][1]) + "." + str(bl_info['version'][2])

def strip_spaces( name):
    return ('_').join( name.split(' '))

def join_names_underscore( name1, name2):
    return ('_').join( (strip_spaces( name1), strip_spaces( name2)))

def join_params( params, directive):
    return ('').join( (('').join( params), directive))

def filter_params( params):
    filter_list = []
    for p in params:
        if p not in filter_list:
            filter_list.append( p)
    return filter_list
        
def get_timestamp():
    now = datetime.datetime.now()
    return "%d-%d-%d %d:%d:%d\n" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
    
def realpath(path):
    return os.path.realpath(efutil.filesystem_path(path))

def inscenelayer(object, scene):
    for i in range(len(object.layers)):
        if object.layers[i] == True and scene.layers[i] == True:
            return True
        else:
            continue
        
def do_export(obj, scene):
    return not obj.hide_render and obj.type in ('MESH', 'SURFACE', 'META', 'TEXT', 'CURVE', 'LAMP') and inscenelayer(obj, scene)

def debug( *args):
    msg = ' '.join(['%s'%a for a in args])
    global EnableDebug
    if EnableDebug:    
        print( "DEBUG:" ,msg)

def asUpdate( *args):
    msg = ' '.join(['%s'%a for a in args])
    print( "appleseed:" ,msg)


#--------------------------------------------------------------------------------------------------
# Write a mesh object to disk in Wavefront OBJ format.
#--------------------------------------------------------------------------------------------------

def get_array2_key( v):
    return int( v[0] * 1000000), int( v[1] * 1000000)

def get_vector2_key( v):
    w = v * 1000000
    return int( w.x), int( w.y)

def get_vector3_key( v):
    w = v * 1000000
    return w.x, w.y, w.z

def write_mesh_to_disk( mesh, mesh_faces, mesh_uvtex, filepath):
    with open( filepath, "w") as output_file:
        # Write file header.
        output_file.write( "# File generated by %s %s.\n" % ( "render_appleseed", version))

        vertices = mesh.vertices
        faces = mesh_faces
        uvtex = mesh_uvtex
        uvset = uvtex.active.data if uvtex else None

        # Sort the faces by material.
        sorted_faces = [( index, face) for index, face in enumerate(faces)]
        sorted_faces.sort( key = lambda item: item[1].material_index)

        # Write vertices.
        output_file.write( "# %d vertices.\n" % len(vertices))
        for vertex in vertices:
            v = vertex.co
            output_file.write( "v %.15f %.15f %.15f\n" % ( v.x, v.y, v.z))

        # Deduplicate and write normals.
        output_file.write( "# Vertex normals.\n")
        normal_indices = {}
        vertex_normal_indices = {}
        face_normal_indices = {}
        current_normal_index = 0
        for face_index, face in sorted_faces:
            if face.use_smooth:
                for vertex_index in face.vertices:
                    vn = vertices[vertex_index].normal
                    vn_key = get_vector3_key(vn)
                    if vn_key in normal_indices:
                        vertex_normal_indices[vertex_index] = normal_indices[vn_key]
                    else:
                        output_file.write( "vn %.15f %.15f %.15f\n" % ( vn.x, vn.y, vn.z))

                        normal_indices[vn_key] = current_normal_index
                        vertex_normal_indices[vertex_index] = current_normal_index
                        current_normal_index += 1
            else:
                vn = face.normal
                vn_key = get_vector3_key( vn)
                if vn_key in normal_indices:
                    face_normal_indices[face_index] = normal_indices[vn_key]
                else:
                    output_file.write( "vn %.15f %.15f %.15f\n" % ( vn.x, vn.y, vn.z))
                    normal_indices[vn_key] = current_normal_index
                    face_normal_indices[face_index] = current_normal_index
                    current_normal_index += 1

        # Deduplicate and write texture coordinates.
        if uvset:
            output_file.write( "# Texture coordinates.\n")
            vt_indices = {}
            vertex_texcoord_indices = {}
            current_vt_index = 0
            for face_index, face in sorted_faces:
                assert len( uvset[face_index].uv) == len( face.vertices)
                for vt_index, vt in enumerate( uvset[face_index].uv):
                    vertex_index = face.vertices[vt_index]
                    vt_key = get_array2_key( vt)
                    if vt_key in vt_indices:
                        vertex_texcoord_indices[face_index, vertex_index] = vt_indices[vt_key]
                    else:
                        output_file.write( "vt %.15f %.15f\n" % ( vt[0], vt[1]))
                        vt_indices[vt_key] = current_vt_index
                        vertex_texcoord_indices[face_index, vertex_index] = current_vt_index
                        current_vt_index += 1

        mesh_parts = []

        # Write faces.
        output_file.write( "# %d faces.\n" % len(sorted_faces))
        current_material_index = -1
        for face_index, face in sorted_faces:
            if current_material_index != face.material_index:
                current_material_index = face.material_index
                mesh_name = "part_%d" % current_material_index
                mesh_parts.append(( current_material_index, mesh_name))
                output_file.write( "o {0}\n".format(mesh_name))
            line = "f"
            if uvset and len( uvset[face_index].uv) > 0:
                if face.use_smooth:
                    for vertex_index in face.vertices:
                        texcoord_index = vertex_texcoord_indices[face_index, vertex_index]
                        normal_index = vertex_normal_indices[vertex_index]
                        line += " %d/%d/%d" % ( vertex_index + 1, texcoord_index + 1, normal_index + 1)
                else:
                    normal_index = face_normal_indices[face_index]
                    for vertex_index in face.vertices:
                        texcoord_index = vertex_texcoord_indices[face_index, vertex_index]
                        line += " %d/%d/%d" % ( vertex_index + 1, texcoord_index + 1, normal_index + 1)
            else:
                if face.use_smooth:
                    for vertex_index in face.vertices:
                        normal_index = vertex_normal_indices[vertex_index]
                        line += " %d//%d" % ( vertex_index + 1, normal_index + 1)

                else:
                    normal_index = face_normal_indices[face_index]
                    for vertex_index in face.vertices:
                        line += " %d//%d" % ( vertex_index + 1, normal_index + 1)
            output_file.write( line + "\n")

        return mesh_parts
        

def resolution(scene):
    xr = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
    yr = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
    return xr, yr

def get_instance_materials(ob):
    obmats = []
    # Grab materials attached to object instances ...
    if hasattr(ob, 'material_slots'):
        for ms in ob.material_slots:
            obmats.append(ms.material)
    # ... and to the object's mesh data
    if hasattr(ob.data, 'materials'):
        for m in ob.data.materials:
            obmats.append(m)
    return obmats

def is_proxy(ob, scene):
    if ob.type == 'MESH' and ob.corona.is_proxy:
        if ob.corona.use_external:
            return ob.corona.external_instance_mesh != ''
        else:
            return ob.corona.instance_mesh is not None and scene.objects[ob.corona.instance_mesh].type == 'MESH'

def get_particle_matrix(ob):
    object_matrix = ob.matrix.copy()
    return object_matrix

def get_psys_instances(ob, scene):
    dupli_list = []
    if not hasattr(ob, 'modifiers'):
        return dupli_list
    for modifier in ob.modifiers:
        if modifier.type == 'PARTICLE_SYSTEM':
            psys = modifier.particle_system
            if not psys.settings.render_type in {'OBJECT', 'GROUP'}:
                continue
            ob.dupli_list_create(scene)
            for obj in ob.dupli_list:
                obj_matrix = get_particle_matrix( obj)
                # Append a list containing the matrix, and the object
                dupli_list.append([obj_matrix, obj.object])
            ob.dupli_list_clear()
    return dupli_list

def get_all_psysobs():
    obs = set()
    for settings in bpy.data.particles:
        if settings.render_type == 'OBJECT' and settings.dupli_object is not None:
            obs.add( settings.dupli_object)
        elif settings.render_type == 'GROUP' and settings.dupli_group is not None:
            obs.update( {ob for ob in settings.dupli_group.objects})
    return obs

def get_all_duplis( scene ):
    obs = set()
    for ob in scene.objects:
        if ob.parent and ob.parent.dupli_type in {'FACES', 'VERTS', 'GROUP'}:
            obs.add( ob)
    return obs
            
def get_matrix(obj):
    obj_mat = obj.matrix.copy()
    return obj_mat

def get_instances(obj_parent, scene, mblur = False):
    asr_scn = scene.appleseed
    obj_parent.dupli_list_create(scene)
    dupli_list = []
    if not mblur:
        for obj in obj_parent.dupli_list :
            obj_matrix = get_matrix( obj)
            dupli_list.append( [obj.object, obj_matrix])
    else:
        current_frame = scene.frame_current
        # Set frame for shutter open time
        scene.frame_set( current_frame, subframe = asr_scn.shutter_open)
        for obj in obj_parent.dupli_list:
            obj_matrix = obj.matrix.copy()
            dupli_list.append( [obj.object, obj_matrix])
            # Move to next frame, collect matrices
            scene.frame_set( current_frame, subframe = asr_scn.shutter_close)
            for dupli in dupli_list:
                dupli.append( obj.matrix.copy())
            # Reset to current frame
            scene.frame_set( current_frame)
    obj_parent.dupli_list_clear()
    return dupli_list

def render_emitter(ob):
    render = False
    for psys in ob.particle_systems:
        if psys.settings.use_render_emitter:
            render = True
            break
    return render

def is_psys_emitter( ob):
    emitter = False
    for mod in ob.modifiers:
        if mod.type == 'PARTICLE_SYSTEM' and mod.show_render:
            psys = mod.particle_system
            if psys.settings.render_type == 'OBJECT' and psys.settings.dupli_object is not None:
                emitter = True
                break
            elif psys.settings.render_type == 'GROUP' and psys.settings.dupli_group is not None:
                emitter = True
                break
    return emitter
    
def get_camera_matrix( camera, global_matrix):
    camera_mat = global_matrix * camera.matrix_world
    origin = camera_mat.col[3]
    forward = -camera_mat.col[2]
    up = camera_mat.col[1]
    target = origin + forward
    return origin, forward, up, target

def is_uv_img( tex):
    if tex and tex.type == 'IMAGE' and tex.image:
        return True

    return False

def ob_mblur_enabled( object, scene):
    return object.appleseed.mblur_enable and object.appleseed.mblur_type == 'object' and scene.appleseed.mblur_enable and scene.appleseed.ob_mblur

def def_mblur_enabled( object, scene):
    return object.appleseed.mblur_enable and object.appleseed.mblur_type == 'deformation' and scene.appleseed.mblur_enable and scene.appleseed.def_mblur

def calc_fov(camera_ob, width, height):
    ''' 
    Calculate horizontal FOV if rendered height is greater than rendered with
    Thanks to NOX exporter developers for this and the next solution 
    '''
    camera_angle = degrees(camera_ob.data.angle)
    if width < height:
        length = 18.0/tan(camera_ob.data.angle/2)
        camera_angle = 2*atan(18.0*width/height/length)
        camera_angle = degrees(camera_angle)
    return camera_angle