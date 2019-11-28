#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Uses multiple overlap matrices and the ideal detector matrices to compute alignment matrices for each sensor.
Each combiner is responsible for a single module.

It requires the misalignment matrices of sensor 0 and 1 for its assigned module.
We will obtain these with microscopic measurements.

The overlap matrices come from the Reco Points and are thusly already in PANDA global!
They were created in the module-local frame of reference. For a more detailed mathematical
description, refer to my PhD thesis.
"""


class alignmentMatrixCombiner:

    def __init__(self, modulePath):
        self.modulePath = modulePath
        self.alignmentMatrices = {}
        self.overlapMatrices = None
        self.idealDetectorMatrices = None
        self.externalMatrices = None

    def setOverlapMatrices(self, matrices):
        self.overlapMatrices = matrices

    def setIdealDetectorMatrices(self, matrices):
        self.idealDetectorMatrices = matrices

    def setExternallyMeasuredMatrices(self, matrices):
        self.externalMatrices = matrices

    def getDigit(self, number, n):
        return int(number) // 10**n % 10

    def getSmallOverlap(self, overlap):
        return str(self.getDigit(overlap, 0))

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    def sortOverlapMatrices(self):
        tempDict = {}
        # add small overlap to each overlap info, we'll need that info later
        for overlapID in self.overlapMatrices:
            smallOverlap = self.getSmallOverlap(overlapID)
            tempDict[smallOverlap] = self.overlapMatrices[overlapID]

        # and sort by new small overlap. that's okay, the real overlapID is still a field of the dict
        self.overlapMatrices = tempDict

    def getIdealMatrixP1ToP2(self, path1, path2):
        # matrix from pnd global to sen1
        m1 = self.idealDetectorMatrices[path1]
        # matrix from pnd global to sen2
        m2 = self.idealDetectorMatrices[path2]
        # matrix from sen1 to sen2
        return m2@inv(m1)

    def baseTransform(self, mat, matFromAtoB):
        """
        Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
        If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
        this function inv(matTo0). I know it's confusing, but that's the way this works.

        Example: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
        """
        return matFromAtoB @ mat @ inv(matFromAtoB)

    def combine1to2(self):

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m2 = self.idealDetectorMatrices[p2]

        m1to2Ideal = self.getIdealMatrixP1ToP2(p1, p2)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)

        mICP1t8 = self.overlapMatrices['4']
        mICP2t8 = self.overlapMatrices['5']

        # * this is the actual computation
        m1to2FromICP = inv(inv(mICP2t8) @ mICP1t8) @ m1to2Ideal

        # transform this matrix to the system of misaligned sensor1
        mTotalFromMathInAstar = self.baseTransform(m1to2FromICP, m1misInPnd)
        mBstar = mTotalFromMathInAstar @ m1misInPnd @ inv(m1to2Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m2))
        return mBstarInSenB

    def combine1to3(self):

        # * matrix path: mat1t8 -> mat8to3
        # the rest is pretty much like in 1->2

        p1 = self.modulePath + '/sensor_1'
        p3 = self.modulePath + '/sensor_3'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m3 = self.idealDetectorMatrices[p3]

        m1to3Ideal = self.getIdealMatrixP1ToP2(p1, p3)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)

        mICP1t8 = self.overlapMatrices['4']
        mICP3t8 = self.overlapMatrices['1']

        # * this is the actual computation
        m1to3FromICP = inv(inv(mICP3t8) @ mICP1t8) @ m1to3Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to3FromICPInAstar = self.baseTransform(m1to3FromICP, m1misInPnd)
        mBstar = m1to3FromICPInAstar @ m1misInPnd @ inv(m1to3Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m3))
        return mBstarInSenB

    def combine1to4a(self):
        # * matrix path: mat1t8 -> mat8to2 -> mat2to9 -> mat9to4

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p4 = self.modulePath + '/sensor_4'
        p8 = self.modulePath + '/sensor_8'
        p9 = self.modulePath + '/sensor_9'

        m1 = self.idealDetectorMatrices[p1]
        m4 = self.idealDetectorMatrices[p4]

        m1to4Ideal = self.getIdealMatrixP1ToP2(p1, p4)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        # mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)
        # mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)

        mICP1t8 = self.overlapMatrices['4']
        mICP2t8 = self.overlapMatrices['5']
        mICP2t9 = self.overlapMatrices['6']
        mICP4t9 = self.overlapMatrices['2']

        # * this is the actual computation
        m1to4FromICP = inv(inv(mICP4t9) @ mICP2t9 @ inv(mICP2t8) @ mICP1t8) @ m1to4Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to4FromICPInAstar = self.baseTransform(m1to4FromICP, m1misInPnd)
        mBstar = m1to4FromICPInAstar @ m1misInPnd @ inv(m1to4Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m4))
        return mBstarInSenB

    def combine1to4b(self):
        # * matrix path: mat1t8 -> mat8to3 -> mat3to7 -> mat7to4

        p1 = self.modulePath + '/sensor_1'
        p3 = self.modulePath + '/sensor_3'
        p4 = self.modulePath + '/sensor_4'
        p7 = self.modulePath + '/sensor_7'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m4 = self.idealDetectorMatrices[p4]

        m1to4Ideal = self.getIdealMatrixP1ToP2(p1, p4)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)
        # mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        # mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)

        mICP1t8 = self.overlapMatrices['4']
        mICP3t7 = self.overlapMatrices['7']
        mICP3t8 = self.overlapMatrices['1']
        mICP4t7 = self.overlapMatrices['8']

        # * this is the actual computation
        m1to4FromICP = inv(inv(mICP4t7) @ mICP3t7 @ inv(mICP3t8) @ mICP1t8) @ m1to4Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to4FromICPInAstar = self.baseTransform(m1to4FromICP, m1misInPnd)
        mBstar = m1to4FromICPInAstar @ m1misInPnd @ inv(m1to4Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m4))
        return mBstarInSenB

    def combine0to5(self):
        # * matrix path: mat0t5

        p0 = self.modulePath + '/sensor_0'
        p5 = self.modulePath + '/sensor_5'

        m0 = self.idealDetectorMatrices[p0]
        m5 = self.idealDetectorMatrices[p5]

        m0to5Ideal = self.getIdealMatrixP1ToP2(p0, p5)
        m0misInPnd = self.baseTransform(self.externalMatrices[p0], m0)

        # mICP0t5 = self.getOverlapMisalignLikeICP(p0, p5)

        mICP0t5 = self.overlapMatrices['0']

        # * this is the actual computation
        m0to5FromICP = inv(mICP0t5) @ m0to5Ideal

        # transform this matrix to the system of misaligned sensor0
        m0to5FromICPInAstar = self.baseTransform(m0to5FromICP, m0misInPnd)
        mBstar = m0to5FromICPInAstar @ m0misInPnd @ inv(m0to5Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m5))
        return mBstarInSenB

    def combine1to6(self):
        # * matrix path: mat1t8 -> mat8to3 -> mat3to6

        p1 = self.modulePath + '/sensor_1'
        p3 = self.modulePath + '/sensor_3'
        p6 = self.modulePath + '/sensor_6'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m6 = self.idealDetectorMatrices[p6]

        m1to6Ideal = self.getIdealMatrixP1ToP2(p1, p6)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP3t6 = self.getOverlapMisalignLikeICP(p3, p6)
        # mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)

        mICP1t8 = self.overlapMatrices['4']
        mICP3t6 = self.overlapMatrices['3']
        mICP3t8 = self.overlapMatrices['1']

        # * this is the actual computation
        m1to6FromICP = inv(mICP3t6 @ inv(mICP3t8) @ mICP1t8) @ m1to6Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to6FromICPInAstar = self.baseTransform(m1to6FromICP, m1misInPnd)
        mBstar = m1to6FromICPInAstar @ m1misInPnd @ inv(m1to6Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m6))
        return mBstarInSenB

    def combine1to7a(self):
        # * matrix path: mat1t8 -> mat8to3 -> mat3to7

        p1 = self.modulePath + '/sensor_1'
        p3 = self.modulePath + '/sensor_3'
        p7 = self.modulePath + '/sensor_7'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m7 = self.idealDetectorMatrices[p7]

        m1to7Ideal = self.getIdealMatrixP1ToP2(p1, p7)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        # mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)

        mICP1t8 = self.overlapMatrices['4']
        mICP3t8 = self.overlapMatrices['1']
        mICP3t7 = self.overlapMatrices['7']

        # * this is the actual computation
        m1to7FromICP = inv(mICP3t7 @ inv(mICP3t8) @ mICP1t8) @ m1to7Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to7FromICPInAstar = self.baseTransform(m1to7FromICP, m1misInPnd)
        mBstar = m1to7FromICPInAstar @ m1misInPnd @ inv(m1to7Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m7))
        return mBstarInSenB

    def combine1to7b(self):
        # * matrix path: mat1t8 -> mat8to2 -> mat2to9 -> mat9to4 -> mat4to7

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p4 = self.modulePath + '/sensor_4'
        p7 = self.modulePath + '/sensor_7'
        p8 = self.modulePath + '/sensor_8'
        p9 = self.modulePath + '/sensor_9'

        m1 = self.idealDetectorMatrices[p1]
        m7 = self.idealDetectorMatrices[p7]

        m1to7Ideal = self.getIdealMatrixP1ToP2(p1, p7)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        # mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)
        # mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)
        # mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)

        mICP1t8 = self.overlapMatrices['4']
        mICP2t8 = self.overlapMatrices['5']
        mICP2t9 = self.overlapMatrices['6']
        mICP4t7 = self.overlapMatrices['8']
        mICP4t9 = self.overlapMatrices['2']

        # * this is the actual computation
        m1to7FromICP = inv(mICP4t7 @ inv(mICP4t9) @ mICP2t9 @ inv(mICP2t8) @ mICP1t8) @ m1to7Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to7FromICPInAstar = self.baseTransform(m1to7FromICP, m1misInPnd)
        mBstar = m1to7FromICPInAstar @ m1misInPnd @ inv(m1to7Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m7))
        return mBstarInSenB

    def combine1to8(self):
        # * matrix path: mat1t8 -> mat8to3 -> mat3to6

        p1 = self.modulePath + '/sensor_1'
        p8 = self.modulePath + '/sensor_8'

        m1 = self.idealDetectorMatrices[p1]
        m8 = self.idealDetectorMatrices[p8]

        m1to8Ideal = self.getIdealMatrixP1ToP2(p1, p8)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)

        mICP1t8 = self.overlapMatrices['4']

        # * this is the actual computation
        m1to8FromICP = inv(mICP1t8) @ m1to8Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to8FromICPInAstar = self.baseTransform(m1to8FromICP, m1misInPnd)
        mBstar = m1to8FromICPInAstar @ m1misInPnd @ inv(m1to8Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m8))
        return mBstarInSenB

    def combine1to9a(self):
        # * matrix path: mat1t8 -> mat8to2 -> mat2to9

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p8 = self.modulePath + '/sensor_8'
        p9 = self.modulePath + '/sensor_9'

        m1 = self.idealDetectorMatrices[p1]
        m9 = self.idealDetectorMatrices[p9]

        m1to9Ideal = self.getIdealMatrixP1ToP2(p1, p9)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        # mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)

        mICP1t8 = self.overlapMatrices['4']
        mICP2t8 = self.overlapMatrices['5']
        mICP2t9 = self.overlapMatrices['6']

        # * this is the actual computation
        m1to9FromICP = inv(mICP2t9 @ inv(mICP2t8)  @ mICP1t8) @ m1to9Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to9FromICPInAstar = self.baseTransform(m1to9FromICP, m1misInPnd)
        mBstar = m1to9FromICPInAstar @ m1misInPnd @ inv(m1to9Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m9))
        return mBstarInSenB

    def combine1to9b(self):
        # * matrix path: mat1t8 -> mat8to3 -> mat3to7 -> mat7to4 -> mat4to9

        p1 = self.modulePath + '/sensor_1'
        p3 = self.modulePath + '/sensor_3'
        p4 = self.modulePath + '/sensor_4'
        p7 = self.modulePath + '/sensor_7'
        p8 = self.modulePath + '/sensor_8'
        p9 = self.modulePath + '/sensor_9'

        m1 = self.idealDetectorMatrices[p1]
        m9 = self.idealDetectorMatrices[p9]

        m1to9Ideal = self.getIdealMatrixP1ToP2(p1, p9)
        m1misInPnd = self.baseTransform(self.externalMatrices[p1], m1)

        # mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        # mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)
        # mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        # mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)
        # mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)

        mICP1t8 = self.overlapMatrices['4']
        mICP3t7 = self.overlapMatrices['7']
        mICP3t8 = self.overlapMatrices['1']
        mICP4t7 = self.overlapMatrices['8']
        mICP4t9 = self.overlapMatrices['2']

        # * this is the actual computation
        m1to9FromICP = inv(mICP4t9 @ inv(mICP4t7) @ mICP3t7 @ inv(mICP3t8) @ mICP1t8) @ m1to9Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to9FromICPInAstar = self.baseTransform(m1to9FromICP, m1misInPnd)
        mBstar = m1to9FromICPInAstar @ m1misInPnd @ inv(m1to9Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m9))
        return mBstarInSenB

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None:
            raise Exception(f'ERROR! Please set overlaps, overlap matrices and ideal detector matrices first!')

        if self.externalMatrices is None:
            raise Exception(f'ERROR! Please set the externally measured matrices for sensor 0 and 1 for module {self.modulePath}!')

        # the overlap matrices from the matrix finders still have their entire overlapID, but we need only the smallOverlap
        self.sortOverlapMatrices()

        # all external matrices are 1D arrays, construct 2D np arrays from them
        for path in self.externalMatrices:
            self.externalMatrices[path] = self.externalMatrices[path]

        mat2mis = self.combine1to2()
        mat3mis = self.combine1to3()
        mat4amis = self.combine1to4a()
        mat4bmis = self.combine1to4b()
        mat5mis = self.combine0to5()
        mat6mis = self.combine1to6()
        mat7amis = self.combine1to7a()
        mat7bmis = self.combine1to7b()
        mat8mis = self.combine1to8()
        mat9amis = self.combine1to9a()
        mat9bmis = self.combine1to9b()

        # compute averages for the matrices that can be reached two ways
        mat4mis = (mat4amis + mat4bmis) / 2     # man I love numpy
        mat7mis = (mat7amis + mat7bmis) / 2
        mat9mis = (mat9amis + mat9bmis) / 2

        # now, all the overlap misalignments are in PND global!

        # copy the given misalignments, so that all are in the final set!
        self.alignmentMatrices[self.modulePath + '/sensor_0'] = self.externalMatrices[self.modulePath + '/sensor_0']
        self.alignmentMatrices[self.modulePath + '/sensor_1'] = self.externalMatrices[self.modulePath + '/sensor_1']

        # store computed misalignment matrices to internal dict
        self.alignmentMatrices[self.modulePath + '/sensor_2'] = mat2mis
        self.alignmentMatrices[self.modulePath + '/sensor_3'] = mat3mis
        self.alignmentMatrices[self.modulePath + '/sensor_4'] = mat4mis
        self.alignmentMatrices[self.modulePath + '/sensor_5'] = mat5mis
        self.alignmentMatrices[self.modulePath + '/sensor_6'] = mat6mis
        self.alignmentMatrices[self.modulePath + '/sensor_7'] = mat7mis
        self.alignmentMatrices[self.modulePath + '/sensor_8'] = mat8mis
        self.alignmentMatrices[self.modulePath + '/sensor_9'] = mat9mis

        print(f'successfully computed misalignments on module {self.modulePath} for {len(self.alignmentMatrices)} sensors!')
