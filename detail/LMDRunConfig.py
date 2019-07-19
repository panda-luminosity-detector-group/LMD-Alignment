#!/usr/bin/env python3

from pathlib import Path

import re
import sys
import os
import json

"""
pathlib wrappr specifically for our LMD case.

uses pathlib internally and stores some additional values as well:

- alignment matrix used
- misalignment matrix used
- alignment factor
- beam momentum
- bunches / binning numbers for Lumi Fit

handles these things implicitly:
- uses json matrices by default
- converts root matrices to json matrices (using ROOT)

most importantly, can also create paths given these parameters:
- beam momentum
- align matrices
- misalign matrices
- reco_ip.json location (for use with ./extractLuminosity)
- lumi_vals.json location (for use with ./extractLuminosity)

example path:

/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-box-0.25/100000/1-500_uncut_aligned

LMD_DATA_DIR: /lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit
momentum: plab_1.5GeV
dpm: dpm_elastic_theta_2.7-13.0mrad_recoil_corrected
misalignment: geo_misalignmentmisMat-box-0.25
tracks: 100000
jobs and aligned: 1-500_uncut_aligned   #TODO: change this in LuminosityFit! aligned should be a sub directory
"""


class LMDRunConfig:

    # no static variables! define object-local variables in __init__ functions
    def __init__(self):
        # find env variabled
        # paths must be stored as strings internally so they can be serialized to JSON!
        lmdFitEnv = 'LMDFIT_BUILD_PATH'
        simDirEnv = 'LMDFIT_DATA_DIR'
        self.__cwd = str(Path.cwd())
        try:
            self.__lumiFitPath = str(Path(os.environ[lmdFitEnv]).parent)
            self.__simDataPath = os.environ[simDirEnv]
        except:
            print("can't find LuminosityFit installation or Data_Dir!")
            print(f"please set {lmdFitEnv} and {simDirEnv}!")
            sys.exit(1)

        self.__fromPath = None
        self.__alignMat = None
        self.__misalignType = None
        self.__misalignMat = None
        self.__alignFactor = None
        self.__momentum = None
        self.__smallBatch = True

    # constructor "overloading"
    @classmethod
    def fromPath(cls, path) -> 'LMDRunConfig':
        temp = cls()
        temp.__fromPath = path
        temp.parse()
        return temp

    def parse(self):
        pass

    @classmethod
    def fromJSON(cls, filename):
        temp = cls()
        with open(filename, 'r') as inFile:
            temp.__dict__ = json.load(inFile)
        return temp

    def toJSON(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.__dict__, outfile, indent=2)
        pass

    # generators for factors, alignments, beam momenta
    def genBeamMomenta(self):
        if self.__smallBatch:
            momenta = ['1.5', '15.0']
        else:
            momenta = ['1.5', '4.06', '8.9', '11.91', '15.0']
        for mom in momenta:
            yield mom

    def genFactors(self):
        if self.__smallBatch:
            factors = ['0.5', '1.00', '2.00']
        else:
            factors = ['0.01', '0.05', '0.10', '0.15', '0.2', '0.25', '0.5', '1.00', '2.00', '3.00', '5.00', '10.00']
        for f in factors:
            yield f

    def genMisalignments(self):
        misalignments = ['sensors', 'box', 'combi', 'modules', 'identity', 'all']
        for mis in misalignments:
            yield mis

    # generates all config objects (all momenta, misaligns etc) as a generator
    def genConfigs(self):
        pass

    def pathAlMatrix(self):
        pass

    def pathMisMatrix(self):
        pass

    def pathRecoIP(self):
        pass

    def pathLumiVals(self):
        pass

    def dump(self):
        print(f'\n\n')
        print(f'------------------------------')
        print(f'DEBUG OUTPUT for LMDRunConfig:\n')
        print(f'Path: {self.__fromPath}')
        print(f'Momentum: {self.__momentum}')
        print(f'Misalign Type: {self.__misalignType}')
        print(f'AlignMatrices: {self.__alignMat}')
        print(f'MisalignMatrices: {self.__misalignMat}')
        print(f'Align Factor: {self.__alignFactor}')
        print(f'------------------------------')
        print(f'\n\n')


if __name__ == "__main__":
    print("Sorry, this module can't be run directly")
