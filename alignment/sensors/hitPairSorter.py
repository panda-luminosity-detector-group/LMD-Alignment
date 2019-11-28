#!/usr/bin/env python3

from pathlib import Path

from random import SystemRandom
import uproot
import numpy as np
import concurrent.futures

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Sorts HitPairs from Lumi_Pairs_*.root to numpy arrays
"""


class hitPairSorter:

    def __init__(self, PairDir, numpyDir):
        self.inputDir = PairDir
        self.shmDir = Path('/dev/shm')
        self.targetDir = numpyDir
        self.targetDir.mkdir(parents=True, exist_ok=True)
        self.availableOverlapIDs = {}
        self.overlapsDone = {}
        self.maxPairs = 6e5
        self.sortInMemory = True
        cryptogen = SystemRandom()
        self.seed = cryptogen.randrange(1000000000)

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

        # mark all as not done
        for ID in self.availableOverlapIDs:
            self.overlapsDone[ID] = False

        # sorting and saving
        for ID in self.availableOverlapIDs:

            # if marked done, skip
            if self.overlapsDone[ID]:
                continue

            # read array from disk
            fileName = self.npyOutputDir / Path(f'pairs-{ID}.npy')
            try:
                oldContent = np.load(fileName)
            # first run, file not already present
            except:
                oldContent = np.empty((7, 0))

            # create mask by ID
            IDmask = (flatOverlaps == float(ID))
            thisContent = np.array([flathit1[IDmask].x, flathit1[IDmask].y, flathit1[IDmask].z, flathit2[IDmask].x, flathit2[IDmask].y, flathit2[IDmask].z, flatDistance[IDmask]])

            # merge
            newContent = np.concatenate((oldContent, thisContent), axis=1)

            # mark as done as soon as there are enough pairs
            if newContent.shape > (7, int(self.maxPairs)):
                newContent = newContent[..., :int(self.maxPairs)]
                self.overlapsDone[ID] = True

            # write back to disk
            np.save(file=fileName, arr=newContent, allow_pickle=False)

        # are all arrays done?
        allDone = True
        for ID in self.availableOverlapIDs:
            if not self.overlapsDone[ID]:
                allDone = False
        return allDone

    def sortAll(self):

        if self.sortInMemory:
            self.npyOutputDir = self.shmDir / Path(f'pairSorter/{self.seed}')
            self.npyOutputDir.mkdir(exist_ok=True, parents=True)
            print(f'sorting in memory, using {str(self.npyOutputDir)}...')
            
        else:
            print('sorting on disk...')
            self.npyOutputDir = self.targetDir

        # create dict for all fileContents, this is rather non-pythonic
        fileContents = {}
        executor = concurrent.futures.ThreadPoolExecutor(2)   # 8 threads

        if len(self.availableOverlapIDs) < 1:
            print(f'ERROR! No available overlap IDs. Did you set them?')
            return

        for ID in self.availableOverlapIDs:
            fileContents[ID] = np.empty((7, 0))

        # check if all files are already there
        allThere = True
        for ID in self.availableOverlapIDs:
            fileName = self.npyOutputDir / Path(f'pairs-{ID}.npy')
            if not Path(fileName).exists():
                allThere = False
                break

        if allThere:
            print(f'All npy files already present in {self.npyOutputDir}, skipping sorter!')
            return

        print('Sorting HitPairs .', end='', flush=True)

        # open the root trees in a TChain-like manner
        lumiPairs = str(self.inputDir / Path('Lumi_Pairs*.root'))
        try:
            for (_, _, arrays) in uproot.iterate(lumiPairs, 'pndsim', [b'PndLmdHitPair._overlapID', b'PndLmdHitPair._hit1', b'PndLmdHitPair._hit2'], entrysteps=float("inf"), executor=executor, reportentries=True):
                # progress bar
                print('.', end='', flush=True)
                allDone = self.sortPairs(arrays, fileContents)

                # every n iterations:
                # load from disk what is already there
                # concat with in memory copy
                # dump to disk again
                # empty memory copy 
                # mark ID as done if maxPairs is reached (this is important, otherwise the file will be load and read again an again!)

                if allDone:
                    print(f'All arrays reached {self.maxPairs} pairs, quitting!')
                    return

        # Keyboard interrupt
        except (KeyboardInterrupt) as e:
            print('caught exception:\n{}\nsaving files...'.format(e))

        except Exception as e:
            print(f'\n\nERROR!\n{e}\n')
            return

        # copy from memory to disk
        if self.sortInMemory:
            srcPath = self.shmDir / Path(f'pairSorter/{self.seed}')
            dstPath = self.targetDir
            for file in srcPath.glob('*.npy'):
                file.copy(dstPath)
                file.unlink()
            srcPath.rmdir()

        print(f'. done!')

        print('\nAll sorting done')
