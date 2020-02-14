#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerModules import alignerModules
from detail.matrixComparator import moduleComparator
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from pathlib import Path
import sys, subprocess, json, re
import numpy as np

np.set_printoptions(precision=3, suppress=True)

latexsigma = r'\textsigma{}'
latexmu = r'\textmu{}'
latexPercent = r'\%'
pipe = r'\textbar{}'
latexPsi = r'\textPsi{}'
latexTheta = r'\textTheta{}'
latexPhi = r'\textPhi{}'

plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

lineOptions = {'capsize':2, 'elinewidth':0.6, 'linewidth':0.4, 'markersize': 5.0, 'ls':'dashed'}

sizes = [(15/2.54, 6/2.54), (15/2.54, 4/2.54), (6.5/2.54, 4/2.54)]
offsetscale = 2.5
offsets = np.arange(-0.02, 0.03, 0.01)
colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

def dummy():
    # from good-ish tracks

    noOftracks = np.arange(150,201, 100)

    resultDict = {}

    trackNPYFile = Path('output/residualVsTrks/tracks.npy')
    trackFile = Path('output/residualVsTrks/factor-1.00-large.json')
    # alignerMod.readTracks(trackNPYFile, isNumpy=True)
    alignerMod = alignerModules()
    alignerMod.readTracks(trackFile, isNumpy=False)
    
    for nTracks in noOftracks:

        matrixFile = f'output/residualVsTrks/alMat-modules-1.00.json'

        alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
        alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
        alignerMod.alignModules(maxNoOfTracks=nTracks)
        alignerMod.saveMatrices(matrixFile)

        #! run comparator
        comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
        comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
        comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
        comp.loadAlignerMatrices(matrixFile)
        result = comp.saveHistogram(f'output/residualVsTrks/{nTracks}-residuals-modules.pdf')
        result = np.ndarray.tolist(result.flatten())

        with open(f'output/residualVsTrks/{nTracks}-VsResiduals.json', 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

        resultDict[str(nTracks)] = result

    print(resultDict)

    with open(f'output/residualVsTrks/nTrksVsResiduals-100.json', 'w') as f:
        json.dump(resultDict, f, indent=2, sort_keys=True)

def plot():

    if True:
        jsonFiles = Path('output/residualVsTrks/').glob('[0-9]*.json')

        lines = []
        for file in jsonFiles:
            m = re.search(r'ualVsTrks/(\d+)-VsResiduals.js', str(file))
            if m:
                nTrk = float(m.group(1))
            else:
                continue

            with open(file, 'r') as f:
                values = np.array(json.load(f)).reshape((40,3))
                mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
                line = [float(nTrk), *mean, *sigma]
                lines.append(line)

    else:
        with open(f'output/residualVsTrks/nTrksVsResiduals-Hand.json', 'r') as f:
            data = json.load(f)
        lines = []
        for nTrk in data:
            values = np.array(data[nTrk]).reshape((40, 3))
            mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
            line = [float(nTrk), *mean, *sigma]
            lines.append(line)

    lines = np.array(lines)
    lines = lines[lines[:,0].argsort()]

    # plot it
    # title = f'Matrix Residuals {pipe} Standard Deviation'
    title = f'Module Alignment Matrix Residuals {pipe} Mean'
    title2 = f'Module Alignment Matrix Residuals {pipe} Standard Deviation'
    
    for i in range(len(sizes)):

        fig, ax = plt.subplots(figsize=sizes[i])
        fig2, ax2 = plt.subplots(figsize=sizes[i])
        colorI = 0

        # Plotting the error bars
        ax.errorbar(lines[:,0]-10, lines[:,1], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexmu}x', **lineOptions)
        ax.errorbar(lines[:,0]+10, lines[:,2], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexmu}y',**lineOptions)

        ax2.errorbar(lines[:,0]-10, lines[:,4], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexsigma}x', **lineOptions)
        ax2.errorbar(lines[:,0]+10, lines[:,5], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexsigma}y', **lineOptions)
            
        # Adding plotting parameters
        ax.set_title(title)
        ax2.set_title(title2)

        ax.set_xlabel(f'Number of Tracks (log scale)')
        ax.set_ylabel(f'Mean [{latexmu}m]')
        
        ax2.set_ylabel(f'Standard Deviation [{latexmu}m]')
        ax2.set_xlabel(f'Number of Tracks (log scale)')
        # get handles
        handles, labels = ax.get_legend_handles_labels()
        handles = [h[0] for h in handles]
        ax.legend(handles, labels, loc='center left',numpoints=1)#, bbox_to_anchor=(1, 0.5))
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
        ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
        ax.set_xscale('log')
        ax.set_xlim((50, 5e5))
        # ax.set_yscale('log')

        handles, labels = ax2.get_legend_handles_labels()
        handles = [h[0] for h in handles]
        ax2.legend(handles, labels, loc='lower left',numpoints=1)#, bbox_to_anchor=(1, 0.5))
        ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
        ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
        ax2.set_xscale('log')
        ax2.set_xlim((50, 5e5))
        # ax2.set_yscale('log')

        
        fig.tight_layout()
        fig.savefig(f'output/residualVsTrks/noOfTrksVsResidual-mean.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig)

        fig2.tight_layout()
        fig2.savefig(f'output/residualVsTrks/noOfTrksVsResidual-std.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig2)

        break

if __name__ == "__main__":
    # dummy()
    plot()