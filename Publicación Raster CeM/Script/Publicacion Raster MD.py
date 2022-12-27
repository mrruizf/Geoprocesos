from arcpy import metadata as md
import arcpy
import os
try:
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    project = aprx.filePath.split('\\')[-1].split('.')[0]
    gdb = aprx.defaultGeodatabase
    file = arcpy.GetParameterAsText(0)
    #file = r'\\172.26.0.20\Elite_Sub_Geografia_Cartografia\MD\Municipios\MDT1_13647000_20211215\MDT1_13647000_20211215.tif'
    mosaic = file.split('\\')[-1].split('.')[0].split('_')[0][0:3].lower()+file.split('\\')[-1].split('.')[0].split('_')[1]
    #1. creación del mosaic dataset 
    with arcpy.EnvManager(outputCoordinateSystem="PROJCS['WGS_1984_Web_Mercator_Auxiliary_Sphere',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator_Auxiliary_Sphere'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],PARAMETER['Auxiliary_Sphere_Type',0.0],UNIT['Meter',1.0]]"):
        arcpy.management.CreateMosaicDataset(gdb, mosaic, "PROJCS['MAGNA-SIRGAS / Origen-Nacional',GEOGCS['GCS_MAGNA',DATUM['D_MAGNA',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',5000000.0],PARAMETER['False_Northing',2000000.0],PARAMETER['Central_Meridian',-73.0],PARAMETER['Scale_Factor',0.9992],PARAMETER['Latitude_Of_Origin',4.0],UNIT['Meter',1.0]]", None, '', "NONE", None)
    arcpy.AddMessage('1. creación del mosaic dataset')
    #lyr = arcpy.management.MakeMosaicLayer(os.path.join(gdb,mosaic), mosaic).getOutput(0)
    arcpy.AddMessage('Agregando el Msaic al canvas de ArcGIS Pro')
    #2. agregar todos los rasters 
    arcpy.management.AddRastersToMosaicDataset(mosaic, "Raster Dataset", file, "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY", "NO_OVERVIEWS", None, 0, 1500, None, '', "SUBFOLDERS", "ALLOW_DUPLICATES", "NO_PYRAMIDS", "NO_STATISTICS", "NO_THUMBNAILS", '', "NO_FORCE_SPATIAL_REFERENCE", "NO_STATISTICS", None, "NO_PIXEL_CACHE") 
    arcpy.AddMessage('2. agregar todos los rasters')
    #3. Calcular estadísticas de la imagen 
    arcpy.management.CalculateStatistics(mosaic, 1, 1, [], "OVERWRITE", r"in_memory\feature_set1")
    arcpy.AddMessage('3. Calcular estadísticas de la imagen')
    #4. Footprint
    rasterObj = arcpy.Raster(file)
    rradiom = rasterObj.pixelType
    arcpy.management.BuildFootprints(mosaic, '', "RADIOMETRY", 1, 2**int(rradiom[1:]), 8000, 0, "NO_MAINTAIN_EDGES", "SKIP_DERIVED_IMAGES", "UPDATE_BOUNDARY", 8000, 100, "NONE", None, 20, 0.05)
    arcpy.AddMessage('4. Construir Footprint')
    #5. Piramidales 
    arcpy.management.BuildPyramidsandStatistics(mosaic, "INCLUDE_SUBDIRECTORIES", "BUILD_PYRAMIDS", "CALCULATE_STATISTICS", "NONE", '', "NONE", 1, 1, [], -1, "NONE", "NEAREST", "DEFAULT", 75, "SKIP_EXISTING", '', "NONE")
    arcpy.AddMessage('5. Construir Piramidales')
    #6. Definir overviews
    map = aprx.listMaps("Map")[0]
    map.addDataFromPath(os.path.join(gdb,mosaic))
    ov = mosaic+'OV'
    foot = mosaic+'\\Footprint'
    nrow = int(rasterObj.width)
    ncol = int(rasterObj.height)
    arcpy.management.DefineOverviews(mosaic, os.path.join(aprx.homeFolder,ov), foot, None, None, -1, nrow, ncol, 4, "NO_FORCE_OVERVIEW_TILES", "BILINEAR", "JPEG", 80)
    arcpy.AddMessage('6. Definir overviews')
    #7. Construir overviews 
    arcpy.management.BuildOverviews(mosaic, '', "DEFINE_MISSING_TILES", "GENERATE_OVERVIEWS", "GENERATE_MISSING_IMAGES", "REGENERATE_STALE_IMAGES")
    arcpy.AddMessage('7. Construir overviews ')
    #Metadato del Mosaic Dataset
    tgt_item_md = md.Metadata(file)
    tgt_item_md1 = md.Metadata(os.path.join(gdb,mosaic))
    tgt_item_md1.title = project
    tgt_item_md1.description = tgt_item_md1.summary = tgt_item_md.description
    tgt_item_md1.tags = tgt_item_md.tags
    tgt_item_md1.description
    tgt_item_md1.save()
    #map.removeLayer(mosaic)
    #map.addDataFromPath(os.path.join(gdb,mosaic))
except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    arcpy.AddError(u"Error de Arcpy :\n {}".format(msgs))
    pass
