#!/usr/bin/env python3

"""
get interaction point position from TrksQA.root 

Steps:
- filter by trkrecstatus (must be 0)
look for 'X Y Z ip something'

"""

import numpy as np                  # for arrays
import matplotlib.pyplot as plt     # for plots
from scipy.stats import norm        # for normal distribution
import seaborn as sns               # for combined hist and gauss fit plot
import uproot
from collections import defaultdict # to concatenate dictionaries

def fitValues(array):
    # okay, so arrays is a multi dimensional array, or jagged array. some lines don't have any values,
    # while some lines have multiple entries. a single line is an event, which is why the array is exactly
    # 100k lines long. a line can have none, one or multiple entries, so first we need to filter out empty events: 

    # use just the recStatus for indexes, this tells us how many recs there are per event
    recStatusJagged = array[b'LMDTrackQ.fTrkRecStatus']
    nonZeroEvents = (recStatusJagged.counts > 0)

    # flatten all arrays for ease of access and apply a mask.
    # this is numpy notation to select some entries according to a criterion and works very fast:
    recStatus = recStatusJagged[nonZeroEvents].flatten()
    module = array[b'LMDTrackQ.fModule'][nonZeroEvents].flatten()
    recX = array[b'LMDTrackQ.fXrec'][nonZeroEvents].flatten()
    recY = array[b'LMDTrackQ.fYrec'][nonZeroEvents].flatten()
    recZ = array[b'LMDTrackQ.fZrec'][nonZeroEvents].flatten()

    # test: print length
    #print('length of mask:', len(nonZeroEvents))     # 100k, for 100k events
    #print('length of module with rec status 0:', len(module))     # 789498, apparently there are multiple entries per event (10 tracks/event?)

    # create another mask for successful recStatus and remove outliers

    for mod in range(0,5):

        recMask = (recStatus == 0) & (np.abs(recX) < 5) & (np.abs(recY) < 5) & (module == mod) 
        #print(len(module[recMask]))     #only 64384 events were reconstructed successfully

        # create a new array that holds the values for module, x, y and z
        # unnessesaryArray = np.array([module[recMask], recX[recMask], recY[recMask], recZ[recMask]])

        #print(unnessesaryArray.shape)

        # now, loop over all 10 corridors and get the average values of x, y (and z), and compare with average of all
        # this is the position of the interaction point!
    
        ip = [np.average(recX[recMask]), np.average(recY[recMask])]
        print('interaction point is at: {0}, module {1}, {2} tracks'.format(ip, np.average(module[recMask]), len(module[recMask])))      # 

    ''' 
    this is: (-0.275, 0.00286), is this realistic?
        
    compare with reco ip:
    {
        "ip_x": "-0.0050814828195684669",
        "ip_y": "0.0015572209906917918",
        "ip_z": "0"
    }

    hm, thats not right... maybe we need to do the gauss fit? let's look at the standard deviation values.
    '''
    #ipSTD = np.std(recX[recMask]), np.std(recY[recMask])
    #print('standard deviation: ', ipSTD)

    # those are quite large, 17.7 and 18.1. This might be a problem. plot them.
    #plt.hist(recX[recMask], bins=100, range={-5,5})
    #plt.show()

    # try a gaus fit
    # best fit of data
    #(mu, sigma) = norm.fit(recX[recMask])
    
    
    # seaborn plot
    #ax = sns.distplot(recX[recMask], fit=norm, kde=False)
    #plt.show()

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

    try:
        # open the root trees in a TChain-like manner
        print('reading files...')
        for arrays in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fModule', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec'], entrysteps=1000000 ):
            # append new array (which is a dict) to result
            #fitValues(arrays)
            print(type(arrays))
            print(arrays)
            print('------------------------')
            resultDict.update(arrays)       # hm, this doesn't work as intended yet

    except Exception as e:
        print('error occured:')
        print(e)
        
    print('========================')
    #print(resultDict)
    fitValues(resultDict)
    

if __name__ == "__main__":
    print('greetings, human.')
    test()
    print('done')