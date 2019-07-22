#!/usr/bin/env python3

from pathlib import Path

import glob
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
"""


class LMDRunConfig:
    # no static variables! define object-local variables in __init__ functions

    # TODO: add getters/setters

    def __init__(self):
        # find env variabled
        # paths must be stored as strings internally so they can be serialized to JSON!
        simDirEnv = 'LMDFIT_DATA_DIR'
        pndRootDir = 'VMCWORKDIR'
        self.__cwd = str(Path.cwd())
        try:
            self.__simDataPath = os.environ[simDirEnv]
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            print("can't find LuminosityFit installation, PandaRoot installation or Data_Dir!")
            print(f"please set {pndRootDir} and {simDirEnv}!")
            sys.exit(1)

        self.__runSteps = []
        self.__fromPath = None
        self.__alignMatFile = None
        self.__misalignMatFile = None
        self.__misalignType = None
        self.__alignType = None
        self.__misalignFactor = None
        self.__alignFactor = None
        self.__momentum = None
        self.__tracksNum = None
        self.__jobsNum = None
        self.__smallBatch = True
        self.__misalignment = False
        self.__alignmentCorrection = False

    #! --------------------- getters without setters

    #! --------------------- setters without getters

    def __setMisalignFactor(self, value):
        self.__misalignFactor = value
    misalignFactor = property(None, __setMisalignFactor)

    def __setMisalignType(self, value):
        self.__misalignType = value
    misalignType = property(None, __setMisalignType)

    #! --------------------- getters and setters

    def __getMisaligned(self):
        return self.__misalignment

    def __setMisaligned(self, value):
        self.__misalignment = value
    misaligned = property(__getMisaligned, __setMisaligned)

    def __getAlignmentCorrection(self):
        return self.__alignmentCorrection

    def __setAlignmentCorrection(self, value):
        self.__alignmentCorrection = value
    alignmentCorrection = property(__getAlignmentCorrection, __setAlignmentCorrection)

    def __getJobsNum(self):
        return self.__jobsNum

    def __setJobsNum(self, value):
        self.__jobsNum = value
    jobsNum = property(__getJobsNum, __setJobsNum)

    def __getTrksNum(self):
        return self.__tracksNum

    def __setTrksNum(self, value):
        self.__tracksNum = value
    trksNum = property(__getTrksNum, __setTrksNum)

    def __getMomentum(self):
        return self.__momentum

    def __setMomentum(self, value):
        self.__momentum = value
    momentum = property(__getMomentum, __setMomentum)

    #! --------------------- constructor "overloading"
    @classmethod
    def fromPath(cls, path) -> 'LMDRunConfig':
        temp = cls()
        temp.__fromPath = path
        temp.parseFromString()
        return temp

    #! --------------------- minimal default constructor
    @classmethod
    def minimalDefault(cls, mom='1.5', misalignType='identity', factor='1.00'):
        temp = cls()
        temp.__tracksNum = '100000'
        temp.__jobsNum = '500'
        temp.__runSteps = [1, 2, 3, 4]
        temp.__momentum = mom
        temp.__alignFactor = factor
        temp.__misalignFactor = factor
        temp.__alignType = misalignType
        temp.__misalignType = misalignType
        temp.__misalignment = True
        temp.__alignmentCorrection = True
        temp.generateMatrixNames()
        return temp

    def parseFromString(self):
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

        # we need at least the misalignment sub directory
        # 0: plab
        # 1: dpm
        # 2: aligned or misalignment!
        # 3: 1-500_uncut or 1-100_cut
        # 4: Num Tracks
        # 5: aligned or something else

        if len(pathParts) < 3:
            print(f'ERROR! path doesn\'t go deep enough, can not extract all information!')
            sys.exit(1)

        self.__runSteps = [1, 2, 3, 4]

        if pathParts[2] == 'no_geo_misalignment':
            self.__misalignType = 'aligned'
            self.__misalignFactor = '1.00'
            self.__misalignment = False

        else:
            match = re.search("geo_misalignmentmisMat-(\w+)-(\d+\.\d+)", pathParts[2])
            if match:
                if len(match.groups()) > 1:
                    self.__misalignType = match.groups()[0]
                    self.__misalignFactor = match.groups()[1]
                    self.__misalignment = True
            else:
                print(f'can\'t parse info from {pathParts[2]}!')

        # set misalign matrices from values!
        self.__misalignMatFile = str(self.pathMisMatrix())

        # ? optional parser arguments
        if len(pathParts) > 3:
            self.__tracksNum = pathParts[3]

        if len(pathParts) > 4:
            match = re.search('1-(\d+)_uncut', pathParts[4])
            if match:
                self.__jobsNum = match.groups()[0]

        # alignment matrix
        if len(pathParts) > 5:
            match = re.search('aligned-alMat-(\w+)-(\d+\.\d+)', pathParts[5])
            if match:
                self.__alignType = match.groups()[0]
                self.__alignFactor = match.groups()[1]
                self.__alignmentCorrection = True

                if self.__alignType != self.__misalignType:
                    print(f'WARNING. Align type is not the same as misalign type. Is this correct?')

                if self.__alignFactor != self.__misalignFactor:
                    print(f'WARNING. Align factor is not the same as misalign type. Is this correct?')

                self.__alignMatFile = str(self.pathAlMatrix())

    #! --------------------- generate matrix name after minimal initialization
    def generateMatrixNames(self):
        if self.__misalignType is None or self.__misalignFactor is None or self.__momentum is None:
            print(f'ERROR! not enough parameters set!')

        self.__misalignMatFile = str(self.pathMisMatrix())
        self.__alignMatFile = str(self.pathAlMatrix())

    #! --------------------- serialization, deserialization
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
        # self.__checkIfNoneAreNone__()
        with open(filename, 'w') as outfile:
            json.dump(self.__dict__, outfile, indent=2)
        pass

    #! --------------------- generators for factors, alignments, beam momenta
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
        if self.__misalignFactor is None:
            print('ERROR! Align factor not set!')
            sys.exit(1)
        if self.__misalignType is None:
            print('ERROR! Align type not set!')
            sys.exit(1)
        if self.__momentum is None:
            print('ERROR! Beam Momentum not set!')
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
            return Path(f'geo_misalignmentmisMat-{self.__misalignType}-{self.__misalignFactor}')

    def __pathTracksNum__(self):
        return Path('*')

    def __jobBaseDir__(self):
        return Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__()

    def __uncut__(self):
        return Path('1-*_uncut')

    def __cut__(self):
        return Path('1-*_xy_m_cut_real')

    def __aligned__(self):
        return Path('aligned*')

    def __bunches__(self):
        return Path('bunches*') / Path('binning*') / Path('merge_data')

    def __lumiVals__(self):
        return Path('lumi-values.json')

    def __recoIP__(self):
        return Path('reco_ip.json')

    # this is a fuck ugly hack, but pathlib fails whenever dots are in a path or file name 
    def __resolveActual__(self, globbedPath):
        result = glob.glob(str(globbedPath))
        if len(result) > 0:
            return Path(result[0])
        else:
            return globbedPath

    #! --------------------- create paths to matrices, json results
    def pathAlMatrix(self):
        # TODO: check if json or root file, convert if needed!
        self.__checkMinimum__()
        return self.__resolveActual__(Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('alMatrices') / Path(f'alMat-{self.__alignType}-{self.__alignFactor}.json'))

    def pathMisMatrix(self):
        # TODO: check if json or root file, convert if needed!
        self.__checkMinimum__()
        return self.__resolveActual__(Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('misMatrices') / Path(f'misMat-{self.__misalignType}-{self.__misalignFactor}.root'))

    def pathRecoIP(self):
        self.__checkMinimum__()
        if self.__alignmentCorrection:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__aligned__() / self.__bunches__() / self.__recoIP__())
        else:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__bunches__() / self.__recoIP__())

    def pathLumiVals(self):
        self.__checkMinimum__()
        if self.__alignmentCorrection:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__aligned__() / self.__bunches__() / self.__lumiVals__())
        else:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__bunches__() / self.__lumiVals__())

    # for AlignIP et al. methods
    def pathTrksQA(self):
        self.__checkMinimum__()
        if self.__alignmentCorrection:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__aligned__())
        else:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__())

    #! --------------------- verbose output

    def dump(self):
        print(f'\n\n')
        print(f'------------------------------')
        print(f'DEBUG OUTPUT for LMDRunConfig:\n')
        print(f'Path: {self.__fromPath}')
        print(f'Momentum: {self.__momentum}')
        print(f'Misalign Type: {self.__misalignType}')
        print(f'Misalign Factor: {self.__misalignFactor}')
        print(f'Align Type: {self.__alignType}')
        print(f'Align Factor: {self.__alignFactor}')
        print(f'AlignMatrices: {self.__alignMatFile}')
        print(f'MisalignMatrices: {self.__misalignMatFile}')
        print(f'TracksQA path: {self.pathTrksQA}')
        print(f'Num Tracks: {self.__tracksNum}')
        print(f'Num Jobs: {self.__jobsNum}')
        print(f'------------------------------')
        print(f'\n\n')


if __name__ == "__main__":
    print("Sorry, this module can't be run directly")