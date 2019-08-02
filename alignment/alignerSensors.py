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


class alignerSensors:

    def __init__(self):
        pass

    @classmethod
    def fromRunConfig(cls, runConfig):
        temp = cls()
        temp.config = runConfig
        return temp


if __name__ == "__main__":
    print(f'Error! Can not be run individually!')
