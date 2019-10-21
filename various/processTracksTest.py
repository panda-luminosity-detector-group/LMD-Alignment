#!/usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
from numpy.linalg import inv
import json
import pandas as pd
import uproot
import re
import sys

with open('input/detectorOverlapsIdeal.json', 'r') as f:
    detectorOverlaps = json.load(f)    

    #make new dict sensorID-> modulePath
    betterDict = {}
    for overlap in detectorOverlaps:
        id1 = detectorOverlaps[overlap]['id1']
        id2 = detectorOverlaps[overlap]['id2']
        betterDict[id1] = detectorOverlaps[overlap]["pathModule"]
        betterDict[id2] = detectorOverlaps[overlap]["pathModule"]

def getPathModuleFromSensorID(sensorID):
    return betterDict[sensorID]

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print('usage: ./processTracksTest.py tracks_processed.json')
        sys.exit(1)

    filename = str(sys.argv[1])
    print(f'reading file...')
    with open(filename, 'r') as f:
        events = json.load(f)['events']
    print(f'done!')

    print(f'len: {len(events)}')

    import code
    code.interact(local=locals())

    sys.exit(0)


    NPevents = np.asarray(events)

    print(f'len of NPevents: {len(NPevents)}')
    
    # list comprehension to filter tracks with no momentum from this dict
    thaThing = [ x for x in NPevents if np.linalg.norm(x['trkMom']) != 0 ]

    print(f'type of thaThing is {type(thaThing)}')
    print(f'len of thaThing: {len(thaThing)}')

    print(f'\n\nAgain, now deeper!\n\n')
    print(f'thaThing[0]: {thaThing[0]}\n\n')

    # basic idea
    # recosForMySensor = [ x for x in thaThing if x['recoHits'][0]['sensorID'] == 215 ]

    # list comprehension to extract only reco hits with sensorID that we want

    # inner comprehension:
    # [x for x in x['recoHits'] if x['sensorID'] == 215]

    # outer comprehension
    # [x for x in thaThing]

    # kinda works!
    # recosForMySensor = [[x for x in thisTrack['recoHits'] if x['sensorID'] == 215 ] for thisTrack in thaThing]

    # recosForMySensor = [[x for x in x['recoHits'] if x['sensorID'] == 215 and len(x) > 0] for x in thaThing]

    desiredModule = '/cave_1/lmd_root_0/half_0/plane_1/module_0'
    newDict = []
    for track in thaThing:
        newTrack = {}
        for reco in track['recoHits']:

            modulePath = getPathModuleFromSensorID(reco['sensorID'])

            if True:
            # if modulePath == desiredModule:
                newTrack['recoHit'] = reco['pos']
                newTrack['recoErr'] = reco['err']
                newTrack['recoSensor'] = reco['sensorID']
                newTrack['trkMom'] = track['trkMom']
                newTrack['trkPos'] = track['trkPos']
                newDict.append(newTrack)

    print(newDict[:1], sep="\n\n")
    
    print(f'new length of filtered tracks: {len(newDict)}')
    print(f'tracks now: {newDict}')