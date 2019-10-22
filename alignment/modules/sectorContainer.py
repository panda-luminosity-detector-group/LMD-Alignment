#!/usr/bin/env python3

import numpy as np
from collections import defaultdict
from numpy.linalg import inv

class sectorContainer():

    def __init__(self, sector):
        #should be 4
        self.modulePaths = []
        self.sector = sector
        
        self.pathFirstMod = ''
        self.matrixFirstMod = ''

        # should be 4
        self.alignMatrices = {}

        # and dicts (key=modulePath) with values for:
        self.recos = defaultdict(list)
        self.tracks = defaultdict(list)

        # attention! I also need the inital, unchanged reco hits for the 
        # final alignment matrix!
        self.initialRecos = defaultdict(list)

    def transformRecoPoints(self, module):
        nRecos = len(self.recos[module])
        # TODO: inverse or not?
        matrix = self.alignMatrices[module]

        recos = np.ones((nRecos, 4))
        recos[:,:4] = np.array(self.recos[module])
        recos = np.matmul( matrix, recos.T).T
        
        # reassign
        self.recos[module] = recos[:3]

    def getAllRecos(self):
        # for track fitter
        result = np.concatenate( (self.recos[i] for i in self.recos) )
        return result

    def getRecos(self, modulePath):
        # to use with matrix finder
        return self.recos[modulePath]

    def getTrackPositions(self, modulePath):
        # to use with matrix finder

        # first: sort recos, tracks to temp arrays by module path

        # then, do calc like in trackReader

        # return trackPositions, recoPositions

        pass

    def setAlignmentMatrix(self, modulePath, matrix):
        self.alignMatrices[modulePath] = matrix

    def addReco(self, modulePath, reco):
        self.recos[modulePath].append(reco)

    def addInitialReco(self, modulepath, reco):
        self.initialRecos[modulepath].append(reco)

    def addTrack(self, modulePath, track):
        self.tracks[modulePath].append(track)

    def print(self):
        print('=== CONTAINER INFO ===')
        print(f'module path keys:\n{self.modulePaths}')
        print(f'recos keys:\n{self.recos.keys()}')
        print(f'tracks keys:\n{self.tracks.keys()}')
        print(f'recos U keys:\n{self.initialRecos.keys()}')

        for i in self.recos:
            print(len(self.recos[i])) 

        for i in self.tracks:
            print(len(self.tracks[i])) 

        for i in self.initialRecos:
            print(len(self.initialRecos)) 
        
    pass
