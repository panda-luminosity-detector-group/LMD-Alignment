#!/usr/bin/env python3

# from alignment.modules.sectorContainer import sectorContainer
from alignment.modules.trackFitter import CorridorFitter
from alignment.modules.trackReader import trackReader
from alignment.sensors import icp

import detail.matrixInterface as mi

import concurrent
import numpy as np

import subprocess

from pathlib import Path

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- determine distance from recos to tracks
- move recos with this matrix
- iteratively repeat
"""


class alignerModules:
    def __init__(self):
        self.alignMatrices = {}
        self.reader = trackReader()
        self.iterations = 5
        print(f"reading detector parameters...")
        self.reader.readDetectorParameters()

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        temp.readAnchorPoints(runConfig.moduleAlignAnchorPointFile)
        temp.readAverageMisalignments(runConfig.moduleAlignAvgMisalignFile)
        return temp

    # words cannot describe how ugly this is, but I'm pressed for time and aesthetics wont get me my phd
    def convertRootTracks(self, dataPath, outJsonFile):
        print(f"converting tracks from ROOT files to json file, using these paths:")
        print(f"data path: {dataPath}")
        print(f"out file: {outJsonFile}")
        if not Path(outJsonFile).exists():
            rootArgs = f'convertRootTracks.C("{str(dataPath)}","{str(outJsonFile)}")'
            print(f"Running root -l -q {rootArgs}")
            result = subprocess.run(
                ["root", "-l", "-q", rootArgs],
                cwd="alignment/modules",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )  # I wish himster had python 3.7  ...
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            print(f"Root converter should be done now.")
        else:
            print(f"processed tracks already exist, skipping.")

    def readTracks(self, fileName, isNumpy=False):
        print(f"reading processed tracks file...")
        if not isNumpy:
            self.reader.readTracksFromJson(fileName)
        else:
            self.reader.readTracksFromNPY(fileName)

    def readAnchorPoints(self, fileName):
        self.anchorPoints = mi.loadMatrices(fileName, False)

    def readAverageMisalignments(self, fileName):
        self.avgMisalignments = mi.loadMatrices(fileName)

    def setIterations(self, iterations):
        self.iterations = iterations

    # ? cuts on track x,y direction
    def dynamicTrackCut(self, newTracks, cutPercent=2):
        com = np.average(newTracks[:, 1, :3], axis=0)

        # shift newhit2 by com of differences
        newhit2 = newTracks[:, 1, :3] - com
        newDist = np.power(newhit2[:, 0], 2) + np.power(newhit2[:, 1], 2)

        cut = int(len(newhit2) * (cutPercent / 100.0))
        newTracks = newTracks[newDist.argsort()]
        newTracks = newTracks[:-cut]
        return newTracks

    # ? cuts on reco-track distance
    def dynamicRecoTrackDistanceCut(self, newTracks, cutPercent=1):

        # don't worry, numpy arrays are copied by reference
        tempTracks = newTracks

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

    def alignModules(self, maxNoOfTracks=0, multiThreaded=False):
        # single thraded
        if not multiThreaded:
            for sector in range(10):
                for result in self.alignSectorICP(sector, maxNoTrks=int(maxNoOfTracks)):
                    path, matrix = result
                    self.alignMatrices[path] = matrix
            return

        # multi-threaded version
        else:
            maxThreads = 8
            print(f"running in {maxThreads} threads.")

            futureList = []

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=maxThreads
            ) as executor:
                # Start the load operations and mark each future with its URL
                for sector in range(10):
                    futureList.append(
                        executor.submit(self.alignSectorICP, sector, int(maxNoOfTracks))
                    )

            print("waiting for remaining jobs...")
            executor.shutdown(wait=True)

            # get all results from the future
            for f in futureList:
                for result in f.result():
                    path, matrix = result
                    self.alignMatrices[path] = matrix
            return

    def saveMatrices(self, fileName):
        mi.saveMatrices(self.alignMatrices, fileName)

    def alignSectorICP(self, sector=0, maxNoTrks=0):
        # check if anchor points were set
        assert hasattr(self, "anchorPoints")

        # TODO: add to config!
        preTransform = False
        useOldFormat = True  # don't change yet, new format is not ready yet!

        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        # get relevant module paths
        modulePaths = self.reader.getModulePathsInSector(sector)

        # make 4x4 matrices to module positions
        moduleMatrices = np.zeros((4, 4, 4))
        for i in range(len(modulePaths)):
            path = modulePaths[i]
            moduleMatrices[i] = np.array(self.reader.detectorMatrices[path]).reshape(
                4, 4
            )

        # * use average misalignment
        averageShift = self.avgMisalignments[str(sector)]

        # get Reco Points from reader
        # TODO: update format or read with uproot directly!
        if useOldFormat:
            allTracks = self.reader.getAllTracksInSector(sector)
            # ? new format! np array with track oris, track dirs, and recos
            nTrks = len(allTracks)
            newTracks = np.ones((nTrks, 6, 4))

            for i in range(nTrks):
                newTracks[i, 0, :3] = allTracks[i]["trkPos"]
                newTracks[i, 1, :3] = allTracks[i]["trkMom"]
                newTracks[i, 2, :3] = allTracks[i]["recoHits"][0]["pos"]
                newTracks[i, 3, :3] = allTracks[i]["recoHits"][1]["pos"]
                newTracks[i, 4, :3] = allTracks[i]["recoHits"][2]["pos"]
                newTracks[i, 5, :3] = allTracks[i]["recoHits"][3]["pos"]
        else:
            raise Exception(f"new track format is not implemented yet!")

        # use only N tracks:
        if maxNoTrks > 0:
            newTracks = newTracks[:maxNoTrks]

        sectorString = str(sector)
        # transform all recos to LMD local
        if preTransform:
            matToLMD = np.linalg.inv(
                np.array(self.reader.detectorMatrices["/cave_1/lmd_root_0"]).reshape(
                    (4, 4)
                )
            )
            for i in range(4):
                newTracks[:, i + 2] = (matToLMD @ newTracks[:, i + 2].T).T

        # transform anchorPoints to PANDA global
        else:
            matFromLMD = np.array(
                self.reader.detectorMatrices["/cave_1/lmd_root_0"]
            ).reshape((4, 4))
            self.anchorPoints[sectorString] = (
                matFromLMD @ self.anchorPoints[sectorString]
            )

        print(f"==================================================")
        print(f"        module aligner for sector {sector}")
        print(f"==================================================")

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

        # ugly hack to plot intermediate track directions for my Diss
        np.save(
            "output/alignmentModules/trackDirections/newTracks-BeforeFirstCut",
            newTracks,
        )

        newTracks = self.dynamicTrackCut(newTracks, 1)

        # ugly hack to plot intermediate track directions for my Diss
        np.save(
            "output/alignmentModules/trackDirections/newTracks-AfterFirstCut", newTracks
        )

        # * =========== iterate cuts and calculation
        # TODO: Check if the reco and direction cuts are even neccessary in the iterations anymore. Seems that one cut at the beginning is enough.
        for iIteration in range(self.iterations):
            print(
                f"running iteration {iIteration}, {len(newTracks)} tracks remaining..."
            )

            np.save(
                f"output/alignmentModules/trackDirections/newTracks-it{iIteration}-step1-noRecoCut",
                newTracks,
            )

            newTracks = self.dynamicRecoTrackDistanceCut(newTracks)

            np.save(
                f"output/alignmentModules/trackDirections/newTracks-it{iIteration}-step2-afterRecoCut",
                newTracks,
            )

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
                T0inv = self.getMatrix(recoPosArr, pIntersection, preTransform)
                totalMatrices[i] = T0inv @ totalMatrices[i]

                # transform recos
                newTracks[:, i + 2] = (T0inv @ newTracks[:, i + 2].T).T

                np.save(
                    f"output/alignmentModules/trackDirections/newTracks-it{iIteration}-step3-afterFit",
                    newTracks,
                )

            # direction cut again
            if iIteration < 3:
                newTracks = self.dynamicTrackCut(newTracks, 1)

            np.save(
                f"output/alignmentModules/trackDirections/newTracks-it{iIteration}-step4-afterDirectionCut",
                newTracks,
            )

            # do track fit
            corrFitter = CorridorFitter(newTracks[:, 2:6])
            resultTracks = corrFitter.fitTracksSVD()

            # update current tracks
            newTracks[:, 0, :3] = resultTracks[:, 0]
            newTracks[:, 1, :3] = resultTracks[:, 1]

            np.save(
                f"output/alignmentModules/trackDirections/newTracks-it{iIteration}-step5-afterTrackFit",
                newTracks,
            )

        # * =========== store matrices
        # 4 planes per sector

        result = []

        for i in range(4):
            # ideal module matrices!
            toModMat = moduleMatrices[i]
            if preTransform:
                # totalMatrices[i] = np.linalg.inv(matToLMD) @ totalMatrices[i] @ (matToLMD)
                totalMatrices[i] = mi.baseTransform(totalMatrices[i], matToLMD, True)
                totalMatrices[i] = mi.baseTransform(totalMatrices[i], toModMat, True)
            else:
                totalMatrices[i] = mi.baseTransform(totalMatrices[i], toModMat, True)

            # add average shift
            totalMatrices[i] = totalMatrices[i] @ averageShift
            result.append((modulePaths[i], totalMatrices[i]))

        print(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print(f"        module aligner for sector {sector} done!         ")
        print(f"-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        return result

    def getMatrix(self, trackPositions, recoPositions, use2D=False):

        # use 2D, use only in LMD local!
        if use2D:
            T, _, _ = icp.best_fit_transform(
                trackPositions[..., :2], recoPositions[..., :2]
            )

            # homogenize
            resultMat = np.identity(4)
            resultMat[:2, :2] = T[:2, :2]
            resultMat[:2, 3] = T[:2, 2]
            return resultMat

        else:
            T, _, _ = icp.best_fit_transform(trackPositions, recoPositions)
            return T
