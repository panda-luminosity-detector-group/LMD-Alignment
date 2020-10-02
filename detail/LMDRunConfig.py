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

- alignment matrix used
- misalignment matrix used
- alignment factor
- beam momentum
- bunches / binning numbers for Lumi Fit

handles these things implicitly:
- uses json matrices by default

most importantly, can also create paths given these parameters:
- beam momentum
- align matrices
- misalign matrices
- reco_ip.json location (for use with ./extractLuminosity)
- lumi_vals.json location (for use with ./extractLuminosity)
"""


class LMDRunConfig:
    def __init__(self):

        #  keep these hidden variables
        self.__JobBaseDir = None

        # new porperties, plain and simple
        self.jobsNum = '100'
        self.trksNum = '100000'
        self.alMatFile = None
        self.misMatFile = None
        self.misalignFactor = None
        self.misalignType = None
        self.seedID = None
        self.misaligned = True
        self.useIdentityAlignment = False
        self.alignmentCorrection = False
        self.useDebug = False
        self.useDevQueue = False
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
        # corrEq = self.alignmentCorrection == other.alignmentCorrection

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

    #! --------------------- minimal default constructor
    @classmethod
    def minimalDefault(cls, mom='1.5', misalignType='identity', factor='1.00'):
        temp = cls()
        temp.momentum = mom
        temp.misalignFactor = factor
        temp.misalignType = misalignType
        return temp

    # #! --------------------- upadte env paths, for example when migrating to a different system
    # # TODO: remove once the whole autogen stuff is gone
    def updateEnvPaths(self):
        simDirEnv = 'LMDFIT_DATA_DIR'

        try:
            self.__simDataPath = os.environ[simDirEnv]
        except:
            raise Exception(f"ERROR! Can't find $SIMDATA, please set {simDirEnv}!")

    #! --------------------- generate matrix name after minimal initialization

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

    #* ----- keep this one
    def __pathMom__(self):
        return Path(f'plab_{self.momentum}GeV')

    #* ----- keep this one
    def __pathDPM__(self):
        return Path('dpm_elastic_theta_2.7-13.0mrad_recoil_corrected')

    #* ----- keep this one
    def __pathMisalignDir__(self):
        if self.misalignType == 'aligned':
            return Path('no_geo_misalignment')
        else:
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

    #* ----- keep this one
    def pathRecoIP(self):
        self.__checkMinimum__()
        return self.__resolveActual__(self.__jobBaseDir__() / self.__uncut__() / self.__alignCorrectionSubDir__() / self.__bunches__() / self.__recoIP__())

    #* ----- keep this one
    def pathLumiVals(self):
        """
        There is a small bug here. This works for all runConfigs that have the correct useAlignCorrection flag, except MultiSeeds.
        Those are currently all set to false and we can only get the lumi vals for the corrected case. but we want uncorrected as well!
        So there is a small hack here (please don't judge me)
        
        
        wait I dont think this is needed anymore. the lumi fit is always done on cut data, because otherwise it reaches > 500%. That's why the true is in the if clause above
        """

        """
        TODO: actually, this is only because the lumi fit was once done ALWAYS on cut data, then on UNcut but only if no alignment was done. This is a mess of course.
        It can be fixed though.

        If you want the extracted lumi for multiSeed (yes, that is possible), always use the UNcor UNcorrected branch (set the if to always fail with an 'and False')
        """
        self.__checkMinimum__()
        if (self.alignmentCorrection or self.misalignType == 'aligned') or True:# and False:
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
        result += (f'QA File Dir: {self.pathTrksQA}\n')
        result += (f'Momentum: {self.momentum}\n')
        result += (f'AlignMatrices: {self.alMatFile}\n')
        result += (f'MisalignMatrices: {self.misMatFile}\n')
        result += (f'TracksQA path: {self.pathTrksQA()}\n')
        result += (f'Num Tracks: {self.trksNum}\n')
        result += (f'Num Jobs: {self.jobsNum}\n')
        result += (f'------------------------------\n')
        result += (f'\n\n')
        return result
