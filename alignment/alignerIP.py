#!/usr/bin/env python3

from detail.LMDRunConfig import LMDRunConfig
from detail.matrices import getMatrixFromJSON, makeHomogenous
from detail.trksQA import getIPfromTrksQA

from pathlib import Path

import json
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
        pass

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    def getLumiPosition(self):

        # TODO: better case separation
        if False:
            # get values from survey / database!
            lumiPos = np.array([0.0, 0.0, 0.0, 1.0])[np.newaxis].T
            lumiMat = getMatrixFromJSON('../input/rootMisalignMatrices/json/detectorMatrices.json', '/cave_1/lmd_root_0')
            newLumiPos = (lumiMat@lumiPos).T[0][:3]
            return newLumiPos
        else:
            # values are pre-calculated for ideal lumi position
            return np.array((25.37812835, 0.0, 1109.13))

    """
    computes rotation from A to B when rotated through origin.
    shift A and B before, if rotation did not already occur through origin!
    
    see https://math.stackexchange.com/a/476311
    or https://en.wikipedia.org/wiki/Cross_product
    """

    def getRot(self, apparent, actual):
        # error handling
        if np.linalg.norm(apparent) == 0 or np.linalg.norm(actual) == 0:
            self.logger.log("ERROR. can't create rotation with null vector")
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
        crossMatrix = np.matmul(dVector, cVector.T) - np.matmul(cVector, dVector.T)

        # compute rotation matrix
        R = np.identity(3) + crossMatrix + np.dot(crossMatrix, crossMatrix) * (1/(1+cosine))

        return R

    # different method, just to be sure
    def getRotWiki(self, apparent, actual):

        # error handling
        if np.linalg.norm(apparent) == 0 or np.linalg.norm(actual) == 0:
            self.logger.log("ERROR. can't create rotation with null vector")
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
            self.logger.log(f'ERROR! Config not set!')
            return
        trksQApath = self.config.pathTrksQA()
        self.logger.log(f'I\'m looking for the IP here: {trksQApath}')

        # FIXME later: read from config or PANDA db/survey
        lumiPos = self.getLumiPosition()
        self.logger.log(f'Lumi Position is:\n{lumiPos}')

        # TODO: create list with about 3 TrksQA files by searching through the directory, no more hard coded values!
        trksQAfile = trksQApath / Path('Lumi_TrksQA_100000.root')
        ipApparent = getIPfromTrksQA(str(trksQAfile))

        # add debug flag or something
        if False:
            ipApparent = np.array([1.0, 0.0, 0.0])

        # FIXME later: read from config or PANDA db/survey
        ipActual = np.array([0.0, 0.0, 0.0])

        self.logger.log(f'IP apparent:\n{ipApparent}')
        self.logger.log(f'IP actual:\n{ipActual}')

        ipApparentLMD = ipApparent - lumiPos
        ipActualLMD = ipActual - lumiPos

        #! order is (IP_from_LMD, IP_actual, i.e. from PANDA)
        Ra = self.getRot(ipApparentLMD, ipActualLMD)
        R1 = makeHomogenous(Ra)

        resultJson = {"/cave_1/lmd_root_0": np.ndarray.tolist(np.ndarray.flatten(R1))}

        if not self.config.alMatFile:
            self.config.generateMatrixNames()

        # FIXME later: save alignment Matrix to DATA path, not PandaRoot path!
        outFileName = self.config.alMatFile

        if Path(outFileName).exists():
            self.logger.log(f'WARNING. Replacing file: {outFileName}')
            Path(outFileName).unlink()

        if not Path(outFileName).parent.exists():
            Path(outFileName).parent.mkdir()

        with open(outFileName, 'w') as outfile:
            json.dump(resultJson, outfile, indent=2)

        self.logger.log(f'interaction point alignment done!')


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
