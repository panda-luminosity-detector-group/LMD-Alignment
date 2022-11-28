#!/usr/bin/env python3

# from alignment.modules.trackReader import trackReader
from pathlib import Path
from matplotlib.ticker import NullFormatter
from matplotlib.ticker import MaxNLocator

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import importlib.util


def dynamicRecoTrackDistanceCut(newTracks, cutPercent=1):

    tempTracks = newTracks

    for i in range(4):
        trackPosArr = tempTracks[:, 0, :3]
        trackDirArr = tempTracks[:, 1, :3]
        recoPosArr = tempTracks[:, 2 + i, :3]

        # norm momentum vectors, this is important for the distance formula!
        trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

        # vectorized distance calculation
        tempV1 = (trackPosArr - recoPosArr)
        tempV2 = (tempV1 * trackDirArr).sum(axis=1)
        dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
        dVec = dVec[:, :2]
        newDist = np.power(dVec[:, 0], 2) + np.power(dVec[:, 1], 2)

        # cut
        cut = int(len(dVec) * cutPercent / 100.0)
        tempTracks = tempTracks[newDist.argsort()]
        tempTracks = tempTracks[:-cut]

    return tempTracks


def doit():

    # import by path
    spec = importlib.util.spec_from_file_location("trackReader", "/media/DataEnc2TBRaid1/Arbeit/LMDscripts/alignment/modules/trackReader.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)

    # all sectors!
    sector = -1
    useCut = False

    for useCut in [True, False]:

        for mom in ['1.5', '15.0']:

            npName = f'input/trackResiduals/procTrks-{mom}.npy'

            if Path(npName).exists():
                print(f'np Tracks found, loading...')
                newTracks = np.load(npName)
                nTrks = len(newTracks)
            
            else:

                fileName = f'input/trackResiduals/processedTracks-{mom}-GeV-aligned.json'

                # load track file
                reader = foo.trackReader()
                reader.readDetectorParameters()
                reader.readTracksFromJson(fileName)
                allTracks = reader.getAllTracksInSector(sector)

                print(f'tracks read from json, cleaning up...')

                #? new format! np array with track oris, track dirs, and recos
                nTrks = len(allTracks)
                newTracks = np.ones((nTrks, 6, 4))

                for i in range(nTrks):
                    newTracks[i, 0, :3] = allTracks[i]['trkPos']
                    newTracks[i, 1, :3] = allTracks[i]['trkMom']
                    newTracks[i, 2, :3] = allTracks[i]['recoHits'][0]['pos']
                    newTracks[i, 3, :3] = allTracks[i]['recoHits'][1]['pos']
                    newTracks[i, 4, :3] = allTracks[i]['recoHits'][2]['pos']
                    newTracks[i, 5, :3] = allTracks[i]['recoHits'][3]['pos']

                # newTracks = newTracks[:900000]
                nTrks = len(newTracks)

                print(f'saving np Tracks...')
                np.save(npName, newTracks, False)
                
            if useCut and True:
                newTracks = dynamicRecoTrackDistanceCut(newTracks, 0.5)
                nTrks = len(newTracks)

            print(f'I will now plot {len(newTracks)} tracks.')
            distMultiArray = np.zeros((4, nTrks, 3))

            print(f'done, creating histograms...')
            for i in range(4):
                trackPosArr = newTracks[:, 0, :3]
                trackDirArr = newTracks[:, 1, :3]
                recoPosArr = newTracks[:, 2 + i, :3]

                # norm momentum vectors, this is important for the distance formula!
                trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

                # vectorized distance calculation
                tempV1 = (trackPosArr - recoPosArr)
                tempV2 = (tempV1 * trackDirArr).sum(axis=1)
                dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)

                distMultiArray[i] = dVec

            #* ----------------- hist preparation
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.colors import LogNorm

            latexmu = r'\textmu{}'
            latexsigma = r'\textsigma{}'
            plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
            plt.rc('text', usetex=True)
            plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

            # plt.tick_params(
            # axis='x',          # changes apply to the x-axis
            # which='both',      # both major and minor ticks are affected
            # bottom=False,      # ticks along the bottom edge are off
            # top=False,         # ticks along the top edge are off
            # labelbottom=False) # labels along the bottom edge are off

            fig, axs = plt.subplots(1, 4, sharex=True, sharey=True)

            scaleFact = 1e4
            myLimit = 4200
            if useCut:
                myLimit /= 10
            myRange = ((-myLimit, myLimit), (-myLimit, myLimit))
            bins = 100
            dunit = f'd [{latexmu}m]'
            xunit = f'dx [{latexmu}m]'
            yunit = f'dy [{latexmu}m]'

            #* -------------- begin 1d hist here

            for i in range(4):
                # calculate 1D distance
                # distances1D = np.linalg.norm(distMultiArray[i], axis=1)

                sigmax = np.std(distMultiArray[i, :, 0] * scaleFact)
                axs[i].hist(distMultiArray[i,:,0] * scaleFact, bins=bins, log=True, range=(-myLimit,myLimit), rasterized=True)
                axs[i].set_title(f'Plane {i+1}')
                axs[i].set_xlabel(f'{xunit}')
                axs[i].set_xlabel(f'{xunit}\n{latexsigma}x={sigmax:.0f}{latexmu}m')
                axs[i].set_ylim((1e1,10000000))
                axs[i].yaxis.set_ticks([1e2, 1e3, 1e4, 1e5, 1e6])  
                axs[i].grid(color='grey', which='major', axis='y', linestyle='dotted')

            axs[0].set_ylabel('Entries (log)')

            fig.set_size_inches((15 / 2.54, 4 / 2.54))
            fig.subplots_adjust(wspace=0, hspace=0)
            if useCut:
                fig.savefig(f'withCut-{mom}-1D.pdf', dpi=300, bbox_inches='tight', pad_inches=0.05)
            else:
                fig.savefig(f'noCut-{mom}-1D.pdf', dpi=300, bbox_inches='tight', pad_inches=0.05)
            
            
            plt.close(fig)
            fig, axs = plt.subplots(1, 4, sharex=True, sharey=True)

            #* -------------- begin 2d hist here

            for i in range(4):
                sigmax = np.std(distMultiArray[i, :, 0] * scaleFact)
                sigmay = np.std(distMultiArray[i, :, 1] * scaleFact)
                axs[i].hist2d(distMultiArray[i, :, 0] * scaleFact,
                              distMultiArray[i, :, 1] * scaleFact,
                              bins=bins,
                              norm=LogNorm(),
                              label='Count (log)',
                              range=myRange,
                              rasterized=True)
                axs[i].set_title(f'Plane {i+1}')
                axs[i].set_aspect('equal', 'box')
                axs[i].set_xlabel(f'{xunit}\n{latexsigma}={sigmax:.0f}{latexmu}m')

            axs[0].set_ylabel(yunit)

            fig.set_size_inches((15 / 2.54, 5 / 2.54))
            fig.subplots_adjust(wspace=0, hspace=0)
            if useCut:
                fig.savefig(f'withCut-{mom}.pdf', dpi=300, bbox_inches='tight', pad_inches=0.05)
            else:
                fig.savefig(f'noCut-{mom}.pdf', dpi=300, bbox_inches='tight', pad_inches=0.05)
            plt.close(fig)


if __name__ == "__main__":
    doit()