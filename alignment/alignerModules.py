#!/usr/bin/env python3

from alignment.modules.trackReader import trackReader

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
import uproot
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
        reader.readTracks(Path('input/moduleAlTest'))

        

    
