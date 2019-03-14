#!/usr/bin/env python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from functions import rootInterface as ri
from functions import pairFinder as finder
from functions import histogramers as hi
from matplotlib.colors import LogNorm
import os
import sys
from matplotlib.backends.backend_pdf import PdfPages

matrices = ri.readJSON("input/matricesIdeal.json")


def histBinaryPairDistancesForDPG(pathpre, misalign, pathpost, cutPercent=0, overlap='0', use2Dcut=True):
    filename = pathpre + misalign + pathpost

    # read binary Pairs
    fileUsable = ri.readBinaryPairFile(filename)

    # apply dynmaic cut
    fileUsable = finder.dynamicCut(fileUsable, cutPercent, use2Dcut)

    # slice to separate vectors
    hit1 = fileUsable[:, :3]
    hit2 = fileUsable[:, 3:6]

    # Make C a homogeneous representation of A and B
    hit1H = np.ones((len(fileUsable), 4))
    hit1H[:, 0:3] = hit1
    hit2H = np.ones((len(fileUsable), 4))
    hit2H[:, 0:3] = hit2

    # make numpy matrix from JSON info
    toSen1 = np.array(matrices[overlap]['matrix1']).reshape(4, 4)

    # invert matrices
    toSen1Inv = np.linalg.inv(toSen1)

    # transform hit1 and hit2 to frame of reference of hit1
    hit1T = np.matmul(toSen1Inv, hit1H.T).T
    hit2T = np.matmul(toSen1Inv, hit2H.T).T

    # make differnce hit array
    dHit = hit2T[:, :3] - hit1T[:, :3]

    # plot differnce hit array
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
    pathpre = 'input/2018-08-himster2-'
    pathpost = '/binaryPairFiles/pairs-' + overlap + '-cm.bin'
    misaligns = [
        'misalign-200u',
    ]
    outpath = 'output/forDPG'
    cuts = [0, 2]

    use2Dcuts = [True, False]

    for usage in use2Dcuts:
        for misalign in misaligns:
            if not os.path.isdir(outpath):
                os.mkdir(outpath)
            for cut in cuts:
                histBinaryPairDistancesForDPG(
                    pathpre, misalign, pathpost, cut, overlap, usage)
                if usage:
                    plt.savefig(outpath+'/'+str(cut)+'-2D.png', dpi=150)
                else:
                    plt.savefig(outpath+'/'+str(cut)+'-1D.png', dpi=150)


if __name__ == "__main__":
    print("Running...")
    pairDxDyDPG()
    print("all done!\n")
