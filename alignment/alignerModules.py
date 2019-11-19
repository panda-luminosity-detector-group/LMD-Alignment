#!/usr/bin/env python3

# from alignment.modules.sectorContainer import sectorContainer
from alignment.modules.trackFitter import CorridorFitter
from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path

import copy
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

        self.alignMatrices = {}

        self.reader = trackReader()
        print(f'reading detector parameters...')
        self.reader.readDetectorParameters()
        print(f'reading processed tracks file...')
        
        # from good-ish tracks
        self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-modulesNoRot-1.00.json'))
        
        # merged Tracks from modulesNoRot-1.00
        # WARNING! there is something wrong on layers 1&2 here!
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-noTrks-chain.json'))
       
       
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-noTrks.json'))
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-aligned.json'))

    def readAnchorPoints(self, fileName):
        with open(fileName, 'r') as f:
            self.anchorPoints = json.load(f)

    #? cuts on track x,y direction
    def dynamicTrackCut(self, newTracks, cutPercent=2, matrixToFoR=None):
        
        # TODO: transform them, if needed, to matrixToFoR
        
        com = np.average(newTracks[:,1,:3], axis=0)

        # shift newhit2 by com of differences
        newhit2 = newTracks[:,1,:3] - com
        newDist = np.power(newhit2[:, 0], 2) + np.power(newhit2[:, 1], 2)

        cut = int(len(newhit2) * cutPercent/100.0)
        newTracks = newTracks[newDist.argsort()]
        newTracks = newTracks[:-cut]
        return newTracks
    
    #? cuts on reco-track distance
    def dynamicRecoTrackDistanceCut(self, newTracks, cutPercent=1):
        
        tempTracks = newTracks

        for i in range(4):
            trackPosArr = tempTracks[:, 0, :3]
            trackDirArr = tempTracks[:, 1, :3]
            recoPosArr = tempTracks[:, 2+i, :3]

            # norm momentum vectors, this is important for the distance formula!
            trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

            # vectorized distance calculation
            tempV1 = (trackPosArr - recoPosArr)
            tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
            dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
            dVec = dVec[:, :2]
            newDist = np.power(dVec[:, 0], 2) + np.power(dVec[:, 1], 2)
            
            # cut
            cut = int(len(dVec) * cutPercent/100.0)
            tempTracks = tempTracks[newDist.argsort()]
            tempTracks = tempTracks[:-cut]
        
        return tempTracks

    def alignModules(self):
        # TODO: multi-thread sectors
        for sector in range(10):
            for path, matrix in self.testICPalignWithOutlierDiscard(sector):
                self.alignMatrices[path] = np.ndarray.tolist(np.ndarray.flatten(matrix))
    
    def saveMatrices(self, fileName):
        with open(fileName, 'w') as f:
            json.dump(self.alignMatrices, f, indent=2)

    #* this is the best one yet. out-source the histogram stuff to the comparator and calculate anchor points, then you are done!
    # FIXME: oh and preTransform only works for sector 0, fix that
    # TODO: after that, rename function, this is the main aligner now
    def testICPalignWithOutlierDiscard(self, sector=0):

        # check if anchor points were set and sector is valid
        assert hasattr(self, 'anchorPoints') 
        assert (sector > -1) and (sector < 10)

        print(f'==========================================')
        print(f'')
        print(f'    Running for sector {sector}!')
        print(f'')
        print(f'==========================================')

        preTransform = False
        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        # get relevant module paths
        modulePaths = self.reader.getModulePathsInSector(sector)

        # make 4x4 matrices to module positions
        moduleMatrices = np.zeros((4,4,4))
        for i in range(len(modulePaths)):
            path = modulePaths[i]
            moduleMatrices[i] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)

        # calc average misalignment
        #* -----------------  compute actual matrices
        misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'
        # misMatPath = '/media/DataEnc2TBRaid1/Arbeit/LMDscripts/input/misMat-aligned-1.00.json'
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
        for p in misalignmatrices:
            misalignmatrices[p] = np.array(misalignmatrices[p]).reshape((4,4))

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatrices[path]
            mat = mat + thisMat
        
        # print(f'average shift of first four modules:')
        averageShift = mat/4.0
        # print(averageShift*1e4)
        #* -----------------  end compute actual matrices

        # get Reco Points from reader
        # TODO: update format or read with uproot directly!
        allTracks = self.reader.getAllTracksInSector(sector)

        #? new format! np array with track oris, track dirs, and recos
        nTrks = len(allTracks)
        newTracks = np.ones((nTrks, 6, 4))

        for i in range(nTrks):
            newTracks[i, 0, :3] = allTracks[i]['trkPos']
            newTracks[i, 1, :3] = allTracks[i]['trkMom']
            newTracks[i, 2, :3] = allTracks[i]['recoHits'][0]['pos']
            newTracks[i, 3, :3] = allTracks[i]['recoHits'][1]['pos']
            newTracks[i, 4, :3] = allTracks[i]['recoHits'][2]['pos']
            newTracks[i, 5, :3] = allTracks[i]['recoHits'][3]['pos']


        #? end new format! np array with track oris, track dirs, and recos

        # use only N tracks:
        # newTracks = newTracks[:10000]

        #* =========== preapare raw data

        sectorString = str(sector)

        # transform all recos to LMD local
        if preTransform:
            matToLMD = np.linalg.inv(np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4)))
            for i in range(4):
                newTracks[:,i + 2] = (matToLMD @ newTracks[:,i + 2].T).T
        
        # transform anchorPoints to PANDA global
        else:
            matFromLMD = np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4))
            self.anchorPoints[sectorString] = (matFromLMD @ self.anchorPoints[sectorString])
        

        # do a first track fit, otherwise we have no starting tracks
        recos = newTracks[:,2:6]
        corrFitter = CorridorFitter(recos)
        corrFitter.useAnchorPoint(self.anchorPoints[sectorString][:3])
        resultTracks = corrFitter.fitTracksSVD()
        
        # update current tracks
        newTracks[:,0,:3] = resultTracks[:,0]
        newTracks[:,1,:3] = resultTracks[:,1]

        # prepare total matrices
        totalMatrices = np.zeros((4,4,4))
        for i in range(4):
            totalMatrices[i] = np.identity(4)

        newTracks = self.dynamicTrackCut(newTracks, 5)
        
        #* =========== iterate cuts and calculation
        iterations = 3
        for _ in range(iterations):

            newTracks = self.dynamicRecoTrackDistanceCut(newTracks)
            
            # 4 planes per sector
            for i in range(4):
                trackPosArr = newTracks[:, 0, :3]
                trackDirArr = newTracks[:, 1, :3]
                recoPosArr = newTracks[:, 2+i, :3]

                # norm momentum vectors, this is important for the distance formula!
                trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

                # vectorized distance calculation
                tempV1 = (trackPosArr - recoPosArr)
                tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
                dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
                
                # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
                pIntersection = recoPosArr+dVec
                
                # we want FROM tracks TO recos
                T0inv = self.getMatrix(recoPosArr, pIntersection, False)

                totalMatrices[i] = T0inv @ totalMatrices[i]

                # transform recos
                newTracks[:, i + 2] = (T0inv @ newTracks[:, i + 2].T).T
            
            # direction cut again
            newTracks = self.dynamicTrackCut(newTracks, 1)
                       
            # do track fit
            corrFitter = CorridorFitter(newTracks[:,2:6])
            resultTracks = corrFitter.fitTracksSVD()
            
            # update current tracks
            newTracks[:,0,:3] = resultTracks[:,0]
            newTracks[:,1,:3] = resultTracks[:,1]
            
        #* =========== store matrices
        # 4 planes per sector
        for i in range(4):
            # ideal module matrices!
            toModMat = np.linalg.inv(moduleMatrices[i])
            
            if preTransform:

                # so yeah, transform matrices from LMD to PANDA then to module, that should do it
                totalMatrices[i] = np.linalg.inv(matToLMD) @ totalMatrices[i] @ (matToLMD)
                totalMatrices[i] = (toModMat) @ totalMatrices[i] @ np.linalg.inv(toModMat)

                totalMatrices[i] = totalMatrices[i] + averageShift
                dMat = totalMatrices[i] - misalignmatrices[modulePaths[i]]
                print(f'\nWITH previous trafo, total diff:\n{(dMat)*1e4}')
                yield modulePaths[i], totalMatrices[i]
            
            else:
                # transform to module
                totalMatrices[i] = (toModMat) @ totalMatrices[i] @ np.linalg.inv(toModMat)
       
                totalMatrices[i] = totalMatrices[i] + averageShift
                dMat = totalMatrices[i] - misalignmatrices[modulePaths[i]]
                print(f'\nno previous trafo, better diff:\n{(dMat)*1e4}')
                yield modulePaths[i], totalMatrices[i]
            print(f' ------------- next -------------')
        
        return

    def getMatrix(self, trackPositions, recoPositions, use2D=False):

        # use 2D, use only in LMD local!
        if use2D:
            T, _, _ = icp.best_fit_transform(trackPositions[..., :2], recoPositions[..., :2])

            # homogenize
            resultMat = np.identity(4)
            resultMat[:2, :2] = T[:2, :2]
            resultMat[:2, 3] = T[:2, 2]
            return resultMat

        else:
            T, _, _ = icp.best_fit_transform(trackPositions, recoPositions)
            return T

    def alignMillepede(self):

        # TODO: sort better by sector!
        sector = 0

        milleOut = f'output/millepede/moduleAlignment-sector{sector}-aligned.bin'

        MyMille = pyMille.Mille(milleOut, True, True)
        
        # sigmaScale = 2.11*1.74*1.71*1.09
        sigmaScale = 6.85 # mille wants it so
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

            if (gotems % 250) == 0:
                    endCalls += 1
                    MyMille.end()

        MyMille.end()

        print(f'Mille binary data ({gotems} records) written to {milleOut}!')
        print(f'endCalls: {endCalls}')
        # now, pede must be called
    
        # with open('writtenData.txt', 'w') as f:
            # f.write(outFile)