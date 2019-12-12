#!/usr/bin/env python3

from pathlib import Path

import glob
import re
import sys
import os
import json

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

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

    def __init__(self):
        # find env variabled
        # paths must be stored as strings internally so they can be serialized to JSON!
        self.updateEnvPaths()
        self.__tracksNum = '100000'
        self.__jobsNum = '100'
        self.__JobBaseDir = None
        self.__fromPath = None
        self.__alignMatFile = None
        self.__misalignMatFile = None
        self.__misalignType = None
        self.__alignType = None
        self.__misalignFactor = None
        self.__alignFactor = None
        self.__momentum = None
        self.__misalignment = True
        self.__alignmentCorrection = False
        self.__debug = False
        self.__useDevQueue = False
        self.__useIdentityAlignment = False
        self.__mergeAlignmentMatrices = False
        self.__sensorAlignerExternalMatrices = None
        self.__moduleAlignAnchorPointFile = None
        self.__moduleAlignAvgMisalignFile = None

    #! --------------------- for sortability
    def __lt__(self, other):
        momLt = float(self.momentum) < float(other.momentum)
        momEq = float(self.momentum) == float(other.momentum)

        typeLt = self.misalignType < other.misalignType
        typeEq = self.misalignType == other.misalignType

        factorLt = float(self.misalignFactor) < float(other.misalignFactor)
        factorEq = float(self.misalignFactor) == float(other.misalignFactor)

        corrLt = self.alignmentCorrection < other.alignmentCorrection
        corrEq = self.alignmentCorrection == other.alignmentCorrection

        if momLt:
            return True
        elif momEq and typeLt:
            return True
        elif momEq and typeEq and factorLt:
            return True
        elif momEq and typeEq and factorEq and corrLt:
            return True
        else:
            return False

    def __eq__(self, other):
        return (not self < other) and (not other < self)

    #! --------------------- getters without setters

    def __getAlMatFile(self):
        return self.__alignMatFile

    def __getMisMatFile(self):
        return self.__misalignMatFile
    alMatFile = property(__getAlMatFile, None)
    misMatFile = property(__getMisMatFile, None)

    #! --------------------- getters and setters

    def __getAvgMisPath(self):
        return self.__moduleAlignAvgMisalignFile

    def __setAvgMisPath(self, val):
        self.__moduleAlignAvgMisalignFile = val
    moduleAlignAvgMisalignFile = property(__getAvgMisPath, __setAvgMisPath)

    def __getAnchorPath(self):
        return self.__moduleAlignAnchorPointFile

    def __setAnchorPath(self, val):
        self.__moduleAlignAnchorPointFile = val
    moduleAlignAnchorPointFile = property(__getAnchorPath, __setAnchorPath)

    def __getExMatPath(self):
        return self.__sensorAlignerExternalMatrices

    def __setExMatPath(self, value):
        self.__sensorAlignerExternalMatrices = value
    sensorAlignExternalMatrixPath = property(__getExMatPath, __setExMatPath)

    def __getMisalignFactor(self):
        return self.__misalignFactor

    def __setMisalignFactor(self, value):
        self.__misalignFactor = value
    misalignFactor = property(__getMisalignFactor, __setMisalignFactor)

    def __getMisalignType(self):
        return self.__misalignType

    def __setMisalignType(self, value):
        self.__misalignType = value

    misalignType = property(__getMisalignType, __setMisalignType)

    def __setUseIdentityAlignment(self, value):
        self.__useIdentityAlignment = value

    def __getUseIdentityAlignment(self):
        return self.__useIdentityAlignment

    useIdentityMisalignment = property(__getUseIdentityAlignment, __setUseIdentityAlignment)

    def __setMergeAlignmentMatrices(self, value):
        self.mergeAlignmentMatrices = value

    def __getMergeAlignmentMatrices(self):
        return self.mergeAlignmentMatrices

    mergeAlignmentMatrices = property(__getMergeAlignmentMatrices, __setMergeAlignmentMatrices)

    def __getDebug(self):
        return self.__debug

    def __setDebug(self, debug):
        self.__debug = debug
    useDebug = property(__getDebug, __setDebug)

    def __getDebugQueue(self):
        return self.__useDevQueue

    def __setDebugQueue(self, debug):
        self.__useDevQueue = debug
    useDevQueue = property(__getDebugQueue, __setDebugQueue)

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
        temp.__momentum = mom
        temp.__misalignFactor = factor
        temp.__misalignType = misalignType
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
            raise Exception(f'ERROR! path doesn\'t go deep enough, can not extract all information!')

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

                if (self.__alignType != self.__misalignType) and self.useDebug:
                    print(f'DEBUG: Align type is not the same as misalign type. Is this correct?')

                if (self.__alignFactor != self.__misalignFactor) and self.useDebug:
                    print(f'DEBUG: Align factor is not the same as misalign type. Is this correct?')

                self.__alignMatFile = str(self.pathAlMatrix())

    #! --------------------- upadte env paths, for example when migrating to a different system
    def updateEnvPaths(self):
        alignmentDir = 'LMD_ALIGNMENT_DIR'
        pndRootDir = 'VMCWORKDIR'
        simDirEnv = 'LMDFIT_DATA_DIR'
        self.__cwd = str(Path.cwd())
        
        try:
            self.__alignmentDir = os.environ[alignmentDir]
        except:
            raise Exception(f"ERROR! Can't find LMDAlignment installation installation, please set {alignmentDir}!")

        try:
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            raise Exception(f"ERROR! Can't find PandaRoot installation, please set {pndRootDir}!")
        
        try:
            self.__simDataPath = os.environ[simDirEnv]
        except:
            raise Exception(f"ERROR! Can't find $SIMDATA, please set {simDirEnv}!")

    #! --------------------- generate matrix name after minimal initialization

    def generateMatrixNames(self):
        if self.__misalignType is None or self.__misalignFactor is None or self.__momentum is None:
            print(f'ERROR! not enough parameters set!')

        if self.__alignType is None:
            self.__alignType = self.__misalignType
        if self.__alignFactor is None:
            self.__alignFactor = self.__misalignFactor

        self.__misalignMatFile = str(self.pathMisMatrix())
        self.__alignMatFile = str(self.pathAlMatrix())
        self.__JobBaseDir = str(self.__resolveActual__(Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__()))

    #! --------------------- serialization, deserialization
    @classmethod
    def fromJSON(cls, filename):
        if not Path(filename).exists():
            raise Exception(f'ERROR! File {filename} can\'t be read!')
        temp = cls()
        with open(filename, 'r') as inFile:
            data = json.load(inFile)

        for key, value in data.items():
            setattr(temp, key, value)

        return temp

    # serialize to JSON
    def toJSON(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.__dict__, outfile, indent=2)
        pass

    #! --------------------- these define the path structure! ---------------------
    def __checkMinimum__(self):
        if self.__misalignFactor is None:
            raise Exception('ERROR! Align factor not set!')
        if self.__misalignType is None:
            raise Exception('ERROR! Align type not set!')
        if self.__momentum is None:
            raise Exception('ERROR! Beam Momentum not set!')

    def __checkIfNoneAreNone__(self):
        for val in self.__dict__.values():
            if val is None:
                raise Exception(f'ERROR in LMDRunConfig: some values are not set!')

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
        return Path(self.__tracksNum)

    def __jobBaseDir__(self):
        if self.__JobBaseDir is None:
            self.__JobBaseDir = str(self.__resolveActual__(Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__()))
        return Path(self.__JobBaseDir)

    def __uncut__(self):
        return Path('1-*_uncut')

    def __cut__(self):
        return Path('1-*_xy_m_cut_real')

    def __alignCorrectionSubDir__(self):
        if self.__alignmentCorrection:
            return Path('aligned*')
        else:
            return Path('no_alignment_correction')

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
            if self.useDebug:
                print(f'DEBUG: can\'t find resolve path on file system, returning globbed path!')
            return globbedPath

    #! --------------------- create paths to matrices, json results
    # alignment matrices are stored in the data directory from which they were found!
    def pathAlMatrixPath(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__()) / Path('alignmentMatrices')

    # TODO: actually, this is pretty pointless here, do this during CREATION of the runConfigs
    def pathAlMatrix(self):
        self.__checkMinimum__()

        if self.__useIdentityAlignment:
            return Path(self.__alignmentDir) / Path('input') / Path('alMat-identity-all.json')
        
        elif self.__mergeAlignmentMatrices:
            return self.pathAlMatrixPath() / Path(f'alMat-merged.json')
        
        else:
            if self.__misalignType == 'box' or self.__misalignType == 'boxRotZ':
                return self.pathAlMatrixPath() / Path(f'alMat-IPalignment-{self.__misalignFactor}.json')
            
            elif self.__misalignType == 'sensors':
                return self.pathAlMatrixPath() / Path(f'alMat-sensorAlignment-{self.__misalignFactor}.json')
            
            elif self.__misalignType == 'singlePlane' :
                return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')
            
            elif self.__misalignType == 'modules':
                return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')
            
            elif self.__misalignType == 'modulesNoRot':
                return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')
            
            elif self.__misalignType == 'modulesOnlyRot':
                return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')
            # TODO: add for combined

    def pathMisMatrix(self):
        self.__checkMinimum__()
        return self.__resolveActual__(Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('misMatrices') / Path(f'misMat-{self.__misalignType}-{self.__misalignFactor}.json'))

    def pathRecoIP(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__recoIP__())

    def pathLumiVals(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__lumiVals__())

    def pathDataBaseDir(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__alignCorrectionSubDir__())

    # for AlignIP et al. methods
    def pathTrksQA(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__())

    def pathJobBase(self):
        return self.__resolveActual__(self.__jobBaseDir__())

    #! --------------------- verbose output

    def dump(self):
        result = ''
        result += (f'\n\n')
        result += (f'------------------------------\n')
        result += (f'DEBUG OUTPUT for LMDRunConfig:\n\n')
        result += (f'Job Base Dir: {self.__JobBaseDir}\n')
        result += (f'Path: {self.__fromPath}\n')
        result += (f'Momentum: {self.__momentum}\n')
        result += (f'Misalign Type: {self.__misalignType}\n')
        result += (f'Misalign Factor: {self.__misalignFactor}\n')
        result += (f'Align Type: {self.__alignType}\n')
        result += (f'Align Factor: {self.__alignFactor}\n')
        result += (f'AlignMatrices: {self.__alignMatFile}\n')
        result += (f'MisalignMatrices: {self.__misalignMatFile}\n')
        result += (f'TracksQA path: {self.pathTrksQA()}\n')
        result += (f'Num Tracks: {self.__tracksNum}\n')
        result += (f'Num Jobs: {self.__jobsNum}\n')
        result += (f'------------------------------\n')
        result += (f'\n\n')
        return result
