#!/usr/bin/env python3

import numpy as np
import sys
sys.path.insert(0, '.')
from alignment.IP.trksQA import getIPfromTrksQA


np.set_printoptions(precision=6)
np.set_printoptions(suppress=True)

if __name__ == "__main__":
    filenames = []
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/aligned-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/box100-noAlign-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/box100-aligned-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/modules-noAlign-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/modules-aligned-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/sensors-noAlign-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/sensors-aligned-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/combi-noAlign-Lumi_TrksQA_100000.root')
    filenames.append('/home/remus/temp/rootcompare/testCombiOrder/combi-alignCombi0-Lumi_TrksQA_100000.root')
    
    for name in filenames:
        print(f'\n\n{name}:')
        ip = np.array(getIPfromTrksQA(name))#*1e1
        print(ip)