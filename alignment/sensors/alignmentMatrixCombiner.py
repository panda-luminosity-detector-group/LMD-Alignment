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

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    def getIdealMatrixP1ToP2(self, path1, path2):
        # matrix from pnd global to sen1
        m1 = np.array(self.idealDetectorMatrices[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(self.idealDetectorMatrices[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return m2@inv(m1)

    # TODO: remove once the other stuff is in the comparer. this function was used for comparisons
    def getMatrixP1ToP2fromMatrixDict(self, path1, path2, mat):
        # matrix from pnd global to sen1
        m1 = np.array(mat[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(mat[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return m2@inv(m1)

    # FIXME: there is still an error in this function
    def getTotalOverlapMatrix(self, p1, p2):

        # prepare ideal matrix, transform to sen1
        matPndTo1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)

        mat1to2ideal = self.getIdealMatrixP1ToP2(p1, p2)
        mat1to2idealIn1 = inv(matPndTo1) @ mat1to2ideal @ (matPndTo1)

        # prepare ICP matrix, transform to sen1
        # TODO: change this to use the actual ICP matrix
        matICPmisalign1to2 = self.getOverlapMisalignLikeICP(p1, p2)
        matICP1to2In1 = inv(matPndTo1) @ matICPmisalign1to2 @ (matPndTo1)

        # make total matrix from ICP matrix and ideal matrix
        mat1to8TotalIn1 = matICP1to2In1 @ mat1to2idealIn1
        return mat1to8TotalIn1

    def baseTransform(self, mat, matFromAtoB):
        """
        Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
        If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
        this function inv(matTo0). I know it's confusing, but that's the way this works.

        Example: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
        """
        return matFromAtoB @ mat @ inv(matFromAtoB)

    def combine1to2VERBOSE(self):

        print('\n\n')
        print('=============')
        print('Combine 1to2:')
        print('=============')
        print('\n\n')

        # * matrix path: mat1t8 -> mat8to2

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p8 = self.modulePath + '/sensor_8'

        # ? ----------- begin cheat for comparison
        with open('input/detectorMatrices-sensors-1.00.json') as f:
            totalMatrices = json.load(f)
        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)
        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

        m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
        m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)

        # * we get this matrix from external measurements, remember!
        m1misInPnd = self.baseTransform(m1mis, m1)

        #! this is the matrix we are looking for!
        m2misInPnd = self.baseTransform(m2mis, m2)

        # get actual matrix from GeoManager
        m1misTo2Actual = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

        # what does this matrix look like in the system of MISALIGNED sensor A?
        # m1misTo2ActualInAstar = self.baseTransform(m1misTo2Actual, inv(m1misInPnd))
        # ? ----------- end cheat for comparison

        matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)

        m1to2Ideal = self.getIdealMatrixP1ToP2(p1, p2)

        # * this is mathematically correct! and it works!
        mTotalFromMath = inv(inv(mICP2t8) @ mICP1t8) @ m1to2Ideal

        # compare with actual (remember, one must be transformed, but it seems more logical to transform the ICP matrices)
        # also, this base transformation mus be done "backwards", look at the calculations
        mTotalFromMathInAstar = self.baseTransform(mTotalFromMath, m1misInPnd)

        # so now, just for shits and giggles, transform both to the module
        m1misTo2ActualInMod = self.baseTransform(m1misTo2Actual, inv(m1misInPnd))
        mTotalFromMathInAstarInMod = self.baseTransform(mTotalFromMathInAstar, inv(m1misInPnd))

        self.dMat(m1misTo2ActualInMod, mTotalFromMathInAstarInMod)

        # and FINALLY, we find the missing matrix B*:
        mBstar = mTotalFromMathInAstar @ m1misInPnd @ m1 @ inv(m2)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m2))

        print(f'so now what remains?')
        self.dMat(mBstarInSenB, m2mis)
        return mBstarInSenB

    def combine1to2(self):

        p1 = self.modulePath + '/sensor_1'
        p2 = self.modulePath + '/sensor_2'
        p8 = self.modulePath + '/sensor_8'

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

        m1to2Ideal = self.getIdealMatrixP1ToP2(p1, p2)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP2t8 = self.overlapMatrices['5']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m3 = np.array(self.idealDetectorMatrices[p3]).reshape(4, 4)

        m1to3Ideal = self.getIdealMatrixP1ToP2(p1, p3)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP3t8 = self.overlapMatrices['1']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m4 = np.array(self.idealDetectorMatrices[p4]).reshape(4, 4)

        m1to4Ideal = self.getIdealMatrixP1ToP2(p1, p4)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)
        mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP2t8 = self.overlapMatrices['5']
        # mICP2t9 = self.overlapMatrices['6']
        # mICP4t9 = self.overlapMatrices['2']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m4 = np.array(self.idealDetectorMatrices[p4]).reshape(4, 4)

        m1to4Ideal = self.getIdealMatrixP1ToP2(p1, p4)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)
        mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP3t7 = self.overlapMatrices['7']
        # mICP3t8 = self.overlapMatrices['1']
        # mICP4t7 = self.overlapMatrices['8']

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

        m0 = np.array(self.idealDetectorMatrices[p0]).reshape(4, 4)
        m5 = np.array(self.idealDetectorMatrices[p5]).reshape(4, 4)

        m0to5Ideal = self.getIdealMatrixP1ToP2(p0, p5)
        m0misInPnd = self.baseTransform(self.externalMatrices['0'], m0)

        mICP0t5 = self.getOverlapMisalignLikeICP(p0, p5)

        # mICP0t5 = self.overlapMatrices['0']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m6 = np.array(self.idealDetectorMatrices[p6]).reshape(4, 4)

        m1to6Ideal = self.getIdealMatrixP1ToP2(p1, p6)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP3t6 = self.getOverlapMisalignLikeICP(p3, p6)
        mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP3t6 = self.overlapMatrices['3']
        # mICP3t8 = self.overlapMatrices['1']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m7 = np.array(self.idealDetectorMatrices[p7]).reshape(4, 4)

        m1to7Ideal = self.getIdealMatrixP1ToP2(p1, p7)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP3t8 = self.overlapMatrices['1']
        # mICP3t7 = self.overlapMatrices['7']W

        # * this is the actual computation
        m1to7FromICP = inv( mICP3t7 @ inv(mICP3t8) @ mICP1t8) @ m1to7Ideal

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m7 = np.array(self.idealDetectorMatrices[p7]).reshape(4, 4)

        m1to7Ideal = self.getIdealMatrixP1ToP2(p1, p7)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)
        mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)
        mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP2t8 = self.overlapMatrices['5']
        # mICP2t9 = self.overlapMatrices['6']
        # mICP4t7 = self.overlapMatrices['8']
        # mICP4t9 = self.overlapMatrices['2']

        # * this is the actual computation
        m1to7FromICP = inv( mICP4t7 @ inv(mICP4t9) @ mICP2t9 @ inv(mICP2t8) @ mICP1t8) @ m1to7Ideal

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m8 = np.array(self.idealDetectorMatrices[p8]).reshape(4, 4)

        m1to8Ideal = self.getIdealMatrixP1ToP2(p1, p8)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)

        # mICP1t8 = self.overlapMatrices['4']

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m9 = np.array(self.idealDetectorMatrices[p9]).reshape(4, 4)

        m1to9Ideal = self.getIdealMatrixP1ToP2(p1, p9)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP2t8 = self.getOverlapMisalignLikeICP(p2, p8)
        mICP2t9 = self.getOverlapMisalignLikeICP(p2, p9)

        # mICP1t8 = self.overlapMatrices['4']
        # mICP2t8 = self.overlapMatrices['5']
        # mICP2t9 = self.overlapMatrices['6']

        # * this is the actual computation
        m1to9FromICP = inv( mICP2t9 @ inv(mICP2t8)  @ mICP1t8) @ m1to9Ideal

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

        m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        m9 = np.array(self.idealDetectorMatrices[p9]).reshape(4, 4)

        m1to9Ideal = self.getIdealMatrixP1ToP2(p1, p9)
        m1misInPnd = self.baseTransform(self.externalMatrices['1'], m1)

        mICP1t8 = self.getOverlapMisalignLikeICP(p1, p8)
        mICP3t7 = self.getOverlapMisalignLikeICP(p3, p7)
        mICP3t8 = self.getOverlapMisalignLikeICP(p3, p8)
        mICP4t7 = self.getOverlapMisalignLikeICP(p4, p7)
        mICP4t9 = self.getOverlapMisalignLikeICP(p4, p9)
        
        # mICP1t8 = self.overlapMatrices['4']
        # mICP3t7 = self.overlapMatrices['7']
        # mICP3t8 = self.overlapMatrices['1']
        # mICP4t7 = self.overlapMatrices['8']
        # mICP4t9 = self.overlapMatrices['2']

        # * this is the actual computation
        m1to9FromICP = inv( mICP4t9 @ inv(mICP4t7) @ mICP3t7 @ inv(mICP3t8) @ mICP1t8) @ m1to9Ideal

        # transform this matrix to the system of misaligned sensor1
        m1to9FromICPInAstar = self.baseTransform(m1to9FromICP, m1misInPnd)
        mBstar = m1to9FromICPInAstar @ m1misInPnd @ inv(m1to9Ideal)

        # transform it to senB, because that's where it lives:
        mBstarInSenB = self.baseTransform(mBstar, inv(m9))
        return mBstarInSenB

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None or self.overlapInfos is None:
            print(f'ERROR! Please set overlaps, overlap matrices and ideal detector matrices first!')
            return

        if self.externalMatrices is None:
            print(f'ERROR! Please set the externally measured matrices for sensor 0 and 1 for module {self.modulePath}!')
            return

        # these two matrices are measured externally, e.g. by microscope
        # for now, they are generated by a different function,
        # but the file description should not change anymore
        # m0t1 = self.getIdealMatrixP1ToP2(self.modulePath + '/sensor_0', self.modulePath + '/sensor_1')
        # m0mis = self.externalMatrices[self.modulePath]['mis0']
        # m1mis = self.externalMatrices[self.modulePath]['mis1']

        # TODO: delete these after everything else is completed. the combiner won't know the misalignment matrices at all!
        # except for the very first one, obviously
        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)

        self.externalMatrices['0'] = np.array(misalignMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
        self.externalMatrices['1'] = np.array(misalignMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)

        cheatMat2star = np.array(misalignMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
        cheatMat3star = np.array(misalignMatrices[self.modulePath + '/sensor_3']).reshape(4, 4)
        cheatMat4star = np.array(misalignMatrices[self.modulePath + '/sensor_4']).reshape(4, 4)
        cheatMat5star = np.array(misalignMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)
        cheatMat6star = np.array(misalignMatrices[self.modulePath + '/sensor_6']).reshape(4, 4)
        cheatMat7star = np.array(misalignMatrices[self.modulePath + '/sensor_7']).reshape(4, 4)
        cheatMat8star = np.array(misalignMatrices[self.modulePath + '/sensor_8']).reshape(4, 4)
        cheatMat9star = np.array(misalignMatrices[self.modulePath + '/sensor_9']).reshape(4, 4)

        if len(self.externalMatrices) < 2:
            print(f'ERROR! Please set the externally measured matrices for sensor 0 and 1 for module {self.modulePath}!')
            return

        # ? create all intermediate matrices here
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

        print('Comparison m2*:')
        self.dMat(cheatMat2star, mat2mis)
        print('Comparison m3*:')
        self.dMat(cheatMat3star, mat3mis)
        print('Comparison m4a*:')
        self.dMat(cheatMat4star, mat4amis)
        print('Comparison m4b*:')
        self.dMat(cheatMat4star, mat4bmis)

        print('Comparison m5*:')
        self.dMat(cheatMat5star, mat5mis)

        print('Comparison m6*:')
        self.dMat(cheatMat6star, mat6mis)
        print('Comparison m7a*:')
        self.dMat(cheatMat7star, mat7amis)
        print('Comparison m7b*:')
        self.dMat(cheatMat7star, mat7bmis)
        print('Comparison m8*:')
        self.dMat(cheatMat8star, mat8mis)
        print('Comparison m9a*:')
        self.dMat(cheatMat9star, mat9amis)
        print('Comparison m9b*:')
        self.dMat(cheatMat9star, mat9bmis)

        # compute averages for the matrices that can be reached two ways

        mat4mis = (mat4amis + mat4bmis) / 2     # damn I love numpy
        mat7mis = (mat7amis + mat7bmis) / 2
        mat9mis = (mat9amis + mat9bmis) / 2

        # store to internal dict
        self.alignmentMatrices[self.modulePath + '/sensor_2'] = mat2mis
        self.alignmentMatrices[self.modulePath + '/sensor_3'] = mat3mis
        self.alignmentMatrices[self.modulePath + '/sensor_4'] = mat4mis
        self.alignmentMatrices[self.modulePath + '/sensor_5'] = mat5mis
        self.alignmentMatrices[self.modulePath + '/sensor_6'] = mat6mis
        self.alignmentMatrices[self.modulePath + '/sensor_7'] = mat7mis
        self.alignmentMatrices[self.modulePath + '/sensor_8'] = mat8mis
        self.alignmentMatrices[self.modulePath + '/sensor_9'] = mat9mis


        if False:
            #! Attention! This is WRONG, it used the old ICP matrices, which were wrong too
            """
            Now, using the stuff I learned above, I can hopefully combine multiple matrices to get mat1to2

            # TODO: still bug in here, this doesn't work!
            """
            p1 = self.modulePath + '/sensor_1'
            p2 = self.modulePath + '/sensor_2'
            p8 = self.modulePath + '/sensor_8'

            # I have thse matrices from the detector design
            mat1to8ideal = self.getIdealMatrixP1ToP2(p1, p8)
            mat2to8ideal = self.getIdealMatrixP1ToP2(p2, p8)

            matPndTo1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            matPndTo2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
            matPndTo8 = np.array(self.idealDetectorMatrices[p8]).reshape(4, 4)

            # I don't have these!
            matMisOn1 = np.array(misalignMatrices[p1]).reshape(4, 4)
            matMisOn2 = np.array(misalignMatrices[p2]).reshape(4, 4)
            matMisOn8 = np.array(misalignMatrices[p8]).reshape(4, 4)

            matMisOn1InPnd = matPndTo1 @ matMisOn1 @ inv(matPndTo1)
            matMisOn2InPnd = matPndTo2 @ matMisOn2 @ inv(matPndTo2)
            matMisOn8InPnd = matPndTo8 @ matMisOn8 @ inv(matPndTo8)

            matPndTo1mis = matMisOn1InPnd @ matPndTo1
            matPndTo2mis = matMisOn2InPnd @ matPndTo2
            matPndTo8mis = matMisOn8InPnd @ matPndTo8

            # this is the ICP-like matrix
            matICP1to8 = self.getOverlapMisalignLikeICP(p1, p8)
            matICP2to8 = self.getOverlapMisalignLikeICP(p2, p8)

            # * but wait, we're in sensor local, transform everything here!
            mat1to8actually = self.getActualMatrixFromGeoManager(p1, p8)
            mat2to8actually = self.getActualMatrixFromGeoManager(p2, p8)
            mat1to2actually = self.getActualMatrixFromGeoManager(p1, p2)

            # this is mat1to2 as seen from the MISALIGNED sensor1!
            # I don't know these, but this is just to see if I found the correct matrix.
            mat1To8actuallyIn1mis = inv(matPndTo1mis) @ mat1to8actually @ (matPndTo1mis)
            mat2To8actuallyIn2mis = inv(matPndTo2mis) @ mat2to8actually @ (matPndTo2mis)
            mat1to2actuallyIn1mis = inv(matPndTo1mis) @ mat1to2actually @ (matPndTo1mis)

            # these are the matrices m4 and m5 and their combination!
            # this is the matrix the ICP finds in the frame of reference of MISALIGNED sensor 0
            mat1to8idealIn1 = inv(matPndTo1) @ mat1to8ideal @ (matPndTo1)
            mat2to8idealIn2 = inv(matPndTo2) @ mat2to8ideal @ (matPndTo2)

            # this is the trick! transform everything to sensor BEFORE you apply the ICP matrix to the ideal
            matICP1to8In1 = inv(matPndTo1) @ matICP1to8 @ (matPndTo1)
            # careful, this should be in sensor TWO, not one, because this is still local to 2!
            matICP2to8In2 = inv(matPndTo2) @ matICP2to8 @ (matPndTo2)

            # apply ICP matrix to ideal IN SENSOR 1/2!
            mat1to8TotalIn1 = matICP1to8In1 @ mat1to8idealIn1
            mat2to8TotalIn2 = matICP2to8In2 @ mat2to8idealIn2

            print(f'compare actual and constructed for 1-8:')
            self.dMat(mat1To8actuallyIn1mis, mat1to8TotalIn1)
            print(f'compare actual and constructed for 2-8:')
            self.dMat(mat2To8actuallyIn2mis, mat2to8TotalIn2)

            # alright, if I want to multiply m4 and m5, they both have to live in the same
            # system of reference, otherwise I just get junk.

            # careful, I can't use m1to2Ideal, because there is misalignment on p2 and p8
            # that we don't know. therefore, this transformation matrix has no misalignment
            # and doesn't work.
            # there are matrices that do have misalignment and point from A to B,
            # they are our overlap matrices!

            # so, use the overlap matrices themselves to transform the matrices
            # I know this base transform is pointless, but for completeness sake leave it in!
            mat2to8TotalIn8 = mat2to8TotalIn2 @ mat2to8TotalIn2 @ inv(mat2to8TotalIn2)

            # this is the things that's been missing for so long! I know the base transform looks
            # inverted, but that's because I need m8to1, and I only have m1to8. to that's fine.
            mat2to8TotalIn1 = inv(mat1to8TotalIn1) @ mat2to8TotalIn8 @ mat1to8TotalIn1

            # they are now both in the system of sensor 1
            mat1to2totalIn1 = inv(mat2to8TotalIn1) @ mat1to8TotalIn1

            print('AND THE GREAT FINALE:')
            print(f'compare actual and constructed for 1-2:')
            self.dMat(mat1to2actuallyIn1mis, mat1to2totalIn1)

        if False:
            # * This is still correct!
            msg = "Example: get perfect mat1to2 and apply misalignment onto it, compare with actual mat1to2"
            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            p1 = self.modulePath + '/sensor_0'
            p2 = self.modulePath + '/sensor_5'

            m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
            m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
            m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

            # get actual matrix from GeoManager
            m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)
            m1misTo2misInMod = self.baseTransform(m1misTo2WithAddedMis, inv(matToModule))

            # method 1: use the perfect matrix, apply misalignments (which we don't actually know)
            # and compare with unknown actual misaligned mat
            mat1to2Perfect = self.getIdealMatrixP1ToP2(p1, p2)
            mat1to2Compute = m2misInPnd @ mat1to2Perfect @ inv(m1misInPnd)

            # transform to module, for ease of reading
            mat1to2ComputeInMod = self.baseTransform(mat1to2Compute, inv(matToModule))
            mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(matToModule))

            print(msg)
            print('Method 1:')
            self.dMat(m1misTo2misInMod, mat1to2ComputeInMod)

        if False:
            # * This is still correct!
            msg = "Example: get ICP matrix and ideal matrix, compare with actual matrix. We can do this onlt if the actual matrix is transformed to MISALIGNED sensor A. After that, we can transform both to the module system."
            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            p1 = self.modulePath + '/sensor_1'
            p2 = self.modulePath + '/sensor_3'

            m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
            m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
            m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

            # get actual matrix from GeoManager
            m1misTo2Actual = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

            # what does this matrix look like in the system of MISALIGNED sensor A?
            m1misTo2ActualInAstar = self.baseTransform(m1misTo2Actual, inv(m1misInPnd))

            # and now, what does it look like in the module?
            m1misTo2ActualInMod = self.baseTransform(m1misTo2ActualInAstar, inv(matToModule))

            # method 2: use ICP matrix and ideal m1, m2 to get misaligned mat
            Micp = self.getOverlapMisalignLikeICP(p1, p2)
            Mideal = self.getIdealMatrixP1ToP2(p1, p2)

            mat1to2fromICP = inv(Micp) @ Mideal
            mat1to2fromICPInModule = self.baseTransform(mat1to2fromICP, inv(matToModule))

            print(msg)
            print('Method 2:')
            self.dMat(m1misTo2ActualInMod, mat1to2fromICPInModule)

        if False:
            # * This is still correct!
            """
            Example: we are sitting in MISALIGNED sensor 1 and want to know the matrix to misaligned sensor2.
            From that matrix, we remove the misalignment of sensor2 (because that is included in sensor2),
            and add the misalignment to sensor1 (because we're sitting in a misaligned spot).
            now compare with the ideal matrix1to2 (in ALIGNED sensor1)
            """

            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            m1 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
            m1mis = np.array(misalignMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
            m2mis = np.array(misalignMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            # matrix to MISALIGNED sensor1
            matPndTo1mis = m1misInPnd @ m1

            # get actual matrix from GeoManager
            m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2', totalMatrices)

            # remove misalign2 from and add misalign1 to this matrix
            m1misTo2NoMisalign = (m1misInPnd) @ inv(m2misInPnd) @ m1misTo2WithAddedMis  # this line is very useful, because we get "inv((m1misInPnd) @ inv(m2misInPnd))" from the ICP!

            # tansform to system of misaligned s1
            m1misTo2misInS1 = self.baseTransform(m1misTo2NoMisalign, inv(matPndTo1mis))

            # compare with perfect matrix
            mat1to2Perfect = self.getIdealMatrixP1ToP2(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2')
            mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(m1))

            self.dMat(m1misTo2misInS1, mat1to2PerfectInMod)

            """
            so, this works and is interesting, because this way, I can find my misalignment to sen2 (if I know it for sen1)
            """

        if False:
            # * This is still correct!
            msg = """
            Example: we sit at misaligned sensor 1, and want to know the matrix to misaligned sensor 2.
            We start with the total matrix from mis1 to mis2, substract mis2 and add mis1.
            We have the inverse ICP matrix and apply it to a misaligned total overlap, compare that with the ideal overlap
            """

            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            p1 = self.modulePath + '/sensor_0'
            p2 = self.modulePath + '/sensor_5'

            m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
            m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
            m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            # matrix to MISALIGNED sensor1
            matPndTo1mis = m1misInPnd @ m1

            # get actual matrix from GeoManager
            m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

            # remove misalign1 from and add misalign2 to this matrix
            m1misTo2MisRemoved = (m1misInPnd) @ inv(m2misInPnd) @ m1misTo2WithAddedMis

            # tansform to system of misaligned s1
            m1misTo2misInS1 = self.baseTransform(m1misTo2MisRemoved, inv(matPndTo1mis))

            # compare with perfect matrix
            mat1to2Perfect = self.getIdealMatrixP1ToP2(p1, p2)
            mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(m1))

            print(msg)
            self.dMat(m1misTo2misInS1, mat1to2PerfectInMod)

            """
            so, this works and is interesting, because this way, I can find my misalignment to sen2 (if I know it for sen1)
            """

        if False:
            #! ATTENTION! WRONG, or at least work in progress!
            msg = "Example: we have the ICP matrix and apply it to a misaligned overlap, compare that with the ideal overlap. We add and remove misalignment by hand."
            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            m1 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)
            m1mis = np.array(misalignMatrices[self.modulePath + '/sensor_0']).reshape(4, 4)
            m2mis = np.array(misalignMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)
            m1misInPnd = m1 @ m1mis @ inv(m1)
            m2misInPnd = m2 @ m2mis @ inv(m2)

            # get actual matrix from GeoManager
            m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_0', self.modulePath + '/sensor_5', totalMatrices)

            # remove misalign1 from and add misalign2 to this matrix
            m1misTo2WithAddedMis = (m1misInPnd) @ inv(m2misInPnd) @ m1misTo2WithAddedMis

            # tansform to system of MISALIGNED s1
            m1misTo2misInS1 = self.baseTransform(m1misTo2WithAddedMis, inv(m1misInPnd))

            # compare with perfect matrix
            mat1to2Perfect = self.getIdealMatrixP1ToP2(self.modulePath + '/sensor_0', self.modulePath + '/sensor_5')
            mat1to2PerfectInS0 = self.baseTransform(mat1to2Perfect, inv(m1))
            print(msg)
            self.dMat(m1misTo2misInS1, mat1to2PerfectInS0)

        if False:
            msg = "I used math to get the ICP matrix. It was a work of art. And math."
            """
            # port this to the comparer! this is how you compare the overlap matrix to the simulation matrix
            ! DO NOT DELETE THIS BLOCK until you ported it to the comparer!
            """

            with open('input/detectorMatrices-sensors-1.00.json') as f:
                totalMatrices = json.load(f)

            m0t5misIcp = self.overlapMatrices['0']

            p1 = self.modulePath + '/sensor_0'
            p2 = self.modulePath + '/sensor_5'

            m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
            m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
            m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
            m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)

            matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

            m1misInPnd = self.baseTransform(m1mis, m1)
            m2misInPnd = self.baseTransform(m2mis, m2)

            m1star = m1misInPnd @ m1
            m2star = m2misInPnd @ m2

            ICPmat = inv(m2misInPnd) @ (m1misInPnd)
            compareICP = self.getOverlapMisalignLikeICP(p1, p2)

            print(msg)
            self.dMat(ICPmat, m0t5misIcp)

        if False:
            print('Which way goes the point trafo?')
            p1 = self.modulePath + '/sensor_0'
            m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)

            point = np.array([0, 0, 0, 1]).reshape(4, 1)     # point in the center of A
            pointInPnd = (m1) @ point

            print(f'point in sensor:{point}')
            print(f'point in pnd:{pointInPnd}')

        """
        now, the overlap misalignments are in PND global, as they should, but to apply them to an ideal overlap,
        they must be transformed into the system of the first sensor of the overlap
        """

        # #! keep cheating, just for now:
        # p1 = self.modulePath + '/sensor_1'
        # p2 = self.modulePath + '/sensor_2'
        # matPndTo1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        # matMisOn1 = np.array(misalignMatrices[p1]).reshape(4, 4)
        # matMisOn1InPnd = matPndTo1 @ matMisOn1 @ inv(matPndTo1)
        # matPndTo1mis = matMisOn1InPnd @ matPndTo1
        # mat1to2actually = self.getActualMatrixFromGeoManager(p1, p2)
        # mat1to2actuallyIn1mis = inv(matPndTo1mis) @ mat1to2actually @ (matPndTo1mis)

        # print(f'while you refine:')
        # self.dMat(mat1to2actuallyIn1mis, m1t2icp)

    #! we don't have some of these matrices, this is cheating and should go in the comparer
    def getOverlapMisalignLikeICP(self, p1, p2):
        with open('input/misMatrices/misMat-sensors-1.00.json') as f:
            misalignMatrices = json.load(f)

        # TODO: include a filter for overlapping sensors!
        # this code works for any sensor pair (which is good),
        # which doesn't make sense because I want overlap matrices!

        matPndTo0 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        matPndTo5 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

        # I don't have these!
        matMisOn0 = np.array(misalignMatrices[p1]).reshape(4, 4)
        matMisOn5 = np.array(misalignMatrices[p2]).reshape(4, 4)

        matMisOn0InPnd = self.baseTransform(matMisOn0, (matPndTo0))
        matMisOn5InPnd = self.baseTransform(matMisOn5, (matPndTo5))

        # this is the ICP like matrix
        # see paper calc.ICP
        mat0to5MisInPnd = inv(matMisOn5InPnd) @ (matMisOn0InPnd)
        return mat0to5MisInPnd

    #! we don't have some of these matrices, this is cheating and should go in the comparer
    def getActualMatrixFromGeoManager(self, p1, p2):
        with open('input/detectorMatrices-sensors-1.00.json') as f:
            totalMatrices = json.load(f)
        matP1toP2 = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)
        return matP1toP2

    #! this doesn't belong here, move it to the comparer or delete it!
    def dMat(self, mat1, mat2):
        mat1 = np.round(mat1, 10)
        mat2 = np.round(mat2, 10)
        dmat = np.round((mat1 - mat2)*1e4, 3)

        print('=== dmat ===')
        # print(f'mat1:\n{mat1}')
        # print(f'mat2:\n{mat2}')
        print(f'dmat *1e4:\n{dmat}')
        print('=== end ===')
