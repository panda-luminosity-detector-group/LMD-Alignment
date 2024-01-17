#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Optional

import numpy as np

from src.alignment.readers.lumiPairReader import LumiPairReader
from src.alignment.sensorAlignmentMatixCombiner import alignmentMatrixCombiner
from src.util.bestFitTransform import best_fit_transform
from src.util.matrix import loadMatrices, saveMatrices

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Performs sensor alignment using the ICP algorithm.
"""


class SensorAligner:
    # must be set before alignment!
    externalMatrices: Optional[dict] = None

    # default values, no need to change
    availableOverlapIDs = range(7)
    availableModuleIDs = range(40)
    npyOutputDir = Path("temp/npPairs")
    use2D = True
    idealDetectorMatrices = loadMatrices("config/detectorMatricesIdeal.json")

    # placeholders, will be filled by the methods
    overlapMatrices = {}
    alignmentMatrices = {}
    sensorAlignMatrices = {}

    with open("config/moduleIDtoModulePath.json") as f:
        moduleIdToModulePath = json.load(f)

    def quantileCut(self, hitPairs: np.array, cutPercent=2) -> np.array:
        """
        Applies a quantile cut to the hit pairs.
        """

        if cutPercent == 0:
            return hitPairs

        # calculate center of mass of differences
        dRaw = hitPairs[:, 3:6] - hitPairs[:, :3]
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = hitPairs[:, 3:6] - com

        # calculate new distance for cut
        dRaw = newhit2 - hitPairs[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        # sort by distance and cut some percent from end (discard outliers)
        cut = int(len(hitPairs) * cutPercent / 100.0)
        # sort by new distance
        hitPairs = hitPairs[newDist.argsort()]
        # cut off largest distances, NOT lowest
        hitPairs = hitPairs[:-cut]

        return hitPairs

    def findMatrix(self, PairData: np.array, thisModule: int) -> np.array:
        """
        Finds the overlap matrix for a given module and np array with pair data.
        """

        # apply dynamic cut
        PairData = self.quantileCut(PairData, 2)

        # Make homogeneous representations of hits1 and hits2
        hit1H = np.ones((len(PairData), 4))
        hit1H[:, 0:3] = PairData[:, :3]

        hit2H = np.ones((len(PairData), 4))
        hit2H[:, 0:3] = PairData[:, 3:6]

        # Attention! Always transform to module-local system,
        # otherwise numerical errors will make the ICP matrices unstable!
        # (because z is at 11m, while x is 30cm and y is 0)
        # also, we're ignoring z distance, which we can not do if we're in
        # PND global, due to the 40mrad rotation.
        transformToLocalSensor = True
        if transformToLocalSensor:
            icpDimension = 2
            # get matrix lmd to module
            modulePath = self.moduleIdToModulePath[str(thisModule)]
            matToModule = self.idealDetectorMatrices[modulePath]

            # invert to transform pairs from lmd to sensor
            toModInv = np.linalg.inv(matToModule)

            # Transform vectors (remember, C and D are vectors of vectors = matrices!)
            hit1T = np.matmul(toModInv, hit1H.T).T
            hit2T = np.matmul(toModInv, hit2H.T).T

        else:
            print("WARNING! ICP working in Panda global, NOT sensor local.")
            print("This will likely produce wrong overlap matrices,")
            print("If the hit points are not transformed beforehand!")
            hit1T = hit1H
            hit2T = hit2H

        if self.use2D:
            icpDimension = 2
            # make 2D versions for ICP
            A = hit1T[:, :2]
            B = hit2T[:, :2]
        else:
            icpDimension = 3
            # make 3D versions for ICP
            A = hit1T[:, :3]
            B = hit2T[:, :3]

        # find ideal transformation
        T, _, _ = best_fit_transform(A, B)

        # print(f'this is T for {moduleIdToModulePath[str(thisModule)]}:\n{T}')

        # copy 3x3 Matrix to 4x4 Matrix
        if icpDimension == 2:
            M = np.identity(4)
            M[:2, :2] = T[:2, :2]
            M[:2, 3] = T[:2, 2]
            thisOverlapMatrix = M

        elif icpDimension == 3:
            thisOverlapMatrix = T

        # transformResultToPND = True
        if transformToLocalSensor:
            # remember, matToModule goes from Pnd->Module
            # base trafo is T A T^-1,
            # T = Pnd->Module
            thisOverlapMatrix = (
                (matToModule) @ thisOverlapMatrix @ np.linalg.inv(matToModule)
            )
        return thisOverlapMatrix

    def findAllOverlapMatrices(self) -> None:
        """
        Finds all overlap matrices and saves them to self.overlapMatrices.
        """
        for moduleID in self.availableModuleIDs:
            pairsOnModule = np.load(f"{self.npyOutputDir}/pairs-modID-{moduleID}.npy")

            self.overlapMatrices[str(moduleID)] = {}
            for overlapID in self.availableOverlapIDs:
                # mask for overlapID
                mask = pairsOnModule[:, 6] == overlapID

                # ignore distance, we don't need it anymore
                pairsOnOverlap = pairsOnModule[mask][:, :6]

                # make dict with overlap matrices
                self.overlapMatrices[str(moduleID)][str(overlapID)] = self.findMatrix(
                    pairsOnOverlap, moduleID
                )

    def combineMatricesOnAllModules(self) -> None:
        """
        Combines all overlap matrices to sensor alignment matrices and saves them to self.sensorAlignMatrices.
        """
        for moduleID in self.availableModuleIDs:
            combiner = alignmentMatrixCombiner(
                moduleID, self.moduleIdToModulePath[str(moduleID)]
            )
            combiner.setIdealDetectorMatrices(self.idealDetectorMatrices)
            combiner.setOverlapMatrices(self.overlapMatrices)
            if self.externalMatrices is not None:
                combiner.setExternallyMeasuredMatrices(self.externalMatrices)
            combiner.combineMatrices()
            self.sensorAlignMatrices.update(combiner.getAlignmentMatrices())

    def setExternalMatrices(self, externalMatricesPath) -> None:
        """
        Sets the external matrices to use for alignment.
        """
        self.externalMatrices = loadMatrices(externalMatricesPath)

    def alignSensors(
        self,
        PairROOTFilesPath: Path,
        outputMatixName="matrices/100u-case-1/EXAMPLE-sensorAlignmentMatrices.json",
    ) -> None:
        """
        Performs sensor alignment, storing alignment matrices to specified destination.
        """

        # sort hit pairs from root files to npy files
        reader = LumiPairReader()
        reader.sortPairs(PairROOTFilesPath)

        # then find all overlap matrices
        self.findAllOverlapMatrices()

        # and combone them to sensor alignment matrices
        self.combineMatricesOnAllModules()

        # lastly, save the matrices
        saveMatrices(self.sensorAlignMatrices, outputMatixName)

        print("Sensor alignment done!")


if __name__ == "__main__":
    print(
        "Cannot be run directly. Please see the example alignment campaigns in jupyter/alignmentCampaign.ipynb."
    )
