#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv

import json

"""
This script reads the artificial misalignment matrices from the simulations to generate
the "externally measured matrices" for sensors 0 and 1 on each module. For the final detector,
these matrices will of course really be measured, but for now, we need to cheat a little.

It will also create a set of non-misaligned external matrices.

This is the script that will also translate the externally measured matrices to a form 
the sensor aligner can read (i.e. all misalignment matrices must be sensor-local and
describe the deviation from the ideal position)
"""

if __name__ == "__main__":
    print('greetings, human.')

    factors = ['0.50', '1.00', '2.00']
    for factor in factors:
        with open(f'input/misMatrices/misMat-sensors-{factor}.json') as f:
            matricesMisalign = json.load(f)
        outputFile = f'input/sensorAligner/externalMatrices-sensors-{factor}.json'
        externalMatrices = {}
        for path in matricesMisalign:
            if path.endswith('sensor_0') or path.endswith('sensor_1'):
                externalMatrices[path] = matricesMisalign[path]
        with open(outputFile, 'w') as fp:
            fp.write(json.dumps(externalMatrices, indent=2))

    with open(f'input/misMatrices/misMat-identity-1.00.json') as f:
        matricesMisalign = json.load(f)
    outputFile = f'input/sensorAligner/externalMatrices-sensors-aligned.json'
    externalMatrices = {}
    for path in matricesMisalign:
        if path.endswith('sensor_0') or path.endswith('sensor_1'):
            externalMatrices[path] = matricesMisalign[path]
    with open(outputFile, 'w') as fp:
        fp.write(json.dumps(externalMatrices, indent=2))


    print('all saved!')