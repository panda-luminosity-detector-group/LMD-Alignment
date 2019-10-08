#!/usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries
import numpy as np
import uproot
import sys

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

TODO: Implement corridor alignment

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- separate by x and y
- give to millepede
- obtain alignment parameters from millepede
- convert to alignment matrices

"""

class alignerModules:
    def __init__(self):
        pass

    """
    sector goes from 0 to 9
    """
    def readTracks(self, filename, sector=0):

        file = uproot.open(filename)
        print(file[b'pndsim/LMDPndTrackFilt'].keys())

        sys.exit(0)

        # uproot.iterate will produce a dict with JaggedArrays, so we can create an empty dict and append each iteration
        resultDict = defaultdict(list)

        try:
            # open the root trees in a TChain-like manner
            print('reading files...')
            for array in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):

                for key in array:
                    resultDict[key] = np.append(resultDict[key], array[key], axis=0)

        except Exception as e:
            print('error occured:')
            print(e)
            sys.exit(0)
