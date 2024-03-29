#!/usr/bin/env python3

from alignment.sensors import icp
from pathlib import Path

import json
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Finds the overlap matrix for two sensors. Requires an overlapID and the set of ideal detector matrices.
"""


class sensorMatrixFinder:
    def __init__(self, overlapID):
        self.overlap = overlapID
        self.use2D = True
        self.PairData = None
        self.idealOverlapInfos = {}
        self.overlapMatrix = None
        self.idealDetectorMatrices = {}
        self.maxPairs = 6e5
        self.dCut = 1.0

    def readNumpyFiles(self, path):

        fileName = path / Path(f"pairs-{self.overlap}.npy")
        # read binary pairs
        try:
            self.PairData = np.load(fileName)
        except:
            raise Exception(f"ERROR! Can not read {fileName}!")

        # reduce to maxPairs
        if self.PairData.shape > (7, int(self.maxPairs)):
            self.PairData = self.PairData[..., : int(self.maxPairs)]

        # the new python Root Reader stores them slightly different...
        self.PairData = np.transpose(self.PairData)

        # apply dynamic cut
        self.PairData = self.dynamicCut(self.PairData, self.dCut)

    def dynamicCut(self, hitPairs, cutPercent=2):

        if cutPercent == 0:
            return hitPairs

        # calculate center of mass of differences
        dRaw = hitPairs[:, 3:6] - hitPairs[:, :3]
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = hitPairs[:, 3:6] - com

        # calculate new distance for cut
        dRaw = newhit2 - hitPairs[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        # sort by distance and cut some percent from start and end (discard outliers)
        cut = int(len(hitPairs) * cutPercent / 100.0)
        # sort by new distance
        hitPairs = hitPairs[newDist.argsort()]
        # cut off largest distances, NOT lowest
        hitPairs = hitPairs[:-cut]

        return hitPairs

    def findMatrix(self):

        if self.idealOverlapInfos is None or self.PairData is None:
            raise Exception(
                f"Error! Please load ideal detector matrices and numpy pairs!"
            )

        if len(self.idealDetectorMatrices) < 1:
            raise Exception("ERROR! Please set ideal detector matrices!")

        # Make C a homogeneous representation of hits1 and hits2
        hit1H = np.ones((len(self.PairData), 4))
        hit1H[:, 0:3] = self.PairData[:, :3]

        hit2H = np.ones((len(self.PairData), 4))
        hit2H[:, 0:3] = self.PairData[:, 3:6]

        # Attention! Always transform to module-local system,
        # otherwise numerical errors will make the ICP matrices unusable!
        # (because z is at 11m, while x is 30cm and y is 0)
        # also, we're ignoring z distance, which we can not do if we're in
        # PND global, due to the 40mrad rotation.
        transformToLocalSensor = True
        if transformToLocalSensor:
            icpDimension = 2
            # get matrix lmd to module
            modulePath = self.idealOverlapInfos[str(self.overlap)]["pathModule"]
            matToModule = self.idealDetectorMatrices[modulePath]

            # invert to transform pairs from lmd to sensor
            toModInv = np.linalg.inv(matToModule)

            # Transform vectors (remember, C and D are vectors of vectors = matrices!)
            hit1T = np.matmul(toModInv, hit1H.T).T
            hit2T = np.matmul(toModInv, hit2H.T).T

        else:
            print("WARNING! ICP working in Panda global, NOT sensor local.")
            print("This will likely produce wrong overlap matrices!")
            hit1T = hit1H
            hit2T = hit2H

        if self.use2D:
            icpDimension = 2
            # make 2D versions for ICP
            A = hit1T[:, :2]
            B = hit2T[:, :2]
        else:
            icpDimension = 3
            # make 3D versions for ICP
            A = hit1T[:, :3]
            B = hit2T[:, :3]

        # find ideal transformation
        T, _, _ = icp.best_fit_transform(A, B)

        # copy 3x3 Matrix to 4x4 Matrix
        if icpDimension == 2:
            M = np.identity(4)
            M[:2, :2] = T[:2, :2]
            M[:2, 3] = T[:2, 2]
            self.overlapMatrix = M

        elif icpDimension == 3:
            self.overlapMatrix = T

        transformResultToPND = True
        if transformResultToPND:
            # remember, matToModule goes from Pnd->Module
            # base trafo is T A T^-1,
            # T = Pnd->Module
            self.overlapMatrix = (
                (matToModule) @ self.overlapMatrix @ np.linalg.inv(matToModule)
            )

    def getOverlapMatrix(self):
        if self.overlapMatrix is None:
            print(f"Error! Please compute matrix first!")
        return self.overlapMatrix
