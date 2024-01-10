#!/usr/bin/env python3

import json
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

from src.alignment.sensorAlignmentMatixCombiner import alignmentMatrixCombiner
from src.util.bestFitTransform import best_fit_transform
from src.util.matrix import loadMatrices, saveMatrices

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Performs sensor alignment using the ICP algorithm.
"""

class SensorAligner:
    idealDetectorMatrices = loadMatrices("config/detectorMatricesIdeal.json")
    availableOverlapIDs = range(7)
    availableModuleIDs = range(40)
    overlapMatrices = {}
    sensorAlignMatrices = {}
    externalMatrices = loadMatrices(
        "matrices/100u-case-1/externalMatrices-sensors.json"
    )
    npyOutputDir = Path("temp/npPairs")
    use2D = True

    with open("config/moduleIDtoModulePath.json") as f:
        moduleIdToModulePath = json.load(f)

    def sortPairs(self, rootFilePath: Path):
        """
        Sorts the pairs from root files to numpy files.

        Returns:
            None
        """
        print("Sorting pairs from root files to numpy files. This may take a while.")
        rootFileWildcard = "Lumi_Pairs_*.root:pndsim"

        runIndex = 0
        maxNoOfFiles = 50

        # delete old files
        if Path(self.npyOutputDir).exists():
            for file in self.npyOutputDir.glob("*.npy"):
                file.unlink()

        if not Path(self.npyOutputDir).exists():
            Path(self.npyOutputDir).mkdir(parents=True)

        for arrays in uproot.iterate(
            rootFilePath + rootFileWildcard,
            [
                "PndLmdHitPair._moduleID",
                "PndLmdHitPair._overlapID",
                "PndLmdHitPair._hit1",
                "PndLmdHitPair._hit2",
            ],
            # library="np", # DONT use numpy yet, we need the awkward array for the TVector3
            allow_missing=True,  # some files may be empty, skip those):
        ):
            runIndex += 1

            # some evvents have no hits, but thats not a problem
            # after the arrays are flattened, those empty events
            # simply disappear
            moduleIDs = np.array(ak.flatten(arrays["PndLmdHitPair._moduleID"]))
            overlapIDs = np.array(ak.flatten(arrays["PndLmdHitPair._overlapID"]))
            hit1x = ak.flatten(arrays["PndLmdHitPair._hit1"].fX)
            hit1y = ak.flatten(arrays["PndLmdHitPair._hit1"].fY)
            hit1z = ak.flatten(arrays["PndLmdHitPair._hit1"].fZ)
            hit2x = ak.flatten(arrays["PndLmdHitPair._hit2"].fX)
            hit2y = ak.flatten(arrays["PndLmdHitPair._hit2"].fY)
            hit2z = ak.flatten(arrays["PndLmdHitPair._hit2"].fZ)

            arr = np.array(
                (moduleIDs, hit1x, hit1y, hit1z, hit2x, hit2y, hit2z, overlapIDs)
            ).T

            for moduleID in self.availableModuleIDs:
                mask = arr[:, 0] == moduleID
                thisOverlapsArray = arr[mask][:, 1:]

                # read array from disk
                fileName = f"{self.npyOutputDir}/pairs-modID-{moduleID}.npy"

                try:
                    oldContent = np.load(fileName)
                # first run, file not already present
                except FileNotFoundError:
                    oldContent = np.empty((0, 7))

                # merge
                newContent = np.concatenate((oldContent, thisOverlapsArray))

                # write back to disk
                np.save(file=fileName, arr=newContent, allow_pickle=False)

            if runIndex == maxNoOfFiles:
                break

    def dynamicCut(self, hitPairs, cutPercent=2):
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

    def findMatrix(self, PairData, thisModule):
        # apply dynamic cut
        PairData = self.dynamicCut(PairData, 2)

        # if idealOverlapInfos is None or PairData is None:
        #     raise Exception(f"Error! Please load ideal detector matrices and numpy pairs!")

        # if len(idealDetectorMatrices) < 1:
        #     raise Exception("ERROR! Please set ideal detector matrices!")

        # Make C a homogeneous representation of hits1 and hits2
        hit1H = np.ones((len(PairData), 4))
        hit1H[:, 0:3] = PairData[:, :3]

        hit2H = np.ones((len(PairData), 4))
        hit2H[:, 0:3] = PairData[:, 3:6]

        # Attention! Always transform to module-local system,
        # otherwise numerical errors will make the ICP matrices unusable!
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

    def findAllOverlapMatrices(self):
        for moduleID in self.availableModuleIDs:
            pairsOnModule = np.load(f"{self.npyOutputDir}/pairs-modID-{moduleID}.npy")

            # print(f"Processing module {moduleID}, loading file {npyOutputDir}/pairs-modID-{moduleID}.npy")

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

    def combineMatricesOnAllModules(self):
        for moduleID in self.availableModuleIDs:
            combiner = alignmentMatrixCombiner(moduleID, self.moduleIdToModulePath[str(moduleID)])
            combiner.setIdealDetectorMatrices(self.idealDetectorMatrices)
            combiner.setOverlapMatrices(self.overlapMatrices)
            combiner.setExternallyMeasuredMatrices(self.externalMatrices)
            combiner.combineMatrices()
            self.sensorAlignMatrices.update(combiner.getAlignmentMatrices())

    def alignSensors(
        self,
        PairROOTFilesPath,
        outputMatixName="matrices/100u-case-1/EXAMPLE-sensorAlignmentMatrices.json",
    ):
        # sort hit pairs from root files to npy files
        # self.sortPairs(PairROOTFilesPath)

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
