#!/usr/bin/env python3

from tqdm import tqdm
import numpy as np
from numpy.linalg import inv
from scipy.optimize import minimize

"""
Fits a single track to 3 or 4 reco hits

TODO: use determinant form of track, minimizer then requires only three paramters
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

        return np.sum( dists )

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
        results = [ minimize(
            TrackFitter(trackRecos),
                np.array([trackRecos[0][0], trackRecos[0][1], 0, 0, 1]),
                method='SLSQP'
                ) for trackRecos in tqdm(self.tracks) ] 

        for track in results:
            thisTrackO = [ track.x[0], track.x[1], 0]
            thisTrackD = [ track.x[2], track.x[3], track.x[4] ]
            self.results.append([thisTrackO, thisTrackD])

    def fitTracksSVD(self):

        """
        you'll get a dict with path -> list of these:

        {'trkMom': [0.6, 0.1, 14.9], 'trkPos': [31.2, 3.93, 1096.98], 'sector': 0, 'valid': True, 'recoPos': [31.2, 3.9, 1096.98]}
        
        fit tracks over all four modules but sort the reco hits and the track to the correct dict position (tracks will be saved 4 times, that is okay!)
        """


        self.fittedTracks = []
        self.trackRecos = []

        for trackRecos in self.tracks:
            pass

        """
        return something like 
        {'trkOri': [0,0,0], 'trkDir' : [0,0,0], 'recoHits' : [ [0,0,0], [0,0,0], [0,0,0], [0,0,0] ]}
        nah...

        return a dict with path -> list of these:
        {'trkOri' : [0,0,0], 'trkDir' : [0,0,0], 'recoPos' : [0,0,0]}
        I think this is the format the moduleAligner can handle
        """

    def fitTracksSVDold(self):
        
        self.fittedTracks = []
        self.trackRecos = []

        for trackRecos in self.tracks:

            # TODO: this is so ugly, all of this needs to be rewritten
            trackRecos = np.array([np.array(line) for line in trackRecos])

            meanPoint = trackRecos.mean(axis=0)

            _, _, vv = np.linalg.svd(trackRecos - meanPoint)

            trkO = meanPoint
            trkD = vv[0]

            # TODO: re-parametrize so that this track originates in plane0... 
            # you can use this: https://en.wikipedia.org/wiki/Line%E2%80%93plane_intersection
            # or not actually, shouldn't really matter 
            self.fittedTracks.append([trkO, trkD])
            self.trackRecos.append(trackRecos)
