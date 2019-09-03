#!/usr/bin/env python3

from numpy.linalg import inv

import numpy as np

import json
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')   # so matplotlib works over ssh/with no DISPLAY

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Comapre ICP matrices from sensor overlap with actual misalignment matrices from PandaROOT.

This is obviously not possible with the actual, physical geometry, but can be used during simulations
to estimate the remaining errors of the misalignment.

We will therefore use the word CHEAT multiple times in here.
"""


class comparator:
    def __init__(self):
        self.idealDetectorMatrices = {}
        self.misalignMatrices = {}

    def baseTransform(self, mat, matFromAtoB):
        """
        Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
        If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
        this function inv(matTo0). I know it's confusing, but that's the way this works.

        Example: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
        """
        return matFromAtoB @ mat @ inv(matFromAtoB)

    def getOverlapMisalignLikeICP(self, p1, p2):

        # TODO: include a filter for overlapping sensors!
        # this code works for any sensor pair (which is good),
        # which doesn't make sense because I want overlap matrices!

        matPndTo0 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
        matPndTo5 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)

        # I don't have these!
        matMisOn0 = np.array(self.misalignMatrices[p1]).reshape(4, 4)
        matMisOn5 = np.array(self.misalignMatrices[p2]).reshape(4, 4)

        matMisOn0InPnd = self.baseTransform(matMisOn0, (matPndTo0))
        matMisOn5InPnd = self.baseTransform(matMisOn5, (matPndTo5))

        # this is the ICP like matrix
        # see paper calc.ICP
        mat0to5MisInPnd = inv(matMisOn5InPnd) @ (matMisOn0InPnd)
        return mat0to5MisInPnd


class overlapComparator(comparator):

    def setOverlapMatrices(self, overlapMatrices):
        self.overlapMatrices = overlapMatrices

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
    def computeOneICP(self, overlapID):

        ICPmatrix = self.overlapMatrices[overlapID]
        p1 = self.overlaps[overlapID]['path1']
        p2 = self.overlaps[overlapID]['path2']
        MisalignLikeICP = self.getOverlapMisalignLikeICP(p1, p2)

        # return values in µm
        return ((MisalignLikeICP - ICPmatrix)[0][3]*1e4), ((MisalignLikeICP - ICPmatrix)[1][3]*1e4)

    def saveHistogram(self, outputFileName):

        differences = []

        # TODO: also include dy, use same output file
        for o in self.overlaps:
            differences.append(self.computeOneICP(o)[0])

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return


class combinedComparator(comparator):

    def cheatMatrices(self):
        cheatMat2star = np.array(misalignMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
        cheatMat3star = np.array(misalignMatrices[self.modulePath + '/sensor_3']).reshape(4, 4)
        cheatMat4star = np.array(misalignMatrices[self.modulePath + '/sensor_4']).reshape(4, 4)
        cheatMat5star = np.array(misalignMatrices[self.modulePath + '/sensor_5']).reshape(4, 4)
        cheatMat6star = np.array(misalignMatrices[self.modulePath + '/sensor_6']).reshape(4, 4)
        cheatMat7star = np.array(misalignMatrices[self.modulePath + '/sensor_7']).reshape(4, 4)
        cheatMat8star = np.array(misalignMatrices[self.modulePath + '/sensor_8']).reshape(4, 4)
        cheatMat9star = np.array(misalignMatrices[self.modulePath + '/sensor_9']).reshape(4, 4)

    #! we don't have some of these matrices, this is cheating and should go in the comparer
    def getActualMatrixFromGeoManager(self, p1, p2):
        with open('input/detectorMatrices-sensors-1.00.json') as f:
            totalMatrices = json.load(f)
        matP1toP2 = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)
        return matP1toP2
