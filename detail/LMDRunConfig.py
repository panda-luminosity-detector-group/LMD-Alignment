#!/usr/bin/env python3

from pathlib import Path

import glob
# import re
# import sys
import os
import json
"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

pathlib wrapper specifically for our LMD case. a config object only hold the parameters for a single simulation run!

uses pathlib internally and stores some additional values as well:

# TODO: remove combiMat and stages, you don't actually need them. a single runCombi function does this work now.

# TODO: this thing was a huge mistake. all those hidden variabled don't need to be hidden and getters and setters are so no neccessary. just make everything a dict entry and be done with it.

TODO: oh and ffs don't auto generate matrix names. just set them at creation time and let the user change them. wtf were you thinking.

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
        # self.__fromPath = None
        # self.__misalignFactor = None
        # self.__alignFactor = None
        # self.__sensorAlignerExternalMatrices = None
        # self.__moduleAlignAnchorPointFile = None
        # self.__moduleAlignAvgMisalignFile = None
        # self.combiMat = ''
        # self.stages = [True, True, True]
        # self.misMatFile = None
        # self.__mergeAlignmentMatrices = False

        #  keep these hidden variables
        self.__JobBaseDir = None

        # new porperties, plain and simple
        # self.alignType = None
        # self.alMatFile = None
        self.alMatFile = None
        self.misMatFile = None
        self.misalignFactor = None
        self.misalignType = None
        # self.moduleAlignAvgMisalignFile = None
        # self.moduleAlignAnchorPointFile = None
        # self.sensorAlignExternalMatrixPath = None
        # self.momentum = None
        self.trksNum = '100000'
        self.jobsNum = '100'
        self.misaligned = True
        self.alignmentCorrection = False
        self.useDebug = False
        self.useDevQueue = False
        self.useIdentityAlignment = False
        self.forDisableCut = False
        self.updateEnvPaths()


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

    #! --------------------- getters and setters

    # def __getAlMatFile(self):
    #     return self.alMatFile

    # def __setAlMatFile(self, value):
    #     self.alMatFile = value

    # def setAlMat(self, value):
    #     self.alMatFile = value

    # alMatFile = property(__getAlMatFile, __setAlMatFile)

    # def __getMisMatFile(self):
    #     return self.misMatFile

    # def __setMisMatFile(self, value):
    #     self.misMatFile = value

    # misMatFile = property(__getMisMatFile, __setMisMatFile)


    # def __getAvgMisPath(self):
    #     return self.__moduleAlignAvgMisalignFile

    # def __setAvgMisPath(self, val):
    #     self.__moduleAlignAvgMisalignFile = val

    # moduleAlignAvgMisalignFile = property(__getAvgMisPath, __setAvgMisPath)

    # def __getAnchorPath(self):
    #     return self.__moduleAlignAnchorPointFile

    # def __setAnchorPath(self, val):
    #     self.__moduleAlignAnchorPointFile = val

    # moduleAlignAnchorPointFile = property(__getAnchorPath, __setAnchorPath)

    # def __getExMatPath(self):
    #     return self.__sensorAlignerExternalMatrices

    # def __setExMatPath(self, value):
    #     self.__sensorAlignerExternalMatrices = value

    # sensorAlignExternalMatrixPath = property(__getExMatPath, __setExMatPath)

    # def __getMisalignFactor(self):
    #     return self.__misalignFactor

    # def __setMisalignFactor(self, value):
    #     self.__misalignFactor = value

    # misalignFactor = property(__getMisalignFactor, __setMisalignFactor)

    # def __getMisalignType(self):
    #     return self.misalignType

    # def __setMisalignType(self, value):
    #     self.misalignType = value

    # misalignType = property(__getMisalignType, __setMisalignType)

    # def __setUseIdentityAlignment(self, value):
    #     self.useIdentityAlignment = value

    # def __getUseIdentityAlignment(self):
    #     return self.useIdentityAlignment

    # useIdentityMisalignment = property(__getUseIdentityAlignment, __setUseIdentityAlignment)

    # def __setMergeAlignmentMatrices(self, value):
    #     self.mergeAlignmentMatrices = value

    # def __getMergeAlignmentMatrices(self):
    #     return self.mergeAlignmentMatrices

    # mergeAlignmentMatrices = property(__getMergeAlignmentMatrices, __setMergeAlignmentMatrices)

    # def __getDebug(self):
    #     return self.useDebug

    # def __setDebug(self, debug):
    #     self.useDebug = debug

    # useDebug = property(__getDebug, __setDebug)

    # def __getDebugQueue(self):
    #     return self.useDevQueue

    # def __setDebugQueue(self, debug):
    #     self.useDevQueue = debug

    # useDevQueue = property(__getDebugQueue, __setDebugQueue)

    # def __getMisaligned(self):
    #     return self.misaligned

    # def __setMisaligned(self, value):
    #     self.misaligned = value

    # misaligned = property(__getMisaligned, __setMisaligned)

    # def __getAlignmentCorrection(self):
    #     return self.alignmentCorrection

    # def __setAlignmentCorrection(self, value):
    #     self.alignmentCorrection = value

    # alignmentCorrection = property(__getAlignmentCorrection, __setAlignmentCorrection)

    # def __getJobsNum(self):
    #     return self.jobsNum

    # def __setJobsNum(self, value):
    #     self.jobsNum = value

    # jobsNum = property(__getJobsNum, __setJobsNum)

    # def __getTrksNum(self):
    #     return self.trksNum

    # def __setTrksNum(self, value):
    #     self.trksNum = value

    # trksNum = property(__getTrksNum, __setTrksNum)

    # def __getMomentum(self):
    #     return self.momentum

    # def __setMomentum(self, value):
    #     self.momentum = value

    # momentum = property(__getMomentum, __setMomentum)

    # #! --------------------- constructor "overloading"
    # @classmethod
    # def fromPath(cls, path) -> 'LMDRunConfig':
    #     temp = cls()
    #     # temp.__fromPath = path
    #     temp.parseFromString()
    #     return temp

    #! --------------------- minimal default constructor
    @classmethod
    def minimalDefault(cls, mom='1.5', misalignType='identity', factor='1.00'):
        temp = cls()
        temp.momentum = mom
        temp.misalignFactor = factor
        temp.misalignType = misalignType
        return temp

    # TODO: you never once used this function. may as well just delete it.
    # def parseFromString(self):
    #     pathParts = Path(self.__fromPath).parts

    #     # search for plab, our dir tree begins here
    #     index = 0
    #     for part in pathParts:
    #         match = re.search("plab_(.*)GeV", part)
    #         if match:
    #             self.momentum = match.groups()[0]
    #             break
    #         index += 1

    #     # from here, we know the directory structure, no more guess work!
    #     pathParts = pathParts[index:]

    #     # we need at least the misalignment sub directory
    #     # 0: plab
    #     # 1: dpm
    #     # 2: aligned or misalignment!
    #     # 3: 1-500_uncut or 1-100_cut
    #     # 4: Num Tracks
    #     # 5: aligned or something else

    #     if len(pathParts) < 3:
    #         raise Exception(f'ERROR! path doesn\'t go deep enough, can not extract all information!')

    #     if pathParts[2] == 'no_geo_misalignment':
    #         self.misalignType = 'aligned'
    #         self.__misalignFactor = '1.00'
    #         self.misaligned = False

    #     else:
    #         match = re.search("geo_misalignmentmisMat-(\w+)-(\d+\.\d+)", pathParts[2])
    #         if match:
    #             if len(match.groups()) > 1:
    #                 self.misalignType = match.groups()[0]
    #                 self.__misalignFactor = match.groups()[1]
    #                 self.misaligned = True
    #         else:
    #             print(f'can\'t parse info from {pathParts[2]}!')

    #     # set misalign matrices from values!
    #     self.misMatFile = str(self.pathMisMatrix())

    #     # ? optional parser arguments
    #     if len(pathParts) > 3:
    #         self.trksNum = pathParts[3]

    #     if len(pathParts) > 4:
    #         match = re.search('1-(\d+)_uncut', pathParts[4])
    #         if match:
    #             self.jobsNum = match.groups()[0]

    #     # alignment matrix
    #     if len(pathParts) > 5:
    #         match = re.search('aligned-alMat-(\w+)-(\d+\.\d+)', pathParts[5])
    #         if match:
    #             self.alignType = match.groups()[0]
    #             self.__alignFactor = match.groups()[1]
    #             self.alignmentCorrection = True

    #             if (self.alignType != self.misalignType) and self.useDebug:
    #                 print(f'DEBUG: Align type is not the same as misalign type. Is this correct?')

    #             if (self.__alignFactor != self.__misalignFactor) and self.useDebug:
    #                 print(f'DEBUG: Align factor is not the same as misalign type. Is this correct?')

    #             self.alMatFile = str(self.pathAlMatrix())

    # #! --------------------- upadte env paths, for example when migrating to a different system
    # # TODO: remove once the whole autogen stuff is gone
    def updateEnvPaths(self):
    #     alignmentDir = 'LMD_ALIGNMENT_DIR'
    #     pndRootDir = 'VMCWORKDIR'
        simDirEnv = 'LMDFIT_DATA_DIR'
    #     self.__cwd = str(Path.cwd())

    #     try:
    #         self.__alignmentDir = os.environ[alignmentDir]
    #     except:
    #         raise Exception(f"ERROR! Can't find LMDAlignment installation installation, please set {alignmentDir}!")

    #     try:
    #         self.__pandaRootDir = os.environ[pndRootDir]
    #     except:
    #         raise Exception(f"ERROR! Can't find PandaRoot installation, please set {pndRootDir}!")

        try:
            self.__simDataPath = os.environ[simDirEnv]
        except:
            raise Exception(f"ERROR! Can't find $SIMDATA, please set {simDirEnv}!")

    #! --------------------- generate matrix name after minimal initialization

    # TODO: nope, just nope. remove and set during creation.
    def generateMatrixNames(self):
        raise Exception(f"You're not supposed to call generateMatrixNames anymore!")

        # if self.misalignType is None or self.__misalignFactor is None or self.momentum is None:
        #     print(f'ERROR! not enough parameters set!')

        # if self.alignType is None:
        #     self.alignType = self.misalignType
        # if self.__alignFactor is None:
        #     self.__alignFactor = self.__misalignFactor

        # self.misMatFile = str(self.pathMisMatrix())
        # self.alMatFile = str(self.pathAlMatrix())
        # self.generateJobBaseDir()

    # keep this in for now
    def generateJobBaseDir(self):
        self.__JobBaseDir = str(self.__resolveActual__(Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__()))

    #! --------------------- serialization, deserialization
    @classmethod
    def fromJSON(cls, filename):
        if not Path(filename).exists():
            raise Exception(f'ERROR! File {filename} cannot be read!')
        temp = cls()
        with open(filename, 'r') as inFile:
            data = json.load(inFile)

        for key, value in data.items():
            setattr(temp, key, value)

        return temp

    # serialize to JSON
    def toJSON(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.__dict__, outfile, indent=2, sort_keys=True)
        pass

    #! --------------------- these define the path structure! ---------------------
    def __checkMinimum__(self):
        # self.__checkIfNoneAreNone__()
        if self.misalignFactor is None:
            raise Exception('ERROR! Align factor not set!')
        if self.misalignType is None:
            raise Exception('ERROR! Align type not set!')
        if self.momentum is None:
            raise Exception('ERROR! Beam Momentum not set!')


    # def __checkIfNoneAreNone__(self):
    #     for val in self.__dict__.values():
    #         if val is None:
    #             raise Exception(f'ERROR in LMDRunConfig: some values are not set!')

    #* ----- keep this one
    def __pathMom__(self):
        return Path(f'plab_{self.momentum}GeV')

    #* ----- keep this one
    def __pathDPM__(self):
        return Path('dpm_elastic_theta_*mrad_recoil_corrected')

    #* ----- keep this one
    def __pathMisalignDir__(self):
        if self.misalignType == 'aligned':
            return Path('no_geo_misalignment')
        else:
            # return Path(f'geo_misalignmentmisMat-{self.misalignType}-{self.__misalignFactor}')
            return Path(f'geo_misalignment{str(Path(self.misMatFile).stem)}')

    #* ----- keep this one
    def __pathTracksNum__(self):
        return Path(self.trksNum)

    #* ----- keep this one
    def __jobBaseDir__(self):
        if self.__JobBaseDir is None:
            self.__JobBaseDir = str(
                self.__resolveActual__(Path(self.__simDataPath) / self.__pathMom__() / self.__pathDPM__() / self.__pathMisalignDir__() / self.__pathTracksNum__()))
        return Path(self.__JobBaseDir)

    #* ----- keep this one
    def __uncut__(self):
        return Path(f'1-{self.jobsNum}_uncut')

    #* ----- keep this one
    def __cut__(self):
        return Path('1-*_xy_m_cut_real')

    #* ----- keep this one
    def __alignCorrectionSubDir__(self):
        if self.alignmentCorrection:
            return Path(f'aligned-{Path(self.alMatFile).stem}')
        else:
            return Path('no_alignment_correction')

    #* ----- keep this one
    def __bunches__(self):
        return Path('bunches*') / Path('binning*') / Path('merge_data')

    #* ----- keep this one
    def __lumiVals__(self):
        return Path('lumi-values.json')

    #* ----- keep this one
    def __recoIP__(self):
        return Path('reco_ip.json')

    # this is a fuck ugly hack, but pathlib fails whenever dots are in a path or file name
    def __resolveActual__(self, globbedPath):
        result = glob.glob(str(globbedPath))
        if len(result) > 0:
            return Path(result[0])
        else:
            if self.useDebug:
                print(f'DEBUG: can\'t find resolve path on file system, returning globbed path:\n{globbedPath}\n')
            return globbedPath

    #! --------------------- create paths to matrices, json results
    #* ----- keep this one
    def pathAlMatrixPath(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__()) / Path('alignmentMatrices')

    # TODO: jesus christ just no. no no no no. delete this too.
    # TODO: actually, this is pretty pointless here, do this during CREATION of the runConfigs and DELETE THIS FUNCTION
    def pathAlMatrix(self):
        raise Exception(f'You\'re not supposed to call pathAlMatrix anymore! Do you need the alMat filename?')
        # self.__checkMinimum__()

        # if self.useIdentityAlignment:
        #     return Path(self.__alignmentDir) / Path('input') / Path('alMat-identity-all.json')

        # elif self.__mergeAlignmentMatrices:
        #     return self.pathAlMatrixPath() / Path(f'alMat-merged.json')

        # else:
        #     if self.misalignType == 'box' or self.misalignType == 'boxRotZ' or self.misalignType == 'box100':
        #         return self.pathAlMatrixPath() / Path(f'alMat-IPalignment-{self.__misalignFactor}.json')

        #     elif self.misalignType == 'sensors':
        #         return self.pathAlMatrixPath() / Path(f'alMat-sensorAlignment-{self.__misalignFactor}.json')

        #     elif self.misalignType == 'singlePlane':
        #         return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')

        #     elif self.misalignType == 'modules':
        #         return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')

        #     elif self.misalignType == 'modulesNoRot':
        #         return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')

        #     elif self.misalignType == 'modulesOnlyRot':
        #         return self.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{self.__misalignFactor}.json')
        #     elif self.misalignType == 'combi':
        #         return self.combiMat

    # TODO: no, just return stored value
    def pathMisMatrix(self):
        raise Exception(f'You\'re not supposed to call pathMisMatrix anymore! Do you need the alMat filename?')
        # self.__checkMinimum__()
        # return self.__resolveActual__(
        #     Path(self.__pandaRootDir) / Path('macro') / Path('detectors') / Path('lmd') / Path('geo') / Path('misMatrices') /
        #     Path(f'misMat-{self.misalignType}-{self.__misalignFactor}.json'))

    #* ----- keep this one
    def pathRecoIP(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__recoIP__())

    #* ----- keep this one
    def pathLumiVals(self):
        self.__checkMinimum__()
        if self.alignmentCorrection or self.misalignType == 'aligned':
            return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__lumiVals__())
        else:
            return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__lumiVals__())

    #* ----- keep this one
    def pathDataBaseDir(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__cut__() / self.__alignCorrectionSubDir__())

    #* ----- keep this one
    def pathTrksQA(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__())

    #* ----- keep this one
    def pathJobBase(self):
        return self.__resolveActual__(self.__jobBaseDir__())

    #! --------------------- verbose output
    # TODO: this may just be the single useful function here. tidy it up!
    def dump(self):
        result = ''
        result += (f'\n\n')
        result += (f'------------------------------\n')
        result += (f'DEBUG OUTPUT for LMDRunConfig:\n\n')
        result += (f'Job Base Dir: {self.__JobBaseDir}\n')
        # result += (f'Path: {self.__fromPath}\n')
        result += (f'Momentum: {self.momentum}\n')
        # result += (f'Misalign Type: {self.misalignType}\n')
        # result += (f'Misalign Factor: {self.__misalignFactor}\n')
        # result += (f'Align Type: {self.alignType}\n')
        # result += (f'Align Factor: {self.__alignFactor}\n')
        result += (f'AlignMatrices: {self.alMatFile}\n')
        result += (f'MisalignMatrices: {self.misMatFile}\n')
        result += (f'TracksQA path: {self.pathTrksQA()}\n')
        result += (f'Num Tracks: {self.trksNum}\n')
        result += (f'Num Jobs: {self.jobsNum}\n')
        result += (f'------------------------------\n')
        result += (f'\n\n')
        return result
