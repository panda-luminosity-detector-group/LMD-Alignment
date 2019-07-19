#!/usr/bin/env python3

from pathlib import Path

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

    def __init__(self, path):
        self._path = Path(path)

        # self._alignMat = findAlignMat()
        # self._misalignMat = findMisalignMat()
        # self._alignFactor = findAlignFactor()
        # self._momentum = findMomentum()

    # def __init__(self):
    #     print('no path specified')

    # generators for factors, alignments, beam momenta

    def genBeamMomenta(self):
        momenta = ['1.5', '4.06', '8.9', '11.91', '15.0',]
        for mom in momenta:
            yield mom

    def genFactors(self):
        factors = ['0.01', '0.05', '0.10', '0.15', '0.2', '0.25', '0.5', '1.00', '2.00', '3.00', '5.00', '10.00']
        for f in factors:
            yield f

    def genMisalignments(self):
        misalignments = ['sensors', 'box', 'combi', 'modules', 'identity', 'all']
        for mis in misalignments:
            yield mis


if __name__ == "__main__":
    print("Sorry, this module can't be run directly")
