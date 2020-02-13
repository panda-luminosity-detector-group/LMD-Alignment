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

    noOftracks = np.arange(5000,500001, 5000)

    resultDict = {}

    trackNPYFile = Path('output/residualVsTrks/tracks.npy')
    alignerMod = alignerModules()
    trackFile = Path('output/residualVsTrks/factor-1.00-huge.json')
    # alignerMod.readTracks(trackNPYFile, isNumpy=True)
    alignerMod.readTracks(trackFile, isNumpy=False)
    
    for nTracks in noOftracks:

        matrixFile = f'output/residualVsTrks/alMat-modules-1.00.json'


        alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
        alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
        alignerMod.alignModules(maxNoOfTracks=nTracks)
        alignerMod.saveMatrices(matrixFile)

        #! run comparator
        comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
        comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
        comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
        comp.loadAlignerMatrices(matrixFile)
        result = comp.saveHistogram(f'output/residualVsTrks/{nTracks}-residuals-modules.pdf')
        result = np.ndarray.tolist(result.flatten())

        with open(f'output/residualVsTrks/{nTracks}-VsResiduals.json', 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

        resultDict[str(nTracks)] = result

    print(resultDict)

    with open(f'output/residualVsTrks/nTrksVsResiduals.json', 'w') as f:
        json.dump(resultDict, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    dummy()