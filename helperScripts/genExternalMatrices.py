#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv

from pathlib import Path

import json
import sys
"""
This script reads the artificial misalignment matrices from the simulations to generate
the "externally measured matrices" for sensors 0 and 1 on each module. For the final detector,
these matrices will of course really be measured, but for now, we need to cheat a little.

It will also create a set of non-misaligned external matrices.

This is the script that will also translate the externally measured matrices to a form 
the sensor aligner can read (i.e. all misalignment matrices must be sensor-local and
describe the deviation from the ideal position)
"""


def autoGen():

    # misaligned part
    factors = ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']
    for factor in factors:
        inFile = f'../Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-sensors-{factor}.json'
        outFile = f'input/sensorAligner/externalMatrices-sensors-{factor}.json'
        filterOneFile(inFile, outFile)

    # aligned part
    inFile = f'../Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-identity-1.00.json'
    outFile = f'input/sensorAligner/externalMatrices-sensors-aligned.json'
    filterOneFile(inFile, outFile)


def filterOneFile(inFile, outFile):

    inFile = Path(inFile)
    outFile = Path(outFile)

    if not inFile.exists():
        raise Exception(f'File {inFile} can not be read!')

    with open(inFile) as f:
        matricesMisalign = json.load(f)

    externalMatrices = {}

    for path in matricesMisalign:
        if path.endswith('sensor_0') or path.endswith('sensor_1'):
            externalMatrices[path] = matricesMisalign[path]

    outFile.parent.mkdir(exist_ok=True, parents=True)

    with open(outFile, 'w') as fp:
        fp.write(json.dumps(externalMatrices, indent=2))


if __name__ == "__main__":
    print('greetings, human.')

    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} inFile outFile\nor:')
        print(f'usage: {sys.argv[0]} --aligned outfile\nor:')
        print(f'usage: {sys.argv[0]} --auto targetDir')
        sys.exit(1)

    outFile = Path(sys.argv[2])
    print(f'Calculating average misalignments...')

    # auto mode, some hardcoded paths here!
    if len(sys.argv) == 1:
        autoGen()
        print('all saved!')

    else:
        inFile = sys.argv[1]
        outFile = sys.argv[2]
        filterOneFile(inFile, outFile)
