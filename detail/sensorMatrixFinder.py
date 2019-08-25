#!/usr/bin/env python3

import numpy as np
import functions.rootInterface as ri
from detail import icp

# TODO: OOP this class, it will be important for Sensor Alignment!

def dynamicCut(fileUsable, cutPercent=2, use2D=True):

    if cutPercent == 0:
        return fileUsable

    if not use2D:
        # calculate new distance for cut
        dRaw = fileUsable[:, 3:6] - fileUsable[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        if cutPercent > 0:
            # sort by distance and cut some percent from start and end (discard outliers)
            cut = int(len(fileUsable) * cutPercent/100.0)
            # sort by new distance
            fileUsable = fileUsable[newDist.argsort()]
            # cut off largest distances, NOT lowest
            fileUsable = fileUsable[cut:-cut]

        return fileUsable

    else:
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


# TODO: this next function needs to be updated!
def findMatrix(path, overlap, cut, matrices, use2D=True):

    # TODO: don't hardcode these!
    filename = path + 'binaryPairFiles/pairs-'
    filename += overlap + '-cm.bin'

    # read binary pairs
    fileUsable = ri.readBinaryPairFile(filename)

    # apply dynamic cut
    fileUsable = dynamicCut(fileUsable, cut, use2D)

    # get lmd to sensor1 matrix1
    # TODO: don't hardcode these!
    toSen1 = np.array(matrices[overlap]['matrix1']).reshape(4, 4)

    # invert to transform pairs from lmd to sensor
    toSen1Inv = np.linalg.inv(toSen1)

    # Make C a homogeneous representation of hits1 and hits2
    hit1H = np.ones((len(fileUsable), 4))
    hit1H[:, 0:3] = fileUsable[:, :3]

    hit2H = np.ones((len(fileUsable), 4))
    hit2H[:, 0:3] = fileUsable[:, 3:6]

    # Transform vectors (remember, C and D are vectors of vectors = matrices!)
    hit1T = np.matmul(toSen1Inv, hit1H.T).T
    hit2T = np.matmul(toSen1Inv, hit2H.T).T

    icpDimension = 2

    if icpDimension == 2:
        # make 2D versions for ICP
        A = hit1T[:, :2]
        B = hit2T[:, :2]
    elif icpDimension == 3:
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
        return M

    elif icpDimension == 3:
        return T


#! attention! both vectors must be in the same system of reference (the first sensor's!)
def findMatrix1to2(cloud1, cloud2):

    numPairs = len(cloud1)

    if numPairs != len(cloud2):
        print('vectors are not equally long!')
        return

    # Make C a homogeneous representation of hits1 and hits2
    hit1H = np.ones(numPairs, 4)
    hit1H[:, 0:3] = cloud1[:, :3]

    hit2H = np.ones(numPairs, 4)
    hit2H[:, 0:3] = cloud2[:, :3]

    icpDimension = 2

    if icpDimension == 2:
        # make 2D versions for ICP
        A = hit1H[:, :2]
        B = hit2H[:, :2]
    elif icpDimension == 3:
        # make 3D versions for ICP
        A = hit1H[:, :3]
        B = hit2H[:, :3]

    # find ideal transformation
    T, _, _ = icp.best_fit_transform(B, A)

    # copy 3x3 Matrix to 4x4 Matrix
    if icpDimension == 2:
        M = np.identity(4)
        M[:2, :2] = T[:2, :2]
        M[:2, 3] = T[:2, 2]
        return M

    elif icpDimension == 3:
        return T


if __name__ == "main":
    print('This is the pairFinder.')
