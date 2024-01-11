#!/usr/bin/env python3
"""
This script reads misalignment matrices for sensor misalignment, module misalignment and box100 matrices
and multiplies them to get a combi matrix. This is more precisely handable.
"""

from pathlib import Path

import json
import subprocess
import sys


def combine(path, factor):

    result = {}

    fileName1 = f'{path}/misMat-sensors-{factor}.json'
    fileName2 = f'{path}/misMat-modules-{factor}.json'
    fileName3 = f'{path}/misMat-box100-{factor}.json'

    with open(fileName1, 'r') as f:
        mat1 = json.load(f)
    with open(fileName2, 'r') as f:
        mat2 = json.load(f)
    with open(fileName3, 'r') as f:
        mat3 = json.load(f)

    result = {**mat1, **mat2, **mat3}
    return result


def runFactors(path, fileName, seedID=None):
    # for all factors
    for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:
        # combine three matrices to one
        result = combine(path, fac)
        targetFile = f'{fileName}-{fac}.json'
        with open(targetFile, 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

        # calculate avg misalign
        command = ('python3', 'helperScripts/genAvgMisalign.py', f'{path}/misMat-modules-{fac}-q.json', f'input/moduleAlignment/multi/avgMisalign-seed{seedID}-{fac}.json')
        subprocess.run(command, cwd='.')

        # calculate extermal matrices
        command = ('python3', 'helperScripts/genExternalMatrices.py', f'{path}/misMat-sensors-{fac}.json', f'input/sensorAligner/multi/externalMatrices-sensors-seed{seedID}-{fac}.json')
        subprocess.run(command, cwd='.')


def fail():
    print(f'cannot parse arguments!')


if __name__ == "__main__":

    # auto mode
    if len(sys.argv) == 1:
        path = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/'
        fileName = f'{path}/misMat-combi'
        runFactors(path, fileName)

    elif len(sys.argv) == 3:
        if sys.argv[1] == '--multiPath':
            pathPrefix = sys.argv[2]

            # for all seeds
            for seedID in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:

                path = Path(f'{pathPrefix}/multi/{seedID}/')
                fileName = f'{path}/../misMat-combiSeed{seedID}'
                runFactors(path, fileName, seedID)

        else:
            fail()

    else:
        fail()