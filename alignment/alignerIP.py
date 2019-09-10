#!/usr/bin/env python3

from alignment.IP.trksQA import getIPfromTrksQA
from detail.LMDRunConfig import LMDRunConfig
from pathlib import Path
from numpy.linalg import inv

import detail.matrixInterface as mi
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This aligner needs a LMDRunConfig object. It will then:

- read TrksQA.root files
- find apparent IP position
- compare with actual IP position from PANDA upstream and compute rotation matrix
- save matrix to json file

Info: all positional vectors are row-major!
"""


class alignerIP:

    def __init__(self):
        self.logger = None
        self.idealDetectorMatrixPath = Path('input') / Path('detectorMatricesIdeal.json')
        self.idealDetectorMatrices = mi.loadMatrices(self.idealDetectorMatrixPath)

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    """
    computes rotation from A to B when rotated through origin.
    shift A and B before, if rotation did not already occur through origin!
    
    see https://math.stackexchange.com/a/476311
    or https://en.wikipedia.org/wiki/Cross_product
    
    This function works on 3D points only, do not give homogenous coordinates to this!
    """

    def getRot(self, apparent, actual):
        # error handling
        if np.linalg.norm(apparent) == 0 or np.linalg.norm(actual) == 0:
            self.logger.log("\nERROR. can't create rotation with null vector!\n")
            return

        # assert shapes
        assert apparent.shape == actual.shape

        # normalize vectors
        apparent = apparent / np.linalg.norm(apparent)
        actual = actual / np.linalg.norm(actual)

        # calc rot angle by dot product
        cosine = np.dot(apparent, actual)  # cosine

        # make 2D vectors so that transposing works
        cVector = apparent[np.newaxis].T
        dVector = actual[np.newaxis].T

        # compute skew symmetric cross product matrix
        crossMatrix = (dVector @ cVector.T) - (cVector @ dVector.T)

        # compute rotation matrix
        R = np.identity(3) + crossMatrix + np.dot(crossMatrix, crossMatrix) * (1/(1+cosine))

        return R

    # different method, just to be sure
    def getRotWiki(self, apparent, actual):

        # error handling
        if np.linalg.norm(apparent) == 0 or np.linalg.norm(actual) == 0:
            self.logger.log("\nERROR. can't create rotation with null vector!\n\n")
            return

        # assert shapes
        assert apparent.shape == actual.shape

        # calc rot axis
        axis = np.cross(apparent, actual)
        axisnorm = np.linalg.norm(axis)
        axisN = axis / axisnorm

        # normalize vectors
        apparentnorm = np.linalg.norm(apparent)
        actualnorm = np.linalg.norm(actual)

        # calc rot angle by dot product
        cos = np.dot(apparent, actual) / (apparentnorm * actualnorm)  # cosine
        sin = axisnorm / (apparentnorm * actualnorm)

        ux = axisN[0]
        uy = axisN[1]
        uz = axisN[2]

        R1 = [[
            cos+ux*ux*(1-cos),      ux*uy*(1-cos)-uz*sin,   ux*uz*(1-cos)+uy*sin], [
            uy*ux*(1-cos)+uz*sin,   cos+uy*uy*(1-cos),      uy*uz*(1-cos)-ux*sin], [
            uz*ux*(1-cos)-uy*sin,   uz*uy*(1-cos)+ux*sin,   cos+uz*uz*(1-cos)
        ]]
        return R1

        # # alternate way
        # u = axisN[np.newaxis]
        # v = np.array([[
        #     0, -uz, uy],[
        #     uz, 0, -ux],[
        #     -uy, ux, 0
        # ]])

        # R2 = cos*np.identity(3) + sin*v + (1-cos)*(u.T@u)
        # return R2

    def computeAlignmentMatrix(self):
        if not self.config:
            self.logger.log(f'ERROR! Config not set!\n')
            return
        trksQApath = self.config.pathTrksQA()
        self.logger.log(f'I\'m looking for the IP here: {trksQApath}\n')

        ipApparent = np.array([0.0, 0.0, 0.0, 1.0])

        # TODO: create list with about 3 TrksQA files by searching through the directory, no more hard coded values!
        trksQAfile = trksQApath / Path('Lumi_TrksQA_1000*.root')        # this will find 1-4 files, should be okay for now
        ipApparent = getIPfromTrksQA(str(trksQAfile))

        # FIXME later: read from config or PANDA db/survey
        ipActual = np.array([0.0, 0.0, 0.0, 1.0])

        self.logger.log(f'IP apparent:\n{ipApparent}\n')
        self.logger.log(f'IP actual:\n{ipActual}\n')

        # we want the rotation of the lumi box, so we have to change the basis
        matPndtoLmd = self.idealDetectorMatrices['/cave_1/lmd_root_0']
        ipApparentLMD = mi.baseTransform(ipApparent, inv(matPndtoLmd))[:3]
        ipActualLMD = mi.baseTransform(ipActual, inv(matPndtoLmd))[:3]

        #! order is: IP_from_LMD, IP_actual (i.e. from PANDA)
        Ra = self.getRot(ipApparentLMD, ipActualLMD)

        # homogenize the matrix again
        R1 = np.identity(4)
        R1[:3, :3] = Ra

        # after that, add the remaining translation (direct shift towards IP)
        self.resultJson = {"/cave_1/lmd_root_0": R1}
        self.logger.log(f'Interaction point alignment done!\n')

    def saveAlignmentMatrix(self, fileName):
        outFileName = fileName

        if Path(outFileName).exists():
            self.logger.log(f'WARNING. Replacing file: {outFileName}!\n')
            Path(outFileName).unlink()

        if not Path(outFileName).parent.exists():
            Path(outFileName).parent.mkdir()

        mi.saveMatrices(self.resultJson, outFileName)


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
