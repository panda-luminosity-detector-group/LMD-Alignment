#!/usr/bin/env python3

"""
Uses multiple overlap matrices and the ideal detector matrices to compute alignment matrices for each sensor.

Every combiner is responsible for a single module.

Steps:

- gather all overlap matrices for module
- base transform to module system
- combine overlap matrices to form 0->x matrices
- gather perfect 0->x matrices (base transformed to module system)
- substract (inverse multiply actually) perfect matrices to combined 0->x matrices
- remainer is misalignment AS GIVEN IN MODULE SYSTEM
- base transform each misalignment matrix to system of respective sensor
- save to dict, return to master
"""

class alignmentMatrixCombiner:

    def __init__(self, module):
        self.module = module
        self.alignmentMatrices = {}

    def setOverlapMatrices(self, matrices):
        self.overlapMatrices = matrices

    def setIdealDetectorMatrices(self, matrices):
        self.idealDetectorMatrices = matrices

    def combineMatrices(self):
        # checks here

        # computations here

        # save to internal state here

        pass

    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    pass