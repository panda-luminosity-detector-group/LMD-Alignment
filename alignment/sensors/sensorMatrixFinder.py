#!/usr/bin/env python3

from alignment.sensors import icp
from pathlib import Path

import json
import numpy as np

"""

Finds the overlap matrix for two sensors. Requires an overlapID and the set of ideal detector matrices.

"""


class sesorMatrixFinder:

    def __init__(self, overlapID):
        self.overlap = overlapID
        self.use2D = True
        self.PairData = None
        self.idealMatrices = None
        self.overlapMatrix = None

    def readIdealMatrices(self, fileName):
        with open(fileName, 'r') as f:
            self.idealMatrices = json.load(f)

    def readNumpyFiles(self, path):

        fileName = path / Path(f'pairs-{self.overlap}.npy')
        # read binary pairs
        try:
            self.PairData = np.load(fileName)
        except:
            print(f'ERROR! Can not read {fileName}!')

        # the new python Root Reader stores them slightly differently...
        self.PairData = np.transpose(self.PairData)

        # apply dynamic cut
        self.PairData = self.dynamicCut(self.PairData, 2)

    def dynamicCut(self, fileUsable, cutPercent=2):

        if cutPercent == 0:
            return fileUsable

        # calculate center of mass of differces
        dRaw = fileUsable[:, 3:6] - fileUsable[:, :3]
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = fileUsable[:, 3:6] - com

        # calculate new distance for cut
        dRaw = newhit2 - fileUsable[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        if cutPercent > 0:
            # sort by distance and cut some percent from start and end (discard outliers)
            cut = int(len(fileUsable) * cutPercent/100.0)
            # sort by new distance
            fileUsable = fileUsable[newDist.argsort()]
            # cut off largest distances, NOT lowest
            fileUsable = fileUsable[:-cut]

        return fileUsable

    def findMatrix(self):

        if self.idealMatrices is None or self.PairData is None:
            print(f'Error! Please load ideal detector matrices and numpy pairs!')
            return

        # get lmd to sensor1 matrix1
        toSen1 = np.array(self.idealMatrices[str(self.overlap)]['matrix1']).reshape(4, 4)

        # invert to transform pairs from lmd to sensor
        toSen1Inv = np.linalg.inv(toSen1)

        # Make C a homogeneous representation of hits1 and hits2
        hit1H = np.ones((len(self.PairData), 4))
        hit1H[:, 0:3] = self.PairData[:, :3]

        hit2H = np.ones((len(self.PairData), 4))
        hit2H[:, 0:3] = self.PairData[:, 3:6]

        # Transform vectors (remember, C and D are vectors of vectors = matrices!)
        hit1T = np.matmul(toSen1Inv, hit1H.T).T
        hit2T = np.matmul(toSen1Inv, hit2H.T).T

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
        T, _, _ = icp.best_fit_transform(B, A)

        # copy 3x3 Matrix to 4x4 Matrix
        if icpDimension == 2:
            M = np.identity(4)
            M[:2, :2] = T[:2, :2]
            M[:2, 3] = T[:2, 2]
            self.overlapMatrix = M

        elif icpDimension == 3:
            self.overlapMatrix = T

    def makeOverlapMatrixToMisalignmentMatrix(self):
        if self.overlapMatrix is None:
            print(f'Error! Please compute matrix first!')
        return self.overlapMatrix

        # FIXME: the misalignment matrices are offset matrices that are applied to a sensor position
        # but we only have overlap matrices here, so we need to compute them first!
