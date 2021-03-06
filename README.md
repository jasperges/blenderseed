## blenderseed

**blenderseed** is a Blender-to-[appleseed](http://appleseedhq.net) exporter for [Blender](https://www.blender.org/) 2.71 and later.

* [**Download** the latest release](https://github.com/appleseedhq/blenderseed/releases)
* [**Read** installation instructions](https://github.com/appleseedhq/blenderseed/wiki/Installation)
* [**Report** bugs and suggest features](https://github.com/appleseedhq/blenderseed/issues)

**blenderseed** includes support for the following features of appleseed:  
* Pinhole, thin lens (supports physically correct depth of field), and spherical camera models
* Camera, transformation and deformation motion blur
* Particle / instance motion blur
* Instancing (dupliverts / duplifaces / "emitter" and "hair" type object and group particle systems)
* BSDF layered materials
* Normal / bump mapping
* Alpha mapping
* Mesh lights
* Point, directional, and sun lights
* Spot lights (supports textures)
* Physical sun/sky
* Gradient, constant, mirror ball map and latitude-longitude map environment models

**blenderseed** also supports 
* Node-based material creation (with Blender's node editor)
* Hair path particle systems exported as geometry
* Export to appleseed.studio or rendering within Blender's image editor
* Selective geometry export (for faster re-export and re-rendering of scenes)
* Material preview rendering
