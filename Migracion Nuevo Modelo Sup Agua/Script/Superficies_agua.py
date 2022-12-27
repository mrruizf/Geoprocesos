"""Listado de funciones"""
import arcpy
import os

def MapearFileGDB(admin_workspace):
    analyze_contents = []
    arcpy.AddMessage("\n***Mapeando la File Geoatabase\n"+str(admin_workspace))
    print("\n***Mapeando la File Geoatabase\n"+str(admin_workspace))
    for dirpath, workspaces, datatypes in arcpy.da.Walk(
            admin_workspace,
            followlinks=True):
        # Cree una ruta completa y agregue tablas, clases de entidad y conjuntos de datos ráster
        analyze_contents += [
            os.path.join(dirpath, datatype) for datatype in datatypes]
        # cree la ruta completa, agregue los conjuntos de datos de características del archivo .GDB
        analyze_contents += [
            os.path.join(dirpath, workspace) for workspace in workspaces]
    return analyze_contents

def analizarGDB(analyze_contents):
    FC = []
    FD = []
    REL = []
    SID = []
    TOP = []
    arcpy.AddMessage("\n***Analizando el contenido de la base de datos")
    print("\n***Analizando el contenido de la base de datos")
    for i in analyze_contents:
        description=arcpy.Describe(i)
        #print(description.dataElementType+"\t"+description.baseName+"\n")
        if description.dataElementType=="DEFeatureClass":
            FC.append(i)
        elif description.dataElementType=="DEFeatureDataset":
            FD.append(i)
        elif description.dataElementType=="DERelationshipClass":
            REL.append(i)
        elif description.dataElementType=="DETopology":
            TOP.append(i)
        else:
            SID.append(i)
    return FC,FD,REL,SID,TOP

def migraSuperficies(featuresDataset,featureClass):
    des = arcpy.Describe(featureClass)
    if featuresDataset == "Superficies_Agua":
        if int(arcpy.management.GetCount(featureClass).getOutput(0)):
            #print("\nFeature Class con información\n"+i.split("\\")[-1]+" "+str(int(arcpy.management.GetCount(featureClass).getOutput(0)))+" "+str(des.shapeType)+"\n")
            if des.shapeType == "Polygon":
                fields = arcpy.ListFields(featureClass)
                for f in fields:
                    #print(f.name+"---"+f.type)
                    if f.name == "NOMBRE_GEOGRAFICO":
                        values = [row[0] for row in arcpy.da.SearchCursor(featureClass, "NOMBRE_GEOGRAFICO")]
                        uniqueValues = set(values)
                        uniqueValues.remove(None)
                        if len(uniqueValues) != 0 or uniqueValues !=[]:
                            print(featureClass)
                            for uv in uniqueValues:
                                expression = u'{}='.format(arcpy.AddFieldDelimiters(featureClass, f.name))+"'"+str(uv)+"'"
                                print(expression)
                                fc = arcpy.management.SelectLayerByAttribute(featureClass,'NEW_SELECTION',expression)
                                arcpy.CopyFeatures_management(fc, des.path+"\\"+str(fc))
                                #with arcpy.da.SearchCursor(featureClass,f.name,where_clause=expression) as cursor:
                                #    for row in cursor:
                                        # Print the name of the residential road
                                #        print(row[0])   
                                #print(uv)
"""
Ejecución del programa
"""

gdb = r"C:\Users\marlon.ruiz\Documents\Herramientas 2022\Generalizacion\GDB_PRUEBA\Carto10000_50577_DG_20190909.gdb"
foldersalida = r"C:\Users\marlon.ruiz\Documents\Herramientas 2022\Generalizacion\GDB_PRUEBA" 
nombregdb = "SALIDA"
if arcpy.Exists(foldersalida+"/"+nombregdb+".gdb")==False:
    FC,FD,REL,SID,TOP = analizarGDB(MapearFileGDB(gdb))
    print("Creando la base de datos")
    arcpy.CreateFileGDB_management(foldersalida,nombregdb + ".gdb")
    for i in FC:
    #print(i.split("\\")[-2])
    migraSuperficies(i.split("\\")[-2],i)
