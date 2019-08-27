#!/usr/bin/env python3

from alignment.sensors.alignmentMatrixCombiner import alignmentMatrixCombiner
from alignment.sensors.compareWithDesignMatrices import idealCompare
from alignment.sensors.hitPairSorter import hitPairSorter
from alignment.sensors.sensorMatrixFinder import sensorMatrixFinder

from detail.LMDRunConfig import LMDRunConfig

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

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
        self.availableOverlapIDs = self.createAllOverlaps()
        self.overlapMatrices = {}
        self.lock = Lock()
        pass

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    # TODO: get these somewhere else, maybe even just the ideal detector matrices
    #! FIXME: this will stop working when there are only four sensors on each side!
    def createAllOverlaps(self):
        overlapIDs = []
        for half in range(2):
            for plane in range(4):
                for module in range(5):
                    for overlap in range(9):
                        overlapIDs.append(str(half*1000 + plane*100 + module*10 + overlap))
        return overlapIDs

    def createAllModule

    def sortPairs(self):
        pairSourcePath = Path(self.config.pathTrksQA())
        numpyPairPath = pairSourcePath / Path('npPairs')

        sorter = hitPairSorter(pairSourcePath, numpyPairPath)
        sorter.availableOverlapIDs = self.availableOverlapIDs
        sorter.sortAll()

    def findSingleMatrix(self, overlapID, numpyPath, idealMatricesPath):

        matrixFinder = sensorMatrixFinder(overlapID)

        with open(idealMatricesPath, 'r') as f:
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
        idealMatricesPath = Path('input') / Path('detectorOverlapsIdeal.json')
        numpyPath = self.config.pathTrksQA() / Path('npPairs')

        if self.config.useDebug:
            print(f'Finding matrices single-threaded!')
            for overlapID in self.availableOverlapIDs:
                self.findSingleMatrix(overlapID, numpyPath, idealMatricesPath)

        else:
            # TODO: automatically set to something reasonable
            maxThreads = 16
            print('Waiting for all Sensor Aligners...')

            with concurrent.futures.ThreadPoolExecutor(max_workers=maxThreads) as executor:
                for overlapID in self.availableOverlapIDs:
                    executor.submit(self.findSingleMatrix, overlapID, numpyPath, idealMatricesPath)

            # wait for all threads, this might not even be needed
            executor.shutdown(wait=True)

    def histCompareResults(self):
        idealMatricesPath = Path('input') / Path('detectorOverlapsIdeal.json')
        
        comparer = idealCompare(self.overlapMatrices)
        comparer.loadPerfectDetectorOverlaps(idealMatricesPath)
        comparer.loadDesignMisalignmentMatrices(self.config.pathMisMatrix())
        
        # TODO: better filename
        histogramFileName = Path('output') / Path(self.config.misalignType)
        comparer.saveHistogram(histogramFileName)

    # TODO: implement!
    def combineAlignmentMatrices(self):
        pass


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
