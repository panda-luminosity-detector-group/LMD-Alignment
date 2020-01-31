#!usr/bin/env python3
from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import uproot
import sys

np.set_printoptions(precision=3, suppress=True)

# TODO: use uniform row major OR column major format, not both ffs

def getIPfromTrksQA(filename, cut=2.0, sensor=-1, module=-1, plane=-1, half=-1, maxTracks=0):

    resArray = np.zeros((6)).T
    
    try:
        # open the root trees in a TChain-like manner
        print(f'reading files {filename}...')
        for array in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):
            resArray = np.vstack((resArray, cleanArray(array)))

    except Exception as e:
        print('error occured:')
        print(e)
        sys.exit(0)

    return resArray
    
# removes all tracks with TrkRecStatus != 0
def cleanArray(arrayDict):

    recStatus = arrayDict[b'LMDTrackQ.fTrkRecStatus'].flatten()
    half = arrayDict[b'LMDTrackQ.fHalf'].flatten()
    module = arrayDict[b'LMDTrackQ.fModule'].flatten()
    recX = arrayDict[b'LMDTrackQ.fXrec'].flatten()
    recY = arrayDict[b'LMDTrackQ.fYrec'].flatten()
    recZ = arrayDict[b'LMDTrackQ.fZrec'].flatten()

    retArray = np.array([recStatus, half, module, recX, recY, recZ]).T
    recStatusMask = (recStatus == 0)
    
    return retArray[recStatusMask]

def extractIP(cleanArray, module=-1, half=-1):

    ipArr = np.ones( (len(cleanArray), 4) )
    ipArr[:,:3] = cleanArray[:,3:6]
    return ipArr

def quantileCut(cleanArray, cut):

    if cut == 0:
        return cleanArray

    # calculate cut length
    cut = int(len(cleanArray) * (cut / 100))

    # don't use average, some values are far too large, median is a better estimation
    comMed = np.median(cleanArray[:,3:6], axis=0)

    # sort by distance and cut largest
    distVec = cleanArray[:,3:6] - comMed
    distVecNorm = np.linalg.norm(distVec, axis=1)
    cleanArray = cleanArray[distVecNorm.argsort()]
    cleanArray = cleanArray[:-cut]

    return cleanArray


if __name__ == "__main__":
    print('oh hai!')

    import matplotlib.pyplot as plt

    latexmu = r'\textmu{}'
    latexsigma = r'\textsigma{}'
    latexPercent = r'\%'
    plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

    # read some 10 files
    # this is the same as in the actual align code
    # box = 'box-0.0'

    if False:
        for box in ['box-0.0', 'box-1.0', 'box-1.5', 'box-2.0']:
            files = f'/home/remus/temp/rootcompare/{box}/Lumi_TrksQA_1000*.root'
            
            array = getIPfromTrksQA(files)
            
            for cut in [0, 2, 4, 6]:
                
                array2 = quantileCut(array, cut)
                ip = extractIP(array2)
                
                mus = np.average(ip, axis=0)
                sigmas = np.std(ip, axis=0)

                fig, ax = plt.subplots(figsize=(7/2.54 , 6/2.54))

                # plot IP x vs y
                ax.hist2d(ip[:,0], ip[:,1], bins=50, norm=LogNorm(), rasterized=True)
                ax.set_xlabel(f'$i_x$, {latexmu}x={np.round(mus[0], 1)}, {latexsigma}x={np.round(sigmas[0], 1)} [cm]')
                ax.set_ylabel(f'$i_y$, {latexmu}y={np.round(mus[1], 1)}, {latexsigma}y={np.round(sigmas[1], 1)} [cm]')
                fig.tight_layout()
                # plt.show()
                #plt.figure(figsize=(10/2.54, 10/2.54))
                fig.savefig(f'output/ipDistribution/{box}-cut{cut}.pdf', dpi=1000, bbox_inches='tight')
                plt.close(fig)

    # plot sigma vs Ntracks, select cutoff as appropriate
    if False:
        cuts = np.arange(0.5, 5.1, 0.1)

        for box in ['box-0.0', 'box-1.0', 'box-1.5', 'box-2.0']:
            files = f'/home/remus/temp/rootcompare/{box}/Lumi_TrksQA_1000*.root'
            cut = 0.0
            
            muArr = []
            sigmaArr = []
            
            array = getIPfromTrksQA(files)
            
            for cut in cuts:
                #print(f'cut: {cut}')
                
                array2 = quantileCut(array, cut)
                ip = extractIP(array2)

                mus = np.average(ip, axis=0)
                sigmas = np.std(ip, axis=0)
                
                muArr.append(mus)
                sigmaArr.append(sigmas)

            muArr = np.array(muArr)
            sigmaArr = np.array(sigmaArr)

            fig, ax = plt.subplots(figsize=(14/2.54 , 5/2.54))
            fig2, ax2 = plt.subplots(figsize=(14/2.54 , 5/2.54))

            # plot IP x vs y
            ax.plot(cuts, muArr[:,0], rasterized=True,marker='1', linestyle='', label=f'{latexmu} x')
            ax.plot(cuts, muArr[:,1], rasterized=True,marker='2', linestyle='', label=f'{latexmu} y')
            ax.set_xlabel(f'Quantile Cut [{latexPercent}]')
            ax.set_ylabel(f'{latexmu} [cm]')

            ax2.plot(cuts, sigmaArr[:,0], rasterized=True,marker='3', linestyle='', label=f'{latexsigma} x')
            ax2.plot(cuts, sigmaArr[:,1], rasterized=True,marker='4', linestyle='', label=f'{latexsigma} y')
            ax2.set_xlabel(f'Quantile Cut [{latexPercent}]')
            ax2.set_ylabel(f'{latexsigma} [cm]')
            
            ax.legend()
            ax2.legend()
            
            fig.tight_layout()
            fig2.tight_layout()

            ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
            ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
            
            fig.savefig(f'output/ipDistribution/mean-vs-cut-{box}.pdf', dpi=1000, bbox_inches='tight')
            fig2.savefig(f'output/ipDistribution/sigma-vs-cut-{box}.pdf', dpi=1000, bbox_inches='tight')
            
            plt.close(fig)
            plt.close(fig2)

    if True:
        pass