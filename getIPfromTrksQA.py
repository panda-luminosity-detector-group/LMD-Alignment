#!/usr/bin/env python3

import numpy as np                  # for arrays
import matplotlib.pyplot as plt     # for plots
from scipy.stats import norm        # for normal distribution
import seaborn as sns               # for combined hist and gauss fit plot
import uproot
from collections import defaultdict  # to concatenate dictionaries

def cleanArray(array):

    # okay, so arrays is a multi dimensional array, or jagged array. some lines don't have any values,
    # while some lines have multiple entries. a single line is an event, which is why the array is exactly
    # 100k lines long. a line can have none, one or multiple entries, so first we need to filter out empty events:

    # use just the recStatus for indexes, this tells us how many recs there are per event
    recStatusJagged = array[b'LMDTrackQ.fTrkRecStatus']
    nonZeroEvents = (recStatusJagged.counts > 0)

    # flatten all arrays for ease of access and apply a mask.
    # this is numpy notation to select some entries according to a criterion and works very fast:
    recStatus = recStatusJagged[nonZeroEvents].flatten()
    half = array[b'LMDTrackQ.fHalf'][nonZeroEvents].flatten()
    module = array[b'LMDTrackQ.fModule'][nonZeroEvents].flatten()
    recX = array[b'LMDTrackQ.fXrec'][nonZeroEvents].flatten()
    recY = array[b'LMDTrackQ.fYrec'][nonZeroEvents].flatten()
    recZ = array[b'LMDTrackQ.fZrec'][nonZeroEvents].flatten()

    # return a dict
    return {'half': half, 'mod': module, 'x': recX, 'y': recY, 'z': recZ}

def fitValues(cleanArray):

    half = cleanArray['half']
    module = cleanArray['mod']
    recX = cleanArray['x']
    recY = cleanArray['y']
    recZ = cleanArray['z']

    # test: print length
    # print('length of mask:', len(nonZeroEvents))     # 100k, for 100k events
    # print('length of module with rec status 0:', len(module))     # 789498, apparently there are multiple entries per event (10 tracks/event?)

    for mod in range(0, 5):
        for fHalf in range(0, 2):
            # apply a mask to remove outliers and filter by module
            recMask = (np.abs(recX) < 5) & (np.abs(recY) < 5) & (module == mod) & (half == fHalf)

            # this is the position of the interaction point!
            ip = [np.average(recX[recMask]), np.average(recY[recMask])]
            print('interaction point is at: {0}, half {3}, module {1}, {2} tracks'.format(
                ip, np.average(module[recMask]), len(module[recMask]), fHalf))

    #ipSTD = np.std(recX[recMask]), np.std(recY[recMask])
    #print('standard deviation: ', ipSTD)

    # those are quite large, 17.7 and 18.1. This might be a problem. plot them.
    #plt.hist(recX[recMask], bins=100, range={-5,5})
    # plt.show()

    # seaborn plot
    axx = sns.distplot(recX[recMask], fit=norm, kde=False)
    axy = sns.distplot(recY[recMask], fit=norm, kde=False)
    axm = sns.distplot(module[recMask], fit=norm, kde=False)
    plt.show()

    #print('min and max val: ', np.min(recX[recMask]), np.max(recX[recMask]) )
    #print('mu, sigma:', mu-ip[0], sigma-ipSTD[0])

    return ip


def test():
    # this file is from
    # /lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-500_uncut
    # so there is no misalignment!
    filename = 'input/TrksQA/Lumi_TrksQA_*.root'

    # uproot.iterate will produce a dict with JaggedArrays, so we can create an empty dict and append each iteration
    resultDict = defaultdict(list)

    lenSum = 0

    try:
        # open the root trees in a TChain-like manner
        print('reading files...')
        for array in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fHalf', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec'], entrysteps=1000000):
            # print(type(arrays))
            # print(arrays)
            # print('------------------------')

            clean = cleanArray(array)
            lenSum += len(clean['mod'])

            for key in clean:
                # print(f'key is {key}, len of {key}:{len(clean[key])}')
                # print(f'type of {key} is {type(clean[key])}')
                # resultDict[key].append(clean[key])

                # append individual arrays
                resultDict[key] = np.append(resultDict[key], clean[key], axis=0)

    except Exception as e:
        print('error occured:')
        print(e)

    print('========================')
    # print(resultDict)

    print(f'sum of lengths is {lenSum}')
    
    for key in resultDict:
        print(f'len of key {key}: {len(resultDict[key])}')

    # great, at this point I now have a dictionary with the keys mod, x, y, z and numpy arrays for the values. perfect!
    print('========================')

    fitValues(resultDict)


if __name__ == "__main__":
    print('greetings, human.')
    test()
    print('done')
