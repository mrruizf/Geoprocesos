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
            FC.append(i.split(".gdb")[-1])
        elif description.dataElementType=="DEFeatureDataset":
            FD.append(i)
        elif description.dataElementType=="DERelationshipClass":
            REL.append(i.split(".gdb")[-1])
        elif description.dataElementType=="DETopology":
            TOP.append(i.split(".gdb")[-1])
        else:
            SID.append(i.split(".gdb")[-1])
    return FC,FD,REL,SID,TOP
"""
*********************************************************************
********************EJECUCIÓN DEL PROGRAMA***************************
*********************************************************************
"""
try:
    gdb = arcpy.GetParameterAsText(0)
    gdbs = gdb.split(";")
    foldersalida =arcpy.GetParameterAsText(1)
    nombregdb =arcpy.GetParameterAsText(2)
    arcpy.AddMessage(gdbs)
    #gdb = r"C:\Users\marlon.ruiz\Downloads\SAN_CARLOS_10K\SAN_CARLOS_P1_2021_V2.gdb"
    #gdbs.append(gdb)
    #gdb1 = r"C:\Users\marlon.ruiz\Downloads\SAN_CARLOS_10K\SAN_CARLOS_P2.gdb"
    #gdbs.append(gdb1)
    #gdb2 = r"C:\Users\marlon.ruiz\Downloads\SAN_CARLOS_10K\San_Carlos_P3_2021.gdb"
    #gdbs.append(gdb2)
    #foldersalida = r"C:\Users\marlon.ruiz\Downloads\SAN_CARLOS_10K" 
    #nombregdb = "SAN_CARLOS"
    if arcpy.Exists(foldersalida+"/"+nombregdb+".gdb")==False:
        FD = {}
        FC = {}
        REL = {}
        TOP = {}
        SID = {}
        DES = {}
        for i in gdbs:
            name = i.split("\\")[-1]
            DES[str(name.split(".gdb")[0])] = arcpy.Describe(i).path
            FC['FC_'+str(name.split(".gdb")[0])],FD['FD_'+str(name.split(".gdb")[0])],REL['REL_'+str(name.split(".gdb")[0])],SID['SID_'+str(name.split(".gdb")[0])],TOP['TOP_'+str(name.split(".gdb")[0])] = analizarGDB(MapearFileGDB(i))
            
        arcpy.AddMessage("Exportando esquema de la base de datos de entrada principal"+str(gdbs[0]))
        print("Exportando esquema de la base de datos de entrada principal"+str(gdbs[0]))
        arcpy.ExportXMLWorkspaceDocument_management(gdbs[0], foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "BINARY", "METADATA")
        arcpy.CreateFileGDB_management(foldersalida,nombregdb + ".gdb")
        arcpy.AddMessage("Importando el esquema a la nueva base de datos")
        print("Importando el esquema a la nueva base de datos")
        arcpy.ImportXMLWorkspaceDocument_management(foldersalida+"/"+nombregdb+".gdb",  foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "DEFAULTS")
        arcpy.AddMessage("Esquema importado a la nueva base de datos"+nombregdb)
        print("Esquema importado a la nueva base de datos"+nombregdb)
        """Llenando"""
        llaves = list(FC.keys())
        llaves
        primera = llaves[0]
        SIN_COPIA = []
        for i in llaves:
            #print("\t\t",i)
            #if primera != i:
            for j in FC[i]:
                destino = foldersalida+"\\"+nombregdb+".gdb\\"+j
                salida = DES[i[3:]]+"\\"+i[3:]+".gdb\\"+j
                if arcpy.Exists(destino)==True:
                    if int(arcpy.management.GetCount(salida).getOutput(0)):
                        #Apend
                        arcpy.AddMessage("Feature de entrada: \n"+salida+"\nFeature de salida: \n"+destino)
                        print("entra \n"+str(salida)+"\n"+str(destino))
                        arcpy.management.Append(salida,destino,"TEST")
                else:
                    arcpy.AddMessage("No Se encuentra\n"+str(salida))
                    print("No Se encuentra\n")
                    SIN_COPIA.append(salida)

        if len(SIN_COPIA)!=0 or SIN_COPIA !=[]:
            arcpy.AddMessage("Elementos que No existen en el esquema de la base de datos inicial")
            for i in SIN_COPIA:
                arcpy.AddMessage(i)

    else:
        arcpy.AddError("La base de datos de destino YA existe, por favor ingrese un nombre distinto para la GDB\n O elimine la base del directorio\n"+foldersalida)
except arcpy.ExecuteError as err:
    arcpy.AddError(err)
finally:
    arcpy.AddMessage(arcpy.GetMessages())
    if arcpy.Exists(foldersalida+"/"+nombregdb+".xml")==True:
        arcpy.management.Delete(foldersalida+"/"+nombregdb+".xml")
