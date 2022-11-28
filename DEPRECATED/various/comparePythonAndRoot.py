#!/usr/bin/env python3
from functions import icp
import json
import uproot
import numpy as np


def readOldBinaryFile():
    #print('rading legacy binary file')
    # read file
    f = open('/home/arbeit/RedPro3TB/simulationData/himster2misaligned-move-data/Pairs/binaryPairFiles/pairs-0-cm.bin', "r")
    fileRaw = np.fromfile(f, dtype=np.double)

    # copy without header
    fileUsable = fileRaw[6:]
    N = int(len(fileUsable)/7)

    # reshape to array with one pair each line
    fileUsable = fileUsable.reshape(N, 7)
    return fileUsable


def readNumpyPairs():
    #print('rading current numpy binary file')
    array = np.load('/home/arbeit/RedPro3TB/simulationData/himster2misaligned-move-data/Pairs/numpyPairs/pairs-0.npy')
    fileUsable = np.transpose(array)
    return fileUsable


def getOldMatrix():
    print('rading legacy matrix file')


def getNumpyMatrix():
    print('computing matrix from numpy file')


if __name__ == "__main__":
    bin1 = readOldBinaryFile()
    bin2 = readNumpyPairs()

    print(len(bin1))
    print(len(bin2))

    print(np.average(bin1[:len(bin2)] - bin2))

    getOldMatrix()
    getNumpyMatrix()
