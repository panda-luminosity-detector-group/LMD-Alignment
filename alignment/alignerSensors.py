#!/usr/bin/env python3

from alignment.sensors.alignmentMatrixCombiner import alignmentMatrixCombiner
from alignment.sensors.compareWithDesignMatrices import idealCompare
from alignment.sensors.hitPairSorter import hitPairSorter
from alignment.sensors.sensorMatrixFinder import sensorMatrixFinder

from detail.LMDRunConfig import LMDRunConfig

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

import collections
import concurrent
import json
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This aligner needs a LMDRunConfig object. It will then:

- read Lumi_Pairs_*.root files
- sort to numpy files
- read all numpy files
- find overlap matrices
- compute misalignment matrices from overlap matrices
- save them as deviation matrices to json

Info: all positional vectors are row-major! This aligner also need info about the geometry
to transform sensor-local matrices to PANDA global:

- detectorOverlapsIdeal.json | containing all design matrices of the Luminosity detector 

TODO: save overlap matrices to json file!
TODO: save log, how many pairs were available for each overlap?
"""


class alignerSensors:

    def __init__(self):
        self.idealOverlapsPath = Path('input') / Path('detectorOverlapsIdeal.json')
        self.idealDetectorMatrixPath = Path('input') / Path('detectorMatricesIdeal.json')
        self.availableOverlapIDs = self.getOverlapsFromJSON()
        self.overlapMatrices = {}                                                           # dictionary overlapID: matrix
        self.lock = Lock()
        pass

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    # this retrieves overlapIDs from the json file
    def getOverlapsFromJSON(self):
        overlapIDs = []
        with open(self.idealOverlapsPath) as overlapsFile:
            idealOverlaps = json.load(overlapsFile)

        for overlapID in idealOverlaps:
            overlapIDs.append(overlapID)

        return overlapIDs

    def sortPairs(self):
        pairSourcePath = Path(self.config.pathTrksQA())
        numpyPairPath = pairSourcePath / Path('npPairs')

        sorter = hitPairSorter(pairSourcePath, numpyPairPath)
        sorter.availableOverlapIDs = self.availableOverlapIDs
        
        sorter.sortAll()

    def findSingleMatrix(self, overlapID, numpyPath, idealOverlapsPath):

        matrixFinder = sensorMatrixFinder(overlapID)

        with open(idealOverlapsPath, 'r') as f:
            idealMatrices = json.load(f)

        matrixFinder.idealMatrices = idealMatrices
        matrixFinder.readNumpyFiles(numpyPath)
        
        matrixFinder.findMatrix()
        
        matrix = matrixFinder.getOverlapMatrix()

        # python ditionaries might be thread safe, but just in case
        with self.lock:
            self.overlapMatrices[overlapID] = matrix

    def findMatrices(self):
        # setup paths
        numpyPath = self.config.pathTrksQA() / Path('npPairs')

        if self.config.useDebug:
            print(f'Finding matrices single-threaded!')
            for overlapID in self.availableOverlapIDs:
                self.findSingleMatrix(overlapID, numpyPath, self.idealOverlapsPath)

        else:
            # TODO: automatically set to something reasonable
            maxThreads = 16
            print('Waiting for all Sensor Aligners...')

            with concurrent.futures.ThreadPoolExecutor(max_workers=maxThreads) as executor:
                for overlapID in self.availableOverlapIDs:
                    executor.submit(self.findSingleMatrix, overlapID, numpyPath, self.idealOverlapsPath)

            # wait for all threads, this might not even be needed
            executor.shutdown(wait=True)
    """
    This function histograms the found ICP matrices vs actual simulation matrices
    """
    def histCompareResults(self):

        comparer = idealCompare(self.overlapMatrices)
        comparer.loadPerfectDetectorOverlaps(self.idealOverlapsPath)
        comparer.loadDesignMisalignmentMatrices(self.config.pathMisMatrix())

        # TODO: better filename
        histogramFileName = Path('output') / Path(self.config.misalignType)
        comparer.saveHistogram(histogramFileName)

    def combineAlignmentMatrices(self):

        sortedMatrices = collections.defaultdict(dict)

        with open(self.idealOverlapsPath) as overlapsFile:
            idealOverlaps = json.load(overlapsFile)

        # sort overlap matrices by module they are on
        for overlapID in self.availableOverlapIDs:
            modulePath = idealOverlaps[overlapID]['pathModule']
            sortedMatrices[modulePath].update({overlapID: self.overlapMatrices[overlapID]})

        print(f'found {len(sortedMatrices)}, modules, should be 40.')

        with open(self.idealDetectorMatrixPath) as idealMatricesFile:
            idealMatrices = json.load(idealMatricesFile)

        for modulePath in sortedMatrices:
            combiner = alignmentMatrixCombiner(modulePath)
            
            combiner.setOverlapMatrices(sortedMatrices[modulePath])
            combiner.setIdealDetectorMatrices(idealMatrices)

            combiner.combineMatrices()
            break


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
