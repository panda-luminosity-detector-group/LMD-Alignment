#!/usr/bin/env python3 

"""
Doesn't work, forget it
"""

import numpy as numpy
import uproot

f = uproot.open("Lumi_MC_100000.root")
events = f["pndsim"]
# Track IDs
lmdPoints = events['LMDPoint'][b'LMDPoint.fTrackID']

# eventIDs
lmdPoints = events['LMDPoint'][b'LMDPoint.fEventId']

# eventIDs
lmdPoints = events['LMDPoint'][b'LMDPoint.fX'].array()

# eventIDs
# lmdPoints = events['LMDPoint'][b'LMDPoint.fEventId']

print(lmdPoints)
# print(lmdPoints.array())