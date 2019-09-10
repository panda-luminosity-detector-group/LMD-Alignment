#!/usr/bin/env python3

from pathlib import Path
from numpy.linalg import inv

import detail.matrixInterface as mi
import numpy as np

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')   # so matplotlib works over ssh/with no DISPLAY

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Comapre ICP matrices from sensor overlap with actual misalignment matrices from PandaROOT.

This is obviously not possible with the actual, physical geometry, but can be used during simulations
to estimate the remaining errors of the misalignment.
"""


class comparator:
    def __init__(self):
        self.idealDetectorMatrices = {}
        self.misalignMatrices = {}

    def loadIdealDetectorMatrices(self, filename):
        self.idealDetectorMatrices = mi.loadMatrices(filename)

    def loadDesignMisalignments(self, filename):
        self.misalignMatrices = mi.loadMatrices(filename)

    def loadAlignerMatrices(self, filename):
        self.alignerResults = mi.loadMatrices(filename)

    def getOverlapMisalignLikeICP(self, p1, p2):
        """Returns a 4x4 matrix that looks just like the one found by the ICP, but infinitely (well, double precision) precise."""

        if len(self.idealDetectorMatrices) < 400 or len(self.misalignMatrices) < 1:
            print('ERROR! Please load ideal and misalignment matrices first!')

        # TODO: include a filter for overlapping sensors!
        # this code works for any sensor pair (which is good),
        # which doesn't make sense because I want overlap matrices!

        matPndTo0 = self.idealDetectorMatrices[p1]
        matPndTo5 = self.idealDetectorMatrices[p2]

        # I don't have these!
        matMisOn0 = self.misalignMatrices[p1]
        matMisOn5 = self.misalignMatrices[p2]

        matMisOn0InPnd = mi.baseTransform(matMisOn0, (matPndTo0))
        matMisOn5InPnd = mi.baseTransform(matMisOn5, (matPndTo5))

        # this is the ICP like matrix
        # see paper.calc.ICP
        mat0to5MisInPnd = inv(matMisOn5InPnd) @ (matMisOn0InPnd)
        return mat0to5MisInPnd


class boxComparator(comparator):

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)
        textStr = 'µα={:1.2f}, σα={:1.2f}'.format(muX, sigX)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Box Rotation Alignment Result', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=20)  # this is only the z distance
        histA.set_title('distance alignment result - generated')   # change to mm!
        histA.set_xlabel('dα [µrad]')
        histA.set_ylabel('count')
        histA.text(0.05, 0.95, textStr, transform=histA.transAxes, fontsize=12, verticalalignment='top')
        return fig

    def saveHistogram(self, outputFileName):

        differences = []

        misMat = self.misalignMatrices["/cave_1/lmd_root_0"]
        alMat = self.alignerResults["/cave_1/lmd_root_0"]

        print(f'matrix actual:\n{misMat}')
        print(f'matrix found:\n{alMat}')

        eActual = mi.rotationMatrixToEulerAngles(misMat)
        eFound = mi.rotationMatrixToEulerAngles(alMat)

        print(f'Euler from actual: {eActual}')
        print(f'Euler from found: {eFound}')
        print(f'Difference: {eActual-eFound}')

        for p in self.alignerResults:
            d = (eActual - eFound)[0]
            differences.append(d*1e6)

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return


class overlapComparator(comparator):

    def loadPerfectDetectorOverlaps(self, fileName):
        self.overlaps = mi.loadMatrices(fileName)

    def loadSensorAlignerOverlapMatrices(self, filename):
        self.overlapMatrices = mi.loadMatrices(filename)

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)
        textStr = 'µx={:1.2f}, σx={:1.2f}'.format(muX, sigX)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Sensor Alignment Result', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=20)  # this is only the z distance
        histA.set_title('diff ICP/actual, 2% 2D cut')   # change to mm!
        histA.set_xlabel('dx [µm]')
        histA.set_ylabel('count')
        histA.text(0.05, 0.95, textStr, transform=histA.transAxes, fontsize=12, verticalalignment='top')
        return fig

    # compute difference ICPmatrix - design overlap misalignment
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

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)
        textStr = 'µx={:1.2f}, σx={:1.2f}'.format(muX, sigX)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Sensor Alignment Result', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=20)  # this is only the z distance
        histA.set_title('Distance Alignment (Result-Generated)')   # change to mm!
        histA.set_xlabel('dx [µm]')
        histA.set_ylabel('count')
        histA.text(0.05, 0.95, textStr, transform=histA.transAxes, fontsize=12, verticalalignment='top')
        return fig

    def saveHistogram(self, outputFileName):

        differences = []

        for p in self.misalignMatrices:
            try:
                differences.append((self.alignerResults[p][3] - self.misalignMatrices[p][3])*1e4)
            except:
                continue

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return
