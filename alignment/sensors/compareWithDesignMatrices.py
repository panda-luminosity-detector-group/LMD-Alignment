#!/usr/bin/env python3

import numpy as np

import json
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')   # so matplotlib works over ssh/with no DISPLAY

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Comapre ICP matrices from sensor overlap with actual misalignment matrices from PandaROOT.
"""


class idealCompare:

    def __init__(self, overlapMatrices):
        self.overlapMatrices = overlapMatrices

    def loadDesignMisalignmentMatrices(self, fileName):
        print(f'Will load design misalignment matrices from {fileName}.')
        with open(fileName) as designFile:
            self.designMatrices = json.load(designFile)

    def loadPerfectDetectorOverlaps(self, fileName):
        print(f'Will load perfect detector overlaps from {fileName}.')
        with open(fileName) as designFile:
            self.overlaps = json.load(designFile)

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)
        textStr = 'µx={:1.2f}, σx={:1.2f}'.format(muX, sigX)

        # plot differnce hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('diff ICP/actual, 2% 2D cut', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=20)  # this is only the z distance
        histA.set_title('distance ICP matrix - generated')   # change to mm!
        histA.set_xlabel('dx [µm]')
        histA.set_ylabel('count')
        histA.text(0.05, 0.95, textStr, transform=histA.transAxes, fontsize=12, verticalalignment='top')
        return fig

    # compute differnce ICPmatrix - design overlap misalignment
    # TODO: this worked only for ICP matrices in sensor-local, they will be in PND global in the future! 
    def computeOneICP(self, overlapID):

        ICPmatrix = self.overlapMatrices[overlapID]

        path1 = self.overlaps[overlapID]['path1']
        path2 = self.overlaps[overlapID]['path2']

        # generate overlap matrix from known misalign matrices like those the ICP would find
        mis1 = np.array(self.designMatrices[path1]).reshape(4, 4)                                                       # misalignment to sensor1
        mis2 = np.array(self.designMatrices[path2]).reshape(4, 4)                                                       # misalignment to sensor2

        # TODO: will soon not longer be here but instead in detectorMatricesIdea.json!
        toSen1 = np.array(self.overlaps[overlapID]['matrix1']).reshape(4, 4)                                            # total matrix PANDA -> sensor1
        toSen2 = np.array(self.overlaps[overlapID]['matrix2']).reshape(4, 4)                                            # total matrix PANDA -> sensor2

        # these lines are wrong if ICP matrices are in PND global
        sen1tosen2 = np.linalg.multi_dot([np.linalg.inv(toSen1), toSen2])                                               # matrix from sensor1 to sensor2, needed for base transform!
        mis2inSen1 = np.linalg.multi_dot([sen1tosen2, mis2, np.linalg.inv(sen1tosen2)])                                 # mis2 in the frame of reference of sensor1, this is a base transform
        mis1to2 = np.linalg.multi_dot([np.linalg.inv(mis1), mis2inSen1])                                                # the final matrix that we want

        # return values in µm
        return ((mis1to2 - ICPmatrix)[0][3]*1e4), ((mis1to2 - ICPmatrix)[1][3]*1e4)

    def saveHistogram(self, outputFileName):

        differences = []

        # TODO: also include dy, use same output file
        for o in self.overlaps:
            differences.append(self.computeOneICP(o)[0])

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return
