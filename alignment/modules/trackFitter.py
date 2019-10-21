#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv
from scipy.optimize import minimize

"""
Fits a single track to 4 reco hits
"""
class TrackFitter:
    """
    init values: a 12 tuple with 3* (rx, ry, rz)  
    """
    def __init__(self, recoHits):
      
        self.recoHits = []
        # 4 dVec, one for each reco point
        noOfPoints = 4
        reco = [0,0,0]

        for i in range(noOfPoints):
            reco[0] = recoHits[i*3 + 0]
            reco[1] = recoHits[i*3 + 1]
            reco[2] = recoHits[i*3 + 2]
            recoHits.append(reco)

    """
    call values: a 5 tuple with [x0, y0, dx, dy, dz]
    """
    def __call__(self, trackGuess):
        
        # track origin should be on first plane, so no z coordinate
        x0, y0, dx, dy, dz = trackGuess[0], trackGuess[1], trackGuess[2], trackGuess[3], trackGuess[4]
        
        trackOrigin = np.array([x0, y0])
        trackDirection = np.array([dx, dy, dz])
        trackDirection = trackDirection / np.linalg.norm(trackDirection)
        
        trkO = np.zeros(3)
        trkO[:2] = trackOrigin
        trkD = trackDirection
                
        dVecs = []

        # TODO: use numpy notation here
        for reco in self.recoHits:
            dVecs.append((trkO - reco) - ((trkO - reco)@trkD) * trkD)

        # distance squre sum
        chi2 = sum(np.linalg.norm(x) for x in dVecs)
        return chi2

class CorridorFitter():
    """
    tracks is a tuple of dicts
    each dict has track -> 5 tuple and recoHits -> 12 tuple
    """
    def __init__(self, tracks):
        self.tracks = tracks

    def fitTracks(self):
        self.results = [minimize(TrackFitter(track['track']), track['recoHits']) for track in self.tracks ] 
