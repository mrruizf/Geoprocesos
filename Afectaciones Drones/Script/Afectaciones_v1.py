import arcpy
from operator import itemgetter
import pandas as pd

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
        arcpy.AddMessage(spatial_ref.exportToString())
        arcpy.management.CreateFeatureclass(arcpy.env.scratchGDB, "MARCO_DRON", "POLYGON", fc2, "DISABLED", "DISABLED", spatial_ref.exportToString(), '', 0, 0, 0, '')
        all_values = [i for i in arcpy.da.SearchCursor(fc3, field_fc3)]
        len(all_values)
        #################################################
        #fieldlist = [f.name for f in arcpy.ListFields(fc2) if not f.name.upper().startswith(('OBJ','SHA'))] #list all fields but objectid and shapefield(s)
        #fieldlist.append('SHAPE@')
        #checkindexes = [fieldlist.index(i) for i in checkfields]
        lista = []
        lista1 = []
        with arcpy.da.SearchCursor(fc2,field_fc2) as cursor:
            for row in cursor:
                if row in all_values:
                    lista.append(str(row[0]))
                    expresion = field_fc2+ "='" + str(row[0])+"'"
                    arcpy.AddMessage(expresion)
                    marco = str(row[0])+"_m".replace('-','_').replace(' ','').replace('(','').replace(')','')
                    afecta = str(row[0])+"_a".replace('-','_').replace(' ','').replace('(','').replace(')','')
                    arcpy.AddMessage(marco)
                    arcpy.AddMessage(afecta)
                    try:
                        arcpy.analysis.Select(fc2, arcpy.env.scratchGDB+"\\"+marco, expresion)
                        arcpy.AddMessage('Select 1')
                        arcpy.analysis.Select(fc3, arcpy.env.scratchGDB+"\\"+afecta, expresion)
                        arcpy.AddMessage('Select 2')
                        arcpy.analysis.Erase(arcpy.env.scratchGDB+"\\"+marco, arcpy.env.scratchGDB+"\\"+afecta, arcpy.env.scratchGDB+"\\"+row[0].replace('-','_').replace(' ','').replace('(','').replace(')',''), tolerancia)
                        arcpy.management.Append(arcpy.env.scratchGDB+"\\"+row[0].replace('-','_').replace(' ','').replace('(','').replace(')',''),arcpy.env.scratchGDB+"\\MARCO_DRON", "NO_TEST", None, '', '')
                        arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+marco)
                        arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+afecta)
                        arcpy.management.Delete( arcpy.env.scratchGDB+"\\"+row[0].replace('-','_').replace(' ','').replace('(','').replace(')',''))
                    except arcpy.ExecuteError:
                        msgs = arcpy.GetMessages(2)
                        arcpy.AddMessage("Error de Arcpy:\n {}".format(msgs))
                        lista1.append(expresion)
                        pass
        expresion = field_fc2+ " NOT IN " +str(tuple(lista))
        arcpy.analysis.Select(fc2, arcpy.env.scratchGDB+"\\MARCO_DRON_WO", expresion)
        arcpy.management.Append(arcpy.env.scratchGDB+"\\MARCO_DRON_WO",arcpy.env.scratchGDB+"\\MARCO_DRON", "NO_TEST", None, '', '')
        in_features = arcpy.env.scratchGDB+"\\MARCO_DRON"
        arcpy.management.CopyFeatures(in_features, workspace_outpu+"\\LIMPIEZA_MARCOS")
        try:
            if len(list1)>0:
                df = pd.DataFrame(lista1)
                print(lista1)
                df.to_excel(workspace_outpu+"\\errores.xlsx")
        except Exception:
            pass
except arcpy.ExecuteError as err:
    arcpy.AddError(err)
