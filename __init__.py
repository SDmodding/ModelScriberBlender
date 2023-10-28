# Updates are posted at: https://github.com/SDmodding/ModelScriberBlender
bl_info = {
    "name": "Sleeping Dogs: DE (Model Scriber)",
    "description": "Script that passes commands to noesis & model scriber.",
    "author": "sneakyevil",
    "version": (1, 0, 2),
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

    def draw(self, context):
        layout = self.layout
        m_TexBox = layout.box()
        m_TexRow = m_TexBox.row(align=True)
        m_TexRow.label(text="Texture Name:", icon="TEXTURE")
        if self.m_UseModelNameAsTextureName:
            m_TexRow.label(text="Using model name.")
        else:
            m_TexRow.prop(self, "m_TextureName")
        m_TexBox.prop(self, "m_UseModelNameAsTextureName")
   
        m_Model = layout.box()
        m_Model.label(text="Model", icon="MESH_DATA")
        m_Model.prop(self, "m_HasNormalMap")
        m_Model.prop(self, "m_HasSpecularLook")

        m_RasterRow = m_Model.row(align=True)
        m_RasterRow.scale_x = 0.5
        m_RasterRow.label(text="Raster State:")
        m_RasterRow.scale_x = 0.0
        m_RasterRow.prop(self, "m_RasterState", text="")

        
        m_ExportModeRow = m_Model.row(align=True)
        m_ExportModeRow.scale_x = 0.5
        m_ExportModeRow.label(text="Export Mode:")
        m_ExportModeRow.scale_x = 0.0
        m_ExportModeRow.prop(self, "m_ExportMode", text="")

        m_Object = layout.box()
        m_Object.label(text="Object", icon="OBJECT_DATA")
        m_Object.prop(self, "m_ApplyModifiers")
        m_Object.prop(self, "m_SelectionOnly")

    def execute(self, context):     
        m_NoesisPath = bpy.context.preferences.addons[__name__].preferences.NoesisPath.replace("\"","")
        if not os.path.exists(m_NoesisPath):
            self.report({ "ERROR" }, "Noesis path is invalid!")
            return { "CANCELLED" }

        m_ModelScriberPath = bpy.context.preferences.addons[__name__].preferences.ModelScriberPath.replace("\"","")   
        if not os.path.exists(m_ModelScriberPath):
            self.report({ "ERROR" }, "Model Scriber path is invalid!")
            return { "CANCELLED" }

        m_OutputDir = os.path.dirname(os.path.abspath(self.filepath))
        m_ModelName = os.path.basename(self.filepath)
        m_ObjFilePath = self.filepath + ".obj"
        bpy.ops.export_scene.obj(
            filepath=m_ObjFilePath,
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
            axis_forward="-Z",
            axis_up="Y"
        )

        # Noesis
        m_NoesisCmd = "\"" + m_NoesisPath + "\" ?cmode \"" + m_ObjFilePath + "\" \"" + m_ObjFilePath + "\""
        subprocess.run(m_NoesisCmd, shell=True)

        # Delete perm/temp if exist
        m_PermFile = self.filepath + ".perm.bin"
        if os.path.exists(m_PermFile):
            os.remove(m_PermFile)

        m_TempFile = self.filepath + ".temp.bin"
        if os.path.exists(m_TempFile):
            os.remove(m_TempFile)

        # Model Scriber
        m_ModelScriberCmd = "\"" + m_ModelScriberPath + "\" -dir \"" + m_OutputDir + "\" -obj \"" + m_ObjFilePath + "\""
        
        m_TextureName = self.m_TextureName
        if self.m_UseModelNameAsTextureName:
            m_TextureName = m_ModelName.split("~")[0]

        if m_TextureName:
            m_ModelScriberCmd += " -texdiffuse \"" + m_TextureName + "_D\""
            if self.m_HasNormalMap:             
                m_ModelScriberCmd += " -texnormal \"" + m_TextureName + "_N\""
            if self.m_HasSpecularLook:             
                m_ModelScriberCmd += " -texspecular \"" + m_TextureName + "_S\""

        # Raster State
        m_ModelScriberCmd += " -rasterstate " + self.m_RasterState

        # Export Mode
        if self.m_ExportMode == "skinned":
            m_ModelScriberCmd += " -skinned"

        subprocess.run(m_ModelScriberCmd, shell=True)

        # Delete object file
        os.remove(m_ObjFilePath)
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
