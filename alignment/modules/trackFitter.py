#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv
from scipy.optimize import minimize

"""
Fits a single track to exactly 4 reco hits

params:
- tracks: an np.array with dimension (nTrks, 4, 3), 4 reco hits with each x, y, z
"""

class CorridorFitter():
    def __init__(self, tracks):
        self.tracks = None
        self.tracks = tracks
        self.nTrks = len(self.tracks)
        self.useAnchor = False

    def useAnchorPoint(self, point):
        assert len(point) == 3
        self.anchorPoint = point
        self.useAnchor = True

    def fitTracksSVD(self):

        self.fittedTrackArr = np.zeros((self.nTrks, 2, 3))

        for i in range(self.nTrks):

            # cut fourth entry, sometimes this is the sensorID
            trackRecos = self.tracks[i][:, :3]
            
            if self.useAnchor:
                trackRecos = np.vstack((self.anchorPoint, trackRecos))

            meanPoint = trackRecos.mean(axis=0)

            _, _, vv = np.linalg.svd(trackRecos - meanPoint)

            trkO = meanPoint
            trkD = vv[0]
            self.fittedTrackArr[i][0] = trkO
            self.fittedTrackArr[i][1] = trkD

        return self.fittedTrackArr

