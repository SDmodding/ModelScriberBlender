# Updates are posted at: https://github.com/SDmodding/ModelScriberBlender
bl_info = {
    "name": "Sleeping Dogs: DE (Model Scriber)",
    "description": "Script that passes commands to noesis & model scriber.",
    "author": "sneakyevil",
    "version": (1, 0, 4),
    "blender": (2, 80, 0),
    "location": "File > Export",
    "warning": "",
    "support": "COMMUNITY",
    "tracker_url": "https://github.com/SDmodding/ModelScriberBlender/issues",
    "category": "Import-Export",
}

import os
import subprocess
import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, AddonPreferences

class SDModelScriberAddonPreferences(AddonPreferences):
    bl_idname = __name__

    ModelScriberPath: StringProperty(
        name = "Model Scriber Path",
        description= "File path to ModelScriber.exe",
        subtype = "FILE_PATH",
    )

    NoesisPath: StringProperty(
        name = "Noesis Path",
        description = "File path to Noesis.exe",
        subtype = "FILE_PATH",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ModelScriberPath")
        layout.prop(self, "NoesisPath")

class SDModelScriberExport(Operator, ExportHelper):
    bl_idname = "sdmodelscribe.export"
    bl_description = "Export Sleeping Dogs Model File"
    bl_label = "Export Model"

    filename_ext = ""

    filter_glob: StringProperty(
        default = "*",
        options = { "HIDDEN" },
        maxlen = 255,
    )

    # Texture
    m_TextureName: StringProperty(name="", description="Name of the texture used with Texture Scriber.\n\nSuffixes:\nDiffuse: '_D'\nNormal Map: '_N'\nSpecular Look: '_S'")
    m_UseModelNameAsTextureName: BoolProperty( name="Use Model Name as Texture Name", description="Will use export name as texture name.\n\nWarning: If you're exporting model that contains '~' it will split and use name before for texture name", default=False )

    # Model
    m_HasNormalMap: BoolProperty(name="Has Normal Map", description="Enable it only when your model uses normal map", default=False)
    m_HasSpecularLook: BoolProperty(name="Has Specular Look", description="Enable it only when your model uses specular look", default=False)
    m_RasterState: EnumProperty(name="Raster State", description="The way the model renders.",
        items = (
            ( "0", "None (Default)", "" ),
            ( "1", "Normal", "" ),
            ( "2", "Disable Write", "" ),
            ( "3", "Invert Disable Write", "" ),
            ( "4", "Disable Depth Test", "" ),
            ( "5", "Double Sided (Back Culling)", "" ),
            ( "6", "Double Sided Alpha", "" ),
            ( "7", "Invert Culling", "" ),
        ),
        default = "0"
    )
    m_ExportMode: EnumProperty(name="Export Mode", description="Basically vertex decl export type.",
        items = (
            ( "uvn", "UVN (Default)", "" ),
            ( "skinned", "Skinned (WIP)", "" )
        ),
        default = "uvn"
    )

    # Object
    m_ApplyModifiers: BoolProperty(name="Apply Modifiers", default=False)
    m_SelectionOnly: BoolProperty(name="Selection Only", description="Export selected objects only", default=False)
    m_GameRotation: BoolProperty(name="Game Rotation", description="Export object with game rotation", default=False)
    m_AppendMode: BoolProperty(name="Append Mode", description="Append object to pre-existing file", default=False)

    def draw(self, context):
        layout = self.layout
        texBox = layout.box()
        texRow = texBox.row(align=True)
        texRow.label(text="Texture Name:", icon="TEXTURE")
        if self.m_UseModelNameAsTextureName:
            texRow.label(text="Using model name.")
        else:
            texRow.prop(self, "m_TextureName")
        texBox.prop(self, "m_UseModelNameAsTextureName")
   
        modelBox = layout.box()
        modelBox.label(text="Model", icon="MESH_DATA")
        modelBox.prop(self, "m_HasNormalMap")
        modelBox.prop(self, "m_HasSpecularLook")

        rasterRow = modelBox.row(align=True)
        rasterRow.scale_x = 0.5
        rasterRow.label(text="Raster State:")
        rasterRow.scale_x = 0.0
        rasterRow.prop(self, "m_RasterState", text="")
      
        exportModeRow = modelBox.row(align=True)
        exportModeRow.scale_x = 0.5
        exportModeRow.label(text="Export Mode:")
        exportModeRow.scale_x = 0.0
        exportModeRow.prop(self, "m_ExportMode", text="")

        objBox = layout.box()
        objBox.label(text="Object", icon="OBJECT_DATA")
        objBox.prop(self, "m_ApplyModifiers")
        objBox.prop(self, "m_SelectionOnly")
        objBox.prop(self, "m_GameRotation")
        objBox.prop(self, "m_AppendMode")

    def execute(self, context):     
        sNoesisPath = bpy.context.preferences.addons[__name__].preferences.NoesisPath.replace("\"","")
        if not os.path.exists(sNoesisPath):
            self.report({ "ERROR" }, "Noesis path is invalid!")
            return { "CANCELLED" }

        sModelScriberPath = bpy.context.preferences.addons[__name__].preferences.ModelScriberPath.replace("\"","")   
        if not os.path.exists(sModelScriberPath):
            self.report({ "ERROR" }, "Model Scriber path is invalid!")
            return { "CANCELLED" }

        sAxisForward = "-Z"
        sAxisUp = "Y"
        if self.m_GameRotation:
            sAxisForward = "Y"
            sAxisUp = "Z"

        sOutputDir = os.path.dirname(os.path.abspath(self.filepath))
        sModelName = os.path.basename(self.filepath)
        sObjFilePath = self.filepath + ".obj"
        bpy.ops.export_scene.obj(
            filepath=sObjFilePath,
            check_existing=False,
            use_selection=self.m_SelectionOnly,
            use_animation=False,
            use_mesh_modifiers=self.m_ApplyModifiers,
            use_edges=True,
            use_smooth_groups=False,
            use_smooth_groups_bitflags=False,
            use_normals=True,
            use_uvs=True,
            use_materials=False,
            use_triangles=True,
            use_nurbs=False,
            use_vertex_groups=False,
            use_blen_objects=False,
            group_by_object=False,
            group_by_material=False,
            keep_vertex_order=False,
            axis_forward=sAxisForward,
            axis_up=sAxisUp
        )

        # Noesis
        sNoesisCmd = "\"" + sNoesisPath + "\" ?cmode \"" + sObjFilePath + "\" \"" + sObjFilePath + "\""
        subprocess.run(sNoesisCmd, shell=True)

        # Delete perm/temp if exist
        sPermFile = self.filepath + ".perm.bin"
        if os.path.exists(sPermFile):
            os.remove(sPermFile)

        sTempFile = self.filepath + ".temp.bin"
        if os.path.exists(sTempFile):
            os.remove(sTempFile)

        # Model Scriber
        sModelScriberCmd = "\"" + sModelScriberPath + "\" -dir \"" + sOutputDir + "\" -obj \"" + sObjFilePath + "\""
        
        sTextureName = self.m_TextureName
        if self.m_UseModelNameAsTextureName:
            sTextureName = sModelName.split("~")[0]

        if not sTextureName == "":
            sModelScriberCmd += " -texdiffuse \"" + sTextureName + "_D\""
            if self.m_HasNormalMap:             
                sModelScriberCmd += " -texnormal \"" + sTextureName + "_N\""
            if self.m_HasSpecularLook:             
                sModelScriberCmd += " -texspecular \"" + sTextureName + "_S\""

        # Raster State
        sModelScriberCmd += " -rasterstate " + self.m_RasterState

        # Export Mode
        if self.m_ExportMode == "skinned":
            sModelScriberCmd += " -skinned"

        if self.m_AppendMode:
            sModelScriberCmd += " -append"

        subprocess.run(sModelScriberCmd, shell=True)

        # Delete object file
        os.remove(sObjFilePath)
        self.report({ "INFO" }, "Successfully exported model!")
        return { "FINISHED" }

def SDModelScriberFuncExport(self, context):
    self.layout.operator(SDModelScriberExport.bl_idname, text="Sleeping Dogs: DE (perm.bin)")

g_Classes = [ SDModelScriberAddonPreferences, SDModelScriberExport ]

def register():
    for m_Class in g_Classes:
        bpy.utils.register_class(m_Class)

    bpy.types.TOPBAR_MT_file_export.append(SDModelScriberFuncExport)

def unregister():
    for m_Class in g_Classes:
        bpy.utils.unregister_class(m_Class)

    bpy.types.TOPBAR_MT_file_export.remove(SDModelScriberFuncExport)

if __name__ == "__main__":
    register()
