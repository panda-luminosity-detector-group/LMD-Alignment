#!/usr/bin/env python3

from pathlib import Path

import uproot
import numpy as np
import concurrent.futures


class hitPairSorter:

    def __init__(self, PairDir):
        self.inputDir = PairDir
        self.npyOutputDir = PairDir / Path('npPairs')
        self.npyOutputDir.mkdir(parents=True, exist_ok=True)

    def createAllOverlaps(self):
        overlapIDs = []
        for half in range(2):
            for plane in range(4):
                for module in range(5):
                    for overlap in range(9):
                        overlapIDs.append(half*1000 + plane*100 + module*10 + overlap)
        return overlapIDs

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
        for ID in self.createAllOverlaps():
            # create mask by ID
            IDmask = (flatOverlaps == ID)
            thisContent = np.array([flathit1[IDmask].x, flathit1[IDmask].y, flathit1[IDmask].z, flathit2[IDmask].x, flathit2[IDmask].y, flathit2[IDmask].z, flatDistance[IDmask]])

            # skip if we have just about enough pairs
            if len(thisContent) > 3e5:
                continue

            oldContent = fileContents[ID]
            fileContents[ID] = np.concatenate((oldContent, thisContent), axis=1)

    def saveAllFiles(self, fileContents):
        for ID in self.createAllOverlaps():
            fileName = self.npyOutputDir / Path(f'pairs-{ID}.npy')

            if Path(fileName).exists():
                print(f'file for {ID} already present, aborting!')

            # actually save
            np.save(file=fileName, arr=fileContents[ID], allow_pickle=False)

    def sortAll(self):
        # create dict for all fileContents, this is rather non-pythonic
        fileContents = {}
        executor = concurrent.futures.ThreadPoolExecutor(8)   # 8 threads
        for ID in self.createAllOverlaps():
            fileContents[ID] = np.empty((7, 0))
        print('pair sorter processing files...')
        # open the root trees in a TChain-like manner
        lumiPairs = str( self.inputDir  / Path('Lumi_Pairs*.root') )
        try:
            for (_, _, arrays) in uproot.iterate(lumiPairs, 'pndsim', [b'PndLmdHitPair._overlapID', b'PndLmdHitPair._hit1', b'PndLmdHitPair._hit2'], entrysteps=1000000, executor=executor, reportentries=True):
                print('.', end='', flush=True)
                self.sortPairs(arrays, fileContents)

        # Keyboard interrupt
        except (KeyboardInterrupt, Exception) as e:
            print('caught exception:\n{}\nsaving files...'.format(e))

        self.saveAllFiles(fileContents)
        print('\ndone')
