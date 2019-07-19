#!/usr/bin/env python3

from pathlib import Path

import re
import sys
import os
import json

"""
pathlib wrapper specifically for our LMD case. a config object only hold the parameters for a single simulation run!

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
        pndRootDir = 'VMCWORKDIR'
        self.__cwd = str(Path.cwd())
        try:
            self.__lumiFitPath = str(Path(os.environ[lmdFitEnv]).parent)
            self.__simDataPath = os.environ[simDirEnv]
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            print("can't find LuminosityFit installation, PandaRoot installation or Data_Dir!")
            print(f"please set {lmdFitEnv}, {pndRootDir} and {simDirEnv}!")
            sys.exit(1)

        self.__fromPath = None
        self.__alignMat = None
        self.__misalignType = None
        self.__misalignMat = None
        self.__alignFactor = None
        self.__momentum = None
        self.__tracksNum = None
        self.__jobsNum = None
        self.__smallBatch = True

    # constructor "overloading"
    @classmethod
    def fromPath(cls, path) -> 'LMDRunConfig':
        temp = cls()
        temp.__fromPath = path
        temp.parse()
        return temp

    def parse(self):
        pathParts = Path(self.__fromPath).parts

        # search for plab, our dir tree begins here
        index = 0
        for part in pathParts:
            match = re.search("plab_(.*)GeV", part)
            if match:
                self.__momentum = match.groups()[0]
                break
            index += 1

        # from here, we know the directory structure, no more guess work!
        pathParts = pathParts[index:]

        # we need at least the mialignment sub directory
        # 0: plab
        # 1: dpm
        # 2: aligned or misalignment!
        if len(pathParts) < 3:
            print(f'ERROR! path doesn\'t go deep enough, can not extract all information!')
            sys.exit(1)

        if pathParts[2] == 'no_geo_misalignment':
            self.__misalignType = 'aligned'
            self.__alignFactor = '1.00'

        else:
            match = re.search("geo_misalignmentmisMat-(.*)-(.*)", pathParts[2])
            if match:
                if len(match.groups()) > 1:
                    self.__misalignType = match.groups()[0]
                    self.__alignFactor = match.groups()[1]
            else:
                print(f'can\'t parse info from {pathParts[2]}!')

        # set misalign matrices from values!
        self.__misalignMat = str(self.pathMisMatrix())

        #? optional parser arguments
        if len(pathParts) > 3:
            self.__tracksNum = pathParts[3]

        # TODO: implement correctly, alignment will be in sub directory somewhere!!
        if len(pathParts) > 4:
            # set align matrices from values!
            # TODO: parse with regex here!
            #self.__alignMat = str(self.pathAlMatrix())
            pass

        else:
            print(f'Info: path too short for alignment info!')

    @classmethod
    def fromJSON(cls, filename):
        if not Path(filename).exists():
            print(f'ERROR! File {filename} can\'t be read!')
            sys.exit(1)
        temp = cls()
        with open(filename, 'r') as inFile:
            temp.__dict__ = json.load(inFile)
        return temp

    # serialize to JSON
    def toJSON(self, filename):
        #self.__checkIfNoneAreNone__()
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
        misalignments = ['aligned', 'sensors', 'box', 'combi', 'modules', 'identity', 'all']
        for mis in misalignments:
            yield mis

    # generates all config objects (all momenta, misaligns etc) as a generator
    def genConfigs(self):
        # TODO: implement!
        pass

    #! --------------------- these define the path structure! ---------------------
    def __checkMinimum__(self):
        if self.__alignFactor is None:
            print('ERROR! Align factor not set!')
            sys.exit(1)
        if self.__misalignType is None:
            print('ERROR! Align type not set!')
            sys.exit(1)

    def __checkIfNoneAreNone__(self):
        for val in self.__dict__.values():
            if val is None:
                print(f'ERROR in LMDRunConfig: some values are not set!')
                sys.exit(1)

    def __pathMom__(self):
        return Path(f'plab_{self.__momentum}GeV')

    def __pathDPM__(self):
        return Path('dpm_elastic_theta_*mrad_recoil_corrected')

    def __pathMisalignDir__(self):
        if self.__misalignType == 'aligned':
            return Path('no_geo_misalignment')
        else:
            return Path(f'geo_misalignmentmisMat-{self.__misalignType}-{self.__alignFactor}')

    def __pathTracksNum__(self):
        return Path('*')

    def __uncut__(self):
        return Path('1-*_uncut')

    def __cut__(self):
        return Path('1-*_xy_m_cut_real')

    def __bunches__(self):
        return Path('bunches*') / Path('binning*') / Path('merge_data')

    def __lumiVals__(self):
        return Path('lumi-values.json')

    def __recoIP__(self):
        return Path('reco_ip.json')

    #! --------------------- end of path structure definition! ---------------------

    def pathAlMatrix(self):
        # TODO: check if json or root file, convert if needed!
        self.__checkMinimum__()
        return Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('alMatrices') / Path(f'alMat-{self.__misalignType}-{self.__alignFactor}.json')

    def pathMisMatrix(self):
        # TODO: check if json or root file, convert if needed!
        self.__checkMinimum__()
        return Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('misMatrices') / Path(f'misMat-{self.__misalignType}-{self.__alignFactor}.root')

    def pathRecoIP(self):
        self.__checkMinimum__()
        return Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__() / self.__uncut__() / self.__bunches__() / self.__recoIP__()

    def pathLumiVals(self):
        self.__checkMinimum__()
        return Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__() / self.__cut__() / self.__bunches__() / self.__lumiVals__()

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
