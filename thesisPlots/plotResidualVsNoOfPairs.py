#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerSensors import alignerSensors
from detail.matrixComparator import overlapComparator
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

def calcVsPairs():
    resultDict = {}

    numberRange1 = np.arange(100,1001, 100)
    numberRange2 = np.arange(1000,10001, 1000)
    numberRange3 = np.arange(10000,100001, 10000)
    numberRange4 = np.arange(100010,400001, 100000)

    allNumbers = np.concatenate((numberRange1,numberRange2,numberRange3,numberRange4))

    print(f'len: {len(allNumbers)}\n{allNumbers}')

    sensorAligner = alignerSensors.fromRunConfig(LMDRunConfig.fromJSON('runConfigs/uncorrected/sensors/15.0/factor-1.00.json'))
    
    for nPairs in allNumbers:

        matrixFile = f'output/residualVsPairs/alMat-sensorOverlaps-1.00.json'

        #! run aligner (find only overlap)
        sensorAligner.maxPairs = nPairs
        sensorAligner.findMatrices('input/npPairsHuge/reduced/')
        sensorAligner.saveOverlapMatrices(matrixFile)

        #! run comparator
        comparator = overlapComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/sensors/15.0/factor-1.00.json'))
        comparator.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
        comparator.loadPerfectDetectorOverlaps('input/detectorOverlapsIdeal.json')
        # comparator.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-sensors-1.00.json')
        comparator.loadDesignMisalignments('output/residualVsPairs/misMat-sensors-1.00.json')
        comparator.loadSensorAlignerOverlapMatrices(matrixFile)
        
        result = comparator.saveHistogram(f'output/residualVsPairs/{nPairs}-residuals-modules.pdf')
        result = np.ndarray.tolist(result.flatten())

        with open(f'output/residualVsPairs/{nPairs}-VsResiduals.json', 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

        resultDict[str(nPairs)] = result

    print(resultDict)

    with open(f'output/residualVsPairs/nTrksVsResiduals-100.json', 'w') as f:
        json.dump(resultDict, f, indent=2, sort_keys=True)

def calcVsIterations():
    noOfIterations = np.arange(0,20, 1)
    resultDict = {}

    trackNPYFile = Path('output/residualVsPairs/tracks.npy')
    trackFile = Path('output/residualVsPairs/factor-1.00-large.json')
    # alignerMod.readTracks(trackNPYFile, isNumpy=True)
    alignerMod = alignerModules()
    alignerMod.readTracks(trackFile, isNumpy=False)
    
    for nIterations in noOfIterations:

        matrixFile = f'output/residualVsIterations/alMat-modules-1.00.json'

        alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
        alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
        alignerMod.iterations = nIterations
        alignerMod.alignModules(maxNoOfTracks=int(50e3))
        alignerMod.saveMatrices(matrixFile)

        #! run comparator
        comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
        comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
        comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
        comp.loadAlignerMatrices(matrixFile)
        result = comp.saveHistogram(f'output/residualVsIterations/{nIterations}-residuals-modules.pdf')
        result = np.ndarray.tolist(result.flatten())

        with open(f'output/residualVsIterations/{nIterations}-VsResiduals.json', 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)

        resultDict[str(nIterations)] = result

    print(resultDict)

    with open(f'output/residualVsPairs/nTrksVsResiduals-100.json', 'w') as f:
        json.dump(resultDict, f, indent=2, sort_keys=True)

def plotNPairs():

    if True:
        jsonFiles = Path('output/residualVsPairs/').glob('[0-9]*.json')

        lines = []
        for file in jsonFiles:
            m = re.search(r'residualVsPairs/(\d+)-VsResiduals.json', str(file))
            if m:
                nTrk = float(m.group(1))
            else:
                continue

            with open(file, 'r') as f:
                values = np.array(json.load(f)).reshape((360,3))
                mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
                line = [float(nTrk), *mean, *sigma]
                lines.append(line)

    else:
        with open(f'output/residualVsPairs/nTrksVsResiduals-Hand.json', 'r') as f:
            data = json.load(f)
        lines = []
        for nTrk in data:
            values = np.array(data[nTrk]).reshape((360, 3))
            mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
            line = [float(nTrk), *mean, *sigma]
            lines.append(line)

    lines = np.array(lines)
    lines = lines[lines[:,0].argsort()]

    # plot it
    # title = f'Matrix Residuals {pipe} Standard Deviation'
    title = f'Sensor Alignment Matrix Residuals {pipe} Mean'
    title2 = f'Sensor Alignment Matrix Residuals {pipe} Standard Deviation'
    
    for i in range(len(sizes)):

        fig, ax = plt.subplots(figsize=sizes[i])
        fig2, ax2 = plt.subplots(figsize=sizes[i])
        colorI = 0

        # Plotting the error bars
        ax.errorbar(lines[:,0], lines[:,1], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexmu}x', **lineOptions)
        ax.errorbar(lines[:,0], lines[:,2], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexmu}y',**lineOptions)

        ax2.errorbar(lines[:,0], lines[:,4], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexsigma}x', **lineOptions)
        ax2.errorbar(lines[:,0], lines[:,5], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexsigma}y', **lineOptions)
            
        # Adding plotting parameters
        ax.set_title(title)
        ax2.set_title(title2)

        ax.set_xlabel(f'Number of Pairs (log scale)')
        ax.set_ylabel(f'Mean [{latexmu}m]')
        
        ax2.set_ylabel(f'Standard Deviation (log) [{latexmu}m]')
        ax2.set_xlabel(f'Number of Pairs (log scale)')
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
        ax2.grid(color='lightgrey', which='major', axis='x', linestyle='dotted')
        ax2.grid(color='lightgrey', which='both', axis='y', linestyle='dotted')
        ax2.set_xscale('log')
        ax2.set_xlim((50, 5e5))
        ax2.set_yscale('log')

        
        fig.tight_layout()
        fig.savefig(f'output/residualVsPairs/noOfTrksVsResidual-mean.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig)

        fig2.tight_layout()
        fig2.savefig(f'output/residualVsPairs/noOfTrksVsResidual-std.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig2)

        break

def plotNIter():

    if True:
        jsonFiles = Path('output/residualVsPairs/').glob('[0-9]*.json')

        lines = []
        for file in jsonFiles:
            m = re.search(r'residualVsPairs/(\d+)-VsResiduals.json', str(file))
            if m:
                nTrk = float(m.group(1))
            else:
                continue

            with open(file, 'r') as f:
                values = np.array(json.load(f)).reshape((360,3))
                mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
                line = [float(nTrk), *mean, *sigma]
                lines.append(line)

    else:
        with open(f'output/residualVsPairs/nTrksVsResiduals-Hand.json', 'r') as f:
            data = json.load(f)
        lines = []
        for nTrk in data:
            values = np.array(data[nTrk]).reshape((360, 3))
            mean, sigma = np.average(values, axis=0), np.std(values, axis=0)
            line = [float(nTrk), *mean, *sigma]
            lines.append(line)

    lines = np.array(lines)
    lines = lines[lines[:,0].argsort()]

    if len(lines) < 1:
        print(f'Error! No lines!')
        sys.exit(1)

    # plot it
    # title = f'Matrix Residuals {pipe} Standard Deviation'
    title = f'Sensor Alignment Matrix Residuals {pipe} Mean'
    title2 = f'Sensor Alignment Matrix Residuals {pipe} Standard Deviation'
    
    for i in range(len(sizes)):

        fig, ax = plt.subplots(figsize=sizes[i])
        fig2, ax2 = plt.subplots(figsize=sizes[i])
        colorI = 0

        # Plotting the error bars
        ax.errorbar(lines[:,0]+1, lines[:,1], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexmu}x', **lineOptions)
        ax.errorbar(lines[:,0]+1, lines[:,2], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexmu}y',**lineOptions)

        ax2.errorbar(lines[:,0]+1, lines[:,4], fmt='.', ecolor=colors[colorI], color=colors[colorI], label=f'{latexsigma}x', **lineOptions)
        ax2.errorbar(lines[:,0]+1, lines[:,5], fmt='.', ecolor=colors[colorI+1], color=colors[colorI+1], label=f'{latexsigma}y', **lineOptions)
            
        # Adding plotting parameters
        ax.set_title(title)
        ax2.set_title(title2)

        ax.set_xlabel(f'Number of Iterations')
        ax.set_ylabel(f'Mean [{latexmu}m]')
        
        ax2.set_xlabel(f'Number of Iterations')
        ax2.set_ylabel(f'Standard Deviation [{latexmu}m]')
        # get handles
        handles, labels = ax.get_legend_handles_labels()
        handles = [h[0] for h in handles]
        ax.legend(handles, labels, loc='center left',numpoints=1)#, bbox_to_anchor=(1, 0.5))
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
        ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
        # ax.set_xscale('log')
        ax.set_xlim((-1, 21))
        # ax.set_yscale('log')
        # ax.set_ylim((0, 100))

        handles, labels = ax2.get_legend_handles_labels()
        handles = [h[0] for h in handles]
        ax2.legend(handles, labels, loc='lower left',numpoints=1)#, bbox_to_anchor=(1, 0.5))
        ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
        ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
        # ax2.set_xscale('log')
        ax2.set_xlim((-1, 21))
        # ax2.set_yscale('log')
        # ax2.set_ylim((0, 100))

        
        fig.tight_layout()
        fig.savefig(f'output/residualVsIterations/noOfIterVsResidual-mean.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig)

        fig2.tight_layout()
        fig2.savefig(f'output/residualVsIterations/noOfIterVsResidual-std.pdf', dpi=1000, bbox_inches='tight')
        plt.close(fig2)

        break

if __name__ == "__main__":

    # calcVsPairs()
    plotNPairs()