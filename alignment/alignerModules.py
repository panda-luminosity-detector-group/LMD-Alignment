#!/usr/bin/env python3

from alignment.modules.trackReader import trackReader

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
import pyMille
import sys

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

TODO: Implement corridor alignment

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- separate by x and y
- give to millepede
- obtain alignment parameters from millepede
- convert to alignment matrices

"""

class alignerModules:
    def __init__(self):

        reader = trackReader()
        reader.readDetectorParameters()
        reader.readTracksFromJson(Path('input/modulesAlTest/tracks_processed.json'))

        # TODO: sort by sector!

        milleOut = 'output/millepede/moduleAlignment.bin'

        MyMille = pyMille.Mille(milleOut)
        
        print(f'Running pyMille...')
        for params in reader.generatorMilleParameters():
            MyMille.write(params[0], params[1], params[2], params[3])
        
        print(f'Mille binary data written to {milleOut}!')
        # now, pede must be called
    
