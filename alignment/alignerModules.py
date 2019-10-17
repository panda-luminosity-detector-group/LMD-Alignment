#!/usr/bin/env python3

from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

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

        self.reader = trackReader()
        print(f'reading detector parameters...')
        self.reader.readDetectorParameters()
        print(f'reading processed tracks file...')
        self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-singlePlane.json'))
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-aligned.json'))

    def alignMillepede(self):

        # TODO: sort better by sector!
        sector = 0

        milleOut = f'output/millepede/moduleAlignment-sector{sector}.bin'

        MyMille = pyMille.Mille(milleOut, True, True)
        
        sigmaScale = 1e1
        gotems = 0
        endCalls = 0

        labels = np.array([1,2,3,4,5,6,7,8,9,10,11,12])
        # labels = np.array([1,2,3])

        outFile = ""

        print(f'Running pyMille...')
        for params in self.reader.generatorMilleParameters():
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
    
        # with open('writtenData.txt', 'w') as f:
            # f.write(outFile)

    def alignICP(self):
        print(f'Oh Hai!')

        module = '/cave_1/lmd_root_0/half_0/plane_0/module_2'
        self.justFuckingRefactorMe(module)
        module = '/cave_1/lmd_root_0/half_0/plane_1/module_2'
        self.justFuckingRefactorMe(module)
        module = '/cave_1/lmd_root_0/half_0/plane_2/module_2'
        self.justFuckingRefactorMe(module)
        module = '/cave_1/lmd_root_0/half_0/plane_3/module_2'
        self.justFuckingRefactorMe(module)
        

    def justFuckingRefactorMe(self, module):
        arrayOne = ()
        arrayTwo = ()

        gotems = 0

        for line in self.reader.generateICPParameters():
            # if True:
            if line[0] == module:
                # print(f'line: {line[1]}, {line[2]}')
                arrayOne = np.append(arrayOne, line[1], axis=0)
                arrayTwo = np.append(arrayTwo, line[2], axis=0)

                # print(f'arrays:\n{arrayOne}\n{arrayTwo}\n')
                gotems += 1

                if gotems > 1000:
                    break

        nElem = len(arrayOne)/3
        arrayOne = arrayOne.reshape((int(nElem), 3))
        arrayTwo = arrayTwo.reshape((int(nElem), 3))

        # use 2D values
        arrayOne = arrayOne[..., :2]
        arrayTwo = arrayTwo[..., :2]

        # print(f'both arrays:\n{arrayOne}\n{arrayTwo}')

        T, _, _ = icp.best_fit_transform(arrayOne, arrayTwo)

        print(f'Result transformation:\n{T}')