#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv
from scipy.optimize import minimize

"""
Fits a single track to 3 or 4 reco hits
"""
class TrackFitter:
    """
    init values: a n*3 tuple with n*(rx, ry, rz)  
    """
    def __init__(self, recoHits):

        assert len(recoHits) == 3 or len(recoHits) == 4
        for reco in recoHits:
            assert reco.shape == (3,)

        self.recoHits = recoHits

    """
    call values: a 5 tuple with [x0, y0, dx, dy, dz]
    """
    def __call__(self, trackGuess):
        
        # track origin should be on first plane, so no z coordinate
        x0, y0, dx, dy, dz = trackGuess[0], trackGuess[1], trackGuess[2], trackGuess[3], trackGuess[4]
        
        # trackOrigin = np.array([x0, y0])
        trackDirection = np.array([dx, dy, dz])
        trkD = trackDirection / np.linalg.norm(trackDirection)
        
        trkO = np.zeros(3)
        trkO[:2] = [x0, y0]
                
        dVecs = []

        # TODO: use numpy notation here
        for reco in self.recoHits:
            dVecs.append((trkO - reco) - ((trkO - reco)@trkD) * trkD)

        # distance squre sum
        chi2 = sum(np.linalg.norm(x) for x in dVecs)
        return chi2

class TrackDirConstraint():
    def __call__(self, trackGuess):
        _, _, dx, dy, dz = trackGuess[0], trackGuess[1], trackGuess[2], trackGuess[3], trackGuess[4]
        trackDirection = np.array([dx, dy, dz])
        trackDirection = trackDirection / np.linalg.norm(trackDirection)
        
        return np.linalg.norm(trackDirection) - 1


class CorridorFitter():
    """
    tracks is a tuple of tuples of tuples
    outer tuple: all tracks (of this sector)
    second layer tuples: all recoHits for this track (3 or 4)
    third layer tuples: 3 tuple for (rx, ry, rz)
    """
    def __init__(self, tracks):
        self.tracks = tracks

    def fitTracks(self):
        # con = {'type': 'eq', 'fun': TrackDirConstraint}
        track0 = np.array([0,0,0,0,1])
        #self.results = [minimize(TrackFitter([0,0,0,0,1]), track['recoHits'], constraints=con ) for track in self.tracks ] 
        self.results = [minimize(TrackFitter(trackRecos), track0) for trackRecos in self.tracks ] 
