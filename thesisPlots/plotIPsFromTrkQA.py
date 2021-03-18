#!/usr/bin/env python3
from collections import defaultdict  # to concatenate dictionaries
import matplotlib.ticker as plticker

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
        for array in uproot.iterate(filename, 'pndsim',
                                    [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):
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

    ipArr = np.ones((len(cleanArray), 4))
    ipArr[:, :3] = cleanArray[:, 3:6]
    return ipArr


def quantileCut(cleanArray, cut):

    if cut == 0:
        return cleanArray

    # calculate cut length
    cut = int(len(cleanArray) * (cut / 100))

    # don't use average, some values are far too large, median is a better estimation
    comMed = np.median(cleanArray[:, 3:6], axis=0)

    # sort by distance and cut largest
    distVec = cleanArray[:, 3:6] - comMed
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
    plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')
    # plt.rcParams["legend.loc"] = 'lower right'

    # read some 10 files
    # this is the same as in the actual align code
    # box = 'box-0.0'

    path = '/media/DataEnc2TBRaid1/Arbeit/VirtualDir/boxIPdist-uncut'

    if False:
        for mom in ('1.5', '15.0'):
            for box in ['box-0.0', 'box-1.0', 'box-2.0']:
                files = f'{path}/{mom}/{box}/Lumi_TrksQA_1000*.root'

                array = getIPfromTrksQA(files)
                print(f'Number of Tracks: {len(array)}')

                for cut in [0]:#, 2, 4, 6, 8, 10, 15, 20]:

                    #* individual plots
                    array2 = quantileCut(array, cut)

                    # default ROOT units are cm, we want mm here
                    ip = extractIP(array2) * 10

                    mus = np.average(ip, axis=0)
                    sigmas = np.std(ip, axis=0)

                    fig, ax = plt.subplots(figsize=(10 / 2.54, 10 / 2.54))
                    ax.set_aspect('equal')

                    # plot IP x vs y
                    ax.hist2d(ip[:, 0], ip[:, 1], bins=50, norm=LogNorm(), rasterized=True)
                    ax.set_xlabel(f'$i_x$ [mm]\n{latexmu}x={mus[0]:.2f} [mm], {latexsigma}x={sigmas[0]:.2f} [mm]')
                    ax.set_ylabel(f'$i_y$ [mm]\n{latexmu}y={mus[1]:.2f} [mm], {latexsigma}y={sigmas[1]:.2f} [mm]')

                    fig.tight_layout()
                    fig.savefig(f'output/ipDistribution/{box}-cut{cut}-{mom}.pdf', dpi=1000, bbox_inches='tight')
                    plt.close(fig)
    if True:
        for box in ['box-0.0', 'box-1.0', 'box-2.0']:

            file1 = f'{path}/1.5/{box}/Lumi_TrksQA_1000*.root'
            file2 = f'{path}/15.0/{box}/Lumi_TrksQA_1000*.root'

            array1 = getIPfromTrksQA(file1)
            array2 = getIPfromTrksQA(file2)

            for cut in [0, 4, 8, 12, 16]:

                array1 = quantileCut(array1, cut)
                array2 = quantileCut(array2, cut)

                # default ROOT units are cm, we want mm here
                ip1 = extractIP(array1) * 10
                ip2 = extractIP(array2) * 10

                mus1 = np.average(ip1, axis=0)
                mus2 = np.average(ip2, axis=0)
                sigmas1 = np.std(ip1, axis=0)
                sigmas2 = np.std(ip2, axis=0)

                xmin1 = np.min(ip1[:,0])
                xmax1 = np.max(ip1[:,0])
                ymin1 = np.min(ip1[:,1])
                ymax1 = np.max(ip1[:,1])

                xmin2 = np.min(ip2[:,0])
                xmax2 = np.max(ip2[:,0])
                ymin2 = np.min(ip2[:,1])
                ymax2 = np.max(ip2[:,1])

                xmin = min(xmin1, xmin2)
                ymin = min(ymin1, ymin2)
                xmax = max(xmax1, xmax2)
                ymax = max(ymax1, ymax2)

                thisrange = [[xmin, xmax], [ymin, ymax]]
               

                #* combined plots
                fig, axis = plt.subplots(1, 2, sharex=True, sharey=True)

                axis[0].hist2d(ip1[:, 0], ip1[:, 1], bins=100, norm=LogNorm(), rasterized=True, range=thisrange)
                axis[0].set_xlabel(f'$i_x$ [mm]\n{latexmu}x={mus1[0]:.2f} [mm], {latexsigma}x={sigmas1[0]:.2f} [mm]')
                axis[0].set_ylabel(f'$i_y$ [mm]\n{latexmu}y={mus1[1]:.2f} [mm], {latexsigma}y={sigmas1[1]:.2f} [mm]')
                axis[0].set_aspect('equal')


                axis[1].hist2d(ip2[:, 0], ip2[:, 1], bins=100, norm=LogNorm(), rasterized=True, range=thisrange)
                axis[1].set_xlabel(f'$i_x$ [mm]\n{latexmu}x={np.round(mus2[0], 1)} [mm], {latexsigma}x={np.round(sigmas2[0], 1)} [mm]')
                axis[1].set_ylabel(f'$i_y$ [mm]\n{latexmu}y={np.round(mus2[1], 1)} [mm], {latexsigma}y={np.round(sigmas2[1], 1)} [mm]')
                axis[1].yaxis.set_label_position('right')
                axis[1].yaxis.set_ticks_position('none')
                axis[1].set_aspect('equal')

                axis[0].set_xlim(xmin, xmax)
                axis[0].set_ylim(ymin, ymax)



                loc = plticker.MultipleLocator(round((xmax-xmin)/3)) # this locator puts ticks at regular intervals
                axis[0].xaxis.set_major_locator(loc)
                axis[0].yaxis.set_major_locator(loc)
                axis[1].xaxis.set_major_locator(loc)
                axis[1].yaxis.set_major_locator(loc)

                fig.set_size_inches((15 / 2.54, 8 / 2.54))
                fig.subplots_adjust(wspace=0, hspace=0)
                fig.savefig(f'output/ipDistribution/{box}-cut{cut}-both.pdf', dpi=300, bbox_inches='tight', pad_inches = 0.05)
                plt.close(fig)



    # plot sigma vs quantile cut, select cutoff as appropriate
    if False:
        for mom in ('1.5', '15.0'):
            cuts = np.arange(0.0, 5.1, 0.05)

            for box in ['box-0.0', 'box-1.0', 'box-2.0']:
                files = f'{path}/{mom}/{box}/Lumi_TrksQA_1000*.root'
                cut = 0.0

                muArr = []
                sigmaArr = []

                array = getIPfromTrksQA(files)
                print(f'Number of Tracks: {len(array)}')

                for cut in cuts:
                    #print(f'cut: {cut}')

                    array2 = quantileCut(array, cut)

                    # default ROOT units are cm, we want mm here
                    ip = extractIP(array2)*1e1

                    mus = np.average(ip, axis=0)
                    sigmas = np.std(ip, axis=0)

                    muArr.append(mus)
                    sigmaArr.append(sigmas)

                    if abs(cut - 4.0) < 0.001:
                        mx, my = mus[0], mus[1]
                        sx, sy = sigmas[0], sigmas[1]

                muArr = np.array(muArr)
                sigmaArr = np.array(sigmaArr)

                fig, ax = plt.subplots(figsize=(14 / 2.54, 5 / 2.54))
                fig2, ax2 = plt.subplots(figsize=(14 / 2.54, 5 / 2.54))

                # plot IP x vs y
                ax.plot(cuts, muArr[:, 0], rasterized=True, marker='1', linestyle='', label=f'{latexmu}x @ 4{latexPercent}={mx:.3f}mm')
                ax.plot(cuts, muArr[:, 1], rasterized=True, marker='2', linestyle='', label=f'{latexmu}y @ 4{latexPercent}={my:.3f}mm')
                ax.set_xlabel(f'Quantile Cut [{latexPercent}]')
                ax.set_ylabel(f'Mean [mm]')

                ax2.plot(cuts, sigmaArr[:, 0], rasterized=True, marker='3', linestyle='', label=f'{latexsigma}x @ 4{latexPercent}={sx:.3f}mm')
                ax2.plot(cuts, sigmaArr[:, 1], rasterized=True, marker='4', linestyle='', label=f'{latexsigma}y @ 4{latexPercent}={sy:.3f}mm')
                ax2.set_xlabel(f'Quantile Cut [{latexPercent}]')
                ax2.set_ylabel(f'Std. Deviation [mm]')

                ax.set_ylim([-6.5,1.5])

                ax.axvline(x=4, color=r'#aa0000', linestyle='-', linewidth=0.5)
                ax2.axvline(x=4, color=r'#aa0000', linestyle='-', linewidth=0.5)

                ax.legend(loc='lower right')
                ax2.legend(loc='upper right')

                fig.tight_layout()
                fig2.tight_layout()

                ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
                ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')

                fig.savefig(f'output/ipDistribution/mean-vs-cut-{mom}-{box}.pdf', dpi=1000, bbox_inches='tight')
                fig2.savefig(f'output/ipDistribution/sigma-vs-cut-{mom}-{box}.pdf', dpi=1000, bbox_inches='tight')

                plt.close(fig)
                plt.close(fig2)

    if True:
        for mom in ('1.5', '15.0'):
            for box in ['box-0.0', 'box-1.0', 'box-2.0']:
                files = f'/media/DataEnc2TBRaid1/Arbeit/VirtualDir/boxIPdist/{mom}/{box}/Lumi_TrksQA_1000*.root'
                array = getIPfromTrksQA(files)
                print(f'Number of Tracks: {len(array)}')

                muArr = []
                sigmaArr = []

                nTracks = np.arange(1000, 50001, 500)
                for number in nTracks:
                    array2 = array[:number]
                    array3 = quantileCut(array2, 4.0)
                    ip = extractIP(array3)

                    mus = np.average(ip, axis=0)
                    sigmas = np.std(ip, axis=0)

                    muArr.append(mus)
                    sigmaArr.append(sigmas)

                muArr = np.array(muArr)
                sigmaArr = np.array(sigmaArr)

                fig, ax = plt.subplots(figsize=(14 / 2.54, 5 / 2.54))
                fig2, ax2 = plt.subplots(figsize=(14 / 2.54, 5 / 2.54))

                # plot IP x vs y
                ax.plot(nTracks, muArr[:, 0]*1e1, rasterized=True, marker='1', linestyle='', label=f'{latexmu} x')
                ax.plot(nTracks, muArr[:, 1]*1e1, rasterized=True, marker='2', linestyle='', label=f'{latexmu} y')
                ax.set_xlabel(f'Number of Tracks')
                ax.set_ylabel(f'Mean [mm]')

                ax2.plot(nTracks, sigmaArr[:, 0]*1e1, rasterized=True, marker='3', linestyle='', label=f'{latexsigma} x')
                ax2.plot(nTracks, sigmaArr[:, 1]*1e1, rasterized=True, marker='4', linestyle='', label=f'{latexsigma} y')
                ax2.set_xlabel(f'Number of Tracks')
                ax2.set_ylabel(f'Std. Deviation [mm]')

                ax.legend()
                ax2.legend()

                fig.tight_layout()
                fig2.tight_layout()

                ax.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')
                ax2.grid(color='lightgrey', which='major', axis='both', linestyle='dotted')

                fig.savefig(f'output/ipDistribution/mean-vs-nTrk-{mom}-{box}.pdf', dpi=1000, bbox_inches='tight')
                fig2.savefig(f'output/ipDistribution/sigma-vs-nTrk-{mom}-{box}.pdf', dpi=1000, bbox_inches='tight')

                plt.close(fig)
                plt.close(fig2)