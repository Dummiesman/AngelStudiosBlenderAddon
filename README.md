# AngelStudiosBlenderAddon
A Blender add-on that handles several formats used in Angel Studios / Rockstar San Diego games from ~1999-2006

## Format chart
| Format | Import Support | Export Support | Notes |
|--------|----------------|----------------|-------|
|BMS     | Yes            |  None          |  Texture import tested for Midtown Madness 1 files. Make sure the texture files reside in the same directory as the .BMS file     |
|DLP        | Yes               | None            |  No texture import, only very basic material support       |
|MOD/XMOD        |  v1.06 through v1.10              |  v1.09 and v1.10              |       |
|BND        |  v1.01 through v1.10              |  v1.01 and v1.10              |  Only geometry type bounds are supported. There is currently no handling for box/sphere/hotdog/composite/grid     |
|SKEL        |  v1.0 and v1.01\*              |  v1.0              | v1.01 is only coincidentally supported. Animation channel information is not retained.      |
|GEO     | No            |  GEO3          |  |

## Installation
1. Grab the latest `io_scene_angelstudios.zip` here https://github.com/Dummiesman/AngelStudiosBlenderAddon/releases
2. In Blender, select Edit > Preferences
3. Select the Add-Ons tab
4. Click Install in the top right corner
5. Select the ZIP file


**Important:** The add-on was developed on Blender 3.3. While it's not a strict requirement you use this version, other versions may not work correctly. I have tested it on Blender 4.1 briefely and it appeared to work, however.

**Known issues:** Models with skeletons don't import correctly at the moment, and animate completely incorrectly.

## Importing a Scene
Under the "Angel Tools" menu in the menu strip, select "Import MOD/XMOD Scene"
Paste in your games `model` path into the `Models Path` input e.g. `C:\Games\Midnight Club 2\models`
Then type in the scene name such as `vp_civicb` and click OK

## Exporting a Scene
Under the "Angel Tools" menu in the menu strip, select "ExportMOD/XMOD Scene"
Paste in your games `model` path into the `Models Path` input e.g. `C:\Games\Midnight Club 2\models`
Type in your scene name such as `vp_civicb`
Select version `1.10` (`1.09` doesn't have shininess support in materials)
Select `XMOD` extension
Click OK

## Materials and Textures
- The shininess variable in XMOD is controlled via the `Roughness` slider in a `Principled BSDF` material. Any other material shader is not supported.
- As long as a texture is assigned, it'll be exported into the XMOD. If a texture is not found on import, a placeholder texture is generated, and you can still export without losing the texture.

## Dealing with MTX Files
MTX files are automatically imported when using "Import MOD/XMOD Scene", and automatically exported when using "ExportMOD/XMOD Scene"
**The `:m` suffix is not recognized by the addon, adding it may break exports. It is not neccessary to use it anymore.**

## Importing an animated model
- First, import a .skel file
- Then import the associated .xmod file 
- On the newly imported model, add an Armature modifier and  bind it to the armature imported from the skel file
**Animation import/export is not yet supported**
