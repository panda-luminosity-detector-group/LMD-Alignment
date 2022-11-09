#!/usr/bin/env python3

from alignment.sensors.alignmentMatrixCombiner import alignmentMatrixCombiner
from alignment.sensors.hitPairSorter import hitPairSorter
from alignment.sensors.sensorMatrixFinder import sensorMatrixFinder

from detail.LMDRunConfig import LMDRunConfig

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

import collections
import concurrent
import detail.matrixInterface as mi
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

TODO: save log, how many pairs were available for each overlap?
"""


class alignerSensors:
    def __init__(self):
        self.idealOverlapsPath = Path("input") / Path("detectorOverlapsIdeal.json")
        self.idealOverlapInfos = mi.loadMatrices(self.idealOverlapsPath, False)

        self.idealDetectorMatrixPath = Path("input") / Path(
            "detectorMatricesIdeal.json"
        )
        self.idealDetectorMatrices = mi.loadMatrices(self.idealDetectorMatrixPath)

        self.availableOverlapIDs = self.getOverlapsFromJSON()
        self.overlapMatrices = {}
        self.alignmentMatrices = {}
        self.maxPairs = 6e5
        self.dCut = 1.0  # dictionary overlapID: matrix
        self.lock = Lock()

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    def loadExternalMatrices(self, fileName):
        self.externalMatrices = mi.loadMatrices(fileName)

    # this retrieves overlapIDs from the json file
    def getOverlapsFromJSON(self):
        overlapIDs = []

        for overlapID in self.idealOverlapInfos:
            overlapIDs.append(overlapID)

        return overlapIDs

    def sortPairs(self):
        pairSourcePath = Path(self.config.pathTrksQA())
        numpyPairPath = pairSourcePath / Path("npPairs")

        sorter = hitPairSorter(pairSourcePath, numpyPairPath)
        sorter.availableOverlapIDs = self.availableOverlapIDs

        sorter.sortAll()

    def findSingleMatrix(self, overlapID, numpyPath):

        matrixFinder = sensorMatrixFinder(overlapID)
        matrixFinder.maxPairs = self.maxPairs
        matrixFinder.idealOverlapInfos = self.idealOverlapInfos
        matrixFinder.idealDetectorMatrices = self.idealDetectorMatrices
        matrixFinder.dCut = self.dCut
        matrixFinder.readNumpyFiles(numpyPath)
        matrixFinder.findMatrix()

        matrix = matrixFinder.getOverlapMatrix()

        # python dictionaries might be thread safe, but just in case
        with self.lock:
            self.overlapMatrices[overlapID] = matrix

    def findMatrices(self, pairPath=None, nPairs=0):
        # setup paths
        if pairPath is None:
            numpyPath = self.config.pathTrksQA() / Path("npPairs")
        else:
            numpyPath = Path(pairPath)

        if (
            self.config.useDebug or True
        ):  # for multiseed, change this back for single scenarios!
            print(f"Finding matrices single-threaded!")
            for overlapID in self.availableOverlapIDs:
                self.findSingleMatrix(overlapID, numpyPath)

        else:
            maxThreads = 16
            print(
                f"Waiting for all Sensor Aligners, using {self.maxPairs} pairs on each sensor..."
            )

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=maxThreads
            ) as executor:
                for overlapID in self.availableOverlapIDs:
                    executor.submit(self.findSingleMatrix, overlapID, numpyPath)

            # wait for all threads, this might not even be needed
            executor.shutdown(wait=True)

    def combineAlignmentMatrices(self):

        if self.externalMatrices == None:
            raise Exception("Error! Please set externally measured matrices!")

        # these are important! the combiner MUST only get the overlap matrices
        sortedMatrices = collections.defaultdict(dict)
        sortedOverlaps = collections.defaultdict(dict)

        if len(self.overlapMatrices) < 360:
            raise Exception(f"Error! Not all overlap matrices could be found!")

        # sort overlap matrices by module they are on
        for overlapID in self.availableOverlapIDs:
            modulePath = self.idealOverlapInfos[overlapID]["pathModule"]
            sortedMatrices[modulePath].update(
                {overlapID: self.overlapMatrices[overlapID]}
            )

        print(f"found {len(sortedMatrices)}, modules, should be 40.")

        # sort overlapInfos to dict by module path
        for modulePath in sortedMatrices:
            for overlapID in self.idealOverlapInfos:
                if self.idealOverlapInfos[overlapID]["pathModule"] == modulePath:
                    sortedOverlaps[modulePath].update(
                        {overlapID: self.idealOverlapInfos[overlapID]}
                    )

        idealMatrices = mi.loadMatrices(self.idealDetectorMatrixPath)

        for modulePath in sortedMatrices:
            combiner = alignmentMatrixCombiner(modulePath)

            combiner.setIdealDetectorMatrices(idealMatrices)
            combiner.setOverlapMatrices(sortedMatrices[modulePath])
            combiner.setExternallyMeasuredMatrices(self.externalMatrices)

            combiner.combineMatrices()

            resultMatrices = combiner.getAlignmentMatrices()
            self.alignmentMatrices.update(resultMatrices)

        print(
            f"combined for all sensors on all modules. length: {len(self.alignmentMatrices)}"
        )

    def saveOverlapMatrices(self, outputFile):
        mi.saveMatrices(self.overlapMatrices, outputFile)

    def saveAlignmentMatrices(self, outputFile):
        mi.saveMatrices(self.alignmentMatrices, outputFile)
