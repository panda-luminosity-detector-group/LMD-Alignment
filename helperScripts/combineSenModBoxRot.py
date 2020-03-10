#!/usr/bin/env python3

"""
This script reads misalignment matrices for sensor misalignment, module misalignment and box100 matrices
and multiplies them to get a combi matrix. This is more precisely handable.
"""

import json
import sys

def combine(factor):

    result = {}

    fileName1 = f'/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-sensors-{factor}.json'
    fileName2 = f'/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-{factor}.json'
    fileName3 = f'/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-box100-{factor}.json'

    with open(fileName1, 'r') as f:
        mat1 = json.load(f)
    with open(fileName2, 'r') as f:
        mat2 = json.load(f)
    with open(fileName3, 'r') as f:
        mat3 = json.load(f)

    result = {**mat1, **mat2, **mat3}
    return result

if __name__ == "__main__":

    for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:
        result = combine(fac)
        fileName = f'/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-combi-{fac}.json'
        # writeMatrix(result, fileName)

        with open(fileName, 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

    pass