#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv

class sectorContainer():

    def __init__(self):
        #should be 4
        self.modulePaths = []
        self.sector = 0
        
        self.pathFirstMod = ''
        self.matrixFirstMod = ''

        # and tuples with values for:
        # recos
        # tracks

    def transformRecoPoints(self):
        pass

    def getAllRecos(self):
        # for track fitter
        pass

    def getRecos(self, modulePath):
        # to use with matrix finder

        # first: sort recos to temp arrays by module path using list comprehension

        pass

    def getTrackPositions(self, modulePath):
        # to use with matrix finder

        # first: sort recos, tracks to temp arrays by module path

        # then, do calc like in trackReader

        # return trackPositions, recoPositions

        pass

    def setRecos(self, recos):
        pass

    def setTracks(self, recos):
        pass

    pass
