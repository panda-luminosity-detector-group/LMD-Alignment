#!/usr/bin/env python3

"""

TODO: Implement corridor alignment

steps:
- read tracks and reco files
- extract tracks and corresponding reco hits
- separate by x and y
- give to millepede
- obtain alignment parameters from millepede
- convert to alignment matrices

"""

from pathlib import Path
import numpy as np

class alignerModules:
    def __init__(self):
        pass