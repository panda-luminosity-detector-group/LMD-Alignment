#!/usr/bin/env python3
from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import uproot
import sys
import json

np.set_printoptions(precision=3, suppress=True)

if __name__ == "__main__":

    print('DEPRECATED')
    sys.exit(1)

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

    momentum = '15.0'
    sources = ['modules', 'sensors']
    misTypes = ['modules', 'sensors', 'overlaps']

    for source in sources:

        with open(f'runConfigs/uncorrected/{source}/{momentum}/allMatrixValues.json', 'r') as f:
            data = json.load(f)

        for misType in misTypes:

            lines = []
            for i in data:
                fac = list(i.keys())[0]
                iVal = i[fac]

                facFloat = float(fac)

                modulesMean = np.array(iVal[misType][0])
                modulesSigma = np.array(iVal[misType][1])

                line = [facFloat, modulesMean[0], modulesMean[1], modulesMean[2], modulesSigma[0], modulesSigma[1], modulesSigma[2]]
                lines.append(line)

            lines = np.array(lines)

            fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))

            ax.errorbar(lines[:,0]-0.02, lines[:,1], yerr=lines[:,4], fmt='3', capsize=4, markersize=10, label=f'{latexmu} x')
            ax.errorbar(lines[:,0]+0.02, lines[:,2], yerr=lines[:,5], fmt='4', capsize=4, markersize=10, label=f'{latexmu} y')
            
            ax.set_xlabel(f'Misalign Factor')
            ax.set_ylabel(f'Matrix Residuals [{latexmu}m]')
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
            fig.savefig(f'output/comparison/mom-{momentum}-misalign-{source}-mats-{misType}.pdf', dpi=1000, bbox_inches='tight')
            plt.close(fig)

        #* -------------- plot Euler angle residuals
        misType = 'box'
        lines = []
        for i in data:
            fac = list(i.keys())[0]
            iVal = i[fac]

            facFloat = float(fac)

            resX = iVal[misType][0][0]
            resY = iVal[misType][0][1]
            resZ = iVal[misType][0][2]

            line = [facFloat, resX, resY, resZ]
            lines.append(line)

        lines = np.array(lines)

        fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))

        ax.errorbar(lines[:,0], lines[:,1], fmt='3', capsize=4, markersize=10, label=f'{latexPsi}')
        ax.errorbar(lines[:,0], lines[:,2], fmt='4', capsize=4, markersize=10, label=f'{latexTheta}')
        # ax.errorbar(lines[:,0], lines[:,3], fmt='2', capsize=4, markersize=10, label=f'{latexPhi}')
        
        ax.set_xlabel(f'Misalign Factor')
        ax.set_ylabel(f'Euler Residuals [{latexmu}rad]')
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
        fig.savefig(f'output/comparison/mom-{momentum}-misalign-{source}-mats-{misType}.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig)


    source = 'box100'
    with open(f'runConfigs/uncorrected/{source}/{momentum}/allMatrixValues.json', 'r') as f:
        data = json.load(f)

    #* -------------- plot matrix residuals
    for misType in misTypes:

        lines = []
        for i in data:
            fac = list(i.keys())[0]
            iVal = i[fac]

            facFloat = float(fac)

            matrixMean = np.array(iVal[misType][0])
            matrixSigma = np.array(iVal[misType][1])

            line = [facFloat, matrixMean[0], matrixMean[1], matrixMean[2], matrixSigma[0], matrixSigma[1], matrixSigma[2]]
            lines.append(line)

        lines = np.array(lines)

        fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))

        ax.errorbar(lines[:,0]-0.02, lines[:,1], yerr=lines[:,4], fmt='3', capsize=4, markersize=10, label=f'{latexmu} x')
        ax.errorbar(lines[:,0]+0.02, lines[:,2], yerr=lines[:,5], fmt='4', capsize=4, markersize=10, label=f'{latexmu} y')
        
        ax.set_xlabel(f'Misalign Factor')
        ax.set_ylabel(f'Matrix Residuals [{latexmu}m]')
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
        fig.savefig(f'output/comparison/mom-{momentum}-misalign-{source}-mats-{misType}.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig)

    #* -------------- plot Euler angle residuals
    misType = 'box'
    lines = []
    for i in data:
        fac = list(i.keys())[0]
        iVal = i[fac]

        facFloat = float(fac)

        resX = iVal[misType][0][0]
        resY = iVal[misType][0][1]
        resZ = iVal[misType][0][2]

        line = [facFloat, resX, resY, resZ]
        lines.append(line)

    lines = np.array(lines)

    fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))

    ax.errorbar(lines[:,0], lines[:,1], fmt='3', capsize=4, markersize=10, label=f'{latexPsi}')
    ax.errorbar(lines[:,0], lines[:,2], fmt='4', capsize=4, markersize=10, label=f'{latexTheta}')
    # ax.errorbar(lines[:,0], lines[:,3]/1e3, fmt='2', capsize=4, markersize=10, label=f'{latexPhi}')
    
    ax.set_xlabel(f'Misalign Factor')
    ax.set_ylabel(f'Euler Residuals [{latexmu}rad]')
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
    fig.savefig(f'output/comparison/mom-{momentum}-misalign-{source}-mats-{misType}.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig)
