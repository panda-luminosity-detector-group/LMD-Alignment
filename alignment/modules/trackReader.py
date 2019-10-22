#!usr/bin/env python3

from alignment.modules.sectorContainer import sectorContainer

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
from numpy.linalg import inv
import json
import uproot
import re
import sys

"""

Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This file handles reading of lmd_tracks and lmd reco_files, and extracts tracks with their corresponding reco hist.

It then gives those values to millepede, obtains the alignment parameters back and writes them to alignment matrices.
"""

class trackReader():
    def __init__(self):
        self.trks = {}
        pass

    """
    sector goes from 0 to 9
    """
    def readTracksFromRoot(self, path, sector=-1):
        """
        Currently not working, please use the json method
        """
        pass

    def readTracksFromJson(self, filename, sector=-1):
        with open(filename, 'r') as infile:
            self.trks = json.load(infile)['events']
            print('file successfully read!')

        # list comprehension to filter tracks with no momentum from this dict
        self.trks = [ x for x in self.trks if np.linalg.norm(x['trkMom']) != 0 ]
        print('empty tracks removed!')

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

        self.detParamDict = {}
        # self.sectorDict = {}

        # fill look-up dicts
        for path in self.detectorMatrices:
            m = p.match(path)
            if m:
                half = int(m.group(3))
                plane = int(m.group(4))
                module = int(m.group(5))
                sector = (module) + (half)*5;
                self.detParamDict[path] = (half, plane, module, sector)
                # self.sectorDict[sector] = 


    def getPathModuleFromSensorID(self, sensorID):
        return self.modPathDict[sensorID]

    def getParamsFromModulePath(self, modulePath):
        return self.detParamDict[modulePath]

    def transformPoint(self, point, matrix):

        # vector must be row-major 3 vector
        assert point.shape == (3,)

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

    def getContainer(self, sector):

        container = sectorContainer(sector)
        
        for track in self.trks:
            
            for reco in track['recoHits']:
                
                thisModulePath = self.getPathModuleFromSensorID(reco['sensorID'])
                (half, _, mod, thisSector) = self.getParamsFromModulePath(thisModulePath)

                if thisSector == sector:
                    # get matrix
                    firstModPath = f'/cave_1/lmd_root_0/half_{half}/plane_0/module_{mod}'
                    firstModMatrix = np.array(self.detectorMatrices[firstModPath]).reshape(4,4)

                    # transform!
                    reco = np.array(reco['pos'])
                    container.addInitialReco(thisModulePath, reco)

                    recoT = self.transformPoint(reco, inv(firstModMatrix))
                    container.addReco(thisModulePath, recoT)

                    # the same track will be added multiple times. this is okay!
                    container.addTrack(thisModulePath, (track['trkPos'], track['trkMom']))

        container.pathFirstMod = firstModPath
        container.matrixFirstMod = firstModMatrix
        container.modulePaths = container.tracks.keys()

        return container

    
    def generateICPParameters(self, modulePath=''):

        # presorter step
        newTracks = []
        for track in self.trks:
            newTrack = {}
            for reco in track['recoHits']:

                thisModulePath = self.getPathModuleFromSensorID(reco['sensorID'])

                if thisModulePath == modulePath:
                    newTrack['recoHit'] = reco['pos']
                    newTrack['recoErr'] = reco['err']
                    newTrack['recoSensor'] = reco['sensorID']
                    newTrack['trkMom'] = track['trkMom'] / np.linalg.norm(track['trkMom'])
                    newTrack['trkPos'] = track['trkPos'] 
                    newTracks.append(newTrack)
        
        thisModMatrix = np.array(self.detectorMatrices[modulePath]).reshape(4,4)

        # TODO: now this can use numpy array notation for even greater speedup
        # return whole np.array instead single lines then
        for track in newTracks:

            recoPos = np.array(track['recoHit'])
            trackOri = np.array(track['trkPos'])
            trackDir = np.array(track['trkMom'])

            # transform track and reco to module system
            thisTrackO = self.transformPoint(trackOri, inv(thisModMatrix))
            thisReco = self.transformPoint(recoPos, inv(thisModMatrix))

            # now, several steps are required. we nee the origin a, the point where origin+direction point at b 
            # then we must transform both, then calculate vector from a to b
            thisTrackDirectionPoint = self.transformPoint((trackOri+trackDir), inv(thisModMatrix))
            thisTrackD = thisTrackDirectionPoint - thisTrackO

            # no transformation this time
            # thisTrackO = trackOri
            # thisTrackD = trackDir
            # thisReco = recoPos

            # get vector from reco hit to line
            # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
            dVec = ((thisTrackO - thisReco) - ((thisTrackO - thisReco)@thisTrackD) * thisTrackD)

            # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
            pIntersection = thisReco+dVec

            yield [pIntersection, thisReco]

    def generatorMilleParameters(self):

        print(f'no of events: {len(self.trks)}')

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
                pathFirstMod = f"/cave_1/lmd_root_0/half_{half}/plane_0/module_{module}"

                # get matrix to first module
                matrixFirstMod = np.array(self.detectorMatrices[pathFirstMod]).reshape(4,4)

                # transform recoHit and track origin
                recoNew = self.transformPoint(recoPos, inv(matrixFirstMod))
                trackOriNew = self.transformPoint(trackOri, inv(matrixFirstMod))

                # track direction requires more work
                trackDirPoint = self.transformPoint(trackOri + trackDir, inv(matrixFirstMod))
                trackDirNew = trackDirPoint - trackOriNew

                # print(f'recoNew: {recoNew}')
                # print(f'trackOriNew: {trackOriNew}')
                # print(f'trackDirNew: {trackDirNew}')

                # better way calculate vector from reco point to track
                # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
                # attention! this goes FROM reco TO track, so minus is important!
                dVec = -((trackOriNew - recoNew) - ((trackOriNew - recoNew)@trackDirNew) * trackDirNew)

                # TODO: this is supposed to be the track position in the module, NOT the reco hit position!

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













        
        