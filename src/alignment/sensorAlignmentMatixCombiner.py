#!/usr/bin/env python3
import numpy as np
from numpy.linalg import inv

from src.util.matrix import baseTransform

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Uses multiple overlap matrices and the ideal detector matrices to compute alignment matrices for each sensor.
Each combiner is responsible for a single module.

It requires the misalignment matrices of sensor 0 and 1 for its assigned module.
We will obtain these with microscopic measurements.

The overlap matrices come from the Reco Points and are thus already in PANDA global. All calculations must
happen in PANDA GLOBAL, but the actual misalignment matrices are applied in the current super frame.
That means the misalignment matrix for sensor 1 is applied in the frame of sensor 1, NOT PANDA GLOBAL.
(Doesn't matter how it was generated, this is the way it's done by FAIRROOT, and that's by design).
For the math to work out, all matrices must be transformed to PANDA GLOBAL before calculations.
To compare the found alignment matrices with the input misalignment matrces, the found alignment
matrices must be transformed to the reference frame of the corresponding sensor.
"""


class alignmentMatrixCombiner:
    def __init__(self, moduleID, modulePath):
        self.moduleID = moduleID
        self.modulePath = modulePath  # was: moduleIdToModulePath[str(self.moduleID)]
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

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    def initCalculator(self):
        # required paths and ideal matrices for base transformations
        p0 = self.modulePath + "/sensor_0"
        p1 = self.modulePath + "/sensor_1"
        p2 = self.modulePath + "/sensor_2"
        p3 = self.modulePath + "/sensor_3"
        p4 = self.modulePath + "/sensor_4"
        p5 = self.modulePath + "/sensor_5"
        p6 = self.modulePath + "/sensor_6"
        p7 = self.modulePath + "/sensor_7"
        self.m0 = self.idealDetectorMatrices[p0]
        self.m1 = self.idealDetectorMatrices[p1]
        self.m2 = self.idealDetectorMatrices[p2]
        self.m3 = self.idealDetectorMatrices[p3]
        self.m4 = self.idealDetectorMatrices[p4]
        self.m5 = self.idealDetectorMatrices[p5]
        self.m6 = self.idealDetectorMatrices[p6]
        self.m7 = self.idealDetectorMatrices[p7]

        # attention! m0star and m1star are applied by FAIRROOT in the system
        # of sensors 0 and 1 respectively
        # that means m1star here is given in sensor 1, not PANDA GLOBAL
        # for the math to work out, m1star must be transformed to PANDA GLOBAL
        m0starInSensor0 = self.externalMatrices[p0]
        m1starInSensor1 = self.externalMatrices[p1]
        self.m0star = baseTransform(m0starInSensor0, self.m0)
        self.m1star = baseTransform(m1starInSensor1, self.m1)

        # see sensorIDs.pdf
        self.mICP0t4 = self.overlapMatrices[str(self.moduleID)]["0"]
        self.mICP1t7 = self.overlapMatrices[str(self.moduleID)]["1"]
        self.mICP2t7 = self.overlapMatrices[str(self.moduleID)]["2"]
        self.mICP3t7 = self.overlapMatrices[str(self.moduleID)]["3"]
        self.mICP3t5 = self.overlapMatrices[str(self.moduleID)]["4"]
        self.mICP3t6 = self.overlapMatrices[str(self.moduleID)]["5"]
        # not used since it's so small
        self.mICP1t5 = self.overlapMatrices[str(self.moduleID)]["6"]

    def combine1to2(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m1star @ inv(inv(self.mICP2t7) @ self.mICP1t7)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m2))

        return mBstarInSensorB

    def combine1to3(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m1star @ inv(inv(self.mICP3t7) @ self.mICP1t7)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m3))

        return mBstarInSensorB

    def combine0to4(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m0star @ inv(self.mICP0t4)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m4))

        return mBstarInSensorB

    def combine1to5(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m1star @ inv(self.mICP3t5 @ inv(self.mICP3t7) @ self.mICP1t7)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m5))

        return mBstarInSensorB

    def combine1to6(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m1star @ inv(self.mICP3t6 @ inv(self.mICP3t7) @ self.mICP1t7)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m6))

        return mBstarInSensorB

    def combine1to7(self):
        # see Equation 7.23 in my PhD thesis
        mBstar = self.m1star @ inv(self.mICP1t7)

        # now, transform mBstar from PANDA GLOBAL into the system of sensorB
        # (because thats where it was applied by FAIRROOT)
        mBstarInSensorB = baseTransform(mBstar, inv(self.m7))

        return mBstarInSensorB

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None:
            raise Exception(
                "ERROR! Please set overlaps, overlap matrices and ideal detector matrices first!"
            )

        if self.externalMatrices is None:
            self.externalMatrices = {}
            print("------------------- ATTENTION !!! -------------------")
            print("No external matrices set! Assuming identity matrices!")
            print("Restuls in wrong matrices if detector is mialigned!!!")
            print("------------------- ATTENTION !!! -------------------")
            self.externalMatrices[self.modulePath + "/sensor_0"] = np.eye(4)
            self.externalMatrices[self.modulePath + "/sensor_1"] = np.eye(4)

        self.initCalculator()

        mat2mis = self.combine1to2()
        mat3mis = self.combine1to3()
        mat4mis = self.combine0to4()
        mat5mis = self.combine1to5()
        mat6mis = self.combine1to6()
        mat7mis = self.combine1to7()

        # now, all the overlap misalignments are in PND global!

        # copy the given misalignments, so that all are in the final set!
        self.alignmentMatrices[self.modulePath + "/sensor_0"] = self.externalMatrices[
            self.modulePath + "/sensor_0"
        ]
        self.alignmentMatrices[self.modulePath + "/sensor_1"] = self.externalMatrices[
            self.modulePath + "/sensor_1"
        ]

        # store computed misalignment matrices to internal dict
        self.alignmentMatrices[self.modulePath + "/sensor_2"] = mat2mis
        self.alignmentMatrices[self.modulePath + "/sensor_3"] = mat3mis
        self.alignmentMatrices[self.modulePath + "/sensor_4"] = mat4mis
        self.alignmentMatrices[self.modulePath + "/sensor_5"] = mat5mis
        self.alignmentMatrices[self.modulePath + "/sensor_6"] = mat6mis
        self.alignmentMatrices[self.modulePath + "/sensor_7"] = mat7mis
