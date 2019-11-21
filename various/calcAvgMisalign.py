#!/usr/bin/env python3

#import detail.matrixInterface as mi

from pathlib import Path
import json
import numpy as np
import sys

def calc(inFile, outFile):
    pass
    # read all input matrices
    with open(inFile, 'r') as f:
        inMats = json.load(f)

    for p in inMats:
        inMats[p] = np.array(inMats[p]).reshape((4,4))

    # find 4 modules per sector

    # calc avg misalign
    avgMisMats = {}

    paths = [
        [
            "/cave_1/lmd_root_0/half_0/plane_0/module_0",
            "/cave_1/lmd_root_0/half_0/plane_1/module_0",
            "/cave_1/lmd_root_0/half_0/plane_2/module_0",
            "/cave_1/lmd_root_0/half_0/plane_3/module_0"
        ],
        [
            "/cave_1/lmd_root_0/half_0/plane_0/module_1",
            "/cave_1/lmd_root_0/half_0/plane_1/module_1",
            "/cave_1/lmd_root_0/half_0/plane_2/module_1",
            "/cave_1/lmd_root_0/half_0/plane_3/module_1"
        ],
        [
            "/cave_1/lmd_root_0/half_0/plane_0/module_2",
            "/cave_1/lmd_root_0/half_0/plane_1/module_2",
            "/cave_1/lmd_root_0/half_0/plane_2/module_2",
            "/cave_1/lmd_root_0/half_0/plane_3/module_2"
        ],
        [
            "/cave_1/lmd_root_0/half_0/plane_0/module_3",
            "/cave_1/lmd_root_0/half_0/plane_1/module_3",
            "/cave_1/lmd_root_0/half_0/plane_2/module_3",
            "/cave_1/lmd_root_0/half_0/plane_3/module_3"
        ],
        [
            "/cave_1/lmd_root_0/half_0/plane_0/module_4",
            "/cave_1/lmd_root_0/half_0/plane_1/module_4",
            "/cave_1/lmd_root_0/half_0/plane_2/module_4",
            "/cave_1/lmd_root_0/half_0/plane_3/module_4"
        ],
        [
            "/cave_1/lmd_root_0/half_1/plane_0/module_0",
            "/cave_1/lmd_root_0/half_1/plane_1/module_0",
            "/cave_1/lmd_root_0/half_1/plane_2/module_0",
            "/cave_1/lmd_root_0/half_1/plane_3/module_0"
        ],
        [
            "/cave_1/lmd_root_0/half_1/plane_0/module_1",
            "/cave_1/lmd_root_0/half_1/plane_1/module_1",
            "/cave_1/lmd_root_0/half_1/plane_2/module_1",
            "/cave_1/lmd_root_0/half_1/plane_3/module_1"
        ],
        [
            "/cave_1/lmd_root_0/half_1/plane_0/module_2",
            "/cave_1/lmd_root_0/half_1/plane_1/module_2",
            "/cave_1/lmd_root_0/half_1/plane_2/module_2",
            "/cave_1/lmd_root_0/half_1/plane_3/module_2"
        ],
        [
            "/cave_1/lmd_root_0/half_1/plane_0/module_3",
            "/cave_1/lmd_root_0/half_1/plane_1/module_3",
            "/cave_1/lmd_root_0/half_1/plane_2/module_3",
            "/cave_1/lmd_root_0/half_1/plane_3/module_3"
        ],
        [
            "/cave_1/lmd_root_0/half_1/plane_0/module_4",
            "/cave_1/lmd_root_0/half_1/plane_1/module_4",
            "/cave_1/lmd_root_0/half_1/plane_2/module_4",
            "/cave_1/lmd_root_0/half_1/plane_3/module_4"
        ]
    ]

    for i in range(10):
        avgMisMats[str(i)] = np.zeros((4,4))
        for path in paths[i]:
            avgMisMats[str(i)] += inMats[path] / 4

        print(f'\nsector {str(i)}:\n{avgMisMats[str(i)]}\n')

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
        print(f'File {inFile} can not be read!')
        sys.exit(1)
    if outFile.exists():
        print(f'Error! File {outFile} already exists.')
        sys.exit(1)

    calc(inFile, outFile)