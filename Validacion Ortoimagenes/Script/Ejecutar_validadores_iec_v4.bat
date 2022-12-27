@echo off 
color 30
echo =============================================================================================
echo = Scripts para la validacion de las medidas de Calidad, Estructura e integridad en imagenes =
echo =============================================================================================
echo.
echo.


C:\Python27\ArcGIS10.8\python C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\04_JUNIO\APLICATIVOS_VALIDACION_V4\Validadores_Imagenes\validador_ei_calidad_v4.py --directorio "C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\02_ABRIL\05_VAL_FUENTEORO\IMAGEN" --rutavectores "C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\02_ABRIL\05_VAL_FUENTEORO\SHP" --escala 2000 --directorioe "C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\02_ABRIL\01_VAL_ORTOFOTOS\V3_act2\VOrto_Reporte_V3_aprob subd_20210323.xls" --vfiltro 254
rem C:\Python27\ArcGIS10.5\python D:\IGAC\Proyectos2021\Validadores\V3\validador_ei_calidad_v3.py --directorio "D:\IGAC\Proyectos2021\Validadores\Imagenes" --rutavectores "D:\IGAC\Proyectos2021\Validadores\Imagenes\Vector" --escala 5000 --directorioe "D:\IGAC\Proyectos2021\Validadores\V3\CONTROL_EXACT\VOrto_Reporte_V3_aprob subd_20210323.xls" --vfiltro 240


echo Para salir presiona una tecla.

pause>nul
exit
echo.
echo.


