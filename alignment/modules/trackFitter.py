#!/usr/bin/env python3

import numpy as np
from numpy.linalg import inv
from scipy.optimize import minimize

class TrackFitter:
    def __init__(self, track_hits):
        self.track_hits = track_hits
        self.alignment_parameters = None
        self.trackfit_parameters = np.array([0.0, 0.0])

    def __call__(self, recoHits):
        direction = np.append(recoHits, [1.0])
        direction = direction / np.linalg.norm(direction)

        chi2 = sum([np.linalg.norm(self.track_hits[0][:2]
                                   + (direction*x[0][2])[:2]
                                   - x[0][:2]+x[1])
                    for x in zip(self.track_hits)])
        return chi2

class PlanCorridorFitter:
    def __init__(self, track_hits):
        self.track_hits = track_hits

    def __call__(self, parameters):

        results = [minimize(x, x.trackfit_parameters,
                            method='BFGS',
                            options={'disp': False})
                   for x in self.track_fitters]

        chi2s = [x.fun for x in results]

        # chi2s = [straightlinefit3d(x, parameters) for x in self.track_hits]
        # print("single iteration finished!")
        return sum(chi2s)