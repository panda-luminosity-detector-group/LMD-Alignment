#!/usr/bin/env python3

import sys, argparse, tqdm
from pathlib import Path
import numpy as np
from concurrent.futures import ThreadPoolExecutor

def readBinary(fileName):
    # read file
    print(f'reading binary pair file')
    f = open(fileName, "r")
    fileRaw = np.fromfile(f, dtype=np.double)

    # ignore header
    fileUsable = fileRaw[6:]
    Npairs = int(len(fileUsable)/7)

    # reshape to array with one pair each line
    fileUsable = fileUsable.reshape(Npairs, 7)
    print(f'done!')
    return fileUsable

def readNPY(fileName, maxPairs = 1e9):
    
    try:
        PairData = np.load(fileName)
    except:
        raise Exception(f'ERROR! Can not read {fileName}!')

    # reduce to maxPairs
    if PairData.shape > (7, int(maxPairs)):
        PairData = PairData[..., :int(maxPairs)]

    # the new python Root Reader stores them slightly different...
    PairData = np.transpose(PairData)
    return PairData

def saveNPY(fileName, pairs):
    # old format requires row-major format, don't ask
    pairs = pairs.T
    np.save(file=fileName, arr=pairs, allow_pickle=False)

if __name__ == "__main__":
    maxPairs = 3e5

    inPath = Path('input/npPairsHuge')
    outPath = Path('input/npPairsHuge/reduced')
    outPathTemp = Path('/dev/shm/doot')

    files = inPath.glob('*.npy')

    print(f'Processing!')
    for file in files:
        fileName = file.name
        print(f'file: {fileName}')
        pairs = readNPY(file, maxPairs)
        saveNPY(outPathTemp / fileName, pairs)

    print(f"done!")