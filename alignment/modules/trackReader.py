#!usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
import uproot
import sys

"""

Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This file handles reading of lmd_tracks and lmd reco_files, and extracts tracks with their corresponding reco hist.

It then gives those values to millepede, obtains the alignment parameters back and writes them to alignment matrices.
"""

class trackReader():
    def __init__(self):
        pass

    """
    sector goes from 0 to 9
    """
    def readTracks(self, path, sector=0):

        """
        Reco file is incredibly easy, there are PixelHits who have fX, fY and fZ values already in PndGlobal, and a sensor ID.
        Sorting by sector is trivial this way.
        They are however still clusters, that means they have to be merged.
        """


        trackFile = uproot.open(path / Path('Lumi_Track_100000.root'))
        #recoFile = uproot.open(path / Path('Lumi_recoMerged_100000.root'))
        
        trackBranch = trackFile[b'pndsim/LMDPndTrack']
        #trackCandSubBranch = trackBranch[b'LMDPndTrack.fTrackCand.fHitId']

        #print(f"Tracks keys: {trackCandSubBranch.interpretation}")

        #flatCand = trackCand.flatten()
        print(f'--------------------------')

        subBranchInBranch = trackBranch["LMDPndTrack.fTrackCand.fHitId"]
        subBranchInBranch2 = trackBranch["LMDPndTrack.fTrackCand.fTimeStamp"]
        subBranchInBranch3 = trackBranch["LMDPndTrack.fTrackParamLast.fiver"]

        print(f'This is the second level:\n{ trackFile[b"pndsim"].show() }')

        #for i in subBranchInBranch.iterkeys():
        #    print(f'Hi! {i}')


        #print(f'Flat test: {(trackCandSubBranch.array("fIndex"))}')

        # print(f"Reco keys: {recoFile[b'pndsim/LMDHitsMerged'].keys()}")

        # * ignore the rest for now 

        sys.exit(0)

        # uproot.iterate will produce a dict with JaggedArrays, so we can create an empty dict and append each iteration
        resultDict = defaultdict(list)

        try:
            # open the root trees in a TChain-like manner
            print('reading files...')
            for array in uproot.iterate(path, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):

                for key in array:
                    resultDict[key] = np.append(resultDict[key], array[key], axis=0)

        except Exception as e:
            print('error occured:')
            print(e)
            sys.exit(0)