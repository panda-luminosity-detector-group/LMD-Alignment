#!/usr/bin/env python3

"""
This is an handler class for matrix related things.
"""

import json
import numpy as np

# TODO: clean up this module, what is it supposed to do?


def getMatrixFromJSON(jsonFile, path):

    with open(jsonFile, 'r') as f:
        jsonData = json.load(f)
        data = jsonData[path]
        matrix = np.array(data)
        matrix = np.reshape(matrix, (4, 4))
        return matrix


# TODO: express homogenization and de-homogenization with 4x4 matrices! it's pretty easy!


def makeHomogenous(matrix):
    shape = np.shape(matrix)
    if np.shape(matrix) == (3,):
        matrix = matrix[np.newaxis]
    shape = np.shape(matrix)
    if shape == (3, 3):
        result = np.identity(4)
        result[:3, :3] = matrix
        return result
    elif shape == (1, 3):
        result = np.ones((1, 4))
        result[0, :3] = matrix[0, :]
        return result
    elif shape == (3, 1):
        result = np.ones((4, 1))
        result[:3, 0] = matrix[:, 0]
        return result
    elif shape == (4, 4):
        # dehomogenize, sue me
        result = np.identity(3)
        result = matrix[:3, :3]
        return result
    else:
        print('ERROR! can only cast 3x3 matrices or 3x1 vectors to homogenous form')
        print('(or de-homogenize the other way round)')


# https://stackoverflow.com/questions/15022630/how-to-calculate-the-angle-from-rotation-matrix

def getEulerAnglesFromRotationMatrix(R):
    if R.shape != (3, 3):
        print(f'can not determine matrix shape correctly')
        return
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


if __name__ == "__main__":
    print('this module is not intended to be run independently.')
