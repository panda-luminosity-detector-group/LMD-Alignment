#!usr/bin/env python3
from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import uproot
import sys

np.set_printoptions(precision=3, suppress=True)

def getIPfromTrksQA(filename, cut=2.0, sensor=-1, module=-1, plane=-1, half=-1, maxTracks=0):

    # uproot.iterate will produce a dict with JaggedArrays, so we can create an empty dict and append each iteration
    resultDict = defaultdict(list)

    try:
        # open the root trees in a TChain-like manner
        print('reading files...')
        for array in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):
            clean = cleanArray(array)

            for key in clean:
                resultDict[key] = np.append(resultDict[key], clean[key], axis=0)

    except Exception as e:
        print('error occured:')
        print(e)
        sys.exit(0)

    # great, at this point I now have a dictionary with the keys mod, x, y, z and numpy arrays for the values. perfect!
    if cut > 0.01:
        resultDict = percentileCut(resultDict, cut)

    ipArr = extractIP(resultDict, module, half)
    
    if maxTracks > 0:
        print(f'he was cuttin on me, sarge!')
        print(f'type: {type(ipArr)}, shape: {ipArr.shape}')
        ipArr = ipArr[:,:maxTracks]
    
    return ipArr


def extractIP(cleanArray, module, half):

    thalf = cleanArray['half']
    tmod = cleanArray['mod']
    recX = cleanArray['x']
    recY = cleanArray['y']
    recZ = cleanArray['z']

    # apply a mask to remove outliers
    recMask = (np.abs(recX) < 5000) & (np.abs(recY) < 5000)

    if module >= 0:
        recMask = recMask & (module == tmod)
    if half >= 0:
        recMask = recMask & (half == thalf)

    # this is the position of the interaction point!
    #ip = [np.average(recX[recMask]), np.average(recY[recMask]), np.average(recZ[recMask]), 1.0]
    ip = np.array([recX[recMask], recY[recMask], recZ[recMask], np.ones(len(recX[recMask]))])
    return ip


def percentileCut(arrayDict, cut):

    # first, remove outliers that are just too large, use a mask
    outMaskLimit = 50
    outMask = (np.abs(arrayDict['x']) < outMaskLimit) & (np.abs(arrayDict['y']) < outMaskLimit) & (np.abs(arrayDict['z']) < outMaskLimit)

    # cut outliers, this creates a copy (performance?)
    for key in arrayDict:
        arrayDict[key] = arrayDict[key][outMask]

    # create new temp array to perform all calculations on - numpy style
    tempArray = np.array((arrayDict['x'], arrayDict['y'], arrayDict['z'], arrayDict['mod'], arrayDict['half'])).T

    # calculate cut length, we're cutting 2%
    cut = int(len(tempArray) * (cut / 100))

    # calculate approximate c.o.m. and shift
    # don't use average, some values are far too large, median is a better estimation
    comMed = np.median(tempArray, axis=0)
    tempArray -= comMed

    # sort by distance and cut largest
    distSq = np.power(tempArray[:, 0], 2) + np.power(tempArray[:, 1], 2) + np.power(tempArray[:, 2], 2)
    tempArray = tempArray[distSq.argsort()]
    tempArray = tempArray[:-cut]

    # shift back
    tempArray += comMed

    # re-save to array for return
    arrayDict['x'] = tempArray[:, 0]
    arrayDict['y'] = tempArray[:, 1]
    arrayDict['z'] = tempArray[:, 2]
    arrayDict['mod'] = tempArray[:, 3]
    arrayDict['half'] = tempArray[:, 4]

    return arrayDict


def cleanArray(arrayDict):
    recStatusJagged = arrayDict[b'LMDTrackQ.fTrkRecStatus']
    nonZeroEvents = (recStatusJagged.counts > 0)

    half = arrayDict[b'LMDTrackQ.fHalf'][nonZeroEvents].flatten()
    module = arrayDict[b'LMDTrackQ.fModule'][nonZeroEvents].flatten()
    recX = arrayDict[b'LMDTrackQ.fXrec'][nonZeroEvents].flatten()
    recY = arrayDict[b'LMDTrackQ.fYrec'][nonZeroEvents].flatten()
    recZ = arrayDict[b'LMDTrackQ.fZrec'][nonZeroEvents].flatten()

    return {'half': half, 'mod': module, 'x': recX, 'y': recY, 'z': recZ}


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
        for box in ['box-0.0', 'box-1.0', 'box-2.0']:
            files = f'/home/remus/temp/rootcompare/{box}/Lumi_TrksQA_1000*.root'
            for cut in [0, 2, 4, 6]:
                # read values
                print(f'cut: {cut}')
                ip = getIPfromTrksQA(files, cut)
                #print(f'IP is at: {ip}')
                mus = np.average(ip, axis=1)
                print(f'averages: {mus}, len: {len(ip[0])}')
                sigmas = np.std(ip, axis=1)
                print(f'sigmas: {sigmas}, len: {len(ip[0])}')

                fig, ax = plt.subplots(figsize=(6/2.54 , 6/2.54))

                # plot IP x vs y
                ax.hist2d(ip[0], ip[1], bins=50, norm=LogNorm(), rasterized=True)
                ax.set_xlabel(f'$i_x$, {latexmu}x={np.round(mus[0], 1)}, {latexsigma}x={np.round(sigmas[0], 1)} [cm]')
                ax.set_ylabel(f'$i_y$, {latexmu}y={np.round(mus[1], 1)}, {latexsigma}y={np.round(sigmas[1], 1)} [cm]')
                fig.tight_layout()
                # plt.show()
                #plt.figure(figsize=(10/2.54, 10/2.54))
                fig.savefig(f'output/ipDistribution/{box}-cut{cut}.pdf', dpi=1000, bbox_inches='tight')
                plt.close(fig)

    # plot sigma vs Ntracks, select cutoff as appropriate
    else:

        cuts = np.arange(0.5, 10.1, 0.5)

        for box in ['box-0.0', 'box-1.0', 'box-2.0']:
            files = f'/home/remus/temp/rootcompare/{box}/Lumi_TrksQA_1000*.root'
            cut = 0.0
            
            muArr = []
            sigmaArr = []
            
            for cut in cuts:
                #print(f'cut: {cut}')
                
                ip = getIPfromTrksQA(files, cut)
                #print(f'IP is at: {ip}')
                mus = np.average(ip, axis=1)
                #print(f'averages: {mus}, len: {len(ip[0])}')
                sigmas = np.std(ip, axis=1)
                #print(f'sigmas: {sigmas}, len: {len(ip[0])}')
                
                muArr.append(mus)
                sigmaArr.append(sigmas)

            print(muArr)
            print(sigmaArr)
            
            muArr = np.array(muArr)
            sigmaArr = np.array(sigmaArr)

            fig, ax = plt.subplots(figsize=(12/2.54 , 5/2.54))

            # plot IP x vs y
            ax.plot(cuts, muArr[:,0], rasterized=True,marker='^', linestyle='', label=f'{latexmu} x | Factor {box}')
            ax.plot(cuts, muArr[:,1], rasterized=True,marker='v', linestyle='', label=f'{latexmu} y | Factor {box}')
            # ax.plot(cuts, sigmaArr[:,0], rasterized=True,marker='^', linestyle='', label=f'{latexsigma} x')
            # ax.plot(cuts, sigmaArr[:,1], rasterized=True,marker='v', linestyle='', label=f'{latexsigma} y')
            ax.set_xlabel(f'Quantile Cut [{latexPercent}]')
            ax.set_ylabel(f'{latexsigma} [cm]')
            ax.legend()
            fig.tight_layout()
            plt.grid(color='lightgrey', which='major', axis='y', linestyle='dotted')
            plt.grid(color='lightgrey', which='major', axis='x', linestyle='dotted')
            fig.savefig(f'output/ipDistribution/mean-vs-cut-{box}.pdf', dpi=1000, bbox_inches='tight')
            plt.close(fig)
