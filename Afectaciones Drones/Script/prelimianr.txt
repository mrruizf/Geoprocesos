import arcpy
from operator import itemgetter

def numer(num):
    try:
        int(num)
        return True
    except ValueError:
        return False

"""
fc2 = r"\\172.26.0.20\Elite_Sub_Geografia_Cartografia\Z_Transferencias\Marlon Ruiz\Dron_Edna\GDB\Proceso_Fotogrametrico_Dron_ON.gdb\EVALUACION_DRON\MARCO_DRON" #input feature class
fc3 = r"\\172.26.0.20\Elite_Sub_Geografia_Cartografia\Z_Transferencias\Marlon Ruiz\Dron_Edna\GDB\Proceso_Fotogrametrico_Dron_ON.gdb\EVALUACION_DRON\AFECTACION_DRON" #target feature class
checkfields = 'ID_AEROFOTO' #fields to compare
"""
try:
    fc2 = arcpy.GetParameterAsText(0)
    field_fc2 = arcpy.GetParameterAsText(1)
    fc3  = arcpy.GetParameterAsText(2)
    field_fc3 = arcpy.GetParameterAsText(3)
    tolerancia = arcpy.GetParameterAsText(4)
    workspace_outpu = arcpy.GetParameterAsText(5)
    if numer(tolerancia) or tolerancia=='':
        #"1 Unknown"
        #################################################
        spatial_ref = arcpy.Describe(fc2).spatialReference
        spatial_ref.exportToString()
        arcpy.management.CreateFeatureclass(arcpy.env.scratchGDB, "MARCO_DRON", "POLYGON", fc2, "DISABLED", "DISABLED", spatial_ref.exportToString(), '', 0, 0, 0, '')
        all_values = [i for i in arcpy.da.SearchCursor(fc3, field_fc3)]
        len(all_values)
        #################################################
        #fieldlist = [f.name for f in arcpy.ListFields(fc2) if not f.name.upper().startswith(('OBJ','SHA'))] #list all fields but objectid and shapefield(s)
        #fieldlist.append('SHAPE@')
        #checkindexes = [fieldlist.index(i) for i in checkfields]
        lista = []
        with arcpy.da.SearchCursor(fc2,field_fc2) as cursor:
            for row in cursor:
                if row in all_values:
                    lista.append(str(row[0]))
                    expresion = field_fc2+ "='" + str(row[0])+"'"
                    print(expresion)
                    arcpy.analysis.Select(fc2, arcpy.env.scratchGDB+"\\"+row[0].replace("-","_m"), expresion)
                    arcpy.analysis.Select(fc3, arcpy.env.scratchGDB+"\\"+row[0].replace("-","_a"), expresion)
                    arcpy.analysis.Erase(arcpy.env.scratchGDB+"\\"+row[0].replace("-","_m"), arcpy.env.scratchGDB+"\\"+row[0].replace("-","_a"), arcpy.env.scratchGDB+"\\"+row[0].replace("-","_"), tolerancia)
                    arcpy.management.Append(arcpy.env.scratchGDB+"\\"+row[0].replace("-","_"),arcpy.env.scratchGDB+"\\MARCO_DRON", "NO_TEST", None, '', '')
                    arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+row[0].replace("-","_m"))
                    arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+row[0].replace("-","_a"))
                    arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+row[0].replace("-","_"))
        expresion = field_fc2+ " NOT IN " +str(tuple(lista))
        arcpy.analysis.Select(fc2, arcpy.env.scratchGDB+"\\MARCO_DRON_WO", expresion)
        arcpy.management.Append(arcpy.env.scratchGDB+"\\MARCO_DRON_WO",arcpy.env.scratchGDB+"\\MARCO_DRON", "NO_TEST", None, '', '')
        in_features = arcpy.env.scratchGDB+"\\MARCO_DRON"
        arcpy.management.CopyFeatures(in_features, workspace_outpu+"\\LIMPIEZA_MARCOS")
                
except arcpy.ExecuteError as err:
    arcpy.AddError(err)