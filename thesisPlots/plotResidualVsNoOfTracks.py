#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerModules import alignerModules
from detail.matrixComparator import moduleComparator
import matplotlib.pyplot as plt

from pathlib import Path
import sys, subprocess, json
import numpy as np

np.set_printoptions(precision=3, suppress=True)

def dummy():
    # from good-ish tracks

    matrixFile = f'output/residualVsTrks/alMat-modules-1.00.json'

    trackFile = Path('output/residualVsTrks/factor-1.00-large.json')

    alignerMod = alignerModules()
    alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
    alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
    alignerMod.readTracks(trackFile)
    alignerMod.alignModules()
    alignerMod.saveMatrices(matrixFile)

    #! run comparator
    comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
    comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
    comp.loadAlignerMatrices(matrixFile)
    comp.saveHistogram('output/residualVsTrks/residuals-modules-2020-02-09-withAnchors.pdf')

if __name__ == "__main__":
    dummy()