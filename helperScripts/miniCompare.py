#!/usr/bin/env python3

"""
Minimal comparison script for results of sensor aligner vs simulation matrices
"""

import json
import numpy as np

# load mis matrices
with open('input/misMatrices/misMat-sensors-1.00.json') as f:
    misMatrices = json.load(f)

# load sensorAligner result

with open('output/sensorAligner-result-1.00.json') as f:
    alMatrices = json.load(f)

# compare

for p in misMatrices:
    mis = np.array(misMatrices[p])
    al = np.array(alMatrices[p])
    diff = (mis-al)*1e4
    print(f'-------------\nx:{diff[3]}\ny:{diff[7]}')