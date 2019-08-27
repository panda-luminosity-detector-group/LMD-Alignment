#!/usr/bin/env python3

import numpy as np

import json
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')   # so matplotlib works over ssh/with no DISPLAY

"""
Comapre ICP matrices from sensor overlap with actual misalignment matrices from PandaROOT.
"""


class idealCompare:

    def __init__(self, overlapMatrices):
        self.overlapMatrices = overlapMatrices

    #! ----------------------- delete from here

    def histogramICP(self):

        misaligns = ['0', '100', '200']
        cuts = [0, 2]
        twoD = [False, True]

        pdfOutPath = './output/forDPG/'

        if not os.path.exists(pdfOutPath):
            os.makedirs(pdfOutPath)

        for misalign in misaligns:
            for cut in cuts:
                for use2D in twoD:
                    print('generating for misalign {}, cut {}'.format(misalign, cut))
                    values = self.computeAllMatrices(cut, misalign, use2D)
                    self.histBinaryPairDistancesForDPG(misalign, values, use2D, cut)
                    print('saving image...')
                    if use2D:
                        d = '2D'
                    else:
                        d = '1D'
                    plt.savefig(pdfOutPath + 'dx-mis{}-cut{}-{}.png'.format(misalign, cut, d), dpi=150)

    def histBinaryPairDistancesForDPG(self, misalign, values, use2Dcut=True, cutPercent=0):

        sigX = np.std(values)
        #muX = np.average(values)
        textStr = 'σx={:1.2f}'.format(sigX)

        # plot differnce hit array
        fig = plt.figure(figsize=(6, 4))

        if cutPercent == 0:
            fig.suptitle('{}u, no cut'.format(misalign), fontsize=16)
        elif use2Dcut:
            fig.suptitle('{}u, {}% 2D cut'.format(misalign, cutPercent), fontsize=16)
        elif not use2Dcut:
            fig.suptitle('{}u, {}% 1D cut'.format(misalign, cutPercent), fontsize=16)

        fig.subplots_adjust(wspace=0.05)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        histA = fig.add_subplot(1, 1, 1)
        histA.hist(values, bins=20, range=[-6.0, 6.0])  # this is only the z distance
        histA.set_title('distance ICP matrix - generated')   # change to mm!
        histA.set_xlabel('d [µm]')
        histA.set_ylabel('count')
        histA.text(0.05, 0.95, textStr, transform=histA.transAxes, fontsize=12, verticalalignment='top')
        return fig

    def computeAllMatrices(self, cut, misalign, use2D):
        overlaps = createAllOverlaps()
        matrices = ri.readJSON("input/overlaps.json")

        # overlaps = overlaps[:20]    # use only first 10 elements for now
        values = []
        print('computing ICP values...')
        for overlap in overlaps:
            values.append(self.computeOneICP(overlap, cut, misalign, matrices, use2D))

        return values

    def computeOneICP(self, overlapID, cut, misalign, matrices, use2D):

        path = 'input/2018-08-himster2-misalign-' + str(misalign) + 'u/'
        ICPmatrix = finder.findMatrix(path, str(overlapID), cut, matrices, use2D)

        # if misalign is 0, the target misalign matrix is the identity matrix
        if misalign == '0':
            return ICPmatrix[0][3]*1e4

        # json paths:
        jsonPath = 'input/rootMisalignMatrices/json/misalignMatrices-SensorsOnly-' + str(misalign) + '.root.json'

        with open(jsonPath, 'r') as f:
            misMat = json.load(f)

        path1 = matrices[str(overlapID)]['path1']
        path2 = matrices[str(overlapID)]['path2']

        # generate overlap matrix from known misalign matrices like those the ICP would find
        mis1 = np.array(misMat[path1]).reshape(4, 4)                                                            # misalignment to sensor1
        mis2 = np.array(misMat[path2]).reshape(4, 4)                                                            # misalignment to sensor2
        toSen1 = np.array(matrices[str(overlapID)]['matrix1']).reshape(4, 4)                                    # total matrix PANDA -> sensor1
        toSen2 = np.array(matrices[str(overlapID)]['matrix2']).reshape(4, 4)                                    # total matrix PANDA -> sensor2
        sen1tosen2 = np.linalg.multi_dot([np.linalg.inv(toSen1), toSen2])                                       # matrix from sensor1 to sensor2, needed for base transform!
        mis2inSen1 = np.linalg.multi_dot([sen1tosen2, mis2, np.linalg.inv(sen1tosen2)])                         # mis2 in the frame of reference of sensor1, this is a base transform
        mis1to2 = np.linalg.multi_dot([np.linalg.inv(mis1), mis2inSen1])                                        # the final matrix that we want

        return ((mis1to2 - ICPmatrix)[0][3]*1e4)

    #! ----------------------- delete until here

    def loadDesignMatrices(self, fileName):
        print(f'Will load design matrices from {fileName}.')
        with open(fileName) as designFile:
            self.designMatrices = json.load(designFile)

    def hist(self):

        # get all overlaps from json (id1, id2, path1, path2 compose an "overlap")

        with open('input/detectorMatricesIdeal.json') as overlapFile:
            overlaps = json.load(overlapFile)

        for o in overlaps:
            path1 = overlaps[o]["path1"]
            path2 = overlaps[o]["path2"]
            print(f'Overlap: {o}')
            print(f'id 1: {overlaps[o]["id1"]}')
            print(f'id 2: {overlaps[o]["id2"]}')
            print(f'path 1: {path1}')
            print(f'path 2: {path2}')

            # these are the design misalignment matrices
            print(f'matrix 1: {self.designMatrices[path1]}')
            print(f'matrix 2: {self.designMatrices[path2]}')

        # get all ideal matrices from json, already done
        

        # get all ICP matrices from constructor

        # get all overlapIDs from constructor

        # compute dx and dy from ideal - ICP

        # histogram that shit

        return
