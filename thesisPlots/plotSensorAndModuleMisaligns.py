#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
import matplotlib.pyplot as plt

from pathlib import Path
import sys, subprocess, json
import numpy as np

np.set_printoptions(precision=3, suppress=True)

latexsigma = r'\textsigma{}'
latexmu = r'\textmu{}'
latexPercent = r'\%'
pipe = r'\textbar{}'
latexPsi = r'\textPsi{}'
latexTheta = r'\textTheta{}'
latexPhi = r'\textPhi{}'

plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

lineOptions = {'capsize': 2, 'elinewidth': 0.6, 'linewidth': 0.4}

# sizes = [(17 / 2.54, 7 / 2.54), (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
sizes = [(17 / 2.54, 7 / 2.54)]  #, (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
offsetscale = 1.0
offsets = np.arange(-0.02, 0.03, 0.01)
colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']


def omniPlots(sensorVals, i, momenta, outTypeName):

    fig, ax = plt.subplots(figsize=sizes[i])
    fig2, ax2 = plt.subplots(figsize=sizes[i])
    fig3, ax3 = plt.subplots(figsize=sizes[i])
    fig4, ax4 = plt.subplots(figsize=sizes[i])
    colorI = 0

    for mom in momenta:

        mask = (sensorVals[:, 0] == float(mom))
        thseVals = sensorVals[mask]

        print(f'Ayy lmao I will print this (Sensor Plot):\n{thseVals}')

        # sort 2D array by second column
        #* order in list: [mom, fac, dX, dY, dR, stdX, stdY, stdR], units are microns and mrad
        thseVals = thseVals[thseVals[:, 1].argsort()]

        # Plot dx, dx MEAN
        ax.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale - 0.00,
                    thseVals[:, 2],
                    fmt='2',
                    ecolor=colors[colorI],
                    color=colors[colorI],
                    label=f'x @ {mom} GeV/c',
                    ls='dashed',
                    **lineOptions)
        ax.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale + 0.00,
                    thseVals[:, 3],
                    fmt='1',
                    ecolor=colors[colorI],
                    color=colors[colorI],
                    label=f'y @ {mom} GeV/c',
                    ls='dashed',
                    **lineOptions)

        # Plot dx, dx STD
        ax2.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale - 0.00,
                     thseVals[:, 5],
                     fmt='2',
                     ecolor=colors[colorI],
                     color=colors[colorI],
                     label=f'x @ {mom} GeV/c',
                     ls='dashed',
                     **lineOptions)
        ax2.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale + 0.00,
                     thseVals[:, 6],
                     fmt='1',
                     ecolor=colors[colorI],
                     color=colors[colorI],
                     label=f'y @ {mom} GeV/c',
                     ls='dashed',
                     **lineOptions)

        # Plot dR MEAN
        ax3.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale - 0.00,
                     thseVals[:, 4] ,
                     fmt='2',
                     ecolor=colors[colorI],
                     color=colors[colorI],
                     label=f'x @ {mom} GeV/c',
                     ls='dashed',
                     **lineOptions)

        # Plot dR STD
        ax4.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale - 0.00,
                     thseVals[:, 7] ,
                     fmt='2',
                     ecolor=colors[colorI],
                     color=colors[colorI],
                     label=f'x @ {mom} GeV/c',
                     ls='dashed',
                     **lineOptions)

        colorI += 1

    # Adding plotting parameters

    ax.set_xlabel(f'Misalign Factor')
    ax2.set_xlabel(f'Misalign Factor')
    ax3.set_xlabel(f'Misalign Factor')
    ax4.set_xlabel(f'Misalign Factor')
    ax.set_ylabel(f'Mean [{latexmu}m]')
    ax2.set_ylabel(f'Standard Deviation [{latexmu}m]')
    ax3.set_ylabel(f'Mean [mrad]')
    ax4.set_ylabel(f'Standard Deviation [mrad]')

    ax.xaxis.set_ticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])
    ax2.xaxis.set_ticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])
    ax3.xaxis.set_ticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])
    ax4.xaxis.set_ticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])

    start, end = ax.get_xlim()
    ax.xaxis.set_view_interval(start, 3.172)
    ax2.xaxis.set_view_interval(start, 3.172)
    ax3.xaxis.set_view_interval(start, 3.172)
    ax4.xaxis.set_view_interval(start, 3.172)

    # get handles
    handles, labels = ax.get_legend_handles_labels()
    handles = [h[0] for h in handles]
    ax.legend(handles, labels, loc='center left', numpoints=1, bbox_to_anchor=(1, 0.5))
    handles, labels = ax2.get_legend_handles_labels()
    handles = [h[0] for h in handles]
    ax2.legend(handles, labels, loc='center left', numpoints=1, bbox_to_anchor=(1, 0.5))
    handles, labels = ax3.get_legend_handles_labels()
    handles = [h[0] for h in handles]
    ax3.legend(handles, labels, loc='center left', numpoints=1, bbox_to_anchor=(1, 0.5))
    handles, labels = ax4.get_legend_handles_labels()
    handles = [h[0] for h in handles]
    ax4.legend(handles, labels, loc='center left', numpoints=1, bbox_to_anchor=(1, 0.5))

    fig.tight_layout()
    ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
    fig.savefig(f'mis-{sys.argv[2]}-residual-{outTypeName}-{i}-mean.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig)

    fig2.tight_layout()
    ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
    fig2.savefig(f'mis-{sys.argv[2]}-residual-{outTypeName}-{i}-std.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig2)

    fig3.tight_layout()
    ax3.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
    fig3.savefig(f'mis-{sys.argv[2]}-residual-{outTypeName}-{i}-rot-mean.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig2)

    fig4.tight_layout()
    ax4.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
    fig4.savefig(f'mis-{sys.argv[2]}-residual-{outTypeName}-{i}-rot-std.pdf', dpi=1000, bbox_inches='tight')
    plt.close(fig2)


def plotSensorMatrices(inputJson, outFileName):
    # now, this contains one misalignment, multiple momenta and for each momentum, multiple factors
    sensorVals = []
    momenta = []

    for mom in mainDict.keys():
        momenta.append(float(mom))
        for factor in mainDict[mom]:
            tsenval = np.array(mainDict[mom][factor]['sensors']).flatten()  # this is a 2x3 array with mean and sigma
            sensorVals.append([float(mom)] + [float(factor)] + np.ndarray.tolist(tsenval))
    sensorVals = np.array(sensorVals)

    # we only want unique entries
    momenta = np.array(momenta)
    momenta = np.sort(momenta)
    momenta = np.unique(momenta, axis=0)

    for i in range(len(sizes)):
        omniPlots(sensorVals, i, momenta, 'sensors')


def plotModuleMatrices(inputJson, outFileName):
    # now, this contains one misalignment, multiple momenta and for each momentum, multiple factors
    moduleVals = []
    momenta = []

    for mom in mainDict.keys():
        momenta.append(float(mom))

        for factor in mainDict[mom]:
            tmodval = np.array(mainDict[mom][factor]['modules']).flatten()  # this is a 2x3 array with mean and sigma
            moduleVals.append([float(mom)] + [float(factor)] + np.ndarray.tolist(tmodval))

    moduleVals = np.array(moduleVals)

    # we only want unique entries
    momenta = np.array(momenta)
    momenta = np.sort(momenta)
    momenta = np.unique(momenta, axis=0)

    print(f'momenta: {momenta}')

    for i in range(len(sizes)):

        omniPlots(moduleVals, i, momenta, 'modules')


def plotBoxMatrices(inputJson, outFileName):
    # now, this contains one misalignment, multiple momenta and for each momentum, multiple factors
    boxVals = []
    momenta = []

    for mom in mainDict.keys():
        momenta.append(float(mom))
        for factor in mainDict[mom]:
            tmodval = np.array(mainDict[mom][factor]['box']).flatten()  # this is a 2x3 array with mean and sigma
            boxVals.append([float(mom)] + [float(factor)] + np.ndarray.tolist(tmodval))

    boxVals = np.array(boxVals)

    # we only want unique entries
    momenta = np.array(momenta)
    momenta = np.sort(momenta)
    momenta = np.unique(momenta, axis=0)

    # title = f'Matrix Residuals {pipe} Standard Deviation'
    title = f'Interaction Point Alignment Matrix Residuals {pipe} Mean'

    for i in range(len(sizes)):

        _, ax = plt.subplots(figsize=sizes[i])
        colorI = 0

        for mom in momenta:

            mask = (boxVals[:, 0] == float(mom))
            thseVals = boxVals[mask]

            # sort 2D array by second column
            thseVals = thseVals[thseVals[:, 1].argsort()]

            #! The box rot values are ABSOLUTE, not residual. That means we have to subtract the design value by hand to get the residual
            # take care! I don't know of all data is generated the same way, you have to check each set individually :(
            if True:
                fixScale = 100  # the amount of misalignment at factor 1.0
                fixFactors = np.array([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]) * fixScale
                print(f'Fix Table (Box Plot):\n{fixFactors}')
                thseVals[:, 2] += fixFactors
                thseVals[:, 3] -= fixFactors

            print(f'Ayy lmao I will print this (Box Plot):\n{thseVals}')

            # Plotting the error bars                                                   , yerr=thseVals[:,3]
            ax.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale - 0.00,
                        thseVals[:, 2],
                        fmt='2',
                        ecolor=colors[colorI],
                        color=colors[colorI],
                        label=f'{latexPsi} @ {mom} GeV/c',
                        ls='dashed',
                        **lineOptions)
            ax.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale + 0.00,
                        thseVals[:, 3],
                        fmt='1',
                        ecolor=colors[colorI],
                        color=colors[colorI],
                        label=f'{latexTheta} @ {mom} GeV/c',
                        ls='dashed',
                        **lineOptions)

            colorI += 1

        # Adding plotting parameters

        ax.set_xlabel(f'Misalign Factor')
        ax.set_ylabel(f'Euler Angle Residual [{latexmu}rad]')

        ax.xaxis.set_ticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])

        start, end = ax.get_xlim()
        ax.xaxis.set_view_interval(start, 3.172)

        # get handles
        handles, labels = ax.get_legend_handles_labels()
        # remove the errorbars
        handles = [h[0] for h in handles]
        # use them in the legend
        ax.legend(handles, labels, loc='center left', numpoints=1, bbox_to_anchor=(1, 0.5))
        plt.tight_layout()

        plt.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')

        plt.savefig(
            f'mis-{sys.argv[2]}-residual-box-{i}.pdf',
            #This is simple recomendation for publication plots
            dpi=1000,
            # Plot will be occupy a maximum of available space
            bbox_inches='tight')
        plt.close()
        break


if __name__ == "__main__":

    # read configs?
    if len(sys.argv) != 3:
        print(f'please specify allMatrixValues.json and outputName (sensors, modules or box100)!')
        print('eg: thesisPlots/plotSensorAndModuleMisaligns.py runConfigs/corrected/box100/allMatrixValues.json box100')
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        mainDict = json.load(f)

    plotSensorMatrices(mainDict, sys.argv[2])
    plotModuleMatrices(mainDict, sys.argv[2])
    plotBoxMatrices(mainDict, sys.argv[2])