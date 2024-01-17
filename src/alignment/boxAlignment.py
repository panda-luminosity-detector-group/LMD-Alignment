#!/usr/bin/env python3

import numpy as np
import uproot

from src.util.matrix import loadMatrices, saveMatrices


class BoxAligner:
    idealDetectorMatrices = loadMatrices("config/detectorMatricesIdeal.json")

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

    def getIPfromRootFiles(self, filename: str, maxNoOfFiles=0) -> np.ndarray:
        """
        Reads the root files and returns the reconstruced average IP from the LMD.
        Returns a 4D vector with the last value being 1 (homogeneous coordinates).
        """

        # make empty 2D (n times 4) result array for each individual IP position (that's per file)
        IPs = np.empty((0, 4))

        runIndex = 0
        for array in uproot.iterate(
            filename,
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

    def getRot(self, apparentIP: np.ndarray, actualIP: np.ndarray) -> np.ndarray:
        """
        computes rotation from A to B when rotated through origin.
        shift A and B before, if rotation did not already occur through origin!

        see https://math.stackexchange.com/a/476311
        or https://en.wikipedia.org/wiki/Cross_product
        and https://en.wikipedia.org/wiki/Rotation_matrix#Conversion_from_rotation_matrix_and_to_axis%E2%80%93angle

        This function works on 3D points only, do not give homogeneous coordinates to this!
        Returns a 3x3 rotation matrix (not homogeneous!).
        """
        # error handling
        if np.linalg.norm(apparentIP) == 0 or np.linalg.norm(actualIP) == 0:
            print("\nERROR. can't create rotation with null vector!\n")
            return

        # assert shapes
        assert apparentIP.shape == actualIP.shape

        # normalize vectors
        apparentIP = apparentIP / np.linalg.norm(apparentIP)
        actualIP = actualIP / np.linalg.norm(actualIP)

        # calc rot angle by dot product
        cosine = np.dot(apparentIP, actualIP)  # cosine

        # make 2D vectors so that transposing works
        cVector = apparentIP[np.newaxis].T
        dVector = actualIP[np.newaxis].T

        # compute skew symmetric cross product matrix
        crossMatrix = (dVector @ cVector.T) - (cVector @ dVector.T)

        # compute rotation matrix
        R = (
            np.identity(3)
            + crossMatrix
            + np.dot(crossMatrix, crossMatrix) * (1 / (1 + cosine))
        )

        return R

    def alignBox(self, path) -> None:
        """
        Aligns the box to the IP.
        Saves the alignment matrices to the given path.
        """

        # even 10 is more than enough, I've had really good results with only 2 already.
        maxNoOfFiles = 5

        rootFileWildcard = "Lumi_TrksQA_*.root:pndsim"
        IPfromLMD = self.getIPfromRootFiles(path + rootFileWildcard, maxNoOfFiles)
        print(f"found this ip: {IPfromLMD}")
        ipApparent = IPfromLMD

        # we want the rotation of the lumi box, so we have to change the basis
        matPndtoLmd = self.idealDetectorMatrices["/cave_1/lmd_root_0"]
        zero = [0, 0, 0, 1]

        # perform passive transformation of these points to the system
        # of the LMD, so that the rotation occurs arund it's origin
        zeroAt = (np.linalg.inv(matPndtoLmd) @ zero)[:3]
        ipApparentLMD = (np.linalg.inv(matPndtoLmd) @ ipApparent)[:3]

        # order is: IP_from_LMD, IP_actual (i.e. from PANDA)
        Ra = self.getRot(ipApparentLMD, zeroAt)

        # homogenize the matrix again
        R1 = np.identity(4)
        R1[:3, :3] = Ra

        # homogenize the matrix again
        R1 = np.identity(4)
        R1[:3, :3] = Ra

        # after that, add the remaining translation (direct shift towards IP), not implemented yet
        boxAlignMatrix = {"/cave_1/lmd_root_0": R1}

        # save matrices
        saveMatrices(boxAlignMatrix, "matrices/100u-case-1/EXAMPLE-boxAlignMatrix.json")

        print("Box alignment done!")


if __name__ == "__main__":
    print(
        "Cannot be run directly. Please see the example alignment campaigns in jupyter/alignmentCampaign.ipynb."
    )
