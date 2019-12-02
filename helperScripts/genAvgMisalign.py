#!/usr/bin/env python3

"""
This script reads the artificial misalignment matrices from the simulations to generate
the "average misalignment matrices"  for all sectors. For the final detector,
these matrices will of course really be measured, but for now, we need to cheat a little.
"""

from pathlib import Path
import json
import numpy as np
import sys

def calcOld(inFile, outFile):
    # read all input matrices
    with open(inFile, 'r') as f:
        inMats = json.load(f)

    for p in inMats:
        inMats[p] = np.array(inMats[p]).reshape((4,4))

    # calc avg misalign
    avgMisMats = {}

    # find 4 modules per sector
    with open('input/moduleAlignment/sectorPaths.json') as f:
        paths = json.load(f)

    for i in range(10):
        avgMisMats[str(i)] = np.zeros((4,4))
        for path in paths[str(i)]:
            avgMisMats[str(i)] += inMats[path] / 4

    # store to output as dict ( sectorString -> matrix )
    saveMatrices = {}
    outFile.parent.mkdir(exist_ok=True, parents=True)
    for p in avgMisMats:
        saveMatrices[p] = np.ndarray.tolist(np.ndarray.flatten(avgMisMats[p]))

    with open(outFile, 'w') as f:
        json.dump(saveMatrices, f, indent=2)

def calc(inFile, outFile):
    # read all input matrices
    with open(inFile, 'r') as f:
        inMats = json.load(f)

    for p in inMats:
        inMats[p] = np.array(inMats[p]).reshape((4,4))

    # calc avg misalign
    avgMisMats = {}

    # find 4 modules per sector
    with open('input/moduleAlignment/sectorPaths.json') as f:
        paths = json.load(f)

    for i in range(10):
        avgMisMats[str(i)] = np.identity(4)
        for path in paths[str(i)]:
            avgMisMats[str(i)] = avgMisMats[str(i)] @ inMats[path]

    # store to output as dict ( sectorString -> matrix )
    saveMatrices = {}
    outFile.parent.mkdir(exist_ok=True, parents=True)
    for p in avgMisMats:
        saveMatrices[p] = np.ndarray.tolist(np.ndarray.flatten(avgMisMats[p]))

    with open(outFile, 'w') as f:
        json.dump(saveMatrices, f, indent=2)

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} inFile outFile')
        sys.exit(1)

    inFile = Path(sys.argv[1])
    outFile = Path(sys.argv[2])

    if not inFile.exists():
        raise Exception(f'File {inFile} can not be read!')
    # if outFile.exists():
    #     raise Exception(f'Error! File {outFile} already exists.')
    
    print(f'Calculating average misalignments...')
    calc(inFile, outFile)
    print(f'all done!')