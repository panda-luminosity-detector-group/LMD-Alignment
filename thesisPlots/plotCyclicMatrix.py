#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerModules import alignerModules
from detail.matrixComparator import cycleComparator
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from pathlib import Path
import sys, subprocess, json, re
import numpy as np

np.set_printoptions(precision=3, suppress=True)

if __name__ == "__main__":

    #! run comparator
    comp = cycleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/sensors/15.0/factor-1.00.json'))
    comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comp.loadSensorAlignerOverlapMatrices('/media/DataEnc2TBRaid1/Arbeit/LMDscripts/output/temp/alMats/sensors-15.0-1.00/alMat-sensorOverlaps-1.00.json')
    comp.loadPerfectDetectorOverlaps('input/detectorOverlapsIdeal.json')
    comp.setSize((12/2.54,8/2.54))
    comp.getValues()
    comp.saveHistogram(f'sensor-C2.pdf')
