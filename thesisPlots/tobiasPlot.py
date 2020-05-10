#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Plot Luminosity without and with alignment at 1.5 and 15 GeV for multiple misalignments in a single image.
"""

from pathlib import Path

import json
import numpy as np
import subprocess
import sys

def plot(valuesUncorrected, valuesCorrected, outFileName):
        if len(valuesUncorrected) < 1 or len(valuesCorrected) < 1:
            raise Exception(f'Error! Value array is empty!')
        # print(values)

        # we're guranteed to only have one single misalign type, therefore we're looping over beam momenta
        momenta = []
        print('gathering momenta')

        for i in valuesUncorrected:
            momenta.append(i[0])

        # we only want unique entries
        momenta = np.array(momenta)
        momenta = np.sort(momenta)
        momenta = np.unique(momenta, axis=0)

        sizes = [(15/2.54, 9/2.54), (15/2.54, 6/2.54), (6.5/2.54, 4/2.54)]
        titlesCorr = ['Luminosity Fit Error, Misaligned Sensors', 'Luminosity Fit Error, Misaligned Sensors', 'Luminosity Fit Error']
        titlesUncorr = ['Luminosity Fit Error, Misaligned Sensors', 'Luminosity Fit Error, Misaligned Sensors', 'Luminosity Fit Error']

        import matplotlib.pyplot as plt
        import matplotlib.ticker as plticker

        latexsigma = r'\textsigma{}'
        latexmu = r'\textmu{}'
        latexPercent = r'\%'
        plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        # plt.rcParams["legend.loc"] = 'upper left'
        plt.rcParams["legend.loc"] = 'upper right'
        
        # Defining the figure and figure size
        
        offsetscale = 1.0
        offsets = np.arange(-0.02, 0.03, 0.01)

        for i in range(len(sizes)):

            fig, ax = plt.subplots(figsize=sizes[i])
            colorI = 0
            iMa = 0

            # colors = ['steelblue', 'red', 'green']
            # these are the default colors, why change them
            # colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']
            colors = [u'#d62728', u'#2ca02c']

            markers = ['^','<', 'v', '>']

            for mom in momenta:
                # print(f'for momentum {mom}, we find:')
                mask = (valuesUncorrected[:,0] == mom)# & (values[:, 2] > -0.3)
                thseVals = valuesUncorrected[mask]
                thseValsTwo = valuesCorrected[mask]

                # sort 2D array by second column
                thseVals = thseVals[thseVals[:,1].argsort()]
                print(f'mom: {mom}\ndata:\n{thseVals}\n-----------------\n')

                # Plotting the error bars
                ax.errorbar(thseVals[:,1]*100-2.5*iMa+2.5, thseVals[:,2], yerr=thseVals[:,3], fmt=markers[iMa], ecolor='black', color=colors[colorI], capsize=2, elinewidth=0.6, label=f'{mom} GeV\nMisaligned', ls='dashed', linewidth=0.4)
                ax.errorbar(thseValsTwo[:,1]*100-2.5*iMa+2.5, thseValsTwo[:,2], yerr=thseValsTwo[:,3], fmt=markers[iMa+1], ecolor='black', color=colors[colorI+1], capsize=2, elinewidth=0.6, label=f'{mom} GeV \nAligned', ls='dashed', linewidth=0.4)
                
                loc = plticker.MultipleLocator(base=50.0) # this locator puts ticks at regular intervals
                ax.xaxis.set_major_locator(loc)
                
                iMa += 2
                # colorI += 2

            if False:
                ax.set_title(titlesCorr[i])
            else:
                ax.set_title(titlesUncorr[i])

            ax.set_xlabel(f'Misalignment [{latexmu}m]')
            # ax.set_ylabel(f'Luminosity Error [{self.latexPercent}]')
            ax.set_ylabel(f'$\Delta L$ [{latexPercent}]')
            
            # get handles
            handles, labels = ax.get_legend_handles_labels()
            # remove the errorbars
            handles = [h[0] for h in handles]
            # use them in the legend
            # ax.legend(handles, labels, loc='upper left',numpoints=1)
            # ax.legend(handles, labels, loc='upper right',numpoints=1)
            ax.legend(handles, labels, loc='lower left',numpoints=1, bbox_to_anchor=(1, -0.1))

            plt.tight_layout()

            plt.grid(color='lightgrey', which='major', axis='y', linestyle='dotted')
            plt.grid(color='lightgrey', which='major', axis='x', linestyle='dotted')
            # plt.legend()

            plt.savefig(f'{outFileName}-{i}.pdf',
                        #This is simple recomendation for publication plots
                        dpi=1000, 
                        # Plot will be occupy a maximum of available space
                        bbox_inches='tight')
            plt.close()

if __name__ == "__main__":

    # I want 1.5 and 15 GeV, 0.5, 1.0 and 2.0 (scale to micro meters, easier to read in quarterly report)
    momenta = ['1.5', '15.0']
    misaligns = ['0.50', '1.00', '2.00']
    # corrected = [False, True]

    # read all files
    valuesUncorrected = []
    valuesCorrected = []

    # files are in output/temp/modules-15.0-1.00-False/lumi-values.json

    for mom in momenta:
        for mis in misaligns:
            # find file
            fileNameFalse = f'output/temp/sensors-{mom}-{mis}-False/lumi-values.json'
            fileNameTrue = f'output/temp/sensors-{mom}-{mis}-True/lumi-values.json'

            with open(fileNameFalse, 'r') as f:
                fValF = json.load(f)

            with open(fileNameTrue, 'r') as f:
                fValT = json.load(f)

            # print(f'fVal: {fValF}')
            # print(f'fVal: {fValT}')

            valuesUncorrected.append([float(mom), float(mis), float(fValF['relative_deviation_in_percent'][0]), float(fValF['relative_deviation_error_in_percent'][0])])
            valuesCorrected.append([float(mom), float(mis), float(fValT['relative_deviation_in_percent'][0]), float(fValT['relative_deviation_error_in_percent'][0])])

    valuesUncorrected = np.array(valuesUncorrected)
    valuesCorrected = np.array(valuesCorrected)

    # sort both

    plot(valuesUncorrected, valuesCorrected, 'tobias')