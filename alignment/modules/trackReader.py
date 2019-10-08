#!usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries

import numpy as np
import uproot
import sys

"""

Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This file handles reading of lmd_tracks and lmd reco_files, and extracts tracks with their corresponding reco hist.

It then gives those values to millepede, obtains the alignment parameters back and writes them to alignment matrices.
"""

class trackReader():
    def __init__(self):
        pass