import arcpy
fc = r'C:\Users\marlon.ruiz\Documents\Herramientas 2022\04. Resultados Pruebas\Resultados_Imagenes\Georreferenciacion\analisis.gdb\RESULTADO_PUNTOS'
fields = 'ID_AEROFOTO'
imagenes = []
with arcpy.da.SearchCursor(fc, fields) as cursor:
    for row in cursor:
        print('{0}'.format(row[0]))
        imagenes.append(row[0])

examinar = []
for i in imagenes:
    print(i)
    a = imagenes.count(i)
    if a > 5:
        examinar.append(i)
        print("\tSe tiene que examinar "+i)

print(len(examinar))
examinar = set(examinar)
print(len(examinar))

import os
with open(r'C:\Users\marlon.ruiz\Documents\Herramientas 2022\04. Resultados Pruebas\Resultados_Imagenes\Georreferenciacion\Listado_examinar.txt', 'w') as f:
    for i in examinar:
        try:
            f.write("%s\n" % i)
        except FileNotFoundError:
            next