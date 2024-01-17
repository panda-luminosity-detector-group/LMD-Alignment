#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Reader class to read the Lumi_TrksQA_*.root files and outputs the average reconstructed IP.
"""

from pathlib import Path

import numpy as np
import uproot


class LumiTrksQAReader:
    def quantileCut(self, xyzArray: np.ndarray, cut=4) -> np.ndarray:
        """
        Performs a quantile cut on the given array.
        """
        if cut == 0:
            return xyzArray

        # calculate cut length
        cut = int(len(xyzArray) * (cut / 100))

        # calculate center of mass (where most points are)
        # don't use average, some values are far too large, median is a better estimation
        comMed = np.median(xyzArray[:, 3:6], axis=0)

        # now, sort by distance and cut largest
        # first, calculate distace of each point to center of mass
        distVec = xyzArray[:, 3:6] - comMed

        # calculate length of these distance vectors
        distVecNorm = np.linalg.norm(distVec, axis=1)

        # sort the entire array by this length
        xyzArray = xyzArray[distVecNorm.argsort()]

        # cut the largest values
        resultArray = xyzArray[:-cut]

        return resultArray

    def getIPfromRootFiles(self, rootFilesPath: Path, maxNoOfFiles=0) -> np.ndarray:
        """
        Reads the root files and returns the reconstruced average IP from the LMD.
        Returns a 4D vector with the last value being 1 (homogeneous coordinates).
        """

        # make empty 2D (n times 4) result array for each individual IP position (that's per file)
        IPs = np.empty((0, 4))

        rootFileWildcard = Path("Lumi_TrksQA_*.root:pndsim")

        runIndex = 0
        for array in uproot.iterate(
            (rootFilesPath / rootFileWildcard).__str__(),
            [
                "LMDTrackQ.fTrkRecStatus",
                "LMDTrackQ.fXrec",
                "LMDTrackQ.fYrec",
                "LMDTrackQ.fZrec",
            ],
            library="np",
            allow_missing=True,
        ):
            recStat = np.concatenate(array["LMDTrackQ.fTrkRecStatus"]).ravel()
            recX = np.concatenate(array["LMDTrackQ.fXrec"]).ravel()
            recY = np.concatenate(array["LMDTrackQ.fYrec"]).ravel()
            recZ = np.concatenate(array["LMDTrackQ.fZrec"]).ravel()

            # apply mask for correctly reconstructed track and tracks within 5cm
            # that means reconstructed IP must be within 5cm of 0 in all directions
            thresh = 5
            mask = (
                (recStat == 0)
                & (np.abs(recX) < thresh)
                & (np.abs(recY) < thresh)
                & (np.abs(recZ) < thresh)
            )

            recXmask = recX[mask]
            recYmask = recY[mask]
            recZmask = recZ[mask]

            # don't worry, this is done by reference, nothing is copied here
            outarray = np.array([recXmask, recYmask, recZmask]).T

            outarray = self.quantileCut(outarray, 4)

            foundIP = np.average(outarray, axis=0)
            resultIPhomogeneous = np.ones(4)
            resultIPhomogeneous[:3] = foundIP
            # print(f"loaded {len(outarray)} tracks")
            # print(f"found ip: {resultIPhomogeneous}")
            IPs = np.vstack((IPs, resultIPhomogeneous))
            runIndex += 1
            if runIndex == maxNoOfFiles:
                break

        print(f"read {runIndex} file(s)")
        return np.average(IPs, axis=0)
