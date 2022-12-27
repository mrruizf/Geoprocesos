"""Listado de funciones"""
import arcpy
import os
#Primer validador
def validarParametros(gdb_nuevo,xml,foldersalida,nombregdb,tdataset,datasetSa):
    if gdb_nuevo == '' and xml == '':
        arcpy.AddError("Se debe ingresar una gdb con el nuevo modelo o un xml")
    elif gdb_nuevo == '' and xml != '':
        if foldersalida == '':
            arcpy.AddError("Se tiene que seleccionar el folder de salida y dar un nombre a la gdb a crear")
        elif foldersalida != '' and nombregdb == '':
            arcpy.AddError("Se tiene que dar un nombre a la gdb a crear")
        elif arcpy.Exists(foldersalida+"/"+nombregdb+".gdb")==True:
            arcpy.AddError("Ya existe la base de datos en el folder seleccionado, seleccione otro folder de salida o ingrese otro nombre para la gdb nueva")
    if tdataset == False and datasetSa == False:
        arcpy.AddError("Se tiene que seleccionar los dataset a migrar, por defecto se seleccionan todos")
    
def MapearFileGDB(admin_workspace):
    analyze_contents = []
    arcpy.AddMessage("\n***Mapeando la File Geoatabase\n"+str(admin_workspace))
    arcpy.AddMessage("\n***Mapeando la File Geoatabase\n"+str(admin_workspace))
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
    arcpy.AddMessage("\n***Analizando el contenido de la base de datos")
    for i in analyze_contents:
        description=arcpy.Describe(i)
        #arcpy.AddMessage(description.dataElementType+"\t"+description.baseName+"\n")
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
def calculaFiledsNombreGeografico(featuresDataset,featureClass,foldersalida,nombregdb):
    if  featuresDataset == "Superficies_Agua":
        in_table = foldersalida+"\\"+nombregdb+".gdb\\NombresGeograficos\\NGeogr"
        field = 'NGSubcateg'
        expression = "clasificar(!NGSubcateg!)"
        if featureClass.split("\\")[-1]=="Banco_Arena":
            code_block = """def clasificar(subcat):
    if subcat is None:
        return 11
    else:
        return subcat"""
            arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
        elif featureClass.split("\\")[-1]=="Humedal":
            code_block = """def clasificar(subcat):
    if subcat is None:
        return 13
    else:
        return subcat"""
            arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
        elif featureClass.split("\\")[-1]=="Isla":
            code_block = """def clasificar(subcat):
    if subcat is None:
        return 10
    else:
        return subcat"""
            arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
        elif featureClass.split("\\")[-1] in ["Drenaje_Doble","Drenaje_Sencillo"]:
            code_block = """def clasificar(subcat):
    if subcat is None:
        return 14
    else:
        return subcat"""
            arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
        elif featureClass.split("\\")[-1] in ["Embalse","Jaguey_P","Jaguey_R","Laguna"]:
            code_block = """def clasificar(subcat):
    if subcat is None:
        return 8
    else:
        return subcat"""
            arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
        arcpy.management.CalculateField(foldersalida+"\\"+nombregdb+".gdb\\NombresGeograficos\\NGeogr",'NGCategori','1',"PYTHON3")
        
"""Función que migra cada feature class que tiene el campo NOMBRE_GEOGRAFICO con algún valor, hace transformaciones de geometría para llegar a punto"""
def migraNombreGeografico(featuresDataset,featureClass,temporal,foldersalida,nombregdb):
    des = arcpy.Describe(featureClass)
    default=arcpy.env.workspace
    if featuresDataset == "Superficies_Agua" and des.featureType not in ["Annotation", "CoverageAnnotation"]:
        if int(arcpy.management.GetCount(featureClass).getOutput(0)):
            fields = arcpy.ListFields(featureClass)
            for f in fields:
                #arcpy.AddMessage(f.name+"---"+f.type)
                if f.name == "NOMBRE_GEOGRAFICO":
                    values = [row[0] for row in arcpy.da.SearchCursor(featureClass, "NOMBRE_GEOGRAFICO")]
                    uniqueValues = set(values)
                    uniqueValues.remove(None)
                    if len(uniqueValues) != 0 or uniqueValues !=[]:
                        arcpy.AddMessage("Entrando a migración nombre Geografico\n"+featureClass+"\n") ######################################## Mensaje de primer Nivel
                        for uv in uniqueValues:
                            expression = u'{}='.format(arcpy.AddFieldDelimiters(featureClass, f.name))+"'"+str(uv)+"'"
                            arcpy.AddMessage(expression+"\t"+str(des.baseName)) ######################################## Mensaje de segundo Nivel
                            arcpy.management.Append(featureClass,temporal+"\\"+featuresDataset+"\\"+featureClass.split("\\")[-1], "TEST", None, '',expression)
                            default = arcpy.env.workspace #Ambiente de trabajo por defecto
                            if des.shapeType == "Polygon":
                                arcpy.AddMessage("Tranformación Tipo de dato Polygon")
                                arcpy.management.FeatureToPoint(temporal+"\\"+featuresDataset+"\\"+featureClass.split("\\")[-1],default+"\\"+featureClass.split("\\")[-1],"INSIDE")
                            elif des.shapeType == "Polyline":
                                arcpy.AddMessage("Tranformación Tipo de dato Línea")
                                arcpy.management.FeatureVerticesToPoints(temporal+"\\"+featuresDataset+"\\"+featureClass.split("\\")[-1],default+"\\"+featureClass.split("\\")[-1],"BOTH_ENDS")
                            arcpy.AlterField_management(default+"\\"+featureClass.split("\\")[-1], f.name, 'NGNPrincip', 'NGNPrincip')
                            expression = u'{}='.format(arcpy.AddFieldDelimiters(featureClass, 'NGNPrincip'))+"'"+str(uv)+"'"
                            arcpy.management.Append(featureClass.split("\\")[-1],foldersalida+"\\"+nombregdb+".gdb\\NombresGeograficos\\NGeogr", "NO_TEST", None, '',expression)
                            calculaFiledsNombreGeografico(featuresDataset,featureClass,foldersalida,nombregdb)
                        arcpy.management.CalculateField(foldersalida+"\\"+nombregdb+".gdb\\NombresGeograficos\\NGeogr","RuleID",'1',"PYTHON3")
def migraSuperficieHidrologia(featuresDataset,featureClass,temporal,foldersalida,nombregdb):
    des = arcpy.Describe(featureClass)
    default=arcpy.env.workspace
    if featuresDataset == "Superficies_Agua" and des.featureType not in ["Annotation", "CoverageAnnotation"]:
        if int(arcpy.management.GetCount(featureClass).getOutput(0)):
            arcpy.AddMessage("Entrando a migración superficie\n"+featureClass+"\n")
            field = "RuleID"
            expression = "clasificar(!RuleID!)"
            if featureClass.split("\\")[-1]=="Banco_Arena":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\BArena"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Cienaga":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                #arcpy.management.CalculateField(in_table,"DATipo","4","PYTHON3")
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 4
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Drenaje_Doble": #Cambio 2 - Cambios en drenaje R, a partir del append, se tenia con codeblock
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\Drenaj_R"
                arcpy.management.Append(featureClass, in_table, "NO_TEST", r'DIdentif "DIdentif" true true false 50 Text 0 0,First,#;DTipo "DTipo" true true false 2 Short 0 0,First,#,Drenaje_Doble,TIPO,-1,-1;DNombre "DNombre" true true false 255 Text 0 0,First,#,Drenaje_Doble,NOMBRE_GEOGRAFICO,0,255;RuleID "RuleID" true true true 4 Long 0 0,First,#,Drenaje_Doble,RuleID,-1,-1;Override "Override" true true true 0 Blob 0 0,First,#,Drenaje_Doble,Override,-1,-1', '', '')
                #arcpy.management.Append(featureClass,in_table, "NO_TEST", r'DTipo "DTipo" true true false 3 Short 1 1,First,#,Drenaje_Doble,TIPO,-1,-1', '','')
                #field = 'RuleID'
                #expression = "!DTipo!"
                #arcpy.management.CalculateField(in_table,field,expression,"PYTHON3")
                field = 'DTipo'
                expression = "clasificar(!DTipo!)"
                code_block = """def clasificar(subcat):
    if subcat ==0:
        return 1
    elif subcat == 1:
        return 2
    elif subcat == 2:
        return 3"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID","!DTipo!","PYTHON3")
            elif featureClass.split("\\")[-1]=="Drenaje_Sencillo": #Cambio 1 - Cambios en drenaje L, a partir del append, se tenia con codeblock
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\Drenaj_L"
                arcpy.management.Append(featureClass, in_table, "NO_TEST", r'DIdentif "DIdentif" true true false 50 Text 0 0,First,#;DEstado "DEstado" true true false 2 Short 0 0,First,#,Drenaje_Sencillo,ESTADO_DRENAJE,-1,-1;DDisperso "DDisperso" true true false 50 Text 0 0,First,#,Drenaje_Sencillo,DISPERSION,0,1;DNombre "DNombre" true true false 255 Text 0 0,First,#,Drenaje_Sencillo,NOMBRE_GEOGRAFICO,0,255;RuleID "RuleID" true true true 4 Long 0 0,First,#,Drenaje_Sencillo,RuleID,-1,-1;Override "Override" true true true 0 Blob 0 0,First,#,Drenaje_Sencillo,Override,-1,-1', '', '')
                #arcpy.management.CalculateField(in_table, "RuleID", "str(!DEstado!)+', '+str(!DDisperso!)", "PYTHON3", '', "TEXT", "NO_ENFORCE_DOMAINS")
                #arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
            elif featureClass.split("\\")[-1]=="Embalse":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                #arcpy.management.CalculateField(in_table,"DATipo","2","PYTHON3")
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 2
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Humedal":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\Humeda"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Isla":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\Isla"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Jaguey_P":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_P"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                field = "DATipo"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID","!DATipo!","PYTHON3")
            elif featureClass.split("\\")[-1]=="Jaguey_R":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                #arcpy.management.CalculateField(in_table,"DATipo","6","PYTHON3")
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 6
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Laguna":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Madrevieja_L":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_L"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 1
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"DATipo","!RuleID!","PYTHON3")
            elif featureClass.split("\\")[-1]=="Madrevieja_R":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 7
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Manglar":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\Mangla"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 7
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Otros_Cuerpos_Agua":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 8
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            elif featureClass.split("\\")[-1]=="Pantano":
                in_table = foldersalida+"\\"+nombregdb+".gdb\\Hidrografia\\DAgua_R"
                arcpy.management.Append(featureClass,in_table, "NO_TEST", None, '','')
                field = 'DATipo'
                expression = "clasificar(!DATipo!)"
                code_block = """def clasificar(subcat):
    if subcat is None:
        return 5
    else:
        return subcat"""
                arcpy.management.CalculateField(in_table,field,expression,"PYTHON3",code_block)
                arcpy.management.CalculateField(in_table,"RuleID",expression,"PYTHON3",code_block)
            
                               
"""
Ejecución del programa
"""
try:
    #gdb = r"C:\Users\marlon.ruiz\Documents\Herramientas 2022\Generalizacion\GDB_PRUEBA\Carto10000_50577_DG_20190909.gdb"
    #foldersalida = r"C:\Users\marlon.ruiz\Documents\Herramientas 2022\Generalizacion\GDB_PRUEBA" 
    #nombregdb = "SALIDA"
    gdb = arcpy.GetParameterAsText(0)
    gdb_nuevo = arcpy.GetParameterAsText(1)
    xml = arcpy.GetParameterAsText(2)
    foldersalida = arcpy.GetParameterAsText(3)
    nombregdb = arcpy.GetParameterAsText(4)
    tdataset = arcpy.GetParameter(5) #De esta forma se pueden leer los bool
    datasetSa = arcpy.GetParameter(6)
    validarParametros(gdb_nuevo,xml,foldersalida,nombregdb,tdataset,datasetSa)
    if gdb_nuevo != '':
        xml = ''
        des = arcpy.Describe(gdb_nuevo)
        nombregdb = des.Basename
        foldersalida = des.Path
        if arcpy.Exists(foldersalida+"/"+nombregdb+".xml")==False:
            arcpy.ExportXMLWorkspaceDocument_management(gdb, foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "BINARY", "METADATA")
            arcpy.ImportXMLWorkspaceDocument_management(arcpy.env.scratchGDB,  foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "DEFAULTS")
        else:
            arcpy.AddError("Ya eiste un archivo xml dentro del directorio de trabajo de la nueva base de datos, por favor elimine este")
        FC,FD,REL,SID,TOP = analizarGDB(MapearFileGDB(gdb))
        #Aqui se pregunta si son todos los dataset
        if tdataset is True:
            for i in FC:
                migraSuperficieHidrologia(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
            for i in FC:
                migraNombreGeografico(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
        #Si se tiene seleccionado únicamnte el dataset de superficies de agua
        elif datasetSa is True:
            for i in FC:
                migraSuperficieHidrologia(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
            for i in FC:
                migraNombreGeografico(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
    elif xml != '':
        if arcpy.Exists(foldersalida+"/"+nombregdb+".xml")==False:
            arcpy.ExportXMLWorkspaceDocument_management(gdb, foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "BINARY", "METADATA")
            arcpy.ImportXMLWorkspaceDocument_management(arcpy.env.scratchGDB,  foldersalida+"/"+nombregdb+".xml", "SCHEMA_ONLY", "DEFAULTS")
        else:
            arcpy.AddError("Ya eiste un archivo xml dentro del directorio de trabajo de la nueva base de datos, por favor elimine este")
        if arcpy.Exists(foldersalida+"/"+nombregdb+".gdb")==False:
            FC,FD,REL,SID,TOP = analizarGDB(MapearFileGDB(gdb))
            #arcpy.AddMessage("Creando la base de datos temporal")
            #arcpy.CreateFileGDB_management(foldersalida,"temporal.gdb")
            arcpy.AddMessage("Creando la base de datos de salida")
            arcpy.CreateFileGDB_management(foldersalida,nombregdb+".gdb")
            #arcpy.AddMessage("Importando el esquema de la bbdd de entrada a la base de datos temporal")
            #arcpy.ImportXMLWorkspaceDocument_management(foldersalida+"/temporal.gdb",  foldersalida+"/"+desc.baseName+".xml", "SCHEMA_ONLY", "DEFAULTS")
            #arcpy.AddMessage("Importando el esquema de la bbdd de salida a la base de datos temporal")
            arcpy.ImportXMLWorkspaceDocument_management(foldersalida+"/"+nombregdb+".gdb", xml, "SCHEMA_ONLY", "DEFAULTS")
            arcpy.AddMessage("Proceso de creación e importación finalizado")
            #arcpy.CreateFileGDB_management(foldersalida,nombregdb+".gdb")
            #Aqui se pregunta si son todos los dataset
            if tdataset is True:
                for i in FC:
                    #arcpy.AddMessage(i.split("\\")[-2])
                    #migraNombreGeografico(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb")
                    migraSuperficieHidrologia(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
                    #migraNombreGeografico(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb",foldersalida,nombregdb)
                for i in FC:
                    #migraSuperficieHidrologia(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb",foldersalida,nombregdb)
                    migraNombreGeografico(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
            #Si se tiene seleccionado únicamnte el dataset de superficies de agua
            elif datasetSa is True:
                for i in FC:
                    #arcpy.AddMessage(i.split("\\")[-2])
                    #migraNombreGeografico(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb")
                    migraSuperficieHidrologia(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
                    #migraNombreGeografico(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb",foldersalida,nombregdb)
                for i in FC:
                    #migraSuperficieHidrologia(i.split("\\")[-2],i,foldersalida+"\\temporal.gdb",foldersalida,nombregdb)
                    migraNombreGeografico(i.split("\\")[-2],i,arcpy.env.scratchGDB,foldersalida,nombregdb)
except arcpy.ExecuteError as err:
    arcpy.AddError(err)
finally:
    arcpy.AddMessage(arcpy.GetMessages())
    if arcpy.Exists(foldersalida+"/"+nombregdb+".xml")==True:
        arcpy.management.Delete(foldersalida+"/"+nombregdb+".xml")
    if arcpy.Exists(foldersalida+"/temporal.gdb")==True:
        arcpy.management.Delete(foldersalida+"/temporal.gdb")
