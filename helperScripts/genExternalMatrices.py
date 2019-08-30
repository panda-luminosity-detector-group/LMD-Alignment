#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv

import json

"""
This script reads ideal detector matrices and the artificial misalignment matrices from the simulations to generate
the "externally measured matrices" for sensors 0 and 1 on each module. For the final detector,
these matrices will of course really be measured, but for now, we need to cheat a little.
"""

def getMatrixP1ToP2fromMatrixDict(path1, path2, mat):
        # matrix from pnd global to sen1
        m1 = np.array(mat[path1]).reshape(4, 4)
        # matrix from pnd global to sen2
        m2 = np.array(mat[path2]).reshape(4, 4)
        # matrix from sen1 to sen2
        return inv(m1)@m2

if __name__ == "__main__":
    print('greetings, human.')

    # load geometry specifications
    with open('input/detectorOverlapsIdeal.json') as f:
        overlapInfos = json.load(f)

    with open('input/detectorMatricesIdeal.json') as f:
        matricesIdeal = json.load(f)

    with open('input/misMatrices/misMat-sensors-1.00.json') as f:
        matricesMisalign = json.load(f)

    outputFile = 'input/externalMatrices-sensors-1.00.json'

    externalMatrices = {}

    for overlapID in overlapInfos:
        pathModule = overlapInfos[overlapID]['pathModule']
        
        misMat0 = matricesMisalign[pathModule + '/sensor_0']
        misMat1 = matricesMisalign[pathModule + '/sensor_1']

        externalMatrices[pathModule] = {}
        externalMatrices[pathModule]['mis0'] = misMat0
        externalMatrices[pathModule]['mis1'] = misMat1

    with open(outputFile, 'w') as fp:
        fp.write(json.dumps(externalMatrices, indent=2))

    print('all saved!')