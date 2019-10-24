#!/usr/bin/env python3

# from alignment.modules.sectorContainer import sectorContainer
from alignment.modules.trackFitter import CorridorFitter
from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

from tqdm import tqdm
from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import json

import numpy as np
import pyMille
import re
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
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-singlePlane-1.00.json'))
        self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-modules-1.00.json'))
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-aligned.json'))

    def dynamicCut(self, cloud1, cloud2, cutPercent=2):

        assert cloud1.shape == cloud2.shape

        if cutPercent == 0:
            return cloud1, cloud2

        # calculate center of mass of differences
        dRaw = cloud2 - cloud1
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = cloud2 - com

        # calculate new distance for cut
        dRaw = newhit2 - cloud1
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        # sort by distance and cut some percent from start and end (discard outliers)
        cut = int(len(cloud1) * cutPercent/100.0)
        
        # sort by new distance
        cloud1 = cloud1[newDist.argsort()]
        cloud2 = cloud2[newDist.argsort()]
        
        # cut off largest distances, NOT lowest
        cloud1 = cloud1[:-cut]
        cloud2 = cloud2[:-cut]

        return cloud1, cloud2

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

    def alignICPold(self):
        print(f'Oh Hai!')

        # open detector geometry
        with open('input/detectorMatricesIdeal.json') as f:
            detectorComponents = json.load(f)

        modules = []

        # get only module paths
        for path in detectorComponents:
            regex = r"^/cave_(\d+)/lmd_root_(\d+)/half_(\d+)/plane_(\d+)/module_(\d+)$"
            p = re.compile(regex)
            m = p.match(path)

            if m:
                # print(m.group(0))
                modules.append(m.group(0))
        
        tracksAndRecos = {}
        matrices= {}

        # jesus what are you doing here
        for mod in tqdm(modules):
            tracksAndRecos[mod] = self.getTracksAndRecoHitsByModule(mod)
            matrices[mod] = self.getMatrix(tracksAndRecos[mod][0], tracksAndRecos[mod][1])

        print(matrices)

        # with open('output/alignmentModules/alMat-modules-singlePlane-1.00.json', 'w') as f:
        #     json.dump(results, f, indent=2)


    def alignICPiterative(self, sector=0):


        assert (sector > -1) and (sector < 10)


        paths = self.reader.getModulePathsInSector(sector)
        
        # temporary helper dicts for the steps between iterations
        recos = {}

        # TODO: remove, this is not needed, it's only here for debug
        matrices = {}

        for path in paths:
            print(f'path: {path}')
            # get tracks and recos in two arrays
            trackPos, recoPos = self.reader.getTrackAndRecoPos(path)

            # print(f'trackpos:\n{trackPos}\nrecopos:\n{recoPos}')

            # 0: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos)
            matrices[path] = T0
            
            print(T0)
            # 1: apply matrices (inversely?) to copy of reco points
            # do this here, not in the track reader

            # print(f'recos before:\n{recoPos}')

            # homogenize
            recosH = np.ones((len(recoPos), 4))
            recosH[:,:3] = recoPos
            # transform
            # TODO: is the direction correct? i.e. inv(T0)?
            recosH = np.matmul(T0, recosH.T).T
            # de-homogenize
            recoPos = recosH[:,:3]

            # print(f'recos after:\n{recoPos}')

            recos[path] = recoPos
            print('\n\n\n\n')

        # print(f'alright, I should now have 4 sets of recos and 4 matrices.')
        # print(f'mats: {matrices}')
        # print(f'recos: {recos}')

        return

        # 2: do track fit with new recos, we need all four planes!
        recos = self.reader.getRecos(0)
        print(f'number of tracks: {len(recos)}')

        # 3: get alignment matrices

        # 4: go to 1 until max_iter is reached


        return

        #* ------ new code using SVD in track fitter

        recos = self.reader.generateICPParametersBySector(0)

        print(f'OI OI OI')
        # print(f'len(recos[0]): {len(recos[0])}')
        # print(f'recos[0]:\n{recos[0]}')
        # print(f'len(recos[1]): {len(recos[1])}')
        # print(f'recos[1]:\n{recos[1]}')

        print(f'attempting fit!')
        corrFitter = CorridorFitter(recos)
        corrFitter.fitTracksSVD()
        # corrFitter.fitTracks()
        results = corrFitter.fittedTracks

        print(f'results:\n{results[:10]}')


        return

        #! ------ old code after here

        # recos = self.reader.generateICPParametersBySector(0)

        print(f'OI OI OI')
        # print(f'len(recos[0]): {len(recos[0])}')
        # print(f'recos[0]:\n{recos[0]}')
        # print(f'len(recos[1]): {len(recos[1])}')
        # print(f'recos[1]:\n{recos[1]}')

        print(f'attempting fit!')
        corrFitter = CorridorFitter(recos)
        corrFitter.fitTracks()
        results = corrFitter.fittedTracks

        print(f'results:\n{results[0]}')

    def getTracksAndRecoHitsByModule(self, module):
        trackPositions = []
        recoPositions = []

        gotems = 0

        for line in self.reader.generateICPParameters(module):
            trackPositions.append(np.ndarray.tolist(line[0]))
            recoPositions.append(np.ndarray.tolist(line[1]))

            gotems += 1
            if gotems == 1000:
                break

        trackPositions = np.array(trackPositions)
        recoPositions = np.array(recoPositions)

        return trackPositions, recoPositions

    def getMatrix(self, trackPositions, recoPositions):
        arrayOne = np.array(trackPositions)
        arrayTwo = np.array(recoPositions)

        # TODO: somewhere else!
        if False:
            arrayOne, arrayTwo = self.dynamicCut(arrayOne, arrayTwo, 5)

        # use 2D
        if False:

            # use 2D values
            arrayOne = arrayOne[..., :2]
            arrayTwo = arrayTwo[..., :2]

            T, _, _ = icp.best_fit_transform(arrayOne, arrayTwo)

            # homogenize
            resultMat = np.identity(4)
            resultMat[:2, :2] = T[:2, :2]
            resultMat[:2, 3] = T[:2, 2]

        else:
            T, _, _ = icp.best_fit_transform(arrayOne, arrayTwo)
            resultMat = T

        return resultMat
    
    def justFuckingRefactorMe(self, module):

        arrayOne = []
        arrayTwo = []

        gotems = 0

        for line in self.reader.generateICPParameters(module):
            # if True:
            arrayOne.append(np.ndarray.tolist(line[0]))
            arrayTwo.append(np.ndarray.tolist(line[1]))

            gotems += 1

            if gotems == 2000:
                break

        arrayOne = np.array(arrayOne)
        arrayTwo = np.array(arrayTwo)

        if True:
            arrayOne, arrayTwo = self.dynamicCut(arrayOne, arrayTwo, 5)

        if False:

            # print(f'Average Distances for {module}:')
            dVec = arrayOne-arrayTwo
            # print(f'{np.average(dVec, axis=0)*1e4}')

            #! begin hist

            # print(dVec.shape)

            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.colors import LogNorm
            
            # plot difference hit array
            fig = plt.figure(figsize=(16/2.54, 16/2.54))
            
            axis = fig.add_subplot(1,1,1)
            axis.hist2d(dVec[:, 0]*1e4, dVec[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')
            axis.set_title(f'2D Distance\n{module}')
            axis.yaxis.tick_right()
            axis.yaxis.set_ticks_position('both')
            axis.set_xlabel('dx [µm]')
            axis.set_ylabel('dy [µm]')
            axis.tick_params(direction='out')
            axis.yaxis.set_label_position("right")

            module = module.replace('/', '-')

            # fig.show()
            fig.savefig(f'output/alignmentModules/{module}.png')
            plt.close(fig)
            #! end hist

        # use 2D values
        arrayOne = arrayOne[..., :2]
        arrayTwo = arrayTwo[..., :2]

        T, _, _ = icp.best_fit_transform(arrayOne, arrayTwo)

        return T

    def trackToEquation(self, trackO, trackD):
        return [0,0,0]

    def equationToTrack(self, equation):
        return [0,0,0], [0,0,0]