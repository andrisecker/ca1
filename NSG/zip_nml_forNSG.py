#!/usr/bin/python
# -*- coding: utf8 -*-
"""
creates .zip archive from the necessary nml files (to sends NetPyNE jobs to NSG REST API afterwards)
authors: András Ecker, Padraig Gleeson last update 09.2017
"""

import os
import sys
import shutil
import zipfile
from pyneuroml import pynml

basePath = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-2])
nmlFolder = os.path.join(basePath, "NeuroML2")


def create_folder(zipName, networkName, copysyn=False):
    """copies the necessary files to a subfolder (in the NSG prefered way)"""
    
    # create directory (if exist it will delete and recreate)
    mainDirName = os.path.join(basePath, "NSG", zipName)
    if os.path.isdir(mainDirName):
        shutil.rmtree(mainDirName)
    os.mkdir(mainDirName)
    
    # cp channels
    os.mkdir(os.path.join(mainDirName, "channels"))
    for file_ in os.listdir(os.path.join(nmlFolder, "channels")):
        if file_.endswith(".channel.nml") or file_ == "Capool.nml":
            shutil.copy2(os.path.join(nmlFolder, "channels", file_), os.path.join(mainDirName, "channels", file_))            
    # cp cells
    os.mkdir(os.path.join(mainDirName, "cells"))
    for file_ in os.listdir(os.path.join(nmlFolder, "cells")):
        if file_.endswith(".cell.nml"):
            shutil.copy2(os.path.join(nmlFolder, "cells", file_), os.path.join(mainDirName, "cells", file_))
    # cp synapses
    if copysyn:   # only for regenerated network (the one generated from scratch in oc. has the synapses inside the .net.nml file)
        os.mkdir(os.path.join(mainDirName, "synapses"))
        shutil.copy2(os.path.join(nmlFolder, "synapses", "exp2Synapses.synapse.nml"),
                     os.path.join(mainDirName, "synapses", "exp2Synapses.synapse.nml"))
        shutil.copy2(os.path.join(nmlFolder, "synapses", "customGABASynapses.synapse.nml"),
                     os.path.join(mainDirName, "synapses", "customGABASynapses.synapse.nml")) 
    # cp network and LEMS file
    os.mkdir(os.path.join(mainDirName, "network"))
    shutil.copy2(os.path.join(nmlFolder, "network", "%s.net.nml"%networkName),
                 os.path.join(mainDirName, "network", "%s.net.nml"%networkName))
    shutil.copy2(os.path.join(nmlFolder, "network", "LEMS_%s.xml"%networkName),
                 os.path.join(mainDirName, "network", "LEMS_%s.xml"%networkName))
                 
    return mainDirName
    

def create_init(mainDirName, networkName):
    """helper function to create init.py file called by NSG"""
    
    s = '#!/usr/bin/python\n'+ \
        '"""init.py to call NetPyNE generated simulation from the top level (not from network folder)"""\n\n' + \
        'import os\n' + \
        'import sys\n\n' + \
        'os.chdir("network")\n' + \
        'sys.path.append(".")\n\n' + \
        'import LEMS_%s_netpyne'%networkName
        
    with open(os.path.join(mainDirName, "init.py"), "w") as f_:
        f_.write(s)

    with open(os.path.join(mainDirName, "network", "__init__.py"), "w") as f_:
        f_.write(" ")


def create_zip(zipName, mainDirName, rm=True):
    "zips content of the folder (in the NSG prefered way)"
    
    # zip created directory (shutils.make_archive won't work here...)
    zf = zipfile.ZipFile(mainDirName+".zip", "w")
    for root, subfolders, files in os.walk(mainDirName):
        for file_ in files:
            fName = os.path.join(root, file_)
            arcName = os.path.join(os.path.relpath(root, os.path.join(basePath, "NSG")), file_)
            zf.write(fName, arcName)
    zf.close()  

    if rm: # remove directory (and keep only the .zip file)
        shutil.rmtree(mainDirName)
    
    print("zip file created: %s.zip"%mainDirName)


if __name__ == "__main__":

    try:
        scale = sys.argv[1] 
    except:
        scale = 100000
    
    zipName = "CA1_nml"
    networkName = "HippocampalNet_scale%s_oc"%scale  # change this to rerun NEURON version instead of oc. generated!
        
    mainDirName = create_folder(zipName, networkName, copysyn=False)
               
    # generate NetPyNE simulation
    pynml.run_jneuroml("", "LEMS_%s.xml"%networkName, "-netpyne",
                       max_memory="14G", exec_in_dir=os.path.join(mainDirName, "network"), verbose=True)  # increase heap size if necessary!
    
    # move .mod files into root (for NSG)                            
    for file_ in os.listdir(os.path.join(mainDirName, "network")):
        if file_.endswith(".mod"):
            shutil.move(os.path.join(mainDirName, "network", file_), os.path.join(mainDirName, file_))
    
    create_init(mainDirName)
    
    create_zip(zipName, mainDirName, rm=False)
    
    
    
    

