#!/usr/bin/env python3

from pathlib import Path
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

    def loadIdealDetectorMatrices(self, filename):
        with open(filename) as f:
            self.idealDetectorMatrices = json.load(f)

        # reshape
        for key, value in self.idealDetectorMatrices.items():
            self.idealDetectorMatrices.update({key: np.array(value).reshape(4, 4)})

    def loadDesignMisalignments(self, filename):

        if not Path(filename).exists():
            print(f'INFO: Misalignment matrix file does not exist. Setting misalignments to identity matrices!')
            self.setMisalignmentsToIdentity()

        else:
            with open(filename) as f:
                self.misalignMatrices = json.load(f)

        # reshape
        # for key, value in self.misalignMatrices.items():
        #     self.misalignMatrices.update({key : np.array(value).reshape(4, 4)})

    # if the geometry is not misaligned, the misalignments can be compared to identity matrices
    # do this after loading the ideal detector matrices
    def setMisalignmentsToIdentity(self):
        for p in self.idealDetectorMatrices:
            self.misalignMatrices[p] = np.identity(4).flatten()

    def baseTransform(self, mat, matFromAtoB):
        """
        Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
        If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
        this function inv(matTo0). I know it's confusing, but that's the way this works.

        Example 1: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
        Example 1: matrixInSensor = baseTransform(matrixInPanda, inv(matrixPandaToSensor))
        """
        return matFromAtoB @ mat @ inv(matFromAtoB)

    # from https://www.learnopencv.com/rotation-matrix-to-euler-angles/
    # Calculates rotation matrix to euler angles
    def rotationMatrixToEulerAngles(self, R):

        R = R.reshape(4, 4)
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def getOverlapMisalignLikeICP(self, p1, p2):

        if len(self.idealDetectorMatrices) < 400 or len(self.misalignMatrices) < 1:
            print('ERROR! Please load ideal and misalignment matrices first!')

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
        # see paper.calc.ICP
        mat0to5MisInPnd = inv(matMisOn5InPnd) @ (matMisOn0InPnd)
        return mat0to5MisInPnd


class boxComparator(comparator):

    def loadAlignerMatrices(self, fileName):
        with open(fileName) as file:
            self.alignerResults = json.load(file)

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

        print(f'matrix actual:\n{np.array(self.misalignMatrices["/cave_1/lmd_root_0"])}')
        print(f'matrix found:\n{np.array(self.alignerResults["/cave_1/lmd_root_0"])}')

        eActual = self.rotationMatrixToEulerAngles(np.array(self.misalignMatrices["/cave_1/lmd_root_0"]))
        eFound = self.rotationMatrixToEulerAngles(np.array(self.alignerResults["/cave_1/lmd_root_0"]))

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
        with open(fileName) as file:
            self.overlaps = json.load(file)

    def loadSensorAlignerOverlapMatrices(self, filename):
        with open(filename) as f:
            self.overlapMatrices = json.load(f)

        # reshape
        for key, value in self.overlapMatrices.items():
            self.overlapMatrices.update({key: np.array(value).reshape(4, 4)})

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

    def loadSensorAlignerResults(self, fileName):
        with open(fileName) as file:
            self.alignerResults = json.load(file)

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

        for p in self.alignerResults:
            differences.append((self.alignerResults[p][3] - self.misalignMatrices[p][3])*1e4)

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return
