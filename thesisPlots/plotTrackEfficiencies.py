#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import uproot
import sys

latexmu = r'\textmu{}'
latexsigma = r'\textsigma{}'
latexPercent = r'\%'
plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')
"""
TODO: At the moment, I only have the TrksQA files from the aligned cases. So I can only do this for the aligned cases.
"""

useMultiSeed = False


def saveAllMomenta(outFileName):

    values = np.load('input/effValuesNonAligned.npy')
    # values = np.load('input/effValuesAligned.npy')
    # values = np.load('input/effValuesAlignedMulti.npy')

    values = values.astype(np.float)

    # we're guranteed to only have one single misalign type, therefore we're looping over beam momenta
    momenta = ['1.5', '4.06', '8.9', '11.91', '15.0']

    sizes = [(15 / 2.54, 9 / 2.54), (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
    titles = ['Luminosity Fit Error, With Alignment', 'Luminosity Fit Error, With Alignment', 'Luminosity Fit Error']

    import matplotlib.pyplot as plt

    latexsigma = r'\textsigma{}'
    latexmu = r'\textmu{}'
    latexEpsilon = r'\epsilon'
    slashtext = r'\text'
    latexPercent = r'\%'
    plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

    plt.rcParams["legend.loc"] = 'upper right'

    # Defining the figure and figure size

    offsetscale = 1.0
    offsets = np.arange(-0.02, 0.03, 0.01)

    for i in range(len(sizes)):

        fig, ax = plt.subplots(figsize=sizes[i])
        colorI = 0

        # these are the default colors, why change them
        colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

        for mom in momenta:
            mask = (values[:, 0] == float(mom))  # & (values[:, 2] > -0.3)
            thseVals = values[mask]

            # sort 2D array by second column
            thseVals = thseVals[thseVals[:, 1].argsort()]

            if useMultiSeed:

                # print(f'\n\nOkay, these are the values for {mom} :\n{thseVals}')

                newArray = []
                # ideally, get the factors from the array, but at this point I don't really care anymore
                for fac in ['0.0', '0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:
                    facMask = (thseVals[:, 1] == float(fac))
                    maskedArray = thseVals[facMask]

                    if len(maskedArray) < 1:
                        continue

                    maskedArray[:, 2] = maskedArray[:, 2] * (100 / 2)  # the baseline was calculated on half a data set, hence the / 2

                    mean = np.mean(maskedArray[:, 2], axis=0)
                    std = np.std(maskedArray[:, 2], axis=0)

                    if not np.isnan(mean) and not np.isnan(std):
                        newLine = [float(mom), float(fac), mean, std]
                        newArray.append(newLine)
                        # print(f'I will add this line: {newLine}')

                newArray = np.array(newArray)

                # print(f'This is the newArray that I\'ll plot:\n{newArray}')

                # add 100% efficiency at misalign 0.0 for clarity (hey it's not cheating)
                newArray = np.vstack(([float(mom), 0.0, 100.0, 0.0], newArray))

                ax.errorbar(newArray[:, 1] + offsets[colorI] * offsetscale,
                            newArray[:, 2],
                            yerr=newArray[:, 3],
                            fmt='d',
                            ecolor=colors[colorI],
                            color=colors[colorI],
                            capsize=2,
                            elinewidth=0.6,
                            label=f'{mom} GeV',
                            ls='dashed',
                            linewidth=0.4)

            else:

                # add 100% efficiency at misalign 0.0 for clarity (hey it's not cheating)
                thseVals = np.vstack(([float(mom), 0.0, 1.0], thseVals))
                # thseVals[:, 2] = thseVals[:, 2] / 2.0  # man I love numpy

                # Plotting the error bars
                ax.errorbar(
                    thseVals[:, 1] + offsets[colorI] * offsetscale,
                    thseVals[:, 2] * 1e2,
                    #yerr=thseVals[:, 3],
                    fmt='d',
                    ecolor='black',
                    color=colors[colorI],
                    capsize=2,
                    elinewidth=0.6,
                    label=f'{mom} GeV',
                    ls='dashed',
                    linewidth=0.4)
            colorI += 1

        ax.set_xlabel(f'Misalign Factor')
        ax.set_ylabel(r'$ \epsilon_{\textrm{misalignment}} $ [\%]')

        # set ticks exactly to the misalign factors
        start, end = ax.get_xlim()
        ax.xaxis.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])
        ax.xaxis.set_view_interval(start, 3.172)

        # get handles
        handles, labels = ax.get_legend_handles_labels()
        # remove the errorbars
        handles = [h[0] for h in handles]
        # use them in the legend
        # ax.legend(handles, labels, loc='upper left',numpoints=1)
        # ax.legend(handles, labels, loc='upper right',numpoints=1)
        ax.legend(handles, labels, loc='best', numpoints=1)

        # set ticks exactly to the misalign factors
        start, end = ax.get_xlim()

        # draw vertical line to separate aligned and misaligned cases
        plt.axvline(x=0.125, color=r'#aa0000', linestyle='-', linewidth=0.5)

        plt.tight_layout()

        plt.grid(color='grey', which='major', axis='y', linestyle=':', linewidth=0.5)
        plt.grid(color='grey', which='major', axis='x', linestyle=':', linewidth=0.5)
        # plt.legend()

        plt.savefig(
            f'{outFileName}-{i}.pdf',
            #This is simple recomendation for publication plots
            dpi=1000,
            # Plot will be occupy a maximum of available space
            bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    print('greetings, human')
    # saveAllMomenta('output/trackEfficienciesAlignedMulti.pdf')
    saveAllMomenta('output/trackEfficienciesNonAlignedMulti.pdf')
    # saveAllMomenta('output/trackEfficienciesAligned.pdf')
    # saveAllMomenta('output/trackEfficienciesNonAligned.pdf')