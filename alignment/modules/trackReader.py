#!usr/bin/env python3

import copy
from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
from numpy.linalg import inv
import json
import uproot
# import pandas as pd
import re
import sys

"""

Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This file handles reading of lmd_tracks and lmd reco_files, and extracts tracks with their corresponding reco hist.

It then gives those values to millepede, obtains the alignment parameters back and writes them to alignment matrices.
"""

class trackReader():

    def readTracksFromRoot(self, path):
        """
        Currently not working, please use the json method
        """
        pass

    def readSyntheticDate(self, filename):
        with open(filename, 'r') as f:
            synthData = json.load(f)
        return synthData

    # TODO: deprecate and simplify reco format
    def readTracksFromJson(self, filename):
        print(f'reading from {filename}...')
        with open(filename, 'r') as infile:
            self.trks = json.load(infile)['events']
            print(f'file successfully read, found {len(self.trks)} tracks!')

        # list comprehension to filter tracks with no momentum from this dict
        print('removing broken tracks...')
        self.trks = [ x for x in self.trks if all(x['trkMom'])]
        self.trks = [ x for x in self.trks if all(x['trkPos'])]

        print('removing empty tracks...')
        self.trks = [ x for x in self.trks if np.linalg.norm(x['trkMom']) != 0 ]
        
        notEnoughRecos = 0
        sectorCrossing = 0

        removeSectorCrossing = False

        # find sector crossing tracks
        print('removing sector-crossing tracks...')
        for track in self.trks:
            # discard tracks that have only three recos, they screw up my indices
            if len(track['recoHits']) != 4:
                track['valid'] = False
                notEnoughRecos += 1
                continue

            # check if all recos are in the same sector
            firstSen = track['recoHits'][0]['sensorID']
            firstPath = self.getPathModuleFromSensorID(firstSen)
            _, _, _, firstSec = self.getParamsFromModulePath(firstPath)
            
            # give each track sector info
            track['sector'] = firstSec
            track['valid'] = True

            # loop over remaining recos
            for reco in track['recoHits'][1:]:
                sensor = reco['sensorID']
                path = self.getPathModuleFromSensorID(sensor)
                _, _, _, sector = self.getParamsFromModulePath(path)
                
                if (sector != firstSec) and removeSectorCrossing:
                    track['valid'] = False
                    sectorCrossing += 1
                    break
        
        # actually remove
        print(f'all tracks: {len(self.trks)}')
        self.trks = [ x for x in self.trks if x['valid'] ]
        print(f'pre-processing done, discarded:\nLess than four recos: {notEnoughRecos}\nSector crosssing: {sectorCrossing}\n==>\n{len(self.trks)} tracks remaining!\n\n')

        # dump tracks to disk as np file
        np.save('output/residualVsTrks/tracks.npy', self.trks, allow_pickle=True)

    def readTracksFromNPY(self, filename):
        print(f'reading tracks from NPY file {filename}')
        self.trks = np.load(filename, allow_pickle=True)
        print(f'done!')

    # this reads detector parameters and sets up several dicts for fast loop ups
    def readDetectorParameters(self):
        with open(Path('input/detectorOverlapsIdeal.json')) as inFile:
            self.detectorOverlaps = json.load(inFile)

        #make new dict sensorID-> modulePath
        self.modPathDict = {}
        for overlap in self.detectorOverlaps:
            id1 = self.detectorOverlaps[overlap]['id1']
            id2 = self.detectorOverlaps[overlap]['id2']
            self.modPathDict[id1] = self.detectorOverlaps[overlap]["pathModule"]
            self.modPathDict[id2] = self.detectorOverlaps[overlap]["pathModule"]


        with open(Path('input/detectorMatricesIdeal.json')) as inFile:
            self.detectorMatrices = json.load(inFile)

        regex = r'^/cave_(\d+)/lmd_root_(\d+)/half_(\d+)/plane_(\d+)/module_(\d+)$'
        p = re.compile(regex)

        # fill look-up dict for parameters
        self.detParamDict = {}
        for path in self.detectorMatrices:
            m = p.match(path)
            if m:
                half = int(m.group(3))
                plane = int(m.group(4))
                module = int(m.group(5))
                sector = (module) + (half)*5;
                self.detParamDict[path] = (half, plane, module, sector)

        # fill look-up dict for paths in a sector
        self.sectorDict = defaultdict(list)
        for path in self.detParamDict:
            _, _, _, sector = self.getParamsFromModulePath(path)
            self.sectorDict[sector].append(path)

    def getPathModuleFromSensorID(self, sensorID):
        return self.modPathDict[sensorID]

    # order is half, plane, module, sector
    def getParamsFromModulePath(self, modulePath):
        return self.detParamDict[modulePath]

    def getModulePathsInSector(self, sector):
        return self.sectorDict[sector]

    # get (a deep copy of) all tracks in a given sector
    def getAllTracksInSector(self, sector=0):
        if sector < 0:
            return self.trks
        else:
            return [ x for x in self.trks if x['sector'] == sector ]

    # TODO: deprecate once SynthDataTest is no longer needed
    def transformPoint(self, point, matrix):
        newPoint = np.ones(4)
        newPoint[:3] = point
        # print(newPoint)
        newPoint = matrix @ newPoint
        # print(newPoint)
        return newPoint[:3]
    
    def generatorMilleParameters(self):

        print(f'no of events: {len(self.trks)}')


        # we transform to LMDlocal
        matToLMD = np.array(self.detectorMatrices['/cave_1/lmd_root_0']).reshape((4,4))

        # TODO: use vectorized version to use numpy!
        # loop over all events
        for event in self.trks:

            # track origin and direction
            trackOri = np.array(event['trkPos'])
            trackDir = np.array(event['trkMom']) / np.linalg.norm(event['trkMom'])

            for reco in event['recoHits']:
                # print(f'hit index: {reco["index"]}')
                # print(f"reco hit pos: {reco['pos']}")
                # print(f"reco hit err: {reco['err']}")
                recoPos = np.array(reco['pos'])

                sensorID = reco['sensorID']
                modulePath = self.getPathModuleFromSensorID(sensorID)

                # determine module position from reco hit
                half, plane, module, sector = self.getParamsFromModulePath(modulePath)

                # create path to first module in this sector
                # pathFirstMod = f"/cave_1/lmd_root_0/half_{half}/plane_0/module_{module}"

                #* get matrix to first module
                # matrixFirstMod = np.array(self.detectorMatrices[pathFirstMod]).reshape(4,4)

                # transform recoHit and track origin
                # recoNew = self.transformPoint(recoPos, inv(matrixFirstMod))
                # trackOriNew = self.transformPoint(trackOri, inv(matrixFirstMod))

                # track direction requires more work
                # trackDirPoint = self.transformPoint(trackOri + trackDir, inv(matrixFirstMod))
                # trackDirNew = trackDirPoint - trackOriNew

                #* transform all reco points and tracks to lmd local here

                # transform recoHit and track origin
                recoNew = self.transformPoint(recoPos, inv(matToLMD))
                trackOriNew = self.transformPoint(trackOri, inv(matToLMD))

                # track direction requires more work
                trackDirPoint = self.transformPoint(trackOri + trackDir, inv(matToLMD))
                trackDirNew = trackDirPoint - trackOriNew

                # print(f'recoNew: {recoNew}')
                # print(f'trackOriNew: {trackOriNew}')
                # print(f'trackDirNew: {trackDirNew}')

                # better way calculate vector from reco point to track
                # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
                # attention! this goes FROM reco TO track, so minus is important!
                dVec = -((trackOriNew - recoNew) - ((trackOriNew - recoNew)@trackDirNew) * trackDirNew)

                # z position of the plane
                dz = (recoNew[2] / trackDirNew[2])

                # position of the track on a module
                px = (trackOriNew + trackDirNew*dz)[0]
                py = (trackOriNew + trackDirNew*dz)[1]
                pz = (trackOriNew + trackDirNew*dz)[2]

                # print(f'------------------------')
                # print(f'dx: {px}, dy: {py}, dz: {dz}')
                # print(f'dVec: {dVec}')

                # okay, at this point, I have all positions, distances and errors in x and y

                if plane == 0:
                    yield from self.milleParamsPlaneOne(px, py, dz, dVec, reco['err'], sector)
                
                elif plane == 1:
                    yield from self.milleParamsPlaneTwo(px, py, dz, dVec, reco['err'], sector)
                
                elif plane == 2:
                    yield from self.milleParamsPlaneThree(px, py, dz, dVec, reco['err'], sector)
                
                elif plane == 3:
                    yield from self.milleParamsPlaneFour(px, py, dz, dVec, reco['err'], sector)
            
    """
    yield TWO lines, one for x, one for y
    """
    def milleParamsPlaneOne(self, px, py, dz, dVec, errVec, sector):
        #! ============== first plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [ -1, 0, -py,       0,0,0,      0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma, sector)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [ 0, -1, px,       0,0,0,      0,0,0,       0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma, sector)

    def milleParamsPlaneTwo(self, px, py, dz, dVec, errVec, sector):
        #! ============== second plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     -1, 0, -py,     0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma, sector)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0, -1, px,      0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma, sector)

    def milleParamsPlaneThree(self, px, py, dz, dVec, errVec, sector):
        #! ============== third plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      -1, 0, -py,     0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma, sector)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0, -1, px,      0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma, sector)

    def milleParamsPlaneFour(self, px, py, dz, dVec, errVec, sector):
        #! ============== third plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0,0,0,      -1, 0, -py]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma, sector)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0,0,0,      0, -1, px]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma, sector)
