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
        # return inv(m1)@m2
        # FIXME: fix this!
        return m2@inv(m1)

    # TODO: remove entire function
    def getIdealMatrixP1ToP2WRONG(self, path1, path2):
        # matrix from pnd global to sen1
        m1 = np.array(self.idealDetectorMatrices[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(self.idealDetectorMatrices[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return inv(m1)@m2

    def getMatrixP1ToP2fromMatrixDict(self, path1, path2, mat):
        # matrix from pnd global to sen1
        m1 = np.array(mat[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(mat[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        # return inv(m1)@m2
        # FIXME: fix this!
        return m2@inv(m1)

    # TODO: I think there is a mistake here still
    def getOverlapMatrixWithMisalignment(self, overlapInfo):

        p1 = overlapInfo['path1']
        p2 = overlapInfo['path2']
        m1to2ideal = self.getIdealMatrixP1ToP2(p1, p2)
        m1to2corr = self.overlapMatrices[overlapInfo['smallOverlap']]

        return m1to2corr@m1to2ideal

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

        with open('input/misMatrices/misMat-sensors-2.00.json') as f:
            misalignMatrices = json.load(f)

        with open('input/detectorMatrices-sensors-2.00.json') as f:
            totalMatrices = json.load(f)

        m1misTo2mis = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2', totalMatrices)

        # # ? current work position
        # print(f'm1to2 from ICP:\n{m1t2icp}')
        # print(f'm1to2 actually:\n{m1misTo2mis}')
        # print(f'difference:\n{(m1t2icp - m1misTo2mis)*1e4}')

        # ? new test

        matPndTo0 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
        matPndTo5 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)

        matPndTo0Misaligned = np.array(totalMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
        matPndTo5Misaligned = np.array(totalMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)

        matMisOn0 = np.array(misalignMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
        matMisOn5 = np.array(misalignMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)

        mat0to5Wrong = self.getIdealMatrixP1ToP2WRONG(self.modulePath + '/sensor_0', self.modulePath + '/sensor_5')
        print(f'wrong mat:\n{mat0to5Wrong}')

        # transform mis5 to 0
        misOn5in0 = mat0to5Wrong @ matMisOn5 @ inv(mat0to5Wrong)

        # misalign is now
        mat0to5misalignmentInPnd = np.round(misOn5in0 @ inv(matMisOn0), 5)

        m1t2misIcp = np.round(self.overlapMatrices['0'], 5)

        print(f'overlap matrix as seen by ICP:\n{m1t2misIcp}')
        print(f'overlap matrix from calculations:\n{mat0to5misalignmentInPnd}')
        print(f'Difference:\n{(m1t2misIcp-mat0to5misalignmentInPnd)*1e4}')

        # ? USE THIS TEST IF UNSURE, IT WORKS!
        if False:

            m3 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_3']).reshape(4, 4)
            m3mis = np.array(misalignMatrices[self.modulePath + '/sensor_3']).reshape(4, 4)
            m3misInPnd = m3 @ m3mis @ inv(m3)
            i3t4misalignedIdeal = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_3', self.modulePath + '/sensor_4', totalMatrices)
            mPndTo4misMyShit = i3t4misalignedIdeal @ m3misInPnd @ m3
            mPndTo4misActually = np.array(totalMatrices[self.modulePath + '/sensor_4']).reshape(4, 4)
            print(f'\n\nFinal Difference: {mPndTo4misMyShit-mPndTo4misActually}')

        # ? OR THIS, IT WORKS AS WELL!
        if False:

            m1 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)

            m1mis = np.array(misalignMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
            m2mis = np.array(misalignMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)

            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            m1misTo2mis = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2', totalMatrices)

            m2me = inv(m2misInPnd) @ m1misTo2mis @ m1misInPnd @ m1

            print(f'm2 me:\n{m2}')
            print(f'm2 actual:\n{m2me}')
            print(f'difference:\n{m2 - m2me}')

        # save to dict sensorID : alignment matrix here

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    pass
