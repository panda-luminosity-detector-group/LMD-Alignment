#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from detail.LMDRunConfig import LMDRunConfig

"""
this script handles all simulation related abstractions.

it:
- browses paths for TrksQA, reco_ip and lumi_vals
- runs simulations (aligned, misaligned)
- runs aligner scripts (alignIP, alignSensors, alignCorridors)
- re-runs simulations with align matrices
- runs ./determineLuminosity
- runs ./extractLuminosity
- compares lumi values before and after alignment
- compares found alignment matrices with actual alignment matrices
- converts JSON to ROOT matrices and vice-versa (with ROOT macros)

TODO:
- remember to delete everything after mc genereation for new run

---------- steps in ideal geometry sim ----------

- run ./doSimulationReconstruction wit correct parameters (doesn't block)
- run ./determineLuminosity (blocks!)
- run ./extractLuminosity   (blocks!)

---------- steps in misaligned geometry sim ----------

- run ./doSimulationReconstruction wit correct parameters
- run ./determineLuminosity
- run ./extractLuminosity

---------- steps in misaligned geometry with correction ----------
- run ./doSimulationReconstruction with correct parameters
- run ./determineLuminosity
- run ./extractLuminosity
- run my aligners
- rerun ./doSimulationReconstruction with correct parameters
- rerun ./determineLuminosity
- rerun ./extractLuminosity


"""


class simWrapper():

    # empty constructor
    def __init__(self):
        # find env variabled
        lmdFitEnv = 'LMDFIT_BUILD_PATH'
        simDirEnv = 'LMDFIT_DATA_DIR'
        self._cwd = Path.cwd()
        try:
            self._lumiFitPath = Path(os.environ[lmdFitEnv]).parent
            self._simDataPath = Path(os.environ[simDirEnv])
        except:
            print("can't find LuminosityFit installation or Data_Dir!")
            print(f"please set {lmdFitEnv} and {simDirEnv}!")
            sys.exit(1)

    @classmethod
    def fromRunConfig(cls, LMDRunConfig) -> 'simWrapper':
        print('I wanna go home (;-;) ')

    def dump(self):
        print(f'\n\nDEBUG OUTPUT for SimWrapper:\n')
        print(f'LumiFit is in: {self._lumiFitPath}')
        print(f'Sim Data is in: {self._simDataPath}')
        print(f'CWD: {self._cwd}')
        print(f'\n\n')

    def setRunConfig(self, LMDRunConfig):
        self._config = LMDRunConfig

    def detLumi(self):
        if self._config is None:
            print(f'please set run config first!')

        absPath = self._config._path
        print(f'path: {absPath}')

        scriptsPath = self._lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # close file desciptor to run command in different process and return
        subprocess.Popen((command, argP, argPval), close_fds=True)


def run():
    path = '/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-box-3.00/100000/1-500_uncut_aligned'
    config = LMDRunConfig(path)

    wrapper = simWrapper()
    wrapper.setRunConfig(config)
    wrapper.detLumi()


def testGenerators():
    config = LMDRunConfig('')
    gen1 = config.genBeamMomenta()
    gen2 = config.genFactors()
    gen3 = config.genMisalignments()

    for i in gen3:
        print(f'i is:{i}')


if __name__ == "__main__":
    print('greetings, human')
    run()
