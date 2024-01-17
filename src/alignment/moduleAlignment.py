#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Performs sensor alignment using the ICP algorithm.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np

from src.alignment.moduleAlignCorridorFitter import CorridorFitter
from src.util.bestFitTransform import best_fit_transform
from src.util.matrix import baseTransform, loadMatrices, saveMatrices


class ModuleAligner:
    # set these before alignment
    anchorPoints: Optional[dict] = None  # Must be set via setAnchorPoints()!
    avgMisalignments: Optional[dict] = None  # Must be set via setExternalMatrices()!

    # default, need no change
    preTransform = True
    iterations = 5  # max number of iterations the module aligner will do
    idealDetectorMatrices = loadMatrices("config/detectorMatricesIdeal.json")
    npyOutputDir = Path("temp/sectorRecos")
    debug = False

    # load geometryString -> sectorID mapping
    with open("config/sectorPaths.json") as f:
        allModulePaths = json.load(f)

    # ------------------- helper functions -------------------

    #  quantile cut on track direction
    def directionQuantileCut(
        self, inputTrackArray: np.ndarray, cutPercent=2
    ) -> np.ndarray:
        """
        Cuts tracks based on their direction. The cut is done in the following way:
        1. Calculate the center of mass of all track directions
        2. Shift all track directions by the center of mass
        3. Calculate the distance of all tracks to the center of mass
        4. Cut the tracks with the highest distance (cutPercent% of all tracks)
        """

        # calculate center of mass of track directions
        com = np.average(inputTrackArray[:, 1, :3], axis=0)

        # shift newhit2 by com of differences
        newhit2 = inputTrackArray[:, 1, :3] - com
        newDist = np.power(newhit2[:, 0], 2) + np.power(newhit2[:, 1], 2)

        cut = int(len(newhit2) * (cutPercent / 100.0))
        inputTrackArray = inputTrackArray[newDist.argsort()]
        inputTrackArray = inputTrackArray[:-cut]
        return inputTrackArray

    # quantile cut on reco-track distance
    def dynamicRecoTrackDistanceCut(
        self, inputTrackArray: np.ndarray, cutPercent=2
    ) -> np.ndarray:
        """
        Cuts tracks based on their distance to the reco hits. The cut is done in the following way:
        1. Calculate the distance of all tracks to the reco hits
        2. Cut the tracks with the highest distance (cutPercent% of all tracks)
        """

        # don't worry, numpy arrays are copied by reference
        tempTracks = inputTrackArray

        for i in range(4):
            trackPosArr = tempTracks[:, 0, :3]
            trackDirArr = tempTracks[:, 1, :3]
            recoPosArr = tempTracks[:, 2 + i, :3]

            # norm momentum vectors, this is important for the distance formula!
            trackDirArr = (
                trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T
            )

            # vectorized distance calculation
            tempV1 = trackPosArr - recoPosArr
            tempV2 = (tempV1 * trackDirArr).sum(axis=1)
            dVec = tempV1 - tempV2[np.newaxis].T * trackDirArr
            dVec = dVec[:, :2]
            newDist = np.power(dVec[:, 0], 2) + np.power(dVec[:, 1], 2)

            # cut
            cut = int(len(dVec) * (cutPercent / 100.0))
            tempTracks = tempTracks[newDist.argsort()]
            tempTracks = tempTracks[:-cut]

        return tempTracks

    # ------------------- main functions -------------------
    def getMatrix(
        self, trackPositions: np.ndarray, recoPositions: np.ndarray, preTransform=False
    ) -> np.ndarray:
        """
        Calculates the alignment matrix between two sets of points,
        here track positions on the detector planes and reco positions.
        """

        # use 2D, use only in LMD local!
        if preTransform:
            T, _, _ = best_fit_transform(
                trackPositions[..., :2], recoPositions[..., :2]
            )

            # homogenize
            resultMat = np.identity(4)
            resultMat[:2, :2] = T[:2, :2]
            resultMat[:2, 3] = T[:2, 2]
            return resultMat

        else:
            T, _, _ = best_fit_transform(trackPositions, recoPositions)
            return T

    def alignSectorICPWorker(self, recoNumpyPaht: Path, sector: int, maxNoTrks=40000) -> dict:
        """
        Aligns a sector using a slimmed down ICP algorithm.
        Returns a dictionary of alignment matrices for the modules.
        """
        npFile = Path(f"sectorID-{sector}.npy")
        sectorRecos = np.load(recoNumpyPaht / npFile)

        # get relevant module paths
        modulePaths = self.allModulePaths[str(sector)]

        # make 4x4 matrices to module positions
        moduleMatrices = np.zeros((4, 4, 4))
        for i in range(len(modulePaths)):
            path = modulePaths[i]
            moduleMatrices[i] = np.array(self.idealDetectorMatrices[path])

        # * use average misalignment
        averageShift = self.avgMisalignments[str(sector)]

        # assing given tracks to internal variable
        newTracks = sectorRecos

        # use only N tracks:
        if maxNoTrks > 0:
            newTracks = newTracks[:maxNoTrks]

        sectorString = str(sector)
        # transform all recos to LMD local
        if self.preTransform:
            matToLMD = np.linalg.inv(
                np.array(self.idealDetectorMatrices["/cave_1/lmd_root_0"])
            )
            for i in range(4):
                newTracks[:, i + 2] = (matToLMD @ newTracks[:, i + 2].T).T

        # transform anchorPoints to PANDA global
        else:
            matFromLMD = np.array(self.idealDetectorMatriceses["/cave_1/lmd_root_0"])
            self.anchorPoints[sectorString] = (
                matFromLMD @ self.anchorPoints[sectorString]
            )

        if self.debug:
            print("==================================================")
            print(f"        module aligner for sector {sector}")
            print("==================================================")

            print(f"number of tracks: {len(newTracks)}")
            print(f"anchor point: {self.anchorPoints[sectorString]}")

        # do a first track fit, otherwise we have no starting tracks
        recos = newTracks[:, 2:6]
        corrFitter = CorridorFitter(recos)
        corrFitter.useAnchorPoint(self.anchorPoints[sectorString][:3])
        resultTracks = corrFitter.fitTracksSVD()

        # update current tracks
        newTracks[:, 0, :3] = resultTracks[:, 0]
        newTracks[:, 1, :3] = resultTracks[:, 1]

        # prepare total matrices
        totalMatrices = np.zeros((4, 4, 4))
        for i in range(4):
            totalMatrices[i] = np.identity(4)

        # * =========== iterate cuts and calculation
        for iIteration in range(self.iterations):
            # print(f"running iteration {iIteration}, {len(newTracks)} tracks remaining...")

            newTracks = self.dynamicRecoTrackDistanceCut(newTracks)
            # 4 planes per sector
            for i in range(4):
                trackPosArr = newTracks[:, 0, :3]
                trackDirArr = newTracks[:, 1, :3]
                recoPosArr = newTracks[:, 2 + i, :3]

                # norm momentum vectors, this is important for the distance formula!
                trackDirArr = (
                    trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T
                )

                # vectorized distance calculation
                tempV1 = trackPosArr - recoPosArr
                tempV2 = (tempV1 * trackDirArr).sum(axis=1)
                dVec = tempV1 - tempV2[np.newaxis].T * trackDirArr

                # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
                pIntersection = recoPosArr + dVec

                # we want FROM tracks TO recos
                T0inv = self.getMatrix(recoPosArr, pIntersection, self.preTransform)
                totalMatrices[i] = T0inv @ totalMatrices[i]

                # transform recos, MAKE SURE THEY ARE SORTED
                newTracks[:, i + 2] = (T0inv @ newTracks[:, i + 2].T).T

            # direction cut again
            if iIteration < 3:
                newTracks = self.directionQuantileCut(newTracks, 1)

            # do track fit
            corrFitter = CorridorFitter(newTracks[:, 2:6])
            resultTracks = corrFitter.fitTracksSVD()

            # update current tracks
            newTracks[:, 0, :3] = resultTracks[:, 0]
            newTracks[:, 1, :3] = resultTracks[:, 1]

        # * =========== store matrices
        result = {}

        # transform the alignment matrices back INTO the system of their respective module
        # since that's where FAIRROOT applies them
        for i in range(4):
            # ideal module matrices!
            toModMat = moduleMatrices[i]

            if self.preTransform:
                totalMatrices[i] = baseTransform(
                    totalMatrices[i], np.linalg.inv(matToLMD)
                )
                totalMatrices[i] = baseTransform(
                    totalMatrices[i], np.linalg.inv(toModMat)
                )
            else:
                totalMatrices[i] = baseTransform(
                    totalMatrices[i], np.linalg.inv(toModMat)
                )

            # add average shift (external measurement)
            totalMatrices[i] = totalMatrices[i] @ averageShift
            result[modulePaths[i]] = totalMatrices[i]

        if self.debug:
            print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            print(f"        module aligner for sector {sector} done!         ")
            print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        
        return result

    def alignSectorWorker(self, reocNumpyFile: Path, sector: int) -> dict:
        pass

    def alignSectors(self) -> None:
        """
        Aligns all sectors using the ICP algorithm.
        Stores the alignment matrices in self.alignmentMatices.
        """

        # actually run the aligner!
        self.alignmentMatices = {}

        # translate the reco hits to format for module Aligner
        if self.debug:
            for iSector in range(10):
                print(f"aligning sector {iSector}...")
                self.alignmentMatices |= self.alignSectorICPWorker(self.npyOutputDir, iSector)
        else:
            print("aligning sectors multithreaded...")
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self.alignSectorICPWorker, self.npyOutputDir, iSector) for iSector in range(10)]

                # Collect the results as they complete
                for future in as_completed(futures):
                    self.alignmentMatices |= future.result()

    def setExternalMatrices(self, externalMatricesFileName) -> None:
        """
        Sets the average misalignments for the modules.
        """
        self.avgMisalignments = loadMatrices(externalMatricesFileName)

    def setAnchorPoints(self, anchorPointFile) -> None:
        """
        Sets the anchor points for the modules.
        """

        # load anchor points
        with open(anchorPointFile) as f:
            self.anchorPoints = json.load(f)

            # check if this is the new version of the anchorpoint format
            if "version" in self.anchorPoints:
                if self.anchorPoints["version"] == 1:
                    # if yes, make every entry a homogeneous point
                    for key in self.anchorPoints:
                        # well except the version string of course
                        if key != "version":
                            self.anchorPoints[key] = [0, 0, self.anchorPoints[key], 1]

            # the old version already contains homogeneous points
            else:
                pass

    def alignModules(
        self,
        LumiRecoFilesPath,
        outputMatixName="matrices/100u-case-1/EXAMPLE-moduleAlignmentMatrices.json",
    ) -> None:
        """
        Aligns all modules using the ICP algorithm. Stores the alignment matrices in outputMatixName.
        """

        if self.anchorPoints is None:
            raise Exception("ERROR! Please set anchor points before alignment!")
        if self.avgMisalignments is None:
            raise Exception("ERROR! Please set external matrices before alignment!")

        if self.debug:
            from src.alignment.readers.recoCSVReader import RecoCSVReader
            reader = RecoCSVReader()
            reader.sortCSVtoNumpy(LumiRecoFilesPath)

        else:
            from src.alignment.readers.lumiRecoReader import LumiRecoReader
            reader = LumiRecoReader()
            reader.sortRecoHitsFromRootFilesToNumpy(LumiRecoFilesPath)

        # align sectors
        self.alignSectors()

        # save matrices
        saveMatrices(self.alignmentMatices, outputMatixName)


if __name__ == "__main__":
    print(
        "Cannot be run directly. Please see the example alignment campaigns in jupyter/alignmentCampaign.ipynb."
    )
