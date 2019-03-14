#!/usr/bin/env python3

from functions import icp
from functions import pairFinder as finder
from functions import rootInterface as ri

import numpy as np

import os

matrices = ri.readJSON("input/matricesIdeal.json")


def ICPmult():

    cuts = [0, 2]

    # prepare
    path = ""

    for cut in cuts:
        targetDir = path + 'output/icp-matrices/'
        # create target dir if need be
        if not os.path.isdir(targetDir):
            os.mkdir(targetDir)

        for overlapID in matrices:
            matrix = finder.findMatrix(path, overlapID, cut, matrices)
            print(matrix)
            #np.savetxt('{}m{}cm.mat'.format(targetDir, overlapID), matrix, delimiter=',')
            #np.savetxt(targetDir + 'm'+overlapID+'cm.mat', matrix, delimiter = ',')

    print('done')


if __name__ == "__main__":
    ICPmult()
