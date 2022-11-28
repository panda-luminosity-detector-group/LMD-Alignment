#!/usr/bin/env python3

import json

# for all factors:

for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:

    path = f'/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/'

    IPalignerResultName = f'{path}misMat-box100-{fac}.json'
    moduleAlignerResultName = f'{path}misMat-modules-{fac}.json'
    sensorAlignerResultName = f'{path}misMat-sensors-{fac}.json'
    
    mergedAlignerResultName = f'{path}misMat-combi-{fac}.json'

    # combine all alignment matrices to one single json File
    with open(sensorAlignerResultName, 'r') as f:
        resOne = json.load(f)

    with open(IPalignerResultName, 'r') as f:
        resTwo = json.load(f)

    with open(moduleAlignerResultName, 'r') as f:
        resThree = json.load(f)

    mergedResult = {**resOne, **resTwo, **resThree}

    with open(mergedAlignerResultName, 'w') as f:
        json.dump(mergedResult, f, indent=2, sort_keys=True)