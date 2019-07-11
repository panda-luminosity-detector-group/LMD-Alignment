#!/usr/bin/env python3

import numpy as np
import uproot, os, sys
from trksQA import getIPfromTrksQA
from matrices import getMatrixFromJSON, makeHomogenous

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

read TrksQA.root files
find apparent IP position
compare with actual IP position from PANDA upstream

save matrix to json file
rerun Reco and Lumi steps
"""

def getLumiPosition():
    lumiPos = np.array([0.0, 0.0, 0.0, 1.0])[np.newaxis].T
    lumiMat = getMatrixFromJSON('../input/rootMisalignMatrices/json/detectorMatrices.json', '/cave_1/lmd_root_0')
    newLumiPos = (lumiMat@lumiPos).T[0][:3]
    return newLumiPos


def getEulerAnglesFromRotationMatrix(R):
    rx = np.arctan2(R[2][1], R[2][2])
    ry = np.arctan2(-R[2][0], np.sqrt(R[2][1]*R[2][1] + R[2][2] * R[2][2]))
    rz = np.arctan2(R[1][0], R[0][0])
    return (rx, ry, rz)


def printMatrixDetails(M1, M2=None):

    if M2 is not None:
        rx1, ry1, rz1 = getEulerAnglesFromRotationMatrix(M1)
        rx2, ry2, rz2 = getEulerAnglesFromRotationMatrix(M2)
        rx = rx1 - rx2
        ry = ry1 - ry2
        rz = rz1 - rz2
        M = M1 - M2
        print(f'M Difference:\n{M}')
    else:
        rx, ry, rz = getEulerAnglesFromRotationMatrix(M1)
        M = M1
        print(f'M:\n{M}')

    print(f'angle x: {rx * 1e3} mrad')
    print(f'angle y: {ry * 1e3} mrad')
    print(f'angle z: {rz * 1e3} mrad')
    print('\n')


# see https://math.stackexchange.com/a/476311
# https://en.wikipedia.org/wiki/Cross_product#Conversion_to_matrix_multiplication
"""
computes rotation from A to B when rotated through origin.
shift A and B before, if rotation did not already occur through origin!
"""
def getRot(A, B):
    # error handling
    if np.linalg.norm(A) == 0 or np.linalg.norm(B) == 0:
        print("ERROR. can't create rotation with null vector")
        return

    # assert shapes
    assert A.shape == B.shape

    # normalize vectors
    A = A / np.linalg.norm(A)
    B = B / np.linalg.norm(B)

    # calc rot angle by dot product
    cosine = np.dot(A, B)  # cosine

    # make 2D vectors so that transposing works
    cw = A[np.newaxis].T
    dw = B[np.newaxis].T

    # compute skew symmetric cross product matrix
    a_x = np.matmul(dw, cw.T) - np.matmul(cw, dw.T)

    # compute rotation matrix
    R = np.identity(3) + a_x + np.dot(a_x, a_x) * (1/(1+cosine))

    return R


def testTwo():

    # TODO: read from config or PANDA db/survey
    lumiPos = getLumiPosition()
    print(f'Lumi Position is:\n{lumiPos}')

    #ipApparent = np.array([1.0, 0.0, 0.0])
    ipApparent = getIPfromTrksQA('../input/TrksQA/box-1.00/Lumi_TrksQA_100000.root')
    # TODO: read from config or PANDA db/survey
    ipActual = np.array([0.0, 0.0, 0.0])

    print(f'IP apparent:\n{ipApparent}')

    ipApparent -= lumiPos
    ipActual -= lumiPos

    #! ======== test classical variant
    R1 = getRot(ipApparent, ipActual)
    R1 = makeHomogenous(R1)

    print('matrix is:')
    printMatrixDetails(R1)

    # read json file here and compare
    mat = getMatrixFromJSON('../input/rootMisalignMatrices/json/misMat-box-1.00.root.json', '/cave_1/lmd_root_0')
    print('matrix should be:')
    printMatrixDetails(mat)

    printMatrixDetails(R1, mat)


if __name__ == "__main__":
    print('greetings, human.')
    testTwo()
    print('all done!')
