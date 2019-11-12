#!/usr/bin/env python3

# from alignment.modules.sectorContainer import sectorContainer
from alignment.modules.trackFitter import CorridorFitter
from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
from tqdm import tqdm

import copy
import json
import numpy as np
import pyMille
import random
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
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-modules-1.00.json'))
        
        
        # from good-ish tracks
        self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-modulesNoRot-1.00.json'))
        
        # merged Tracks from modulesNoRot-1.00
        # WARNING! there is something wrong on layers 1&2 here!
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-noTrks-chain.json'))
       
       
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-noTrks.json'))
        # self.reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed-aligned.json'))

    
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


    def dynamicCutOne(self, cloud, cutPercent=2, matrixToFoR=None):
        
        if matrixToFoR is not None:
            # transform cloud hits here
            pass
        
        com = np.average(cloud, axis=0)

        # shift newhit2 by com of differences
        newhit2 = cloud - com
        newDist = np.power(newhit2[:, 0], 2) + np.power(newhit2[:, 1], 2)

        cut = int(len(newhit2) * cutPercent/100.0)
        cloud = cloud[newDist.argsort()]
        cloud = cloud[:-cut]
        return cloud
    
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

    # TODO: deprecate, use vectorized version in trasnformRecos
    def transformRecoHit(self, point, matrix):
        # vector must be row-major 3 vector
        assert len(point) == 3

        # homogenize
        vecH = np.ones(4)
        vecH[:3] = point

        # make 2D array, reshape and transpose
        vecH = vecH.reshape((1,4)).T

        # perform actual transform
        vecH = matrix @ vecH

        # de-homogenize
        vecNew = vecH[:3] / vecH[3]
        
        # and re-transpose
        vecNew = vecNew.T.reshape(3)

        return vecNew

    def getTracksOnModule(self, allTracks, modulePath):

        filteredTracks = []

        # TODO: express the outer loop as list comprehension as well, for speedup
        for track in allTracks:
            # filter relevant recos
            # track['recoHits'] = [x for x in track['recoHits'] if ( self.getPathModuleFromSensorID(x['sensorID']) == modulePath) ]
            newtrack = copy.deepcopy(track)
            goodRecos = [x for x in track['recoHits'] if ( self.reader.getPathModuleFromSensorID(x['sensorID']) == modulePath) ]
            
            if len(goodRecos) == 1:
                newtrack['recoPos'] = goodRecos[0]['pos']
                # this info is not needed anymore
                newtrack.pop('recoHits', None)
                filteredTracks.append(newtrack)
        
        # return just the newTracks list of dicts, the mouleAligner will take it from here
        return filteredTracks

    # oen way function, the results go to track fitter and are then discarded
    def getAllRecosFromAllTracks(self, allTracks):
        nTrks = len(allTracks)

        # this array has nTrks entries, each entry has 4 reco hits, each reco hit has 3 values
        recoPosArr = np.zeros((nTrks, 4, 3))

        for i in range(nTrks):
            nRecos = len(allTracks[i]['recoHits'])
            if nRecos != 4:
                print('listen. you fucked up.')
                continue

            for j in range(nRecos):
                recoPosArr[i, j] = allTracks[i]['recoHits'][j]['pos']
        
        return recoPosArr

    #* this function modifies the resident data! be careful!
    # allTracks is all data
    # matrices is a dict modulePath->np.array() 
    def transformRecos(self, allTracks, matrices, inverse=False):

        # TODO: this can be vectorized by:
        # first writing all reco points to 4 arrays
        # then transforming the arrays vectorized
        # then reassigning the new reco values

        for track in allTracks:

            # loop over reco hits
            for reco in track['recoHits']:

                # for every reco hit, find path from sensorID
                thisPath = self.reader.getPathModuleFromSensorID(reco['sensorID'])

                # transform reco hit using matrix from matrices
                if inverse:
                    reco['pos'] = self.transformRecoHit( reco['pos'], np.linalg.inv(matrices[thisPath]) )
                else:
                    reco['pos'] = self.transformRecoHit( reco['pos'], matrices[thisPath] )

        return allTracks

    #* this function modifies the resident data! be careful!
    # allTracks is (reference to) all data
    # matrices is a dict modulePath->np.array() 
    def updateTracks(self, allTracks, newTracks):
        assert len(newTracks) == len(allTracks)
        nTrks = len(newTracks)

        for i in range(nTrks):
            allTracks[i]['trkPos'] = newTracks[i][0]
            allTracks[i]['trkMom'] = newTracks[i][1]
        
        return allTracks

    def getRecosFromAlltracks(self, filteredTracks):
        
        nTrks = len(filteredTracks)
        recoPosArr = np.zeros((nTrks, 3))
        for i in range(nTrks):
            recoPosArr[i] = filteredTracks[i]['recoPos']
        return recoPosArr
    
    def baseTransformMatrix(self, matrix, basisMatrix, inverse=False):
        if inverse:
            return basisMatrix @ matrix @ np.linalg.inv(basisMatrix)
        else: 
            return np.linalg.inv(basisMatrix) @ matrix @ basisMatrix
    
    # one way function, the results are only important for matrix finder and are then discarded
    # filteredTracks are the tracks for a single module with a single reco hit!
    def getTrackPosFromTracksAndRecos(self, filteredTracks):
        
        nTrks = len(filteredTracks)
                
        trackPosArr = np.zeros((nTrks, 3))
        trackDirArr = np.zeros((nTrks, 3))
        recoPosArr = np.zeros((nTrks, 3))
        # dVecTest = np.zeros((nTrks, 3))

        for i in range(nTrks):
            trackPosArr[i] = filteredTracks[i]['trkPos']
            trackDirArr[i] = filteredTracks[i]['trkMom']
            recoPosArr[i] = filteredTracks[i]['recoPos']

        # optionally, transform the track to a different frame of reference

        # compare this with the vectorized version
        # for i in range(nTrks):
        #     # normalize fukn direction here, again
        #     trackDirArr[i] /= np.linalg.norm(trackDirArr[i])
        #     dVecTest[i] = ((trackPosArr[i] - recoPosArr[i]) - np.dot((trackPosArr[i] - recoPosArr[i]), trackDirArr[i]) * trackDirArr[i])

        # norm momentum vectors, this is important for the distance formula!
        trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

        # vectorized version, much faster
        tempV1 = (trackPosArr - recoPosArr)
        tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
        dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
        
        # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
        pIntersection = recoPosArr+dVec
        # pIntersection = recoPosArr+dVecTest
        return pIntersection, recoPosArr

    def applyNoiseToRecos(self, allTracks, sigma, multipleScattering):
        
        mu = 0
        for track in allTracks:
            for reco in track['recoHits']:
                dx = random.gauss(mu, sigma)
                dy = random.gauss(mu, sigma)

                if multipleScattering:
                    # get plane
                    thisRecoPath = self.reader.getPathModuleFromSensorID(reco['sensorID'])
                    _, plane, _, _ = self.reader.getParamsFromModulePath(thisRecoPath)

                    MSsigma = plane * 25.0*1e-4
                    dx += random.gauss(mu, MSsigma)
                    dy += random.gauss(mu, MSsigma)

                # generate matrix
                matrix = np.identity(4)
                matrix[0,3] = dx
                matrix[1,3] = dy

                # transform reco hit using matrix from matrices
                reco['pos'] = self.transformRecoHit( reco['pos'], matrix)

        return allTracks
    
    def prepareSynthDataOLD(self, sector):
        
        synthData = self.reader.readSyntheticDate('testscripts/LMDPoints_processed.json')
        nMCtrks = len(synthData)

        # filter by sector 0
        sector0 = []
        # sector = 0
        print(f'starting to sort {nMCtrks} tracks...')

        # for sector in range(10):

        # select only corridor 0
        for event in synthData:
            tempPoints = []
            for point in event:
                path = self.reader.getPathModuleFromSensorID( point[3] )
                _, _, _, thissector = self.reader.getParamsFromModulePath(path)
                
                if thissector == sector:
                    tempPoints.append(point)
            
            if len(tempPoints) == 4:
                temparray = np.array(tempPoints)
                # print(temparray)
                sector0.append(temparray)

        print(f'done, {len(sector0)} left.')

        # prepare empty allTracks list
        allTracks = []
        for i in range(len(sector0)):
            thisTrack = {}
            thisTrack['recoHits'] = []

            for point in sector0[i]:
                recoPoint = {}
                recoPoint['pos'] = point[:3]
                recoPoint['sensorID'] = int(point[3])
                thisTrack['recoHits'].append(recoPoint)

            allTracks.append(thisTrack)

        print(f'=== allTracks is now {len(allTracks)} entries long.')

        modulePaths = self.reader.getModulePathsInSector(sector)
        misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'

        #! cheat hard here for now:
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
            
        with open(misMatPath) as f:
            misalignmatricesOriginal = json.load(f)
        
        # make 4x4 matrices
        moduleMatrices = {}
        for path in misalignmatrices:
            moduleMatrices[path] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)
            misalignmatrices[path] = np.array(misalignmatrices[path]).reshape((4,4))
            misalignmatricesOriginal[path] = np.array(misalignmatricesOriginal[path]).reshape((4,4))

        # transform accoring to calculations
        for path in misalignmatrices:
            mis = misalignmatrices[path]
            modMat = moduleMatrices[path]
            mis = modMat @ mis @ np.linalg.inv(modMat)
            misalignmatrices[path] = mis

        #! ====================  apply misalignment
        allTracks = self.transformRecos(allTracks, (misalignmatrices))

        print(f'recos "misaligned". performing first track fit.')

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatricesOriginal[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)
        
        #! apply 23mu noise and multiple scattering
        # this works only if the points are transformed to LMD local!
        # allTracks = self.applyNoiseToRecos(allTracks, 23.0*1e-4, True)
        use2D = False

        #! define anchor point
        print(f'performing first track fit.')
        anchorPoint = [-18.93251088, 0.0, 2.51678065]
        
        recos = self.getAllRecosFromAllTracks(allTracks)
        corrFitter = CorridorFitter(recos)
        # corrFitter.useAnchorPoint(anchorPoint)
        resultTracks = corrFitter.fitTracksSVD()
        allTracks = self.updateTracks(allTracks, resultTracks)
    
        #* allTracks now look just like real data
        print(f'track fit complete.')
       
        print('\n\n')
        print(f'===================================================================')
        print(f'Inital misalignment:')
        print(f'===================================================================')
        print('\n\n')

        # np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        for path in modulePaths:
            filteredTracks = self.getTracksOnModule(allTracks, path)
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)
            trackPos, recoPos = self.dynamicCut(trackPos, recoPos, 5)

            #? 1: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos, use2D)

            print('after transform:')
            matrix1 = T0
            toModMat = moduleMatrices[path]

            # transform matrix to module?
            matrix10 = np.linalg.inv(toModMat) @ matrix1 @ (toModMat)
            matrix10  = matrix10 + averageShift
            print(f'transformed normal:\n{matrix10*1e4}')
            print(f'actual:\n{misalignmatricesOriginal[path]*1e4}')
            print(f'\nDIFF:\n{(matrix10-misalignmatricesOriginal[path])*1e4}\n\n')
            print(f' ------------- next -------------')

        #* okay, fantastic, the matrices are identiy matrices. that means at least distance LMDPoint to mc track works 

        print(f'\n\n\n')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'\n\n\n')
        return

    def testICPalignWithOutlierDiscard(self, sector=0):

        print(f'==========================================')
        print(f'')
        print(f'    Running for sector {sector}!')
        print(f'')
        print(f'==========================================')

        preTransform = True
        histDat = True

        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        assert (sector > -1) and (sector < 10)

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
        # misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-singlePlane-1.00.json'
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
        for p in misalignmatrices:
            misalignmatrices[p] = np.array(misalignmatrices[p]).reshape((4,4))

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatrices[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)
        #* -----------------  end compute actual matrices

        # get Reco Points from reader
        allTracks = self.reader.getAllTracksInSector(sector)

        #! new format! np array with track oris, track dirs, and recos

        nTrks = len(allTracks)
        newTracks = np.ones((nTrks, 6, 4))

        for i in range(nTrks):
            newTracks[i, 0, :3] = allTracks[i]['trkPos']
            newTracks[i, 1, :3] = allTracks[i]['trkMom']
            newTracks[i, 2, :3] = allTracks[i]['recoHits'][0]['pos']
            newTracks[i, 3, :3] = allTracks[i]['recoHits'][1]['pos']
            newTracks[i, 4, :3] = allTracks[i]['recoHits'][2]['pos']
            newTracks[i, 5, :3] = allTracks[i]['recoHits'][3]['pos']

        # use only N tracks:
        newTracks = newTracks[:10000]

        # transform all recos, ignore tracks

        if preTransform:
            matToLMD = np.linalg.inv(np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4)))
            for i in range(4):
                newTracks[:,i + 2] = (matToLMD @ newTracks[:,i + 2].T).T

        # do a first track fit, otherwise we have no starting tracks
        recos = newTracks[:,2:6]

        # anchor for sector0
        # anchorPoint = [0.0, 0.0, -1110.5, 1.0]
        
        # anchor for sector1
        anchorPoint = [0.0, 0.0, -1110.5, 1.0]
        
        
        if not preTransform:
            matToLMD = np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4))
            anchorPoint = (matToLMD @ anchorPoint)

        corrFitter = CorridorFitter(recos)
        corrFitter.useAnchorPoint(anchorPoint[:3])
        resultTracks = corrFitter.fitTracksSVD()
        
        # update current tracks
        newTracks[:,0,:3] = resultTracks[:,0]
        newTracks[:,1,:3] = resultTracks[:,1]

        # prepare total matrices
        totalMatrices = np.zeros((4,4,4))
        for i in range(4):
            totalMatrices[i] = np.identity(4)

        newTracks = self.dynamicTrackCut(newTracks, 5)
        
        iterations = 5
        for iIteration in tqdm(range(iterations)):

            if histDat:
                #! begin hist
                import matplotlib
                import matplotlib.pyplot as plt
                from matplotlib.colors import LogNorm
                
                # plot difference hit array
                fig = plt.figure(figsize=(9/2.54, 9/2.54))
                
                axis = fig.add_subplot(1,1,1)
                axis.hist2d(newTracks[:, 1, 0]*1e4, newTracks[:, 1, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-300,300), (-300,300)))
                axis.set_title(f'track px vs py')
                axis.yaxis.tick_left()
                axis.set_xlabel('px [µm]')
                axis.set_ylabel('py [µm]')
                axis.tick_params(direction='out')
                axis.yaxis.set_label_position("left")

                # axis2 = fig.add_subplot(1,2,2)
                # axis2.hist(newTracks[:, 1, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
                # axis2.set_title(f'pz')
                # axis2.yaxis.tick_right()
                # axis2.set_xlabel('pz [µm]')
                # axis2.set_ylabel('count')
                # axis2.yaxis.set_label_position("right")

                fig.tight_layout()
                fig.savefig(f'output/alignmentModules/test/trackDirections/sec{sector}-it{iIteration}.png')
                plt.close(fig)
                #! end hist

            
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
                
                if histDat:

                    #! begin hist
                    # dVec = pIntersection - recoPosArr

                    fig = plt.figure(figsize=(16/2.54, 9/2.54))
                    axis2 = fig.add_subplot(1,2,1)
                    axis2.hist2d(dVec[:, 0]*1e4, dVec[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-300,300), (-300,300)))
                    axis2.set_title(f'track/reco dx vs dy')
                    axis2.yaxis.tick_left()
                    axis2.set_xlabel('dx [µm]')
                    axis2.set_ylabel('dy [µm]')
                    axis2.tick_params(direction='out')
                    axis2.yaxis.set_label_position("left")

                    axis3 = fig.add_subplot(1,2,2)
                    axis3.hist(dVec[:, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
                    axis3.set_title(f'dz')
                    axis3.yaxis.tick_right()
                    axis3.set_xlabel('dz [µm]')
                    axis3.set_ylabel('count')
                    axis3.yaxis.set_label_position("right")

                    fig.tight_layout()
                    fig.savefig(f'output/alignmentModules/test/trackDirections/sec{sector}-it{iIteration}-plane{i}.png')
                    plt.close(fig)

                    #! end hist


                # switch point cloud order, we want FROM tracks TO recos
                T0inv = self.getMatrix(recoPosArr, pIntersection, True)

                totalMatrices[i] = T0inv @ totalMatrices[i]

                # transform recos
                newTracks[:, i + 2] = (T0inv @ newTracks[:, i + 2].T).T
            # print(f'--------------------------------------')
            
            # direction cut again
            newTracks = self.dynamicTrackCut(newTracks, 1)
                       
            # do track fit
            corrFitter = CorridorFitter(newTracks[:,2:6])
            resultTracks = corrFitter.fitTracksSVD()
            
            # update current tracks
            newTracks[:,0,:3] = resultTracks[:,0]
            newTracks[:,1,:3] = resultTracks[:,1]
            
        # 4 planes per sector
        for i in range(4):
            toModMat = moduleMatrices[i]
            if preTransform:
                totalMatrices[i] = totalMatrices[i] + averageShift
                print(f'\nWITH previous trafo, total diff:\n{(totalMatrices[i] - misalignmatrices[modulePaths[i]])*1e4}')
            else:
                totalMatrices[i] = np.linalg.inv(toModMat) @ totalMatrices[i] @ (toModMat)
                totalMatrices[i] = totalMatrices[i] + averageShift
                print(f'\nno previous trafo, better diff:\n{(totalMatrices[i] - misalignmatrices[modulePaths[i]])*1e4}')
            print(f' ------------- next -------------')
        
        return

    #* this one is pretty close to completion, outlier rejection and performance improvents are missing
    def alignICP(self, sector=0):
        np.set_printoptions(precision=3)
        np.set_printoptions(suppress=True)

        assert (sector > -1) and (sector < 10)

        # get relevant module paths
        modulePaths = self.reader.getModulePathsInSector(sector)

        # make 4x4 matrices
        moduleMatrices = {}
        for path in modulePaths:
            moduleMatrices[path] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)

        # get Reco Points from reader
        allTracks = self.reader.getAllTracksInSector(sector)

        # this one works, but I prefer to go a different way
        # anchorPoint = [-18.93251088, 0.0, 2.51678065]

        anchorPoint = [0.0, 0.0, -1110.5, 1.0]
        matToLMD = np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4))
        anchorPoint = (matToLMD @ anchorPoint)[:3]

        print(f'anchorPoint: {anchorPoint}')

        # do a first track fit, otherwise we have no starting tracks
        print(f'performing first track fit.')
        recos = self.getAllRecosFromAllTracks(allTracks)
        corrFitter = CorridorFitter(recos)
        corrFitter.useAnchorPoint(anchorPoint)
        resultTracks = corrFitter.fitTracksSVD()
        allTracks = self.updateTracks(allTracks, resultTracks)

        # first track fit is done, I have basic tracks and recos now 

        # TODO: move this to the comparator, it's the only one who is allowed to cheat. same goes for the stuff down below
        #* -----------------  compute actual matrices
        misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'
        # misMatPath = '/media/DataEnc2TBRaid1/Arbeit/LMDscripts/input/misMat-aligned-1.00.json'
        # misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-singlePlane-1.00.json'
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
        for p in misalignmatrices:
            misalignmatrices[p] = np.array(misalignmatrices[p]).reshape((4,4))

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatrices[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)

        #* -----------------  end compute actual matrices

        print('\n\n')
        print(f'===================================================================')
        print(f'Inital misalignment:')
        print(f'===================================================================')
        print('\n\n')

        for path in modulePaths:

            # if path != '/cave_1/lmd_root_0/half_0/plane_0/module_0':
                # continue

            filteredTracks = self.getTracksOnModule(allTracks, path)
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)
            trackPosCut, recoPosCut = self.dynamicCut(trackPos, recoPos, 5)

            T0 = self.getMatrix(trackPosCut, recoPosCut)

            # print('after transform:')
            T0inv = np.linalg.inv(T0)
            toModMat = moduleMatrices[path]

            # transform matrix to module?
            T0inPnd = np.linalg.inv(toModMat) @ T0inv @ (toModMat)
            T0inPnd = T0inPnd + averageShift
            # totalInPnd = np.linalg.inv(toModMat) @ totalMatrices[path] @ (toModMat)
            # totalInPnd = totalInPnd + averageShift

            print(f'T0inv:\n{T0inv*1e4}')
            print(f'diff:\n{(T0inPnd - misalignmatrices[path])*1e4}')
            # print(f'total matrix:\n{totalInPnd*1e4}')
            # print(f'actual matrix:\n{misalignmatrices[path]*1e4}')
            # print(f'\nbetter diff:\n{(totalInPnd - misalignmatrices[path])*1e4}')
            print(f' ------------- next -------------')

        print(f'\n\n\n')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'\n\n\n')

        #! ------- iterative part here

        iterations = 50
        alignMatrices = {}
        totalMatrices = {}

        for path in modulePaths:
            totalMatrices[path] = np.identity(4)

        for i in tqdm(range(iterations)):
            
            # for all four modules in sector
            
            for path in modulePaths:

                # steps:

                # 1 determine current trafo matrix
                filteredTracks = self.getTracksOnModule(allTracks, path)
                trackPosHere, recoPosHere = self.getTrackPosFromTracksAndRecos(filteredTracks)
                # trackPosCut, recoPosCut = self.dynamicCut(trackPos, recoPos, 5)

                T0 = self.getMatrix(trackPosHere, recoPosHere)

                # print('after transform:')
                T0inv = np.linalg.inv(T0)
                # T0inv = T0
                # print(path)
                # if path == '/cave_1/lmd_root_0/half_0/plane_0/module_0':
                #     toModMat = moduleMatrices[path]

                #     print(f'T0inv in pnd:\n{self.baseTransformMatrix(T0inv, toModMat) *1e4}')
                #     print(f'totalMatrices:\n{totalMatrices[path]*1e4}')

                alignMatrices[path] = T0inv
                totalMatrices[path] = T0inv @ totalMatrices[path]
                # totalMatrices[path] = totalMatrices[path] @ T0inv


            # 1 shift recos according to last transformation matrix
            # print(f'first track before:\n{allTracks[0]["recoHits"][0]["pos"]}')
            allTracks = self.transformRecos(allTracks, alignMatrices)
            # print(f'first track after:\n{allTracks[0]["recoHits"][0]["pos"]}')

            # 2 fit tracks
            # do NOT use the anchor point here any more!
            recosNew = self.getAllRecosFromAllTracks(allTracks)
            corrFitter = CorridorFitter(recosNew)
            # corrFitter.useAnchorPoint(anchorPoint)
            resultTracksNew = corrFitter.fitTracksSVD()
            allTracks = self.updateTracks(allTracks, resultTracksNew)

            # 4 if new trafo matrix is small (almost no change), then we converged and can quit
            pass


        #! ------- end iterative part

        # TODO: move this to the comparator, it's the only one who is allowed to cheat. same goes for the stuff down below
        #* -----------------  compute actual matrices
        # misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
        for p in misalignmatrices:
            misalignmatrices[p] = np.array(misalignmatrices[p]).reshape((4,4))

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatrices[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)

        #* -----------------  end compute actual matrices

        print('\n\n')
        print(f'===================================================================')
        print(f'Final misalignment:')
        print(f'===================================================================')
        print('\n\n')

        for path in modulePaths:

            # if path != '/cave_1/lmd_root_0/half_0/plane_0/module_0':
            #     continue

            filteredTracks = self.getTracksOnModule(allTracks, path)
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)
            trackPos, recoPos = self.dynamicCut(trackPos, recoPos, 5)

            #? 1: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos)

            # print('after transform:')
            T0inv = np.linalg.inv(T0)
            toModMat = moduleMatrices[path]

            # transform matrix to module?
            T0inPnd = np.linalg.inv(toModMat) @ T0inv @ (toModMat)
            T0inPnd = T0inPnd + averageShift
            totalInPnd = np.linalg.inv(toModMat) @ totalMatrices[path] @ (toModMat)
            totalInPnd = totalInPnd + averageShift

            lastInPnd = np.linalg.inv(toModMat) @ alignMatrices[path] @ (toModMat)

            # print(f'diff:\n{(T0inPnd - misalignmatrices[path])*1e4}')
            print(f'total matrix:\n{totalInPnd*1e4}')
            # print(f'last matrix:\n{alignMatrices[path]*1e4}')
            # print(f'last matrix in pnd:\n{lastInPnd*1e4}')
            print(f'actual matrix:\n{misalignmatrices[path]*1e4}')
            # print(f'average shift:\n{averageShift*1e4}')
            print(f'\nbetter diff:\n{(totalInPnd - misalignmatrices[path])*1e4}')
            print(f' ------------- next -------------')

        print(f'\n\n\n')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'\n\n\n')


    def alignICPiterative(self, sector=0):

        np.set_printoptions(precision=3)
        np.set_printoptions(suppress=True)

        assert (sector > -1) and (sector < 10)

        modulePaths = self.reader.getModulePathsInSector(sector)
        allTracks = self.reader.getAllTracksInSector(sector)

        misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
        
        with open(misMatPath) as f:
            misalignmatricesOriginal = json.load(f)

        # make 4x4 matrices
        moduleMatrices = {}
        for path in misalignmatrices:
            moduleMatrices[path] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)
            misalignmatrices[path] = np.array(misalignmatrices[path]).reshape((4,4))
            misalignmatricesOriginal[path] = np.array(misalignmatricesOriginal[path]).reshape((4,4))

        # transform accoring to calculations
        for path in misalignmatrices:
            mis = misalignmatrices[path]
            modMat = moduleMatrices[path]
            mis = modMat @ mis @ np.linalg.inv(modMat)
            misalignmatrices[path] = mis

        #! okay fuck this, I KNOW the misalignment. If I move the reco points back and do the track fit, I HAVE to get zero!
        # allTracks = self.transformRecos(allTracks, misalignmatrices)
        #* okay, this works. I know I am this close.
        # what if I compensate TWICE?
        # allTracks = self.transformRecos(allTracks, misalignmatrices)
        # allTracks = self.transformRecos(allTracks, misalignmatrices)
        #* works as expected, the resulting misalignments are just the other direction
        # which means, I'm comparing against the wrong thing.

        #! okay, I think I know the problem. the z values of the recos are not all on the same plane,
        # as some hits are on the front side of the module, some on the back, 
        # and some in the middle, due to the merged Hits.
        #! transform all to lmdlocal, try again!
        lmdLocalMatrices = {}
        for path in misalignmatrices:
            lmdLocalMatrices[path] = np.array(self.reader.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4))
        # allTracks = self.transformRecos(allTracks, lmdLocalMatrices, True)

        # #! ====================  apply misalignment
        # with open(misMatPath) as f:
        #     doot = json.load(f)
        
        # for p in doot:
        #     mork = np.array(doot[p]).reshape((4,4))
        #     modMat = moduleMatrices[p]
        #     mis = modMat @ mork @ np.linalg.inv(modMat)
        #     doot[p] = mis
        
        # # return 
        # allTracks = self.transformRecos(allTracks, (doot))

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatricesOriginal[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)

        anchorPoint = [-18.93251088, 0.075, 2.51678065]

        # do a first track fit, otherwise we have no starting tracks
        print(f'performing first track fit.')
        for path in modulePaths:
            recos = self.getAllRecosFromAllTracks(allTracks)
            corrFitter = CorridorFitter(recos)
            corrFitter.useAnchorPoint(anchorPoint)
            resultTracks = corrFitter.fitTracksSVD()
            allTracks = self.updateTracks(allTracks, resultTracks)

        print('\n\n')
        print(f'===================================================================')
        print(f'Inital misalignment:')
        print(f'===================================================================')
        print('\n\n')

        for path in modulePaths:
            filteredTracks = self.getTracksOnModule(allTracks, path)
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)
            trackPos, recoPos = self.dynamicCut(trackPos, recoPos, 5)

            #! begin hist
            dVec = recoPos
            print(dVec.shape)

            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.colors import LogNorm
            
            # plot difference hit array
            fig = plt.figure(figsize=(16/2.54, 9/2.54))
            
            axis = fig.add_subplot(1,2,1)
            axis.hist2d(dVec[:, 0]*1e4, dVec[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-300,300), (-300,300)))
            axis.set_title(f'2D Distance\n{path}')
            axis.yaxis.tick_right()
            axis.yaxis.set_ticks_position('both')
            axis.set_xlabel('dx [µm]')
            axis.set_ylabel('dy [µm]')
            axis.tick_params(direction='out')
            axis.yaxis.set_label_position("right")

            axis2 = fig.add_subplot(1,2,2)
            axis2.hist(dVec[:, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
            axis2.set_title(f'z position\n{path}')
            axis2.yaxis.tick_right()
            axis2.yaxis.set_ticks_position('both')
            axis2.set_xlabel('dx [µm]')
            axis2.set_ylabel('dy [µm]')
            axis2.tick_params(direction='out')
            axis2.yaxis.set_label_position("right")

            path1 = path.replace('/', '-')

            # fig.show()
            fig.savefig(f'output/alignmentModules/test/actual-{path1}.png')
            plt.close(fig)
            #! end hist


            #? 1: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos)

            #! slight bug here, I confused the direction of misalignment
            T1 = np.linalg.inv(T0)
            # print(f'{path}:\n{T0*1e4}')
            # print(f'{path} inverted:\n{T1*1e4}')

            # print(f'naked T0:\n{T0*1e4}')
            print('after transform:')
            matrix1 = T0
            toModMat = moduleMatrices[path]

            # transform matrix to module?
            matrix10 = (toModMat) @ matrix1 @ np.linalg.inv(toModMat)
            matrix10 = matrix10 + averageShift
            # print(f'transformed normal:\n{matrix10*1e4}')
            # print(f'actual:\n{misalignmatricesOriginal[path]*1e4}')
            print(f'\nDIFF:\n{(matrix10-misalignmatricesOriginal[path])*1e4}\n\n')
            print(f' ------------- next -------------')

        if False:

            print('\n\n')
            print(f'===================================================================')
            print(f'Fitting for sector {sector}! {len(allTracks)} tracks are available.')
            print(f'===================================================================')
            print('\n\n')

            # this one I need
            matrices = {}
            for path in modulePaths:
                matrices[path] = np.identity(4)

            completeMatrices = {}
            for path in modulePaths:
                completeMatrices[path] = np.identity(4)

            iterations = 10
            #* ------------------------ begin iteration loop
            for _ in tqdm(range(iterations), desc='Iterating'):

                for path in modulePaths:
                    # print(f'path: {path}')
                    # get tracks and recos in two arrays
                    filteredTracks = self.getTracksOnModule(allTracks, path)
                    # print(newTracks[0])
                    trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)

                    # print(f'trackpos:\n{trackPos}\nrecopos:\n{recoPos}')

                    #? 1: get initial align matrices for 4 modules
                    T0 = self.getMatrix(trackPos, recoPos)
                    T1 = np.linalg.inv(T0)
                    matrices[path] = T1
                    completeMatrices[path] = T1 @ completeMatrices[path]
                    
                #? 2: apply matrices to all recos
                # print(f'shifting reco hits...')
                allTracks = self.transformRecos(allTracks, matrices)

                #? 3: fit tracks again
                # print(f'fitting tracks...')
                recos = self.getAllRecosFromAllTracks(allTracks)
                corrFitter = CorridorFitter(recos)
                resultTracks = corrFitter.fitTracksSVD()
                allTracks = self.updateTracks(allTracks, resultTracks)

            #* ------------------------ end iteration loop

            # the recos are now shifted to the position of the "ideal" track fits
            # now, calculate alignment matrices one last time in the f.o.r. of the module

            # these are the ideal positional matrices.
            moduleMatrices = {}
            for path in modulePaths:
                moduleMatrices[path] = np.linalg.inv(np.array(self.reader.detectorMatrices[path]).reshape(4,4))
            
            # print(allTracks[0])
            
            #! I think this entire block isn't even neccessary
            #! EITHER of these blocks is enough, they compute the same thing different ways

            # derive matrices another way
            simplyDerivedMatrices = {}
            #* now, think easy. all the recos have been moved. try to find the distance between the original recos
            #* and the new recos. this should be the misalignment
            for path in modulePaths:

                originalTracks = self.reader.getAllTracksInSector(sector)
                filteredOriginalTracks = self.getTracksOnModule(originalTracks, path)

                # get tracks and recos in two arrays
                filteredTracks = self.getTracksOnModule(allTracks, path)

                assert len(filteredTracks) == len(filteredOriginalTracks)
                nTrks = len(filteredOriginalTracks)

                originalRecos = np.zeros((nTrks, 3))
                newRecos = np.zeros((nTrks, 3))

                # transform all three to local module
                for i in range(nTrks):
                    originalRecos[i] = np.array(filteredOriginalTracks[i]['recoPos'])
                    newRecos[i] = np.array(filteredTracks[i]['recoPos'])

                    originalRecos[i] = self.transformRecoHit(originalRecos[i], moduleMatrices[path])
                    newRecos[i] = self.transformRecoHit(newRecos[i], moduleMatrices[path])

                # get final alignment matrix
                T0 = self.getMatrix(originalRecos, newRecos)
                simplyDerivedMatrices[path] = np.linalg.inv(T0)
                

            print('\n\n')
            print(f'===================================================================')
            print(f' GRAND FINALE:')
            print(f'===================================================================')
            print('\n\n')

            #! cheat hard here for now:
            with open('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json') as f:
                misalignmatrices = json.load(f)

            #! WAIT! There is one last bug here! The misalignment matrix you provided was module-local, but
            #! the matrix you get here is PANDA-global! transform it, and you should have it!
            for path in modulePaths:
                matrix = np.linalg.inv(completeMatrices[path])
                # matrix0 = completeMatrices[path]
                toModMat = moduleMatrices[path]

                # transform matrix to module?
                matrix1 = (toModMat) @ matrix @ np.linalg.inv(toModMat)
                #* matrix1 is the one I get when comparing transformed and original recos.


                # matrix10 = (toModMat) @ matrix0 @ np.linalg.inv(toModMat)

                otherMatrix = np.array(misalignmatrices[path]).reshape((4,4))
                # otherMatrix = (toModMat) @ otherMatrix @ np.linalg.inv(toModMat)

                print(f'matrix1:\n{matrix1*1e4}')
                print(f'simplyDerivedMatrix:\n{simplyDerivedMatrices[path]*1e4}')
                # print(f'dMat:\n{(matrix1-simplyDerivedMatrices[path])*1e4}')
                print(f'actual matrix:\n{otherMatrix*1e4}')
                print(f'\nDIFF:\n{(matrix1-otherMatrix)*1e4}\n\n')

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