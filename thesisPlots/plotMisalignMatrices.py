#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerModules import alignerModules
from detail.matrixComparator import moduleComparator
from detail.matrixComparator import combinedComparator
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

if __name__ == "__main__":

    # #! run comparator
    # comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
    # comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    # comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json')
    # comp.loadAlignerMatrices('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
    # comp.setSize((12/2.54,8/2.54))
    # result = comp.saveHistogram(f'modules-1.0.pdf')
    # result = np.ndarray.tolist(result.flatten())

     #! run comparator
    comp = combinedComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
    comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json')
    comp.loadAlignerMatrices('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-sensors-3.00.json')
    # comp.setSize((12/2.54,8/2.54))
    result = comp.saveHistogram(f'sensors-1.0.pdf')
    result = np.ndarray.tolist(result.flatten())
