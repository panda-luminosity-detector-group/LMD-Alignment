#!/usr/bin/env python3

"""
Interface class that handles:
- loading and saving of matrices to and from json
- change of basis
- (de) homogenization
- get euelr angles from rotation matrix
- get rotation matrix from two points 
"""

import json
import numpy as np

from pathlib import Path
from numpy.linalg import inv


def loadMatrices(fileName, reshape=True):

    if not Path(fileName).exists():
        print(f'ERROR! File not found: {fileName}!')
        return

    with open(fileName, 'r') as f:
        temp = json.load(f)

    if reshape:
        for p in temp:
            temp[p] = np.array(temp[p]).reshape(4, 4)
    return temp


def saveMatrices(matrices, fileName):

    # create path if needed
    if not Path(fileName).parent.exists():
        Path(fileName).parent.mkdir()

    # warn if overwriting
    if Path(fileName).exists():
        print(f'WARNING. Replacing file: {fileName}!\n')
        Path(fileName).unlink()

    # flatten matrices, make a copy (pass-by-reference!)
    saveMatrices = {}
    for p in matrices:
        saveMatrices[p] = np.ndarray.tolist(np.ndarray.flatten(matrices[p]))

    with open(fileName, 'w') as f:
        json.dump(saveMatrices, f, indent=2)


def baseTransform(mat, matFromAtoB):
    """
    Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
    If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
    this function inv(matTo0). I know it's confusing, but that's the way this works.

    Example 1: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
    Example 2: matrixInSensor = baseTransform(matrixInPanda, inv(matrixPandaToSensor))
    """
    return matFromAtoB @ mat @ inv(matFromAtoB)

# from https://www.learnopencv.com/rotation-matrix-to-euler-angles/
# Calculates rotation matrix to euler angles


def rotationMatrixToEulerAngles(R):

    assert(R.shape() == (4, 4) or R.shape() == (3, 3))
    
    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])
