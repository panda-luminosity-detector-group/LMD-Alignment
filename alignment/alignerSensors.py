#!/usr/bin/env python3

from detail.hitPairSorter import hitPairSorter
from detail.LMDRunConfig import LMDRunConfig
from detail.matrices import getMatrixFromJSON, makeHomogenous
from detail.trksQA import getIPfromTrksQA

from pathlib import Path


import json
import numpy as np

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This aligner needs a LMDRunConfig object. It will then:

- read Lumi_Pairs_*.root files
- sort to numpy files
- read all numpy files
- find overlap matrices
- save them as deviation matrices to json

Info: all positional vectors are row-major! This aligner also need info about the geometry
to transform sensor-local matrices to PANDA global:

- detector_matrices.json | containing all design matrices of the Luminosity detector 



"""


class alignerSensors:

    def __init__(self):
        pass

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp

    def sortPairs(self):
        pairSourcePath = self.config.pathTrksQA()
        #sorter = hitPairSorter( (Path('input') / Path('LumiPairsTest')) )
        sorter = hitPairSorter(Path(pairSourcePath))

        sorter.sortAll()

    def findMatrices(self):
        # go to npy dir
        # do the following multi threaded (thread pool executor, look into runSimulations)

        # read all npys
        # create matrix finder for each
        # compute matrix
        
        pass

if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
