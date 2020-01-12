#!/usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path

def getTrackEfficiency(inQAname, outfilename):

    # uproot.iterate will produce a dict with JaggedArrays, so we can create an empty dict and append each iteration
    try:
        # open the root trees in a TChain-like manner
        print(f'reading file {str(inQAname)}')
        for array in uproot.iterate(str(inQAname), 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fThetarec']):
            clean, recStatus = np.array(cleanArray(array))
            print(f'clean: {clean}')

    except Exception as e:
        print(f'exception!\n{e}')
        print(f'is kill')
        return

    maskStatGood = ( (recStatus == 0))
    maskStatBAd = ( (recStatus != 0))
    good = clean[maskStatGood]
    bad = clean[maskStatBAd]

    print(f'len: good:{len(good)}, bad:{len(bad)}')
    eff = len(good)*100 / (len(good) + len(bad))

    plt.hist(good, bins=50, range=(0.002, 0.01))
    plt.suptitle(f'ThetaRec (for RecStatus=0)\nTrack Efficiency: {eff:.1f}%')
    #plt.yscale('log')
    # plt.show()
    plt.savefig(outfilename)
    plt.close()

def cleanArray(arrayDict):

    # use just the recStatus for indexes, this tells us how many recs there are per event
    recStatusJagged = arrayDict[b'LMDTrackQ.fTrkRecStatus']
    nonZeroEvents = (recStatusJagged.counts > 0)

    # flatten all arrays for ease of access and apply a mask.
    # this is numpy notation to select some entries according to a criterion and works very fast:
    thetaRec = arrayDict[b'LMDTrackQ.fThetarec'][nonZeroEvents].flatten()
    recStatus = arrayDict[b'LMDTrackQ.fTrkRecStatus'][nonZeroEvents].flatten()

    return thetaRec, recStatus

if __name__ == "__main__":

    paths = Path('/home/remus/temp/rootcompare').glob('*')
    goodfiles = []
    for path in paths:
        files = path.glob('*.root')
        files = [x for x in files if x.is_file()]
        goodfiles.append(files[0])

    i = 0
    for file in goodfiles:
        getTrackEfficiency(str(file), f'{i}.png')
        i += 1