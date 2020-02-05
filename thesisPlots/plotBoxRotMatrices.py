#!/usr/bin/env python3
from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from pathlib import Path
import uproot
import sys
import json
import re

np.set_printoptions(precision=3, suppress=True)

def rotationMatrixToEulerAngles(R):

    assert(R.shape == (4, 4) or R.shape == (3, 3))
    
    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])

if __name__ == "__main__":

    import matplotlib.pyplot as plt

    latexmu = r'\textmu{}'
    latexsigma = r'\textsigma{}'

    latexPsi = r'\textPsi'
    latexTheta = r'\textTheta'
    latexPhi = r'\textPhi'

    latexPercent = r'\%'
    plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

    files = Path('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/').glob('misMat-box100-*.json')

    lines = []

    for file in files:
        with open(file, 'r') as f:

            data = json.load(f)
            array = data["/cave_1/lmd_root_0"]
            matrix = np.array(array).reshape((4,4)) 
            angles = rotationMatrixToEulerAngles(matrix)
        
        m = re.search(r'misMat-box100-(\d?\.\d\d)\.json', str(file))

        if m:
            fac = float(m.group(1))
            lines.append([fac, angles[0], angles[1], angles[2]])
        else:
            continue
        
    lines = np.array(lines)
    

    #* -------------- plot Euler angle residuals
    misType = 'box100'
    # source = 'box'
    fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))

    ax.errorbar(lines[:,0], lines[:,1]*1e6, fmt='3', capsize=4, markersize=10, label=f'{latexPsi}')
    ax.errorbar(lines[:,0], lines[:,2]*1e6, fmt='4', capsize=4, markersize=10, label=f'{latexTheta}')
    # ax.errorbar(lines[:,0], lines[:,3]*1e6, fmt='.', capsize=4, markersize=5, label=f'{latexPhi}')
    
    ax.set_xlabel(f'Misalign Factor')
    ax.set_ylabel(f'Euler Angles [{latexmu}rad]')
    ax.legend()
    ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')

    # --------- zoom out x
    xlim = ax.get_xlim()
    # example of how to zoomout by a factor of 0.1
    xfactor = 0.1
    new_xlim = (xlim[0] + xlim[1])/2 + np.array((-0.5, 0.5)) * (xlim[1] - xlim[0]) * (1 + xfactor) 
    ax.set_xlim(new_xlim)
    #/ --------- zoom out x

    # --------- zoom out y
    ylim = ax.get_ylim()
    # example of how to zoomout by a factor of 0.1
    yfactor = 0.1 
    new_ylim = (ylim[0] + ylim[1])/2 + np.array((-0.5, 0.5)) * (ylim[1] - ylim[0]) * (1 + yfactor) 
    ax.set_ylim(new_ylim)
    #/ --------- zoom out y

    # get handles
    handles, labels = ax.get_legend_handles_labels()
    # remove the errorbars
    handles = [h[0] for h in handles]
    # use them in the legend
    ax.legend(handles, labels, loc='upper right',numpoints=1)

    fig.tight_layout()
    fig.savefig(f'output/matrixMisaligns/actual-misalign-{misType}-mats.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig)