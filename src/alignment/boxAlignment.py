#!/usr/bin/env python3

import numpy as np

from src.alignment.readers.lumiTrkQAtoIPReader import LumiTrksQAReader
from src.util.matrix import loadMatrices, saveMatrices


class BoxAligner:
    idealDetectorMatrices = loadMatrices("config/detectorMatricesIdeal.json")

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

        reader = LumiTrksQAReader()
        IPfromLMD = reader.getIPfromRootFiles(path, maxNoOfFiles)

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
