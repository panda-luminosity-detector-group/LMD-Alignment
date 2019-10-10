#!usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
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

    def readDetectorParameters(self):
        with open(Path('input/detectorOverlapsIdeal.json')) as inFile:
            self.detectorOverlaps = json.load(inFile)

    def getPathModuleFromSensorID(self, sensorID):
        for overlap in self.detectorOverlaps:
            if self.detectorOverlaps[overlap]['id1'] == sensorID or self.detectorOverlaps[overlap]['id2'] == sensorID:
                return self.detectorOverlaps[overlap]["pathModule"]

    def getSectorFromModulePath(self, modulePath):
        # "/cave_1/lmd_root_0/half_1/plane_0/module_3"
        regex = "\/cave_(\d+)\/lmd_root_(\d+)\/half_(\d+)\/plane_(\d+)\/module_(\d+)"
        p = re.compile(regex)
        m = p.match(modulePath)
        if m:
            half = int(m.group(3))
            plane = int(m.group(4))
            module = int(m.group(5))
            sector = (module) + (half)*5;
            return plane, sector

    def generatorMilleParameters(self):

        print(f'no of events: {len(self.trks)}')

        # TODO: loop over all events!

        # TODO: transform all values to system of first... module? yes, module, since this is using the ideal position

        print(f"verbose!\ntrack pos: {self.trks[0]['trkPos']}\ntrack mom: {self.trks[0]['trkMom']}")

        # track origin and direction
        trackOri = np.array(self.trks[0]['trkPos'])
        trackDir = np.array(self.trks[0]['trkMom']) / np.linalg.norm(self.trks[0]['trkMom'])

        # print(f'track parameters: A=[trackOri] and u=[trackDir] (length [np.linalg.norm(self.trks[0]["trkMom"])])')

        print(f'fecking track eh:\n{self.trks[0]}\n')

        for reco in self.trks[0]['recoHits']:
            # print(f'hit index: {reco["index"]}')
            # print(f"reco hit pos: {reco['pos']}")
            # print(f"reco hit err: {reco['err']}")
            recoPos = np.array(reco['pos'])

            apVec = trackOri - recoPos
            dist = np.linalg.norm( np.cross(apVec, trackDir))# / np.linalg.norm(trackDir)

            # better way calculate vector from reco point to track
            # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
            dVec = (trackOri - recoPos) - ((trackOri - recoPos)@trackDir) * trackDir

            # print(f'------------------------')
            
            # print(f'dVec: [dVec]')
            # print(f'-this dist: [np.linalg.norm(dVec)]')
            # print(f'other dist: [dist]')

            # okay, at this point, I have all positions, distances and errors in x and y

            # TODO: determine plane number for reco hit
            px = reco['pos'][0]
            py = reco['pos'][1]

            sensorID = reco['sensorID']
            modulePath = self.getPathModuleFromSensorID(sensorID)
            plane, sector = self.getSectorFromModulePath(modulePath)

            dz = 20 # TODO: change by plane!

            if plane == 0:
                dz = 0 # TODO: use reco z val!
                yield from self.milleParamsPlaneOne(px, py, dz, dVec, reco['err'])
            
            elif plane == 1:
                dz = 20 # TODO: use reco z val!
                yield from self.milleParamsPlaneTwo(px, py, dz, dVec, reco['err'])
            
            elif plane == 2:
                dz = 30 # TODO: use reco z val!
                yield from self.milleParamsPlaneThree(px, py, dz, dVec, reco['err'])
            
            elif plane == 3:
                dz = 40 # TODO: use reco z val!
                yield from self.milleParamsPlaneFour(px, py, dz, dVec, reco['err'])
            
    
    """
    yield TWO lines, one for x, one for y
    """
    def milleParamsPlaneOne(self, px, py, dz, dVec, errVec):
        #! ============== first plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [ -1, 0, -py,       0,0,0,      0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [ 0, -1, px,       0,0,0,      0,0,0,       0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma)

    def milleParamsPlaneTwo(self, px, py, dz, dVec, errVec):
        #! ============== second plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     -1, 0, -py,     0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0, -1, px,      0,0,0,      0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma)

    def milleParamsPlaneThree(self, px, py, dz, dVec, errVec):
        #! ============== third plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      -1, 0, -py,     0,0,0]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0, -1, px,      0,0,0]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma)

    def milleParamsPlaneFour(self, px, py, dz, dVec, errVec):
        #! ============== third plane
        #* -------------- x values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0,0,0,      -1, 0, -py]
        #? ------ local derivtives
        derLC = [ 1, dz, 0, 0]
        #? ------ residual, error
        residual = dVec[0]   # distance x reco to track!
        sigma = errVec[0]    # error in x direction         
        
        yield (derGL, derLC, residual, sigma)

        #* -------------- y values
        #? ------ global derivtives
        derGL = [0,0,0,     0,0,0,      0,0,0,      0, -1, px]
        #? ------ local derivtives
        derLC = [ 0, 0, 1, dz]
        #? ------ residual, error
        residual = dVec[1]   # distance y reco to track!
        sigma = errVec[1]    # error in y direction   

        yield (derGL, derLC, residual, sigma)













        
        