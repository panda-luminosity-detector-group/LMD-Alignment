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
        self.colors = ['xkcd:coral', 'xkcd:kelly green', 'xkcd:dark sky blue']
        plt.rc('font', family = 'serif', serif = 'STIXGeneral') 

    def loadIdealDetectorMatrices(self, filename):
        self.idealDetectorMatrices = mi.loadMatrices(filename)

    def loadDesignMisalignments(self, filename):
        self.misalignMatrices = mi.loadMatrices(filename)

    def loadAlignerMatrices(self, filename):
        self.alignerResults = mi.loadMatrices(filename)

    def getOverlapMisalignLikeICP(self, p1, p2):
        """Returns a 4x4 matrix that looks just like the one found by the ICP, but infinitely precise (well, double precision)."""

        if len(self.idealDetectorMatrices) < 400 or len(self.misalignMatrices) < 1:
            print('ERROR! Please load ideal and misalignment matrices first!')

        # TODO: include a filter for overlapping sensors!
        # this code works for any sensor pair (which is good),
        # which doesn't make sense because I want overlap matrices!

        matPndTo0 = self.idealDetectorMatrices[p1]
        matPndTo5 = self.idealDetectorMatrices[p2]

        try:
            matMisOn0 = self.misalignMatrices[p1]
            matMisOn5 = self.misalignMatrices[p2]

            matMis0InPnd = mi.baseTransform(matMisOn0, (matPndTo0))
            matMis5InPnd = mi.baseTransform(matMisOn5, (matPndTo5))

            # this is the ICP like matrix
            # see paper.calc.ICP
            mat0to5MisInPnd = inv(matMis5InPnd) @ (matMis0InPnd)

        except(KeyError):
            mat0to5MisInPnd = np.identity(4)

        return mat0to5MisInPnd


class boxComparator(comparator):

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Box Rotation Alignment Result, all axes', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)

        bucketLabels = ['rot x', 'rot y', 'rot z']
        
        histA.hist(values, bins=15, histtype='bar', label=bucketLabels, color=self.colors)  # this is only the z distance
        histA.set_title('distance alignment result - generated')   # change to mm!
        histA.set_xlabel('d [µrad]')
        histA.set_ylabel('count')
        plt.legend()
        return fig

    def saveHistogram(self, outputFileName):

        if self.alignerResults is None:
            print(f'Aligner results not found! Skipping...')
            return
        if self.idealDetectorMatrices is None:
            print(f'Ideal Detector Matrices not found! Skipping...')
            return
        if self.misalignMatrices is None:
            print(f'Design Misalignments not found! Skipping...')
            return

        Path(outputFileName).parent.mkdir(parents=True, exist_ok=True)

        try:
            misMat = self.misalignMatrices["/cave_1/lmd_root_0"]
        except(KeyError):
            print(f'Misalignment Matrix not found in misalignments file. That means this volume was not misaligned.')
            misMat = np.identity(4)

        alMat = self.alignerResults["/cave_1/lmd_root_0"]

        # print(f'matrix actual:\n{misMat}')
        # print(f'matrix found:\n{alMat}')

        eActual = mi.rotationMatrixToEulerAngles(misMat)
        eFound = mi.rotationMatrixToEulerAngles(alMat)

        print(f'Euler from actual: {eActual}')
        print(f'Euler from found: {eFound}')
        print(f'Difference: {eActual-eFound}')

        d = (eActual - eFound).reshape((1,3))*1e6       # reshape, scale to um

        self.histValues(d)
        plt.savefig(outputFileName, dpi=150)

        return


class overlapComparator(comparator):

    def loadPerfectDetectorOverlaps(self, fileName):
        self.overlaps = mi.loadMatrices(fileName, False)

    def loadSensorAlignerOverlapMatrices(self, filename):
        self.overlapMatrices = mi.loadMatrices(filename)

    def histValues(self, values):

        muX = np.round(np.average(values[:,0]), 2)
        sigX = np.round(np.std(values[:,0]), 2)

        muY = np.round(np.average(values[:,1]), 2)
        sigY = np.round(np.std(values[:,1]), 2)
       
        muZ = np.round(np.average(values[:,2]), 2)
        sigZ = np.round(np.std(values[:,2]), 2)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        fig.suptitle('Found Overlap Matrices', fontsize=16)

        bucketLabels = [f'dx, µx={muX}, σx={sigX}', f'dy, µy={muY}, σy={sigY}', f'dz, µz={muZ}, σz={sigZ}']

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=15, label=bucketLabels, histtype='bar', color=self.colors)
        histA.set_title('diff ICP/actual, 2% 2D cut')   # change to mm!
        histA.set_xlabel('d [µm]')
        histA.set_ylabel('count')
        plt.legend()
        return fig

    # compute difference ICPmatrix - design overlap misalignment
    def computeOneICP(self, overlapID):

        ICPmatrix = self.overlapMatrices[overlapID]
        p1 = self.overlaps[overlapID]['path1']
        p2 = self.overlaps[overlapID]['path2']
        MisalignLikeICP = self.getOverlapMisalignLikeICP(p1, p2)

        if True:
            # transform to module system so that dz is zero and the matrices are more easily comparable
            modulePath = self.overlaps[overlapID]['pathModule']
            matModule = self.idealDetectorMatrices[modulePath]
            ICPmatrix = mi.baseTransform(ICPmatrix, inv(matModule))
            MisalignLikeICP = mi.baseTransform(MisalignLikeICP, inv(matModule))
        
        # return values in µm
        dMat = (MisalignLikeICP - ICPmatrix)*1e4
        returnArray = np.array([dMat[0,3], dMat[1,3], dMat[2,3]]).reshape(1,3)
        
        return returnArray

    def saveHistogram(self, outputFileName):

        if self.overlapMatrices is None:
            print(f'Overlap ICP Matrices not found! Skipping...')
            return
        if len(self.overlapMatrices) < 360:
            print(f'not all matrices are in overlap file. something went VERY wrong!')
            return
        if self.idealDetectorMatrices is None:
            print(f'Ideal Detector Matrices not found! Skipping...')
            return
        if self.misalignMatrices is None:
            print(f'Design Misalignments not found! Skipping...')
            return

        Path(outputFileName).parent.mkdir(parents=True, exist_ok=True)

        differences = np.empty((0,3))

        for o in self.overlaps:
            differences = np.append(differences, self.computeOneICP(o), axis=0)

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return


class combinedComparator(comparator):

    def histValues(self, values):

        muX = np.round(np.average(values[:,0]), 2)
        sigX = np.round(np.std(values[:,0]), 2)

        muY = np.round(np.average(values[:,1]), 2)
        sigY = np.round(np.std(values[:,1]), 2)
       
        muZ = np.round(np.average(values[:,2]), 2)
        sigZ = np.round(np.std(values[:,2]), 2)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Sensor Alignment Final Result', fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        bucketLabels = [f'dx, µx={muX}, σx={sigX}', f'dy, µy={muY}, σy={sigY}', f'dz, µz={muZ}, σz={sigZ}']

        histA.hist(values, bins=15, label=bucketLabels, histtype='bar', color=self.colors)
        histA.set_title('Distance Alignment Matrix dx (Result-Generated)')   # change to mm!
        histA.set_xlabel('d [µm]')
        histA.set_ylabel('count')
        plt.legend()
        return fig

    def saveHistogram(self, outputFileName):

        if self.alignerResults is None:
            print(f'Aligner results not found! Skipping...')
            return
        if self.idealDetectorMatrices is None:
            print(f'Ideal Detector Matrices not found! Skipping...')
            return
        if self.misalignMatrices is None:
            print(f'Design Misalignments not found! Skipping...')
            return

        Path(outputFileName).parent.mkdir(parents=True, exist_ok=True)

        differences = np.empty((0,3))

        for p in self.misalignMatrices:
            try:
                matResult = self.alignerResults[p]
                matMisalign = self.misalignMatrices[p]

                # return values in µm
                dMat = (matResult - matMisalign)*1e4
                values = np.array([dMat[0,3], dMat[1,3], dMat[2,3]]).reshape(1,3)

                differences = np.append(differences, values, axis=0)
            except:
                continue

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        self.histValues(differences)
        plt.savefig(outputFileName, dpi=150)

        return
