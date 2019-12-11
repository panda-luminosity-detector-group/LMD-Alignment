#!/usr/bin/env python3

# from alignment.modules.trackReader import trackReader
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import importlib.util

def doit():

    # import by path
    spec = importlib.util.spec_from_file_location("trackReader", "/media/DataEnc2TBRaid1/Arbeit/LMDscripts/alignment/modules/trackReader.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)

    fileName = 'input/trackResiduals/processedTracks-1.5-GeV-aligned.json'

    # load track file
    reader = foo.trackReader()
    reader.readDetectorParameters()
    reader.readTracksFromJson(fileName)
    tracks = reader.getAllTracksInSector(0)

    print(tracks[0])

    # gather paths

    # calc distcanes for all four planes 

    # try two cases: lump all sectors together and do it by sector

    # hist to four 2d diagrams, from plane 1 (left) trough 4 (right)


if __name__ == "__main__":
    doit()