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

        # first: filter tracks that are not even in the same sector, that should remove 90%
        # _, _, _, thisSector = self.reader.getParamsFromModulePath(modulePath)
        #allTracks = self.reader.getAllTracksInSector(thisSector)

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
    def transformRecos(self, allTracks, matrices):

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
        # for i in range(len(newTracks)):
        #     dVecTest[i] = ((trackPosArr[i] - recoPosArr[i]) - np.dot((trackPosArr[i] - recoPosArr[i]), trackDirArr[i]) * trackDirArr[i])

        # norm momentum vectors, this is important for the distance formula!
        trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

        # vectorized version, much faster
        tempV1 = (trackPosArr - recoPosArr)
        tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
        dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
        
        # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
        pIntersection = recoPosArr+dVec
        return pIntersection, recoPosArr

    def alignICPiterative(self, sector=0):

        assert (sector > -1) and (sector < 10)

        modulePaths = self.reader.getModulePathsInSector(sector)
        allTracks = self.reader.getAllTracksInSector(sector)
        # originalTracks = copy.deepcopy(allTracks)

        # these are the ideal positional matrices.
        moduleMatrices = {}
        for path in modulePaths:
            moduleMatrices[path] = np.linalg.inv(np.array(self.reader.detectorMatrices[path]).reshape(4,4))

        print('\n\n')
        print(f'===================================================================')
        print(f'Inital misalignment:')
        print(f'===================================================================')
        print('\n\n')

        for path in modulePaths:
            filteredTracks = self.getTracksOnModule(allTracks, path)
            # print(newTracks[0])
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)

            # print(f'trackpos:\n{trackPos}\nrecopos:\n{recoPos}')

            #? 1: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos)
            T1 = np.linalg.inv(T0)
            print(f'{path}:\n{T1*1e4}')



        print('\n\n')
        print(f'===================================================================')
        print(f'Fitting for sector {sector}! {len(allTracks)} tracks are available.')
        print(f'===================================================================')
        print('\n\n')

        # TODO: remove, this is not needed, it's only here for debug
        # temporary helper dicts for the steps between iterations
        # recos = {}

        # this one I need
        matrices = {}
        for path in modulePaths:
            matrices[path] = np.identity(4)

        completeMatrices = {}
        for path in modulePaths:
            completeMatrices[path] = np.identity(4)

        iterations = 5
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
                
                # print(f'recos before:\n{recoPos}')

                # # homogenize
                # recosH = np.ones((len(recoPos), 4))
                # recosH[:,:3] = recoPos
                # # transform
                # # TODO: is the direction correct? i.e. inv(T0)?
                # recosH = np.matmul(T0, recosH.T).T
                # # de-homogenize
                # recoPos = recosH[:,:3]


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

        # transform all recos to their respective module
        # actually, don't. get filtered tracks by module and transform there
        # allTracks = self.transformRecos(allTracks, moduleMatrices)
        
        #! I think this entire block isn't even neccessary
        #! EITHER of these blocks is enough, they compute the same thing different ways
        # print('\n\n')
        # print(f'===================================================================')
        # print(f' Final matrices ready:')
        # print(f'===================================================================')
        # print('\n\n')

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
            
            # print(f'final matrix:\n{T0*1e4}')

        print('\n\n')
        print(f'===================================================================')
        print(f' GRAND FINALE:')
        print(f'===================================================================')
        print('\n\n')

        #! cheat hard here for now:
        with open('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json') as f:
            misalignmatrices = json.load(f)

        for path in modulePaths:
            matrix = np.linalg.inv(completeMatrices[path])
            toModMat = moduleMatrices[path]
            # transform matrix to module?
            matrix = (toModMat) @ matrix @ np.linalg.inv(toModMat)

            otherMatrix = np.array(misalignmatrices[path]).reshape((4,4))
            # otherMatrix = (toModMat) @ otherMatrix @ np.linalg.inv(toModMat)

            print(f'accumulated matrix:\n{matrix*1e4}')
            print(f'simplyDerivedMatrix:\n{simplyDerivedMatrices[path]*1e4}')
            # print(f'dMat:\n{(matrix-simplyDerivedMatrices[path])*1e4}')
            print(f'actual matrix:\n{otherMatrix*1e4}\n\n')

        return

        #* ------ new code using SVD in track fitter

        recos = self.reader.generateICPParametersBySector(0)

        print(f'OI OI OI')
        # print(f'len(recos[0]): {len(recos[0])}')
        # print(f'recos[0]:\n{recos[0]}')
        # print(f'len(recos[1]): {len(recos[1])}')
        # print(f'recos[1]:\n{recos[1]}')


        print(f'results:\n{resultTracks[:10]}')


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
        resultTracks = corrFitter.fittedTracks

        print(f'results:\n{resultTracks[0]}')

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
