#!/usr/bin/env python3

import copy
from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
from numpy.linalg import inv
import json
import uproot
# import pandas as pd
import re
import struct
import sys

class PndTrackCandHit(uproot.rootio.ROOTStreamedObject):
    _first_format = struct.Struct(">d")
    _n_format = struct.Struct(">i")
    _fX_dtype = np.dtype(">f4")
    # _fY_dtype = np.dtype(">f8")
    # _fZ_dtype = np.dtype(">f8")

    @classmethod
    def _readinto(cls, self, source, cursor, context, parent):
        self.first = cursor.field(source, self._first_format)
        self.fX = []
        self.fY = []
        self.fZ = []
        while True:
            try:
                n = cursor.field(source, self._n_format)
                fX = cursor.array(source, n, self._fX_dtype)
                fY = cursor.array(source, n, self._fX_dtype)
                fZ = cursor.array(source, n, self._fX_dtype)
            except IndexError:
                break
            else:
                self.fX.extend(fX)
                self.fY.extend(fY)
                self.fZ.extend(fZ)
        return self

def test():

    filename = Path('input/modulesAlTest/Lumi_recoMerged_100000.root')


    tree = uproot.open(filename)["pndsim"]
    branch = tree["LMDHitsMerged"]

    interp = uproot.asgenobj(PndTrackCandHit, branch._context, skipbytes=0)
    data = branch.array(interp)

    print(data)

    # f = uproot.open(filename)
    # events = f["pndsim"]
    # # Track IDs
    # lmdPoints = events['LMDHitsMerged'][b'LMDHitsMerged.fX']

    # # eventIDs
    # lmdPoints = events['LMDPoint'][b'LMDPoint.fEventId']

    # # eventIDs
    # lmdPoints = events['LMDPoint'][b'LMDPoint.fX'].array()

    # # eventIDs
    # # lmdPoints = events['LMDPoint'][b'LMDPoint.fEventId']

    # print(lmdPoints)
    # print(lmdPoints.array())

    pass

if __name__ == "__main__":
    print('running')
    test()