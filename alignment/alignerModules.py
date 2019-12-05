#!/usr/bin/env python3

# from alignment.modules.sectorContainer import sectorContainer
from alignment.modules.trackFitter import CorridorFitter
from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

import detail.matrixInterface as mi

import concurrent
import numpy as np
#import pyMille
import random
import re
import subprocess
import sys

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- determine distance from recos to tracks
- move recos with this matrix
- iteratively repeat

#TODO: maybe also do with millepede
"""

class alignerModules:
    def __init__(self):
        self.alignMatrices = {}
        self.reader = trackReader()
        self.iterations = 5
        print(f'reading detector parameters...')
        self.reader.readDetectorParameters()
        self.__debug = False

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        temp.readAnchorPoints(runConfig.moduleAlignAnchorPointFile)
        temp.readAverageMisalignments(runConfig.moduleAlignAvgMisalignFile)
        return temp    

    # words cannot describe how ugly this is, but I'm pressed for time and aesthetics wont get me my phd
    def convertRootTracks(self, dataPath, outJsonFile):
        rootArgs=f'convertRootTracks.C("{str(dataPath)}","{str(outJsonFile)}")'
        subprocess.run(['root', '-l', '-q', rootArgs], cwd='alignment/modules')

    def readTracks(self, fileName):
        print(f'reading processed tracks file...')
        self.reader.readTracksFromJson(fileName)
        # TODO: read from root file directly and use new track format from the start

    def readAnchorPoints(self, fileName):
        self.anchorPoints = mi.loadMatrices(fileName, False)

    def readAverageMisalignments(self, fileName):
        self.avgMisalignments = mi.loadMatrices(fileName)

    def setIterations(self, iterations):
        self.iterations = iterations
    
    #? cuts on track x,y direction
    def dynamicTrackCut(self, newTracks, cutPercent=2):
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

        if not self.__debug:
            for sector in range(10):
                for path, matrix in self.alignSectorICP(sector):
                    self.alignMatrices[path] = matrix
        else:
            for path, matrix in self.alignSectorICP(2):
                self.alignMatrices[path] = matrix

        return

        # TODO: multi-thread sectors
        # maxThreads = 10
        # print(f'running in {maxThreads} threads.')
        
        # with concurrent.futures.ThreadPoolExecutor(max_workers=maxThreads) as executor:
        #     # Start the load operations and mark each future with its URL
        #     for sector in range(10):
        #         executor.submit(self.alignSectorICP, sector)

        # print('waiting for all jobs...')
        # executor.shutdown(wait=True)

    def saveMatrices(self, fileName):
        mi.saveMatrices(self.alignMatrices, fileName)

    def alignSectorICP(self, sector=0):
        # check if anchor points were set
        assert hasattr(self, 'anchorPoints') 

        preTransform = True
        useOldFormat = True     # don't change yet, new format is not ready yet!

        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        # get relevant module paths
        modulePaths = self.reader.getModulePathsInSector(sector)

        # make 4x4 matrices to module positions
        moduleMatrices = np.zeros((4,4,4))
        for i in range(len(modulePaths)):
            path = modulePaths[i]
            moduleMatrices[i] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)

        #* use average misalignment
        averageShift = self.avgMisalignments[str(sector)]

        # get Reco Points from reader
        # TODO: update format or read with uproot directly!
        if useOldFormat:
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
        else:
            raise Exception(f'new track format is not implemented yet!')

        # use only N tracks:
        # newTracks = newTracks[:10000]

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
        
        print(f'==================================================')
        print(f'        module aligner for sector {sector}')
        print(f'==================================================')

        print(f'number of tracks: {len(newTracks)}')
        print(f'anchor point: {self.anchorPoints[sectorString]}')

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
        for iIteration in range(self.iterations):
            print(f'running iteration {iIteration}, {len(newTracks)} tracks remaining...')
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

                # print(f'{newTracks[0]}\n\n')
                if self.__debug and i == 0:
                    #* ----------------- begin hist here
                    import matplotlib
                    import matplotlib.pyplot as plt
                    from matplotlib.colors import LogNorm

                    # dTest = dVec
                    dTest1 = trackPosArr
                    dTest2 = trackDirArr
                    dTest3 = recoPosArr
                    dTest4 = dVec

                    # fig = plt.figure(figsize=(16/2.54, 9/2.54))
                    fig = plt.figure(figsize=(16/2.54, 16/2.54))

                    axis2 = fig.add_subplot(2,2,1)
                    axis2.hist2d(dTest1[:, 0]*1e4, dTest1[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-150,150), (-150,150)))
                    axis2.set_title(f'trackPos dx vs dy, nTrks: {len(dVec)}')
                    axis2.yaxis.tick_left()
                    axis2.set_xlabel('dx [µm]')
                    axis2.set_ylabel('dy [µm]')
                    axis2.tick_params(direction='out')
                    axis2.yaxis.set_label_position("left")

                    axis3 = fig.add_subplot(2,2,2)
                    axis3.hist2d(dTest2[:, 0]*1e4, dTest2[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-150,150), (-150,150)))
                    axis3.set_title(f'trackDir dx vs dy, nTrks: {len(dVec)}')
                    axis3.yaxis.tick_right()
                    axis3.set_xlabel('dx [µm]')
                    axis3.set_ylabel('dy [µm]')
                    axis3.tick_params(direction='out')
                    axis3.yaxis.set_label_position("right")

                    axis4 = fig.add_subplot(2,2,3)
                    axis4.hist2d(dTest3[:, 0]*1e4, dTest3[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-150,150), (-150,150)))
                    axis4.set_title(f'recoPos dx vs dy, nTrks: {len(dVec)}')
                    axis4.yaxis.tick_left()
                    axis4.set_xlabel('dx [µm]')
                    axis4.set_ylabel('dy [µm]')
                    axis4.tick_params(direction='out')
                    axis4.yaxis.set_label_position("left")

                    axis5 = fig.add_subplot(2,2,4)
                    axis5.hist2d(dTest4[:, 0]*1e4, dTest4[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-150,150), (-150,150)))
                    axis5.set_title(f'dVec dx vs dy, nTrks: {len(dVec)}')
                    axis5.yaxis.tick_right()
                    axis5.set_xlabel('dx [µm]')
                    axis5.set_ylabel('dy [µm]')
                    axis5.tick_params(direction='out')
                    axis5.yaxis.set_label_position("right")


                    # axisZ = fig.add_subplot(1,2,2)
                    # axisZ.hist(dTest1[:, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
                    # axisZ.set_title(f'dz')
                    # axisZ.yaxis.tick_right()
                    # axisZ.set_xlabel('dz [µm]')
                    # axisZ.set_ylabel('count')
                    # axisZ.yaxis.set_label_position("right")

                    fig.tight_layout()
                    fig.savefig(f'output/alignmentModules/test/trackDirections/sec{sector}-it{iIteration}-plane{i}.png')
                    plt.close(fig)
                    #* ----------------- end hist here

                # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
                pIntersection = recoPosArr+dVec
                
                # we want FROM tracks TO recos
                T0inv = self.getMatrix(recoPosArr, pIntersection, preTransform)
                # T0inv = self.getMatrix(recoPosArr, pIntersection)
                totalMatrices[i] = T0inv @ totalMatrices[i]

                if self.__debug and i == 0:
                    print(f'current Matrix:\n{T0inv}\ntotal matrix:\n{totalMatrices[i]}')

                # transform recos
                newTracks[:, i + 2] = (T0inv @ newTracks[:, i + 2].T).T
            
            # direction cut again
            if iIteration < 5:
                newTracks = self.dynamicTrackCut(newTracks, 1)
                       
            # do track fit
            corrFitter = CorridorFitter(newTracks[:,2:6])
            resultTracks = corrFitter.fitTracksSVD()
            
            # update current tracks
            newTracks[:,0,:3] = resultTracks[:,0]
            newTracks[:,1,:3] = resultTracks[:,1]
            print(f'\nnewTracks[0]:\n{newTracks[0]}\n')
            
        #! ------------ cheat here. for now
        actualMats = mi.loadMatrices('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
        print(f'mats loaded')
        #! ------------ end cheat here.
        
        #* =========== store matrices
        # 4 planes per sector
        totalMatricesTransformed = {}
        totalMatricesTransformedPlusAvg = {}
        for i in range(4):
            # ideal module matrices!
            toModMat = np.linalg.inv(moduleMatrices[i])
            
            # TODO: use baseTransform from matrix interface here
            if preTransform:
                totalMatricesTransformed[i] = np.linalg.inv(matToLMD) @ totalMatrices[i] @ (matToLMD)
                totalMatricesTransformed[i] = (toModMat) @ totalMatricesTransformed[i] @ np.linalg.inv(toModMat)
            else:
                totalMatricesTransformed[i] = (toModMat) @ totalMatrices[i] @ np.linalg.inv(toModMat)
       
            # add average shift
            # Attention! You can't just add two matrices, multiply them!
            totalMatricesTransformedPlusAvg[i] = totalMatricesTransformed[i] @ averageShift

            #! ------------ cheat here. for now
            print(f'\n\n======================')
            print(f'big cheat here:')
            print(f'path: {modulePaths[i]}')
            print(f'averageShift:\n{averageShift}')
            print(f'totalMatrices[i]:\n{totalMatrices[i]}')
            print(f'totalMatricesTransformed[i]:\n{totalMatricesTransformed[i]}')
            print(f'totalMatricesTransformedPlusAvg[i]:\n{totalMatricesTransformedPlusAvg[i]}')
            print(f'actualMats[i]:\n{actualMats[modulePaths[i]]}')
            print(f'DIFFERENCE (1e4):\n{(actualMats[modulePaths[i]]-totalMatricesTransformedPlusAvg[i])*1e4}')
            print(f'======================\n\n')
            #! ------------ end cheat here.


            yield modulePaths[i], totalMatricesTransformedPlusAvg[i]
        
        print(f'-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
        print(f'        module aligner for sector {sector} done!         ')
        print(f'-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
        return

    # TODO externalize, same as for sensor aligner!
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