#!/usr/bin/env python3

import numpy as np

"""
Fits a single track to exactly 4 reco hits

params:
- tracks: an np.array with dimension (nTrks, 4, 3), 4 reco hits with each x, y, z
"""


class CorridorFitter:
    def __init__(self, tracks):
        self.tracks = tracks
        self.nTrks = len(self.tracks)
        self.useAnchor = False

    def useAnchorPoint(self, point):
        assert len(point) == 3 or len(point) == 4
        self.anchorPoint = point
        self.useAnchor = True

    def fitTracksSVD(self):

        self.fittedTrackArr = np.zeros((self.nTrks, 2, 3))

        for i in range(self.nTrks):
            # cut fourth entry, sometimes this is the sensorID or homogeneous coordinate
            trackRecos = self.tracks[i][:, :3]

            if self.useAnchor:
                trackRecos = np.vstack((self.anchorPoint[:3], trackRecos))

            # see https://stackoverflow.com/questions/2298390/fitting-a-line-in-3d
            meanPoint = trackRecos.mean(axis=0)
            _, _, vv = np.linalg.svd(trackRecos - meanPoint)

            self.fittedTrackArr[i][0] = meanPoint

            # flip tracks that are fitted backwards
            if vv[0, 2] < 0:
                self.fittedTrackArr[i][1] = -vv[0]
            else:
                self.fittedTrackArr[i][1] = vv[0]

        return self.fittedTrackArr
