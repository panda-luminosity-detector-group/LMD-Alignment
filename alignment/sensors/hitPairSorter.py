#!/usr/bin/env python3

from pathlib import Path

import uproot
import numpy as np
import concurrent.futures

"""
Sorts HitPairs from Lumi_Pairs_*.root to numpy arrays
"""

class hitPairSorter:

    def __init__(self, PairDir, numpyDir):
        self.inputDir = PairDir
        self.npyOutputDir = numpyDir
        self.npyOutputDir.mkdir(parents=True, exist_ok=True)
        self.availableOverlapIDs = {}

    def sortPairs(self, arrays, fileContents):
        # use just the overlaps for indexes, this tells us how many pairs there are in a given event
        overlaps = arrays[b'PndLmdHitPair._overlapID']
        # apply a mask. this is numpy notation to select some entries according to a criterion and works very fast
        mask = (overlaps.counts >= 1)

        # select the hits
        hit1, hit2 = arrays[b'PndLmdHitPair._hit1'], arrays[b'PndLmdHitPair._hit2']

        # make regular numpy arrays
        flatOverlaps = overlaps[mask].flatten()
        flathit1 = hit1[mask].flatten()
        flathit2 = hit2[mask].flatten()
        flatDistance = (flathit1 - flathit2).mag    # calculate distance vectorized

        # sorting and saving
        for ID in self.availableOverlapIDs:
            # create mask by ID
            IDmask = (flatOverlaps == ID)
            thisContent = np.array([flathit1[IDmask].x, flathit1[IDmask].y, flathit1[IDmask].z, flathit2[IDmask].x, flathit2[IDmask].y, flathit2[IDmask].z, flatDistance[IDmask]])

            # skip if we have just about enough pairs
            if len(thisContent) > 3e5:
                continue

            oldContent = fileContents[ID]
            fileContents[ID] = np.concatenate((oldContent, thisContent), axis=1)

    def saveAllFiles(self, fileContents):
        for ID in self.availableOverlapIDs:
            fileName = self.npyOutputDir / Path(f'pairs-{ID}.npy')

            # check if array is empty
            if len(fileContents[ID][0]) < 1:
                print(f'array {ID} empty, skipping...')
                continue

            if Path(fileName).exists():
                print(f'file for {ID} already present, aborting!')

            # actually save
            np.save(file=fileName, arr=fileContents[ID], allow_pickle=False)

    def sortAll(self):
        # create dict for all fileContents, this is rather non-pythonic
        fileContents = {}
        executor = concurrent.futures.ThreadPoolExecutor(8)   # 8 threads
        
        for ID in self.availableOverlapIDs:
            fileContents[ID] = np.empty((7, 0))

        # check if all files are already there
        allThere = True
        for ID in self.availableOverlapIDs:
            fileName = self.npyOutputDir / Path(f'pairs-{ID}.npy')
            if not Path(fileName).exists():
                allThere = False

        if allThere:
            print(f'All npy files already present, skipping sorter!')
            return

        print('Sorting HitPairs .', end='', flush=True)

        # open the root trees in a TChain-like manner
        lumiPairs = str( self.inputDir  / Path('Lumi_Pairs*.root') )
        try:
            for (_, _, arrays) in uproot.iterate(lumiPairs, 'pndsim', [b'PndLmdHitPair._overlapID', b'PndLmdHitPair._hit1', b'PndLmdHitPair._hit2'], entrysteps=1000000, executor=executor, reportentries=True):
                # progress bar
                print('.', end='', flush=True)
                self.sortPairs(arrays, fileContents)

        # Keyboard interrupt
        except (KeyboardInterrupt, Exception) as e:
            print('caught exception:\n{}\nsaving files...'.format(e))

        print(f'. done!')

        self.saveAllFiles(fileContents)
        print('\ndone')
