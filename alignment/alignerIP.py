#!/usr/bin/env python3

from detail.LMDRunConfig import LMDRunConfig
from detail.matrices import getMatrixFromJSON, makeHomogenous
from detail.trksQA import getIPfromTrksQA

from pathlib import Path

# TODO: this class shouldn't import json, handle this some other way
import json
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

read TrksQA.root files
find apparent IP position
compare with actual IP position from PANDA upstream

save matrix to json file
rerun Reco and Lumi steps

- FIXME: unify vector handling. most vectors are still row-major and not homogenous!
- FIXME: all path arguments should be Pathlib objects!

- TODO: scan multiple directories for TrksQA, parse align factor, compute box rotation matrices and store to pandaroot dir! 
"""


class alignerIP:

    def __init__(self):
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
            print("ERROR. can't create rotation with null vector")
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
            print("ERROR. can't create rotation with null vector")
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
            print(f'ERROR! Config not set!')
            return

        trksQApath = self.config.pathTrksQA()
        print(f'I\'m looking for the IP here: {trksQApath}')

        # TODO: read from config or PANDA db/survey
        lumiPos = self.getLumiPosition()
        print(f'Lumi Position is:\n{lumiPos}')

        # TODO: change for Himster
        # TODO: create list with about 10 TrksQA files by searching through the directory, no more hard coded values!
        trksQAfile = trksQApath / Path('Lumi_TrksQA_100000.root')

        # TODO: change for Himster
        ipApparent = getIPfromTrksQA(str(trksQAfile))
        
        # TODO: add debug flag or something
        if False:
            ipApparent = np.array([1.0, 0.0, 0.0])

        # FIXME later: read from config or PANDA db/survey
        ipActual = np.array([0.0, 0.0, 0.0])

        print(f'IP apparent:\n{ipApparent}')

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
            print(f'WARNING. Replacing file: {outFileName}')
            Path(outFileName).unlink()

        with open(outFileName, 'w') as outfile:
            json.dump(resultJson, outfile, indent=2)

        print(f'interaction point alignment done!')


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')

    # def getBoxMatrix(self, trksQApath=Path('../input/TrksQA/box-2.00/'), alignName=''):

    #     lumiPos = self.getLumiPosition()
    #     print(f'Lumi Position is:\n{lumiPos}')

    #     #ipApparent = np.array([1.0, 0.0, 0.0])
    #     trksQAfile = trksQApath / Path('Lumi_TrksQA_100000.root')

    #     ipApparent = getIPfromTrksQA(str(trksQAfile))
    #     ipActual = np.array([0.0, 0.0, 0.0])

    #     print(f'IP apparent:\n{ipApparent}')

    #     ipApparentLMD = ipApparent - lumiPos
    #     ipActualLMD = ipActual - lumiPos

    #     #! order is (IP_from_LMD, IP_actual) (i.e. from PANDA)
    #     Ra = self.getRot(ipApparentLMD, ipActualLMD)
    #     R1 = makeHomogenous(Ra)

    #     print('matrix is:')
    #     self.printMatrixDetails(R1)

    #     if alignName != '':
    #         print(f'comparing with design matrix:')
    #         # read json file here and compare
    #         try:
    #             mat1 = getMatrixFromJSON('../input/rootMisalignMatrices/json/misMat-box-2.00.root.json', '/cave_1/lmd_root_0')
    #             print('matrix should be:')
    #             printMatrixDetails(mat1)
    #             printMatrixDetails(R1, mat1)
    #         except:
    #             print(f"can't open matrix file: {alignName}")

    #     resultJson = {"/cave_1/lmd_root_0": np.ndarray.tolist(np.ndarray.flatten(R1))}

    #     outFileName = Path.cwd().parent / Path('output') / Path(alignName).with_suffix('.json')  # (alignName)
    #     with open(outFileName, 'w') as outfile:
    #         json.dump(resultJson, outfile, indent=2)

    #     print(resultJson)

    #     ipA1 = makeHomogenous(ipActualLMD).T
    #     print(f'ip A1: \n{ipA1}')
    #     print(f'with this matrix, the IP would be at:\n{(np.linalg.inv(R1)@ipA1).T[0] + makeHomogenous(lumiPos)}')

    # implement anew using strictly homogenous, column-major vectors!
    # points have w=1, vectors have w=0. de-homogenize with x/w, y/w, z/w
    # vectors CAN NOT be de-homogenized, but the points they point to can be.
    # so, construct a point by origin + v = point_v_points_to
    # this way, v gets its w=1 back
    # see https://math.stackexchange.com/questions/645672/what-is-the-difference-between-a-point-and-a-vector
    # def getBoxMatrixHomogenous():
    #     origin = np.array([0,0,0,1])[np.newaxis].T
    #     pass
