#!/usr/bin/env python3

from pathlib import Path
from numpy.linalg import inv

import detail.matrixInterface as mi
import numpy as np

import matplotlib
import matplotlib.pyplot as plt

import re

matplotlib.use('Agg')   # so matplotlib works over ssh/with no DISPLAY

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Comapre ICP matrices from sensor overlap with actual misalignment matrices from PandaROOT.

This is obviously not possible with the actual, physical geometry, but can be used during simulations
to estimate the remaining errors of the misalignment.

TODO: use single histogram function for ALL comparators, and merely change the difference calculation functions. Then all histograms will look the same.
TODO: also, check comparison for the matrices that were not aligned, ie sensor matrices during module alignment. something seems off there.

"""


class comparator:
    def __init__(self, runConfig):
        self.config = runConfig
        self.idealDetectorMatrices = {}
        self.misalignMatrices = {}
        self.resultArray = np.zeros(1)
        goodColors = ['xkcd:coral', 'xkcd:pale orange', 'xkcd:dark lilac', 'xkcd:teal green', 'xkcd:bluish grey', 'xkcd:dark sky blue']
        self.colors = [goodColors[1], goodColors[3], goodColors[5]]
        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')


        #plt.rcParams['axes.spines.left'] = False
        plt.rcParams['axes.spines.right'] = False
        plt.rcParams['axes.spines.top'] = False
        #plt.rcParams['axes.spines.bottom'] = False

        plt.rcParams["legend.loc"] = 'upper left'

    def loadIdealDetectorMatrices(self, filename):
        print(f'loading ideal detector matrices from:\n{filename}')
        self.idealDetectorMatrices = mi.loadMatrices(filename)

    def loadDesignMisalignments(self, filename):
        print(f'loading design misalignments from:\n{filename}')
        self.misalignMatrices = mi.loadMatrices(filename)

    def loadAlignerMatrices(self, filename):
        print(f'loading align matrices from:\n{filename}')
        self.alignerResults = mi.loadMatrices(filename)

    def getOverlapMisalignLikeICP(self, p1, p2):
        """Returns a 4x4 matrix that looks just like the one found by the ICP, but infinitely precise (well, double precision)."""

        if len(self.idealDetectorMatrices) < 400 or len(self.misalignMatrices) < 1:
            raise Exception('ERROR! Please load ideal and misalignment matrices first!')

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

    def makeHist(self, title, xlabel, ylabel):
        theseValues = self.resultArray

         # prepare figure
        fig = plt.figure()

        fig.set_size_inches(8/2.54, 5/2.54)

        fig.suptitle(title)
        fig.subplots_adjust(wspace=0.05)
        # fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        # fig.tight_layout()
        histA = fig.add_subplot(1, 1, 1)
        
        # statistics
        mu = np.average(theseValues, axis=0)
        sigX = np.std(theseValues, axis=0)

        # prepare args, labels
        # bucketLabels = [f'{self.latexsigma} dx={sigX[0]:.2f}{self.latexmu}m', f'{self.latexsigma} dy={sigX[1]:.2f}{self.latexmu}m', f'{self.latexsigma} rot z={sigX[2]:.2f}{self.latexmu}rad']
        bucketLabels = [f'{self.latexsigma}x={sigX[0]:.2f}{self.latexmu}m', f'{self.latexsigma}y={sigX[1]:.2f}{self.latexmu}m', f'{self.latexsigma} rot z={sigX[2]:.2f}{self.latexmu}rad']
        kwargs = dict(histtype='stepfilled', alpha=0.75, bins=15, label=bucketLabels, color=self.colors[:2])

        # histogram
        histA.hist(theseValues[...,:2], **kwargs)  # this is only the z distance

        # names, titles
        # histA.set_title('distance alignment result - generated')   # change to mm!
        histA.set_xlabel(title)
        histA.set_ylabel(ylabel)

        # manually set legend order
        handles,labels = histA.get_legend_handles_labels()
        handles = [handles[1], handles[0]]
        labels = [labels[1], labels[0]]
        histA.legend(handles,labels,loc=2)
        return fig

    def saveHist(self, outputFileName):
        plt.savefig(outputFileName,
                    #This is simple recomendation for publication plots
                    dpi=1000, 
                    # Plot will be occupy a maximum of available space
                    bbox_inches='tight')
        plt.close()


class boxComparator(comparator):

    def histValues(self, values):

        muX = np.average(values)
        sigX = np.std(values)

        # plot difference hit array
        fig = plt.figure(figsize=(6, 4))

        # TODO: better title
        fig.suptitle('Box Rotation Alignment Residuals')

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)

        bucketLabels = ['rot x', 'rot y', 'rot z']
        
        histA.hist(values, bins=15, histtype='bar', label=bucketLabels, color=self.colors)  # this is only the z distance
        histA.set_title('distance alignment result - generated')   # change to mm!
        histA.set_xlabel(f'd [{self.latexmu}rad]')
        histA.set_ylabel('count')
        plt.legend()
        return fig

    def saveHistogram(self, outputFileName):

        if self.alignerResults is None:
            raise Exception(f'Aligner results not found! Skipping...')
        if self.idealDetectorMatrices is None:
            raise Exception(f'Ideal Detector Matrices not found! Skipping...')
        if self.misalignMatrices is None:
            raise Exception(f'Design Misalignments not found! Skipping...')

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
        plt.savefig(outputFileName, dpi=300)
        plt.close()

        return


class moduleComparator(comparator):

    def histValues(self, values):

        # prepare figure
        fig = plt.figure()

        fig.set_size_inches(8/2.54, 5/2.54)

        fig.suptitle('Module Misalignment Residuals')
        fig.subplots_adjust(wspace=0.05)
        # fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        # fig.tight_layout()
        histA = fig.add_subplot(1, 1, 1)
        
        # statistics
        mu = np.average(values, axis=0)
        sigX = np.std(values, axis=0)

        # prepare args, labels
        # bucketLabels = [f'{self.latexsigma} dx={sigX[0]:.2f}{self.latexmu}m', f'{self.latexsigma} dy={sigX[1]:.2f}{self.latexmu}m', f'{self.latexsigma} rot z={sigX[2]:.2f}{self.latexmu}rad']
        bucketLabels = [f'{self.latexsigma}x={sigX[0]:.2f}{self.latexmu}m', f'{self.latexsigma}y={sigX[1]:.2f}{self.latexmu}m', f'{self.latexsigma} rot z={sigX[2]:.2f}{self.latexmu}rad']
        kwargs = dict(histtype='stepfilled', alpha=0.75, bins=15, label=bucketLabels, color=self.colors[:2])

        # histogram
        histA.hist(values[...,:2], **kwargs)  # this is only the z distance

        # names, titles
        # histA.set_title('distance alignment result - generated')   # change to mm!
        histA.set_xlabel(f'd [{self.latexmu}m]')
        histA.set_ylabel('count')

        # manually set legend order
        handles,labels = histA.get_legend_handles_labels()
        handles = [handles[1], handles[0]]
        labels = [labels[1], labels[0]]
        histA.legend(handles,labels,loc=2)

        return fig

    def saveHistogram(self, outputFileName):

        if self.alignerResults is None:
            raise Exception(f'Aligner results not found! Skipping...')
        if self.idealDetectorMatrices is None:
            raise Exception(f'Ideal Detector Matrices not found! Skipping...')
        if self.misalignMatrices is None:
            raise Exception(f'Design Misalignments not found! Skipping...')

        Path(outputFileName).parent.mkdir(parents=True, exist_ok=True)

        resValues = []

        modules = []
        # get only module paths
        for path in self.idealDetectorMatrices:
            regex = r"^/cave_(\d+)/lmd_root_(\d+)/half_(\d+)/plane_(\d+)/module_(\d+)$"
            p = re.compile(regex)
            m = p.match(path)

            if m:
                if m.group(3) != 1:
                    modules.append(m.group(0))
        
        results = {}

        for mod in modules:
            alMat = self.alignerResults[mod]
            
            if self.config.misalignType == 'modules':
                actualMat = self.misalignMatrices[mod]
            else:
                actualMat = np.identity(4)

            diffMat = alMat-actualMat
            dAlpha = mi.rotationMatrixToEulerAngles(diffMat)

            values = [diffMat[0,3]*1e4, diffMat[1,3]*1e4, dAlpha[2]]
            resValues.append(values)
        
        resValues = np.array(resValues)

        self.histValues(resValues)
        plt.savefig(outputFileName,
                    #This is simple recomendation for publication plots
                    dpi=1000, 
                    # Plot will be occupy a maximum of available space
                    bbox_inches='tight')
        plt.close()

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
        fig = plt.figure()
        fig.set_size_inches(16/2.54, 9/2.54) 

        bucketLabels = [f'dx, {self.latexmu}x={muX}, {self.latexsigma}x={sigX}', f'dy, {self.latexmu}y={muY}, {self.latexsigma}y={sigY}', f'dz, {self.latexmu}z={muZ}, {self.latexsigma} z={sigZ}']

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        kwargs = dict(histtype='stepfilled', alpha=0.75, bins=50, label=bucketLabels, color=self.colors[:2])
        histA.hist(values[...,:2], **kwargs)
        histA.set_title('Overlap Matrices ICP/actual | 2\% 2D cut')   # change to mm!
        histA.set_xlabel(f'd [{self.latexmu}m]')
        histA.set_ylabel('count')
       
        handles, labels = plt.gca().get_legend_handles_labels()
        order = [1,0]
        plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
        
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
        
        # return values in {self.latexmu}m
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
        plt.savefig(outputFileName,
                    #This is simple recomendation for publication plots
                    dpi=1000, 
                    # Plot will be occupy a maximum of available space
                    bbox_inches='tight')
        plt.close()

        return

class cycleComparator(comparator):

    def loadPerfectDetectorOverlaps(self, fileName):
        self.overlaps = mi.loadMatrices(fileName, False)

    def loadSensorAlignerOverlapMatrices(self, filename):
        self.overlapMatrices = mi.loadMatrices(filename)

    def calcCyclicMatrix(self, overlapIDs):
        result = np.identity(4)
        for overlapID in overlapIDs:
            result = result @ self.overlapMatrices[overlapID]
        return result

    # use dictionary for now, loead from config file later!
    def getCycleTuple(self, smallOverlap):
        masterDict = {
            '0': [0,1,2],       # 0to5
            '1': [0,1,2],       # 3to8
            
            '2': [0,1,2],       # 4to9
            '3': [0,1,2],       # 3to6
            '4': [0,1,2],       # 1to8
            '5': [0,1,2],       # 2to8
            '6': [0,1,2],       # 2to9
            '7': [0,1,2],       # 3to7  
            '8': [0,1,2],       # 4to7
        }
        return masterDict[smallOverlap]


    # TODO: implement cyclic matrices check!
    def prepareValues(self):
        # TODO: read misalign matrices, calculate cyclic matrices for all modules (10 per Module, 40 Modules), store result matrices  
        self.resultArray = np.array((400,3))

        #TODO: for all modules:
            # for 10 cyclic cases
                # get corresponding overlapIDs as tuple
                # give tuple to function and get matrix

        for path in self.overlapMatrices:
            print(f'self.overlapMatrices[path]')


    def histValues(self, fileName):
        # call function from base class
        self.makeHist('Cyclic Residuals', 'x label', 'y label')
        self.saveHist('testFile.pdf')
    pass

class combinedComparator(comparator):

    def histValues(self, values):

        muX = np.round(np.average(values[:,0]), 2)
        sigX = np.round(np.std(values[:,0]), 2)

        muY = np.round(np.average(values[:,1]), 2)
        sigY = np.round(np.std(values[:,1]), 2)
       
        muZ = np.round(np.average(values[:,2]), 2)
        sigZ = np.round(np.std(values[:,2]), 2)

        # plot difference hit array
        fig = plt.figure()
        fig.set_size_inches(8/2.54, 5/2.54) 

        #fig.subplots_adjust(wspace=0.05)
        #fig.tight_layout(rect=[0.5, 0.03, 1, 0.45])
        histA = fig.add_subplot(1, 1, 1)
        
        # bucketLabels = [f'dx, {self.latexmu}x={muX}, {self.latexsigma}x={sigX}', f'dy, {self.latexmu}y={muY}, {self.latexsigma}y={sigY}', f'dz, {self.latexmu}z={muZ}, {self.latexsigma} z={sigZ}']
        bucketLabels = [f'{self.latexsigma}x={sigX}{self.latexmu}m', f'{self.latexsigma}y={sigY}{self.latexmu}m', f'{self.latexsigma} z={sigZ}']

        kwargs = dict(histtype='stepfilled', alpha=0.75, bins=50, label=bucketLabels, color=self.colors[:2])
        histA.hist(values[...,:2], **kwargs)

        histA.set_title('Sensor Alignment Residuals')
        histA.set_xlabel(f'd [{self.latexmu}m]')
        histA.set_ylabel('count')

        handles, labels = plt.gca().get_legend_handles_labels()
        order = [1,0]
        plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order])

        #You must select the correct size of the plot in advance

        return fig

    def saveHistogram(self, outputFileName):

        if self.alignerResults is None:
            raise Exception(f'Aligner results not found! Skipping...')
        if self.idealDetectorMatrices is None:
            raise Exception(f'Ideal Detector Matrices not found! Skipping...')
        if self.misalignMatrices is None:
            raise Exception(f'Design Misalignments not found! Skipping...')

        Path(outputFileName).parent.mkdir(parents=True, exist_ok=True)

        differences = np.empty((0,3))

        for p in self.alignerResults:
            # check if this path is for a sensor!
            if 'sensor' not in p or 'sensor_0' in p or 'sensor_1' in p:
                continue
            try:
                matResult = self.alignerResults[p]
                matMisalign = self.misalignMatrices[p]

                # return values in {self.latexmu}m
                dMat = (matResult - matMisalign)*1e4
                values = np.array([dMat[0,3], dMat[1,3], dMat[2,3]]).reshape(1,3)

                differences = np.append(differences, values, axis=0)
            except:
                matResult = self.alignerResults[p]
                matMisalign = np.identity(4)

                # return values in {self.latexmu}m
                dMat = (matResult - matMisalign)*1e4
                values = np.array([dMat[0,3], dMat[1,3], dMat[2,3]]).reshape(1,3)

                differences = np.append(differences, values, axis=0)

        self.histValues(differences)
        plt.savefig(outputFileName,
                    #This is simple recomendation for publication plots
                    dpi=1000, 
                    # Plot will be occupy a maximum of available space
                    bbox_inches='tight')
        plt.close()

        return
