import arcpy
fc = r'C:\Users\marlon.ruiz\Documents\Herramientas 2022\04. Resultados Pruebas\Resultados_Imagenes\Georreferenciacion\analisis.gdb\MARCOS_SIN_GEO_2'
fields = 'ID_AEROFOTO'
arcpy.management.CreateFeatureclass(arcpy.env.scratchGDB, "Resultado", "POINT", fc, "DISABLED", "DISABLED", 'GEOGCS["GCS_MAGNA",DATUM["D_MAGNA",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision', '', 0, 0, 0, '')
# For each row print the WELL_ID and WELL_TYPE fields, and the
# the feature's x,y coordinates
with arcpy.da.SearchCursor(fc, fields) as cursor:
    for row in cursor:
        print('{0}'.format(row[0]))
        arcpy.analysis.Select(fc, arcpy.env.scratchGDB+"\\"+row[0].replace("-",""), "ID_AEROFOTO ='{}'".format(row[0]))
        arcpy.cartography.SimplifyPolygon(arcpy.env.scratchGDB+"\\"+row[0].replace("-",""), arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_simply", "POINT_REMOVE", "100 Meters", "0 Unknown", "RESOLVE_ERRORS", "KEEP_COLLAPSED_POINTS", None)
        arcpy.management.FeatureVerticesToPoints(arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_simply", arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_point", "ALL")
        arcpy.management.Append(arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_point",arcpy.env.scratchGDB+"\\Resultado", "NO_TEST", None, '', '')
        arcpy.management.Delete(arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_simply")
        arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+row[0].replace("-",""))
        arcpy.management.Delete(arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_point")
        arcpy.management.Delete(arcpy.env.scratchGDB+"\\"+row[0].replace("-","")+"_simply_Pnt")
        
out_feature_class = r'C:\Users\marlon.ruiz\Documents\Herramientas 2022\04. Resultados Pruebas\Resultados_Imagenes\Georreferenciacion\analisis.gdb\RESULTADO_PUNTOS'
in_features = arcpy.env.scratchGDB+"\\Resultado"
arcpy.management.CopyFeatures(in_features, out_feature_class)
