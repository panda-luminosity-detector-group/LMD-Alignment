#!/usr/bin/env python3

# from alignment.modules.trackReader import trackReader
from pathlib import Path
from matplotlib.ticker import NullFormatter

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import importlib.util

def dynamicRecoTrackDistanceCut(newTracks, cutPercent=1):
    
    tempTracks = newTracks

    for i in range(4):
        trackPosArr = tempTracks[:, 0, :3]
        trackDirArr = tempTracks[:, 1, :3]
        recoPosArr = tempTracks[:, 2+i, :3]

        # norm momentum vectors, this is important for the distance formula!
        trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

        # vectorized distance calculation
        tempV1 = (trackPosArr - recoPosArr)
        tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
        dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
        dVec = dVec[:, :2]
        newDist = np.power(dVec[:, 0], 2) + np.power(dVec[:, 1], 2)
        
        # cut
        cut = int(len(dVec) * cutPercent/100.0)
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

    for mom in ['1.5', '15.0']:

        # fileName = 'input/trackResiduals/processedTracks-1.5-GeV-aligned-mini.json'
        fileName = f'input/trackResiduals/processedTracks-{mom}-GeV-aligned.json'
        # fileName = 'input/trackResiduals/processedTracks-15.0-GeV-aligned.json'

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

        if useCut and True:
            newTracks = dynamicRecoTrackDistanceCut(newTracks, 0.5)
            nTrks = len(newTracks)

        distMultiArray = np.zeros((4, nTrks, 3))

        print(f'done, creating histograms...')
        for i in range(4):
            trackPosArr = newTracks[:, 0, :3]
            trackDirArr = newTracks[:, 1, :3]
            recoPosArr = newTracks[:, 2+i, :3]

            # norm momentum vectors, this is important for the distance formula!
            trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

            # vectorized distance calculation
            tempV1 = (trackPosArr - recoPosArr)
            tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
            dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)

            distMultiArray[i] = dVec

        #* ----------------- begin hist here
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm

        latexmu = r'\textmu{}'
        latexsigma = r'\textsigma{}'
        plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
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
        myLimit = 220
        myRange = ((-myLimit,myLimit), (-myLimit,myLimit))
        bins = 150
        xunit = f'dx [{latexmu}m]'
        yunit = f'dy [{latexmu}m]'

        for i in range(4):
            sigma = np.round(np.std(distMultiArray[i, :, 0]*scaleFact),2)
            axs[i].hist2d(distMultiArray[i, :, 0]*scaleFact, distMultiArray[i, :, 1]*scaleFact, bins=bins, norm=LogNorm(), label='Count (log)', range=myRange, rasterized=True)
            axs[i].set_title(f'Plane {i+1}')
            axs[i].set_aspect('equal', 'box')
            axs[i].set_xlabel(f'{xunit}\n{latexsigma}={sigma}{latexmu}m')

        axs[0].set_ylabel(yunit)

        fig.set_size_inches((14/2.54, 5/2.54))
        fig.subplots_adjust(wspace=0,hspace=0)
        fig.tight_layout()
        if useCut:
            fig.savefig(f'withCut-{mom}.pdf')
        else:
            fig.savefig(f'noCut-{mom}.pdf')
        plt.close(fig)

if __name__ == "__main__":
    doit()