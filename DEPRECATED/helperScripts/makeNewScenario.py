#!/usr/bin/env python3

from pathlib import Path
from scipy.spatial.transform import Rotation as R

import numpy as np

import json
import random
import sys
"""
This script creates an entire combined misalignment simulation scenario, or multiple even. 
For different scenarios with the same misalign factor, a sample number will be chosen.

Things that need to be done:
- create Sensor Misalign
- create Module Misalign
- create IP misalign

- calc sensor external matrices
- calc module avg matrices
- calc anchor points (?, nah, those should be fix)

- create runConfig with these matrices
- don't actually run, this is done manually

TODOs:
- multiple momenta
- 
"""

#! these are the remaining uncertainties after initial measurements (factor 1.0)
BOX_X_SIGMA = 0.1
BOX_Y_SIGMA = 0.1
BOX_Z_SIGMA = 0.1

BOX_RX_SIGMA = 0.001
BOX_RY_SIGMA = 0.001
BOX_RZ_SIGMA = 0.001

MODULE_X_SIGMA = 0.01
MODULE_Y_SIGMA = 0.01
MODULE_Z_SIGMA = 0.00

MODULE_RX_SIGMA = 0.0
MODULE_RY_SIGMA = 0.0
MODULE_RZ_SIGMA = 0.014

SENSORS_X_SIGMA = 0.01
SENSORS_Y_SIGMA = 0.01
SENSORS_Z_SIGMA = 0.0

SENSORS_RX_SIGMA = 0.0
SENSORS_RY_SIGMA = 0.0
SENSORS_RZ_SIGMA = 0.0025

factors = [
    '0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50',
    '3.00'
]


def homogenize(matrix):
    result = np.identity(4)
    matrix = np.array(matrix)

    if matrix.shape == (3, ):
        result[:3, 3] = matrix
    elif matrix.shape == (3, 3):
        result[:3, :3] = matrix
    else:
        raise Exception(f'Cannot homogenize matrix of shape {matrix.shape}')
    return result


if __name__ == "__main__":
    print('greetings, human.')

    np.set_printoptions(precision=6)
    np.set_printoptions(suppress=True)
    random.seed(128)

    r = R.from_euler('xyz', (45, 45, 45), degrees=False)
    r = homogenize(r.as_matrix())
    print(r)
    t = homogenize((1, 2, 3))
    print(t)
    print(f'multiplication test:\n{t@r}')

    print(f'testing random:')
    sigma = 1.0
    for _ in range(10):
        print(f'{random.gauss(0, sigma)}')