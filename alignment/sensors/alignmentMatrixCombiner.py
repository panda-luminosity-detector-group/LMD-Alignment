#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Uses multiple overlap matrices and the ideal detector matrices to compute alignment matrices for each sensor.
Each combiner is responsible for a single module.

Steps:

- gather all overlap matrices for module in a dict 
- base transform to module system
- combine overlap matrices to form 0->x matrices
- gather perfect 0->x matrices (base transformed to module system)
- substract (inverse multiply actually) perfect matrices to combined 0->x matrices
- remainder is misalignment AS GIVEN IN MODULE SYSTEM
- base transform each misalignment matrix to system of respective sensor
- save to dict, return to master
"""

class alignmentMatrixCombiner:

    def __init__(self, modulePath):
        self.modulePath = modulePath
        self.alignmentMatrices = {}

    def setOverlapMatrices(self, matrices):
        self.overlapMatrices = matrices

    def setIdealDetectorMatrices(self, matrices):
        self.idealDetectorMatrices = matrices

    def getDigit(self, number, n):
        return int(number) // 10**n % 10

    def getSmallOverlap(self, overlap):
        return self.getDigit(overlap, 0)

    def combineMatrices(self):
        # checks here
        if self.overlapMatrices is None or self.idealDetectorMatrices is None:
            print(f'ERROR! Please set overlaps and ideal detector matrices first!')
            return

        # computations here
        print(f'\n\nCombiner for {self.modulePath}:\n{self.overlapMatrices}\n')

        # create all intermediate matrices here

        # compute here

        # remove ideal here

        # remainder is here

        # transform here

        # save to dict sensorID : alignment matrix here


    def getAlignmentMatrices(self):
        return self.alignmentMatrices

    pass