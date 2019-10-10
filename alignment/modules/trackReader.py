#!usr/bin/env python3

from collections import defaultdict  # to concatenate dictionaries
from pathlib import Path
import numpy as np
import json
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

    """
    sector goes from 0 to 9
    """
    def readTracksFromRoot(self, path, sector=0):

        """
        Currently not working, please use the json method
        """

    def readTracksFromJson(self, filename, sector=0):
        print(f'Oh hai!')

        with open(filename, 'r') as infile:
            trks = json.load(infile)['events']
            print('file successfully read!')

        print(f'no of events: {len(trks)}')
        print(f"verbose!\ntrack pos: {trks[0]['trkPos']}\ntrack mom: {trks[0]['trkMom']}")

        # track origin and direction
        trackOri = np.array(trks[0]['trkPos'])
        trackDir = np.array(trks[0]['trkMom']) / np.linalg.norm(trks[0]['trkMom'])

        print(f'track parameters: A={trackOri} and u={trackDir} (length {np.linalg.norm(trks[0]["trkMom"])})')

        for reco in trks[0]['recoHits']:
            # print(f'hit index: {reco["index"]}')
            # print(f"reco hit pos: {reco['pos']}")
            # print(f"reco hit err: {reco['err']}")
            recoPos = np.array(reco['pos'])

            apVec = trackOri - recoPos
            dist = np.linalg.norm( np.cross(apVec, trackDir))# / np.linalg.norm(trackDir)

            # better way calculate vector from reco point to track
            # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
            dVec = (trackOri - recoPos) - ((trackOri - recoPos)@trackDir) * trackDir

            print(f'------------------------')
            
            print(f'dVec: {dVec}')
            print(f'-this dist: {np.linalg.norm(dVec)}')
            print(f'other dist: {dist}')

            # okay, at this point, I have all distcanes in x and y