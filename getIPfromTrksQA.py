#!/usr/bin/env python3

import numpy as np                  # for arrays
import matplotlib.pyplot as plt     # for plots
from scipy.stats import norm        # for normal distribution
import seaborn as sns               # for combined hist and gauss fit plot
import uproot, os, sys
from collections import defaultdict  # to concatenate dictionaries
from matplotlib.colors import LogNorm   # for LogNorm

import matplotlib
matplotlib.use('Agg')   # so matplotlib works over ssh

def cleanArray(arrayDict):

    # okay, so arrays is a multi dimensional array, or jagged array. some lines don't have any values,
    # while some lines have multiple entries. a single line is an event, which is why the array is exactly
    # 100k lines long. a line can have none, one or multiple entries, so first we need to filter out empty events:

    # use just the recStatus for indexes, this tells us how many recs there are per event
    recStatusJagged = arrayDict[b'LMDTrackQ.fTrkRecStatus']
    nonZeroEvents = (recStatusJagged.counts > 0)

    # flatten all arrays for ease of access and apply a mask.
    # this is numpy notation to select some entries according to a criterion and works very fast:
    recStatus = recStatusJagged[nonZeroEvents].flatten()
    half = arrayDict[b'LMDTrackQ.fHalf'][nonZeroEvents].flatten()
    module = arrayDict[b'LMDTrackQ.fModule'][nonZeroEvents].flatten()
    recX = arrayDict[b'LMDTrackQ.fXrec'][nonZeroEvents].flatten()
    recY = arrayDict[b'LMDTrackQ.fYrec'][nonZeroEvents].flatten()
    recZ = arrayDict[b'LMDTrackQ.fZrec'][nonZeroEvents].flatten()

    # return a dictl 
    return {'half': half, 'mod': module, 'x': recX, 'y': recY, 'z': recZ}

def percentileCut(arrayDict, cut):

    # first, remove outliers that are just too large, use a mask
    # TODO: find reasonable value!
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
    distSq = np.power( tempArray[:,0] , 2 ) + np.power( tempArray[:,1] , 2 ) + np.power( tempArray[:,2] , 2)
    tempArray = tempArray[distSq.argsort()]
    tempArray = tempArray[:-cut]
    
    # shift back
    tempArray += comMed
    
    # re-save to array for return
    arrayDict['x'] = tempArray[:,0]
    arrayDict['y'] = tempArray[:,1]
    arrayDict['z'] = tempArray[:,2]
    arrayDict['mod'] = tempArray[:,3]
    arrayDict['half'] = tempArray[:,4]

    return arrayDict

def histValues(cleanArray, align, cut):

    half = cleanArray['half']
    module = cleanArray['mod']
    recX = cleanArray['x']
    recY = cleanArray['y']
    #recZ = cleanArray['z']

    if cut > 0.01:
        outPath = 'output/recoIP/' + align + 'cut2/'
    else:
        outPath = 'output/recoIP/' + align

    if not os.path.exists(outPath):
        os.makedirs(outPath)

    byModule = False

    if byModule:
        for mod in range(0, 5):
            for fHalf in range(0, 2):
                # apply a mask to remove outliers and filter by module
                recMask = (np.abs(recX) < 5000) & (np.abs(recY) < 5000) & (module == mod) & (half == fHalf)

                # this is the position of the interaction point!
                ip = [np.average(recX[recMask]), np.average(recY[recMask]), np.std(recX[recMask]), np.std(recY[recMask])]

                print('interaction point is at: {0}, half {3}, module {1}, {2} tracks'.format(
                    ip, np.average(module[recMask]), len(module[recMask]), fHalf))
            
                if cut > 0.01:
                    # fixed range 10cm
                    plt.hist2d(recX[recMask] * 1e1, recY[recMask] * 1e1, bins=50, norm=LogNorm(), range=[[-100,100],[-100,100]])
                
                else:
                    # fixed range 5m
                    plt.hist2d(recX[recMask] * 1e1, recY[recMask] * 1e1, bins=50, norm=LogNorm(), range=[[-500 * 1e1, 500 * 1e1], [-500 * 1e1, 500 * 1e1]])
                
                plt.colorbar()
                
                legend = f'µx={round(ip[0] * 10, 2)}, µy={round(ip[1] * 10, 2)}, σx={round(ip[2] * 10, 2)}, σy={round(ip[3] * 10, 2)} mm'
                
                plt.title(f'Reco IP for half {fHalf}, module {mod}\n' + legend)
                plt.xlabel('x position [mm]')
                plt.ylabel('y position [mm]')
                
                plt.tight_layout()
                plt.savefig(outPath + f'rec-ip-h{fHalf}m{mod}.png', dpi=300)
                plt.close()

    else:
        recMask = (np.abs(recX) < 5000) & (np.abs(recY) < 5000)
        # this is the position of the interaction point!
        ip = [np.average(recX[recMask]), np.average(recY[recMask]), np.std(recX[recMask]), np.std(recY[recMask])]

        print('interaction point is at: {0}'.format(ip))

        if cut > 0.01:
            # fixed range 10cm
            plt.hist2d(recX[recMask] * 1e1, recY[recMask] * 1e1, bins=50, norm=LogNorm(), range=[[-100,100],[-100,100]])
            
        else:
            # fixed range 5m
            plt.hist2d(recX[recMask] * 1e1, recY[recMask] * 1e1, bins=50, norm=LogNorm(), range=[[-500 * 1e1, 500 * 1e1], [-500 * 1e1, 500 * 1e1]])
        
        plt.colorbar()
        
        legend = f'µx={round(ip[0] * 10, 2)}, µy={round(ip[1] * 10, 2)}, σx={round(ip[2] * 10, 2)}, σy={round(ip[3] * 10, 2)} mm'
        
        plt.title(f'Reco IP\n' + legend)
        plt.xlabel('x position [mm]')
        plt.ylabel('y position [mm]')
        
        plt.tight_layout()
        plt.savefig(outPath + f'rec-ip-allModules.png', dpi=300)
        plt.close()

    return ip

def plotIPsxy(cleanArray, align, cut):
    half = cleanArray['half']
    module = cleanArray['mod']
    recX = cleanArray['x']
    recY = cleanArray['y']
    #recZ = cleanArray['z']

    ips = []

    if cut > 0.01:
        outPath = 'output/recoIP/' + align + 'cut2/'
    else:
        outPath = 'output/recoIP/' + align

    if not os.path.exists(outPath):
        os.makedirs(outPath)

    for mod in range(0, 5):
        for fHalf in range(0, 2):
            # apply a mask to remove outliers and filter by module
            recMask = (np.abs(recX) < 5000) & (np.abs(recY) < 5000) & (module == mod) & (half == fHalf)

            # this is the position of the interaction point!
            ip = [np.average(recX[recMask]), np.average(recY[recMask])]
            ips.append(ip)
            #print(f'appended: {ip}')
    
    #print(f'that is x: {ips[:,0]} and y: {ips[:,1]}')

    #for i in ips:
    #    print(i)

    nips = np.array(ips)

    # print(type(nips))
    # print(nips)

    # auto range
    plt.hist2d(nips[:,0] * 1e1, nips[:, 1] * 1e1, bins=50, norm=LogNorm())
    # plt.colorbar()
    
    plt.axes().set_aspect(aspect='equal', adjustable='datalim')
    
    #legend = f'µx={round(ip[0] * 10, 2)}, µy={round(ip[1] * 10, 2)}, σx={round(ip[2] * 10, 2)}, σy={round(ip[3] * 10, 2)} mm'
    plt.title(f'Reco IPs for {align}\n')
    plt.xlabel('x position [mm]')
    plt.ylabel('y position [mm]')
    
    plt.tight_layout()
    plt.savefig(outPath + f'rec-ips.png', dpi=300)
    plt.close()

    return ip

def readIPs(align, cut=0.0):
    # this file is from
    # /lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-500_uncut
    # so there is no misalignment!
    filename = 'input/TrksQA/' + align + 'Lumi_TrksQA_*.root'

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
    print('========================')

    if cut > 0.01:
        resultDict = percentileCut(resultDict, cut)

    histValues(resultDict, align, cut)
    #plotIPsxy(resultDict, align, cut)

if __name__ == "__main__":
    print('greetings, human.')
    
    # cut in percent
    cuts = (0.0, 2.0)

    for cut in cuts:
        readIPs('aligned/', cut)
        # readIPs('box-0.50/', cut)
        # readIPs('box-1.00/', cut)
        # readIPs('box-2.00/', cut)
        # readIPs('box-5.00/', cut)
        # readIPs('modules-0.01/', cut)
        # readIPs('modules-0.10/', cut)
        # readIPs('modules-0.15/', cut)
        # readIPs('modules-0.50/', cut)
        # readIPs('modules-1.00/', cut)
        # readIPs('modules-2.00/', cut)
        readIPs('combi-0.50/', cut)
        readIPs('combi-1.00/', cut)
        readIPs('combi-2.00/', cut)

    print('done')
