#!/usr/bin/env python3

import json
import numpy as np
from numpy.linalg import inv

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

- gather perfect 0->x matrices
- substract (inverse multiply actually) perfect matrices to combined 0->x matrices
- remainder is misalignment AS GIVEN IN PANDA GLOBAL SYSTEM
- base transform each misalignment matrix to system of respective sensor
- save to dict, return to master
"""


class alignmentMatrixCombiner:

    def __init__(self, modulePath):
        self.modulePath = modulePath
        self.alignmentMatrices = {}
        self.overlapMatrices = None
        self.overlapInfos = None
        self.idealDetectorMatrices = None
        self.externalMatrices = None

    def setOverlapMatrices(self, matrices):
        self.overlapMatrices = matrices

    def setIdealDetectorMatrices(self, matrices):
        self.idealDetectorMatrices = matrices

    def setExternallyMeasuredMatrices(self, matrices):
        self.externalMatrices = matrices

    def setOverlapInfos(self, infos):
        # should only contain the overlap infos relevant to THIS combiner, not all the overlaps!
        self.overlapInfos = infos
        tempDict = {}
        # add small overlap to each overlap info, we'll need that info later
        for info in self.overlapInfos:

            # check if modulePath from constructor and overlapInfo match
            if self.modulePath != self.overlapInfos[info]['pathModule']:
                print(f"ERROR! Module path mis match: {self.modulePath} and {self.overlapInfos[info]['pathModule']}")

            smallOverlap = self.getSmallOverlap(info)
            self.overlapInfos[info]['smallOverlap'] = smallOverlap
            tempDict[smallOverlap] = self.overlapInfos[info]

        # and sort by new small overlap. that's okay, the real overlapID is still a field of the dict
        self.overlapInfos = tempDict

    def getDigit(self, number, n):
        return int(number) // 10**n % 10

    def getSmallOverlap(self, overlap):
        return str(self.getDigit(overlap, 0))

    def getIdealMatrixP1ToP2(self, path1, path2):
        # matrix from pnd global to sen1
        m1 = np.array(self.idealDetectorMatrices[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(self.idealDetectorMatrices[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return m2@inv(m1)

    def getMatrixP1ToP2fromMatrixDict(self, path1, path2, mat):
        # matrix from pnd global to sen1
        m1 = np.array(mat[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(mat[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return m2@inv(m1)

    def getOverlapMatrixWithMisalignment(self, overlapInfo):

        p1 = overlapInfo['path1']
        p2 = overlapInfo['path2']
        # m1to2ideal = self.getIdealMatrixP1ToP2(p1, p2)
        # m1to2corr = self.overlapMatrices[overlapInfo['smallOverlap']]

        # #transform both matrices to this sensor! sensor or module?!
        # matToThisSensor = np.array(self.idealDetectorMatrices[overlapInfo['pathModule']]).reshape(4,4)
        # m1to2ideal = matToThisSensor @ m1to2ideal @ inv(matToThisSensor)
        # m1to2corr = matToThisSensor @ m1to2corr @ inv(matToThisSensor)
        # return m1to2corr@m1to2ideal
        return self.cheatICPmatrix(p1, p2)

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None or self.overlapInfos is None:
            print(f'ERROR! Please set overlaps, overlap matrices and ideal detector matrices first!')
            return

        if self.externalMatrices is None:
            print(f'ERROR! Please set the externally measured matrices for sensor 0 and 1 for module {self.modulePath}!')
            return

        # create all intermediate matrices here
        m0 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['0'])
        m1 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['1'])
        m2 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['2'])
        m3 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['3'])
        m4 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['4'])
        m5 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['5'])
        m6 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['6'])
        m7 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['7'])
        m8 = self.getOverlapMatrixWithMisalignment(self.overlapInfos['8'])

        # these two matrices are measured externally, e.g. by microscope
        # for now, they are generated by a different function,
        # but the file description should not change anymore
        # m0t1 = self.getIdealMatrixP1ToP2(self.modulePath + '/sensor_0', self.modulePath + '/sensor_1')
        # m0mis = self.externalMatrices[self.modulePath]['mis0']
        # m1mis = self.externalMatrices[self.modulePath]['mis1']

        m1t2icp = inv(m5) @ m4

        # ? wrong after here, although it kinda worked...
        # m1t2icp = m4 @ inv(m5)
        # m1t3icp = m4 @ inv(m1)
        # m1t4icpa = m4 @ inv(m5) @ m6 @ inv(m2)
        # m1t4icpb = m4 @ inv(m1) @ m7 @ inv(m8)

        # m1t5icp = m0
        # m1t6icp = m4 @ inv(m1) @ m3
        # m1t7icp = m4 @ inv(m1) @ m7
        # m1t8icp = m4
        # m1t9icpa = m4 @ inv(m5) @ m6
        # m1t9icpb = m4 @ inv(m1) @ m7 @ inv(m8) @ m2

        # print(f'm0t1: {m0t1}')
        # print(f'm1t2: {m1t2icp}')
        # print(f'm1t3: {m1t3icp}')
        # print(f'm1t4a: {m1t4icpa}')
        # print(f'm1t4b: {m1t4icpb}')
        # print(f'm1t5: {m1t5icp}')
        # print(f'm1t6: {m1t6icp}')
        # print(f'm1t7: {m1t7icp}')
        # print(f'm1t8: {m1t8icp}')
        # print(f'm1t9a: {m1t9icpa}')
        # print(f'm1t9b: {m1t9icpb}')

        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)

        with open('input/detectorMatrices-sensors-1.00.json') as f:
            totalMatrices = json.load(f)

        # TODO: port this to the comparer! this is how you compare the overlap matrix to the simulation matrix
        if False:
            print('New test, ICP matrices should be in PND global now!')

            m0t5misIcp = self.overlapMatrices['0']

            matPndTo0 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
            matPndTo5 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)

            matMisOn0 = np.array(misalignMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
            matMisOn5 = np.array(misalignMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)

            matMisOn0InPnd = matPndTo0 @ matMisOn0 @ inv(matPndTo0)
            matMisOn5InPnd = matPndTo5 @ matMisOn5 @ inv(matPndTo5)

            matMis0to5 = matMisOn5InPnd @ inv(matMisOn0InPnd)

            matMis0to5 = np.round(matMis0to5, 5)
            m0t5misIcp = np.round(m0t5misIcp, 5)

            print(f'overlap matrix as seen by ICP:\n{m0t5misIcp}')
            print(f'overlap matrix from calculations:\n{matMis0to5}')
            print(f'Difference:\n{(m0t5misIcp-matMis0to5)*1e4}')

        if False:
            # test bed to get total matrices

            p1 = self.modulePath + '/sensor_0'
            p2 = self.modulePath + '/sensor_5'

            mat0to5ICP = self.overlapMatrices['0']
            
            mat0to5ideal = self.getIdealMatrixP1ToP2(p1, p2)
            mat0to5actually = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

            matPndTo0 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            matPndTo5 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

            # I don't have these!
            matMisOn0 = np.array(misalignMatrices[p1]).reshape(4, 4)
            matMisOn5 = np.array(misalignMatrices[p2]).reshape(4, 4)

            matMisOn0InPnd = matPndTo0 @ matMisOn0 @ inv(matPndTo0)
            matMisOn5InPnd = matPndTo5 @ matMisOn5 @ inv(matPndTo5)

            matPndTo0mis = matMisOn0InPnd @ matPndTo0
            matPndTo5mis = matMisOn5InPnd @ matPndTo5

            # this is the ICP like matrix
            mat0to5MisInPnd = matMisOn5InPnd @ inv(matMisOn0InPnd)

            #* but wait, we're in sensor local, transform everything here!
            mat0to5actually = inv(matPndTo0mis) @ mat0to5actually @ (matPndTo0mis)
            
            mat0to5ideal = inv(matPndTo0) @ mat0to5ideal @ (matPndTo0)
            matWanted = inv(matPndTo0) @ mat0to5MisInPnd @ (matPndTo0)
            matWanted = matWanted @ mat0to5ideal
            print(f'my new difference')
            self.dMat(matWanted, mat0to5actually)

        # ? current work position

        """
        now, the overlap misalignments are in PND global, as they should, but to apply them to an ideal overlap,
        they must be transformed into the system of the first sensor of the overlap
        """
        p41 = self.modulePath + '/sensor_1'
        p42 = self.modulePath + '/sensor_8'
        mat4 = self.cheatICPmatrix(p41, p42)
        mat4Perfect = self.cheatActualMatrix(p41, p42)
        self.dMat(mat4, mat4Perfect)
        
        p51 = self.modulePath + '/sensor_2'
        p52 = self.modulePath + '/sensor_8'
        mat5 = self.cheatICPmatrix(p51, p52)
        mat5Perfect = self.cheatActualMatrix(p51, p52)
        self.dMat(mat5, mat5Perfect)

        cheat1to2 = inv(mat5) @ mat4
        perfect1to2 = self.cheatActualMatrix(p41, p51)

        self.dMat(cheat1to2, perfect1to2)
        # save to dict sensorID : alignment matrix here

    def cheatICPmatrix(self, p1, p2):

        mat0to5ideal = self.getIdealMatrixP1ToP2(p1, p2)

        matPndTo0 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        matPndTo5 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

        # I don't have these! but I cheat
        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)

        matMisOn0 = np.array(misalignMatrices[p1]).reshape(4, 4)
        matMisOn5 = np.array(misalignMatrices[p2]).reshape(4, 4)

        matMisOn0InPnd = matPndTo0 @ matMisOn0 @ inv(matPndTo0)
        matMisOn5InPnd = matPndTo5 @ matMisOn5 @ inv(matPndTo5)

        # this is the ICP like matrix
        mat0to5MisInPnd = matMisOn5InPnd @ inv(matMisOn0InPnd)

        #* but wait, we're in sensor local, transform everything here!
        mat0to5ideal = inv(matPndTo0) @ mat0to5ideal @ (matPndTo0)
        matWanted = inv(matPndTo0) @ mat0to5MisInPnd @ (matPndTo0)
        matWanted = matWanted @ mat0to5ideal
        return matWanted

    def cheatActualMatrix(self, p1, p2):
        with open('input/detectorMatrices-sensors-1.00.json') as f:
            totalMatrices = json.load(f)

        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)

        mat0to5actually = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

        matPndTo0 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)

        # I don't have these!
        matMisOn0 = np.array(misalignMatrices[p1]).reshape(4, 4)

        matMisOn0InPnd = matPndTo0 @ matMisOn0 @ inv(matPndTo0)
        matPndTo0mis = matMisOn0InPnd @ matPndTo0

        #* but wait, we're in sensor local, transform everything here!
        mat0to5actually = inv(matPndTo0mis) @ mat0to5actually @ (matPndTo0mis)
        return mat0to5actually


    def dMat(self, mat1, mat2):
        mat1 = np.round(mat1, 5)
        mat2 = np.round(mat2, 5)
        dmat = (mat1 - mat2)*1e4

        print('=== dmat ===')
        print(f'mat1:\n{mat1}')
        print(f'mat2:\n{mat2}')
        print(f'dmat *1e4:\n{dmat}')
        print('=== end ===')

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    pass
