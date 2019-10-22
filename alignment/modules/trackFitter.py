#!/usr/bin/env python3

from tqdm import tqdm
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

        self.recoHits = np.array(recoHits)

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
                
        # dVecs = []
        dists = []

        # TODO: use numpy notation here
        for reco in self.recoHits:
            dVec = (trkO - reco) - ((trkO - reco)@trkD) * trkD
            # dVecs.append(dVec)
            dists.append(np.linalg.norm(dVec))

        # print(f'recoHits:\n{self.recoHits}')

        # reco = self.recoHits

        # numpy notation

        # dVecs = (trkO - reco[,:]) - ((trkO - reco[,:])@trkD) * trkD
        # dists = np.linalg.norm(dVecs)

        
        # print(f'dVecs:\n{dVecs}')
        # print(f'dists:\n{dists}')
        return np.sum( dists )
        # return np.sum(dVec)
        # print(f'dVec: {dVec}')
        # dists = np.linalg.norm(  )

        # different distance estimation:
        # for reco in self.recoHits:
        #     rx, ry, rz = reco[0], reco[1], reco[2]
        #     dists.append(np.linalg.norm(reco - (trkO + rz*trkD)))

        # distance squre sum
        # chi2 = sum( np.array(dists) )
        # return chi2

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
        print(f'fitting tracks...')
        self.results = [ minimize(
            TrackFitter(trackRecos),
                np.array([trackRecos[0][0], trackRecos[0][1], 0, 0, 1]),
                method='SLSQP'
                ) for trackRecos in tqdm(self.tracks) ] 
