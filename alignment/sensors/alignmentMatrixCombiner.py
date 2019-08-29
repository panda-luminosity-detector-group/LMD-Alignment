#!/usr/bin/env python3

import json
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Uses multiple overlap matrices and the ideal detector matrices to compute alignment matrices for each sensor.
Each combiner is responsible for a single module.

Steps:

WAIT UPDATE

Okay so now I can create the overlap matrices like they are in the geometry (with alignment) from the ideal matrices plus the misalignment for the overlap.
perfect, I only need to do the three steps I did to arrive here backwards! no base transforming etc, just do the three steps backwards.

END UPDATE

REMEMBER. The overlap matrices come from the Reco Points and are thusly already in PANDA global!

- gather all overlap matrices for module in a dict 
- base transform to module system
- combine overlap matrices to form 0->x matrices
- gather perfect 0->x matrices (base transformed to module system)
- substract (inverse multiply actually) perfect matrices to combined 0->x matrices
- remainder is misalignment AS GIVEN IN MODULE SYSTEM
- base transform each misalignment matrix to system of respective sensor
- save to dict, return to master
"""


class alignmentMatrixCombiner:

    def __init__(self, modulePath):
        self.modulePath = modulePath
        self.alignmentMatrices = {}

    def setOverlapMatrices(self, matrices):
        self.overlapMatrices = matrices

    def setIdealDetectorMatrices(self, matrices):
        self.idealDetectorMatrices = matrices

    def setOverlapInfos(self, infos):
        self.overlapInfos = infos
        tempDict = {}
        # add small overlap to each overlap info, we'll need that info later
        for info in self.overlapInfos:
            smallOverlap = self.getSmallOverlap(info)
            self.overlapInfos[info]['smallOverlap'] = smallOverlap
            tempDict[smallOverlap] = self.overlapInfos[info]

        # and sort by new small overlap. that's okay, the real overlapID is still a field of the dict
        self.overlapInfos = tempDict

    def getDigit(self, number, n):
        return int(number) // 10**n % 10

    def getSmallOverlap(self, overlap):
        return str(self.getDigit(overlap, 0))

    def getMatrixP1ToP2(self, path1, path2):
        # matrix from pnd global to sen1
        m1 = np.array(self.idealDetectorMatrices[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(self.idealDetectorMatrices[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return np.linalg.inv(m1)@m2

    def getMatrixP1ToP2fromMatrixDict(self, path1, path2, mat):
        # matrix from pnd global to sen1
        m1 = np.array(mat[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(mat[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return np.linalg.inv(m1)@m2

    def getOverlapMatrixWithMisalignment(self, overlapID):

        # this is atm the smallOverlap, which is wrong
        p1 = self.overlapInfos[overlapID]['path1']
        p2 = self.overlapInfos[overlapID]['path2']
        m1to2ideal = self.getMatrixP1ToP2(p1, p2)
        # this needs the complete overlapID
        m1to2corr = self.overlapMatrices[overlapID]

        return m1to2corr@m1to2ideal

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None or self.overlapInfos is None:
            print(f'ERROR! Please set overlaps, overlap matrices and ideal detector matrices first!')
            return

        # create all intermediate matrices here
        """
        TGeoHMatrix sen1to2 = mat4 * mat5.Inverse();
        TGeoHMatrix sen1to3 = mat4 * mat1.Inverse();
        TGeoHMatrix sen1to4a = mat4 * mat5.Inverse() * mat6 * mat2.Inverse();
        TGeoHMatrix sen1to4b = mat4 * mat1.Inverse() * mat7 * mat8.Inverse();

        TGeoHMatrix sen1to5 = mat0;		// well, kind of...
        TGeoHMatrix sen1to6 = mat4 * mat1.Inverse() * mat3;
        TGeoHMatrix sen1to7 = mat4 * mat1.Inverse() * mat7;
        TGeoHMatrix sen1to8 = mat4;
        TGeoHMatrix sen1to9a = mat4 * mat5.Inverse() * mat6;
        TGeoHMatrix sen1to9b = mat4 * mat1.Inverse() * mat7 * mat8.Inverse() * mat2;
        """

        #! test here, only overlap 0, sensor 0 to 5
        print(self.overlapInfos)
        mA = self.getOverlapMatrixWithMisalignment("0")
        print(f'Overlap matrix from ideal and ICP:\n{mA}')

        with open('input/detectorMatrices-sensors-2.00.json') as nf:
            actualMatrices = json.load(nf)

        p1 = "/cave_1/lmd_root_0/half_0/plane_0/module_0/sensor_0"
        p2 = "/cave_1/lmd_root_0/half_0/plane_0/module_0/sensor_5"

        mB = self.getMatrixP1ToP2fromMatrixDict(p1, p2, actualMatrices)
        print(f'Overlap matrix from geo manager with misalignment:\n{mB}')

        print(f'The moment you\'ve been waiting for: difference!\n{(mA - mB)*1e4}')

        # ? compute here

        # self.overlapInfos is now sorted by smallOverlap, but contains the complete overlapID as well. that should be enough!

        # there is inconsistent use of overlapID and smallOverlap here!
        m0 = self.getOverlapMatrixWithMisalignment(self.overlapInfos["0"]['overlapID'])

        # remove ideal here

        # remainder is here

        # transform here

        # save to dict sensorID : alignment matrix here

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    pass
