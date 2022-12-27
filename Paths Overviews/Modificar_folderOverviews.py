import os
import shutil


listaOver = []
hecho = []
nohecho = []
for path, directories, files in os.walk(folder):
    #.aprx
    for name in files:
        if name.endswith(".tif"): #and (name.startswith('mds') or name.startswith('mdt') or name.startswith('orto')):
            try:
                over = os.path.join(path.split('\\')[0],path.split('\\')[1],path.split('\\')[2],path.split('\\')[3],path.split('\\')[4],path.split('\\')[4])+str('_Overview').replace('\\','/')
                file = os.path.join(path,name)
                overfile = os.path.join(over,file.split('\\')[-1])
                #os.makedirs(over, exist_ok=True)
                os.mkdir(over)
                print(over)
                shutil.copyfile(file, overfile)
                hecho.append(overfile)
                print(overfile)
                '''if not os.path.exists(over):
                    os.makedirs(over, exist_ok=True)
                    #print(over)'''
            except FileExistsError:
                print('\t\t Error')
                nohecho.append(overfile)
                next  