#!/usr/bin/env python3

from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import sys
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')   # so matplotlib works over ssh


def dynamicCut(fileUsable, cutPercent=2, use2DCut=True):

    if use2DCut:
        return fileUsable

    else:

        if cutPercent == 0:
            return fileUsable

        # calculate center of mass of differences
        dRaw = fileUsable[:, 3:6] - fileUsable[:, :3]
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = fileUsable[:, 3:6] - com

        # calculate new distance for cut
        dRaw = newhit2 - fileUsable[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        if cutPercent > 0:
            # sort by distance and cut some percent from start and end (discard outliers)
            cut = int(len(fileUsable) * cutPercent/100.0)
            # sort by new distance
            fileUsable = fileUsable[newDist.argsort()]
            # cut off largest distances, NOT lowest
            fileUsable = fileUsable[:-cut]

        return fileUsable


def readBinaryPairFile(filename):
    # read file
    f = open(filename, "r")
    fileRaw = np.fromfile(f, dtype=np.double)

    # ignore header
    fileUsable = fileRaw[6:]
    Npairs = int(len(fileUsable)/7)

    # reshape to array with one pair each line
    fileUsable = fileUsable.reshape(Npairs, 7)
    return fileUsable


def histBinaryPairDistancesForDPG(binPairFile, cutPercent=0, overlap='0', use2Dcut=True):
    filename = binPairFile

    # read binary Pairs
    fileUsable = readBinaryPairFile(filename)

    # apply dynmaic cut
    fileUsable = dynamicCut(fileUsable, cutPercent, use2Dcut)

    # slice to separate vectors
    hit1 = fileUsable[:, :3]
    hit2 = fileUsable[:, 3:6]

    # Make C a homogeneous representation of A and B
    hit1H = np.ones((len(fileUsable), 4))
    hit1H[:, 0:3] = hit1
    hit2H = np.ones((len(fileUsable), 4))
    hit2H[:, 0:3] = hit2

    with open("../input/detectorMatricesIdeal.json", "r") as f:
        matrices = json.load(f)

    with open("../input/detectorOverlapsIdeal.json", "r") as f:
        overlaps = json.load(f)

    path1 = overlaps[overlap]['path1']
    path2 = overlaps[overlap]['path2']

    # make numpy matrix from JSON info
    toSen1 = np.array(matrices[path1]).reshape(4, 4)

    # invert matrices
    toSen1Inv = np.linalg.inv(toSen1)

    # transform hit1 and hit2 to frame of reference of hit1
    hit1T = np.matmul(toSen1Inv, hit1H.T).T
    hit2T = np.matmul(toSen1Inv, hit2H.T).T

    # make differnce hit array
    dHit = hit2T[:, :3] - hit1T[:, :3]

    # plot difference hit array
    fig = plt.figure(figsize=(8, 4))
    if use2Dcut:
        fig.suptitle('{}% 2D cut'.format(cutPercent), fontsize=16)
    else:
        fig.suptitle('{}% 1D cut'.format(cutPercent), fontsize=16)

    fig.subplots_adjust(wspace=0.05)

    histA = fig.add_subplot(1, 2, 1)
    histA.hist(fileUsable[:, 6]*10, bins=150, log=True,
               range=[0.25, 1.2])  # this is only the z distance
    histA.set_title('distance')   # change to mm!
    histA.set_xlabel('d [mm]')
    histA.set_ylabel('count (logarithmic)')

    histB = fig.add_subplot(1, 2, 2)
    histB.hist2d(dHit[:, 0]*10, dHit[:, 1]*10, bins=150,
                 norm=LogNorm(), range=[[-01.3, 01.3], [-01.3, 01.3]])
    histB.set_title('2d distance')
    histB.yaxis.tick_right()
    histB.yaxis.set_ticks_position('both')
    histB.set_xlabel('dx [mm]')
    histB.set_ylabel('dy [mm]')
    histB.tick_params(direction='in')
    histB.yaxis.set_label_position("right")

    return fig


def pairDxDyDPG():

    overlap = '0'
    #pathpre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
    pathpre = '../input/2018-08-himster2-'
    pathpost = '/binaryPairFiles/pairs-' + overlap + '-cm.bin'
    misaligns = [
        'misalign-200u',
    ]
    outpath = Path('../output/forDPG')
    cuts = [0, 2]

    use2Dcuts = [True, False]

    for usage in use2Dcuts:
        for misalign in misaligns:
            if not outpath.exists:
                outpath.mkdir(parents=True, exist_ok=True)
            for cut in cuts:

                filename = Path(pathpre + misalign + pathpost)

                histBinaryPairDistancesForDPG(filename, cut, overlap, usage)
                if usage:
                    plt.savefig(outpath / Path(str(cut)+'-2D.pdf'), dpi=1200)
                else:
                    plt.savefig(outpath / Path(str(cut)+'-1D.pdf'), dpi=1200)


if __name__ == "__main__":
    print("Running...")
    pairDxDyDPG()
    print("all done!\n")
