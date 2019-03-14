#!/usr/bin/env python3

from functions import icp
from functions import pairFinder as finder
from functions import rootInterface as ri

import numpy as np

import os
import json

matrices = ri.readJSON("input/overlaps.json")


def createAllOverlaps():
    overlapIDs = []
    for half in range(2):
        for plane in range(4):
            for module in range(5):
                for overlap in range(9):
                    overlapIDs.append(half*1000 + plane*100 + module*10 + overlap)
    return overlapIDs


def ICPmult():
    cuts = [0, 2]
    path = "input/2018-08-himster2-misalign-200u/"
    for cut in cuts:
        targetDir = 'output/icp-matrices/'
        # create target dir if need be
        if not os.path.isdir(targetDir):
            os.mkdir(targetDir)

        for overlapID in matrices:
            matrix = finder.findMatrix(path, overlapID, cut, matrices)
            print(matrix)
            #np.savetxt('{}m{}cm.mat'.format(targetDir, overlapID), matrix, delimiter=',')
            #np.savetxt(targetDir + 'm'+overlapID+'cm.mat', matrix, delimiter = ',')
    print('done')


def testICPone(overlapID, cut):

    path = "input/2018-08-himster2-misalign-200u/"
    ICPmatrix = finder.findMatrix(path, str(overlapID), cut, matrices)
    # print(ICPmatrix)

    # json paths:
    jsonPath = 'input/rootMisalignMatrices/json/misalignMatrices-SensorsOnly-200.root.json'

    with open(jsonPath, 'r') as f:
        misMat = json.load(f)

    path1 = matrices[str(overlapID)]['path1']
    path2 = matrices[str(overlapID)]['path2']
    # print(path1)

    # generate overlap matrix like the ICP would from known misalign matrices
    mis1 = np.array(misMat[path1]).reshape(4, 4)            # misalignment to sensor1
    mis2 = np.array(misMat[path2]).reshape(4, 4)            # same for sensor2
    toSen1 = np.array(matrices[str(overlapID)]['matrix1']).reshape(4, 4)                                               # total matrix PANDA -> sensor1
    toSen2 = np.array(matrices[str(overlapID)]['matrix2']).reshape(4, 4)                                               # total matrix PANDA -> sensor2
    sen1tosen2 = np.linalg.multi_dot([np.linalg.inv(toSen1), toSen2])                                       # matrix from sensor1 to sensor2, needed for base transform!
    mis2inSen1 = np.linalg.multi_dot([sen1tosen2, mis2, np.linalg.inv(sen1tosen2)])                         # mis2 in the frame of reference of sensor1, this is a base transform
    mis1to2 = np.linalg.multi_dot([np.linalg.inv(mis1), mis2inSen1])                                        # the final matrix that we want

    # print(mis1to2)

    # print('ermagehrd. smol?')
    # print('dx: {} µm'.format((mis1to2 - ICPmatrix)[0][3]*1e4))
    # print('dy: {} µm'.format((mis1to2 - ICPmatrix)[1][3]*1e4))
    return ((mis1to2 - ICPmatrix)[0][3]*1e4)


def computeAllMatrices():
    overlaps = createAllOverlaps()

    overlaps = overlaps[:10]    # use only first 10 elements for now

    values = []
    print('computing ICP values...')
    for overlap in overlaps:
        values.append(testICPone(overlap, 0))

    print(values)


if __name__ == "__main__":
    computeAllMatrices()
