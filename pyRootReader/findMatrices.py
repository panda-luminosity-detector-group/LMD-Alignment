#!/usr/bin/env python3
from functions import icp
import json
import uproot
import numpy as np

with open("matricesIdeal.json", 'r') as f:
    matrices = json.load(f)


def findOne(ID, pairArray):
    #fileName = './numpyPairs/pairs-{}.npy'.format(ID)
    # read binary pairs
    #fileUsable = np.load(fileName)

    # the new python Root Reader stores them slightly differently... although, maybe just change that?
    #fileUsable = np.transpose(fileUsable)

    # print(fileUsable)

    # apply dynamic cut
    fileUsable = dynamicCut(pairArray, 2)

    # get lmd to sensor1 matrix1
    toSen1 = np.array(matrices[str(ID)]['matrix1']).reshape(4, 4)

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


if __name__ == "__main__":
    print('cannot run stand-alone!')
