#!/usr/bin/env python3

import uproot, sys, os
import numpy as np
import concurrent.futures

def createAllOverlaps():
    overlapIDs = []
    for half in range(2):
        for plane in range(4):
            for module in range(5):
                for overlap in range(9):
                    overlapIDs.append(half*1000 + plane*100 + module*10 + overlap)
    return overlapIDs

def sortPairs(arrays, fileContents):
    # use just the overlaps for indexes, this tells us how many pairs there are in a given event
    overlaps = arrays[b'PndLmdHitPair._overlapID']
    # apply a mask. this is numpy notation to select some entries according to a criterium and works very fast
    mask = (overlaps.counts >= 1)

    # select the hits
    hit1, hit2 = arrays[b'PndLmdHitPair._hit1'], arrays[b'PndLmdHitPair._hit2']

    # make regular numpy arrays
    flatOverlaps = overlaps[mask].flatten()
    flathit1 = hit1[mask].flatten()
    flathit2 = hit2[mask].flatten()
    flatDistance = (flathit1 - flathit2).mag    # calculate distance vectorized

    # sorting and saving
    for ID in createAllOverlaps():
        # create mask by ID
        IDmask = (flatOverlaps == ID)
        thisContent = np.array([flathit1[IDmask].x, flathit1[IDmask].y, flathit1[IDmask].z, flathit2[IDmask].x, flathit2[IDmask].y, flathit2[IDmask].z, flatDistance[IDmask]])
        
        # skip if we have just about enough pairs
        if len(thisContent) > 3e5:
            continue
        
        oldContent = fileContents[ID]
        fileContents[ID] = np.concatenate((oldContent, thisContent), axis=1)

def saveAllFiles(fileContents):
    for ID in createAllOverlaps():
        #print('saving file {}'.format(ID))
        fileName = './numpyPairs/pairs-{}.npy'.format(ID)

        if os.path.exists(fileName):
            print('file for {} already present, aborting!'.format(ID))
        
        # actually save
        np.save(file=fileName, arr=fileContents[ID], allow_pickle=False)

def sortAll():
    # check for targetDir
    targetDir = './numpyPairs/'
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)
    # else:
    #     print('the target directory exists, to prevent over write errors, this program will now terminate.')
    #     sys.exit()

    # create dict for all fileContents, this is rather non-pythonic
    fileContents = {}
    executor = concurrent.futures.ThreadPoolExecutor(8)   # 8 threads
    for ID in createAllOverlaps():
        fileContents[ID] = np.empty((7,0))
    print('processing files...')
    # open the root trees in a TChain-like manner
    try:
        for (a, b, arrays) in uproot.iterate(
                '/home/arbeit/RedPro3TB/simulationData/himster2misaligned-move-data/Pairs/Lumi_Pairs*.root',
                'pndsim',
                [b'PndLmdHitPair._overlapID', b'PndLmdHitPair._hit1', b'PndLmdHitPair._hit2'],
                entrysteps=1000000, executor=executor, reportentries=True):
            # TODO: there is still a bug here, the above doesn't work without a entrysteps definition
            print('a:{}, b:{}'.format(a,b))
            sortPairs(arrays, fileContents)
    except (KeyboardInterrupt, Exception) as e :
        print('caught exception:\n{}\nsaving files...'.format(e))
    
    saveAllFiles(fileContents)
    print('done')

if __name__ == "__main__":
    sortAll()
    print('all sorted! read and find matrices with other script.')