#!/usr/bin/env python3

from alignment.modules.trackReader import trackReader

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
import pyMille
import sys

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

TODO: Implement corridor alignment

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- separate by x and y
- give to millepede
- obtain alignment parameters from millepede
- convert to alignment matrices

"""

class alignerModules:
    def __init__(self):

        sector = 0

        reader = trackReader()
        reader.readDetectorParameters()
        reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed.json'))

        # TODO: sort better by sector!

        milleOut = f'output/millepede/moduleAlignment-sector{sector}.bin'

        MyMille = pyMille.Mille(milleOut, True, True)
        
        sigmaScale = 1e2
        gotems = 0
        endCalls = 0

        labels = np.array([1,2,3,4,5,6,7,8,9,10,11,12])
        # labels = np.array([1,2,3])

        outFile = ""

        print(f'Running pyMille...')
        for params in reader.generatorMilleParameters():
            if params[4] == sector:
                # TODO: slice here, use only second plane
                # paramsN = params[0][3:6]
                # if np.linalg.norm(np.array(paramsN)) == 0:
                #     continue

                # TODO: this order of parameters does't match the interface!!!
                MyMille.write(params[1], params[0], labels, params[2], params[3]*sigmaScale)
                # print(f'params: {paramsN}')
                # print(f'residual: {params[2]}, sigma: {params[3]*sigmaScale} (factor {params[2]/(params[3]*sigmaScale)})')
                # labels += 3
                gotems += 1

                outFile += f'{params[1]}, {params[0]}, {labels}, {params[2]}, {params[3]*sigmaScale}\n'

                if (gotems % 200) == 0:
                    endCalls += 1
                    MyMille.end()


                # if gotems == 1e4:
                #     break
        
        MyMille.end()

        print(f'Mille binary data ({gotems} records) written to {milleOut}!')
        print(f'endCalls: {endCalls}')
        # now, pede must be called
    
        with open('writtenData.txt', 'w') as f:
            f.write(outFile)