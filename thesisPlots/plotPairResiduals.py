#!/usr/bin/env python3

import sys

# so I can import modules
sys.path.insert(0, '.')
from detail.LMDRunConfig import LMDRunConfig
from alignment.alignerModules import alignerModules
from detail.matrixComparator import moduleComparator
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.colors import LogNorm

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

def dynamicCut(fileUsable, cutPercent=2, use2DCut=True):
    print(f'applying cut...')
    if cutPercent <= 0:
        print(f'no cut, back to sender')
        return fileUsable

    cut = int(len(fileUsable) * cutPercent/100.0)
    
    if not use2DCut:
        print(f'using 1D')
        newDist = fileUsable[:, 6]
        fileUsable = fileUsable[newDist.argsort()]
        fileUsable = fileUsable[cut:-cut]
        
        print(f'done!')
        return fileUsable

    else:

        print(f'using 2D')
        # calculate center of mass of differences
        dRaw = fileUsable[:, 3:6] - fileUsable[:, :3]
        com = np.average(dRaw, axis=0)

        # shift newhit2 by com of differences
        newhit2 = fileUsable[:, 3:6] - com

        # calculate new distance for cut
        dRaw = newhit2 - fileUsable[:, :3]
        newDist = np.power(dRaw[:, 0], 2) + np.power(dRaw[:, 1], 2)

        # sort by new distance
        fileUsable = fileUsable[newDist.argsort()]
        # cut off largest distances, NOT lowest
        fileUsable = fileUsable[:-cut]

        print(f'done!')
        return fileUsable

# to illustrate how the dynamic cut works
def plotResiduals1Dand2D(pairs, overlap):
    fileUsable = pairs

    # slice to separate vectors
    hit1 = fileUsable[:, :3]
    hit2 = fileUsable[:, 3:6]

    # Make C a homogeneous representation of A and B
    hit1H = np.ones((len(fileUsable), 4))
    hit1H[:, 0:3] = hit1
    hit2H = np.ones((len(fileUsable), 4))
    hit2H[:, 0:3] = hit2

    with open("input/detectorMatricesIdeal.json", "r") as f:
        matrices = json.load(f)

    with open("input/detectorOverlapsIdeal.json", "r") as f:
        overlaps = json.load(f)

    path1 = overlaps[overlap]['path1']
    path2 = overlaps[overlap]['path2']

    # make numpy matrix from JSON info
    toSen1 = np.array(matrices[path1]).reshape(4, 4)

    # invert matrices
    toSen1Inv = np.linalg.inv(toSen1)

    # transform hit1 and hit2 to frame of reference of hit1
    hit1T = np.matmul(toSen1Inv, hit1H.T).T
    hit2T = np.matmul(toSen1Inv, hit2H.T).T

    # make differnce hit array
    dHit = hit2T[:, :3] - hit1T[:, :3]

    print(dHit)
    print(f'averages: {np.average(dHit, axis=0)}')

    # plot difference hit array
    fig = plt.figure(figsize=(15/2.54, 12/2.54))
    
    # if use2Dcut:
    #     fig.suptitle('{}\% 2D cut'.format(cutPercent), fontsize=11)
    # else:
    #     fig.suptitle('{}\% 1D cut'.format(cutPercent), fontsize=11)

    histA = fig.add_subplot(2, 3, 1)
    histA.hist(fileUsable[:, 6]*1e1, bins=150, log=True, range=[0.25, 1.2])  # this is only the z distance
    # histA.set_title('Distance')   # change to mm!
    # histA.set_xlabel('d [mm]')
    histA.set_ylabel('Count (log)')

    histB = fig.add_subplot(2, 3, 4)
    histB.hist2d(dHit[:, 0]*10, dHit[:, 1]*10, bins=150, norm=LogNorm(), range=[[-01.3, 01.3], [-01.3, 01.3]], label='Count (log)')
    # histB.set_title('2D Distance')
    histB.yaxis.tick_right()
    histB.yaxis.set_ticks_position('left')
    histB.set_xlabel('dx [mm]')
    histB.set_ylabel('dy [mm]')
    histB.tick_params(direction='out')
    histB.yaxis.set_label_position("left")

    #* -------------- plot 1D Cut
    
    
    
    
    
    
    #* -------------- plot 2D Cut

    fig.tight_layout()
    fig.savefig('test001.pdf')

def readBinaryFile(filename, overlap):
    # read file
    print(f'reading binary pair file')
    f = open(filename, "r")
    fileRaw = np.fromfile(f, dtype=np.double)

    # ignore header
    fileUsable = fileRaw[6:]
    Npairs = int(len(fileUsable)/7)

    # reshape to array with one pair each line
    fileUsable = fileUsable.reshape(Npairs, 7)
    print(f'done!')
    return fileUsable

def readPairFile(fileName):
    maxPairs = 1e9
    try:
        PairData = np.load(fileName)
    except:
        raise Exception(f'ERROR! Can not read {fileName}!')

    # reduce to maxPairs
    if PairData.shape > (7, int(maxPairs)):
        PairData = PairData[..., :int(maxPairs)]

    # the new python Root Reader stores them slightly different...
    PairData = np.transpose(PairData)
    return PairData

def test():
    overlap = '10'

    fileName = f'input/binaryPairFiles/pairs-{overlap}.npy'
    pairs = readPairFile(fileName)

    print(f'no of pairs: {len(pairs)}')
    
    plotResiduals1Dand2D(pairs, overlap)

def plotFourPlanes():

    area = '1'

    # read binary Pairs for corridor
    file1 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-{area}-cm.bin'
    file2 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-10{area}-cm.bin'
    file3 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-20{area}-cm.bin'
    file4 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-30{area}-cm.bin'

    pairs1 = readBinaryFile(file1, '0')
    pairs2 = readBinaryFile(file2, '0')
    pairs3 = readBinaryFile(file3, '0')
    pairs4 = readBinaryFile(file4, '0')

    dHit1 = pairs1[:,:3] - pairs1[:,3:6]
    dHit2 = pairs2[:,:3] - pairs2[:,3:6]
    dHit3 = pairs3[:,:3] - pairs3[:,3:6]
    dHit4 = pairs4[:,:3] - pairs4[:,3:6]

    dHit1 = dHit1 * -1 
    dHit2 = dHit2 * -1 
    dHit3 = dHit3 * -1 
    dHit4 = dHit4 * -1 

    Nbins = 150
    Srasterized = True

    # plot difference hit array
    fig = plt.figure(figsize=(15/2.54, 5/2.54))
    
    ax1 = fig.add_subplot(1, 4, 1)
    ax1.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax1.set_title('Plane 1')
    ax1.yaxis.set_ticks_position('both')
    ax1.set_xlabel('dx [mm]')
    ax1.set_ylabel('dy [mm]')
    ax1.tick_params(direction='in')
    ax1.yaxis.set_label_position('left')
    ax1.set_xlim([-01.2, 01.2])
    ax1.set_ylim([-01.2, 01.2])

    ax2 = fig.add_subplot(1, 4, 2, sharey=ax1)
    ax2.hist2d(dHit2[:, 0]*10, dHit2[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax2.set_title('Plane 2')
    ax2.yaxis.set_ticks_position('both')
    ax2.set_xlabel('dx [mm]')
    ax2.tick_params(direction='in')
    ax2.set_xlim([-01.2, 01.2])
    ax2.set_ylim([-01.2, 01.2])
    ax2.set_yticklabels([])

    ax3 = fig.add_subplot(1, 4, 3, sharey=ax1)
    ax3.hist2d(dHit3[:, 0]*10, dHit3[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax3.set_title('Plane 3')
    ax3.yaxis.set_ticks_position('both')
    ax3.set_xlabel('dx [mm]')
    ax3.tick_params(direction='in')
    ax3.set_xlim([-01.2, 01.2])
    ax3.set_ylim([-01.2, 01.2])
    ax3.set_yticklabels([])

    ax4 = fig.add_subplot(1, 4, 4, sharey=ax1)
    ax4.hist2d(dHit4[:, 0]*10, dHit4[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax4.set_title('Plane 4')
    ax4.yaxis.set_ticks_position('both')
    ax4.set_xlabel('dx [mm]')
    ax4.tick_params(direction='in')
    ax4.set_xlim([-01.2, 01.2])
    ax4.set_ylim([-01.2, 01.2])
    ax4.set_yticklabels([])

    fig.tight_layout()
    fig.subplots_adjust(hspace = .001)
    fig.savefig('pairs-dxdy.pdf', dpi=300, bbox_inches='tight', pad_inches = 0)

def plotMultipleCuts():
    area = '1'

    # read binary Pairs for corridor
    file1 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-30{area}-cm.bin'

    pairs1 = readBinaryFile(file1, '0')

    dHit1 = pairs1[:,3:6] - pairs1[:,:3]
    Nbins = 150
    Srasterized = True

    # plot difference hit array
    fig = plt.figure(figsize=(15/2.54, 5/2.54))
    
    ax1 = fig.add_subplot(1, 4, 1)
    ax1.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax1.set_title('No Cut')
    ax1.yaxis.set_ticks_position('both')
    ax1.set_xlabel('dx [mm]')
    ax1.set_ylabel('dy [mm]')
    ax1.tick_params(direction='in')
    ax1.yaxis.set_label_position('left')
    ax1.set_xlim([-01.2, 01.2])
    ax1.set_ylim([-01.2, 01.2])

    pairs1 = dynamicCut(pairs1, 0.5)
    dHit1 = pairs1[:,3:6] - pairs1[:,:3]

    ax2 = fig.add_subplot(1, 4, 2, sharey=ax1)
    ax2.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax2.set_title('0.5 \% Cut')
    ax2.yaxis.set_ticks_position('both')
    ax2.set_xlabel('dx [mm]')
    ax2.tick_params(direction='in')
    ax2.set_xlim([-01.2, 01.2])
    ax2.set_ylim([-01.2, 01.2])
    ax2.set_yticklabels([])

    pairs1 = dynamicCut(pairs1, 1.0)
    dHit1 = pairs1[:,3:6] - pairs1[:,:3]

    ax3 = fig.add_subplot(1, 4, 3, sharey=ax1)
    ax3.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax3.set_title('1.0 \% Cut')
    ax3.yaxis.set_ticks_position('both')
    ax3.set_xlabel('dx [mm]')
    ax3.tick_params(direction='in')
    ax3.set_xlim([-01.2, 01.2])
    ax3.set_ylim([-01.2, 01.2])
    ax3.set_yticklabels([])

    pairs1 = dynamicCut(pairs1, 2.0)
    dHit1 = pairs1[:,3:6] - pairs1[:,:3]

    ax4 = fig.add_subplot(1, 4, 4, sharey=ax1)
    ax4.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax4.set_title('2.0 \% Cut')
    ax4.yaxis.set_ticks_position('both')
    ax4.set_xlabel('dx [mm]')
    ax4.tick_params(direction='in')
    ax4.set_xlim([-01.2, 01.2])
    ax4.set_ylim([-01.2, 01.2])
    ax4.set_yticklabels([])

    fig.tight_layout()
    fig.subplots_adjust(hspace = .001)
    fig.savefig('pairs-dxdy-cuts.pdf', dpi=300, bbox_inches='tight', pad_inches = 0)

def plot1Dvs2DCuts():
    area = '1'

    # read binary Pairs for corridor
    file1 = f'input/2018-08-himster2-misalign-200u/binaryPairFiles/pairs-30{area}-cm.bin'

    pairs1 = readBinaryFile(file1, '0')

    dHit1 = pairs1[:,3:6] - pairs1[:,:3]
    Nbins = 150
    Srasterized = True

    # plot difference hit array
    fig = plt.figure(figsize=(15/2.54, 10.5/2.54))
    
    ax1 = fig.add_subplot(2, 3, 4)
    ax1.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax1.yaxis.set_ticks_position('both')
    ax1.set_xlabel('dx [mm]')
    ax1.set_ylabel('dy [mm]')
    ax1.tick_params(direction='in')
    ax1.yaxis.set_label_position('left')
    ax1.set_xlim([-01.2, 01.2])
    ax1.set_ylim([-01.2, 01.2])

    ax4 = fig.add_subplot(2, 3, 1)
    ax4.hist(pairs1[:, 6]*1e1, bins=150, log=True, range=[0.25, 1.2], rasterized=Srasterized)  # this is only the z distance
    ax4.set_title('No Cut')
    ax4.set_xlabel('d [mm]')
    ax4.set_ylabel('Count (log)')

    pairsN = dynamicCut(pairs1, 2, False)
    dHit1 = pairsN[:,3:6] - pairsN[:,:3]

    ax5 = fig.add_subplot(2, 3, 2, sharey=ax4)
    ax5.hist(pairsN[:, 6]*1e1, bins=150, log=True, range=[0.25, 1.2], rasterized=Srasterized)  # this is only the z distance
    ax5.set_title('1D Cut')
    ax5.set_xlabel('d [mm]')

    ax2 = fig.add_subplot(2, 3, 5, sharey=ax1)
    ax2.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax2.yaxis.set_ticks_position('both')
    ax2.set_xlabel('dx [mm]')
    ax2.tick_params(direction='in')
    ax2.set_xlim([-01.2, 01.2])
    ax2.set_ylim([-01.2, 01.2])

    pairsN = dynamicCut(pairs1, 2)
    dHit1 = pairsN[:,3:6] - pairsN[:,:3]

    ax6 = fig.add_subplot(2, 3, 3, sharey=ax4)
    ax6.hist(pairsN[:, 6]*1e1, bins=150, log=True, range=[0.25, 1.2], rasterized=Srasterized)  # this is only the z distance
    ax6.set_title('2D Cut')
    ax6.set_xlabel('d [mm]')

    ax3 = fig.add_subplot(2, 3, 6, sharey=ax1)
    ax3.hist2d(dHit1[:, 0]*10, dHit1[:, 1]*10, bins=Nbins, norm=LogNorm(), rasterized=Srasterized)
    ax3.yaxis.set_ticks_position('both')
    ax3.set_xlabel('dx [mm]')
    ax3.tick_params(direction='in')
    ax3.set_xlim([-01.2, 01.2])
    ax3.set_ylim([-01.2, 01.2])

    fig.tight_layout()
    # fig.subplots_adjust(hspace = .25)
    fig.savefig('pairs-dxdy-1Dvs2D.pdf', dpi=300, bbox_inches='tight', pad_inches = 0)

if __name__ == "__main__":
    print(f'greetings human.')
    # test()
    # plotFourPlanes()
    # plotMultipleCuts()
    # plotResiduals1Dand2D()
    plot1Dvs2DCuts()
    