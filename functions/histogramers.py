#!/usr/bin/env python3

import functions.rootInterface as ri
import functions.pairFinder as finder
import numpy as np
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

if __name__ == "main":
    print("Sorry, this module can't be run directly")


class histogram(object):

    def __init__(self, matrices):
        self.__matrices = matrices

    def histBinaryPairFileSingle_dx_dy(self, path, overlapID, cut, axes):

        filename = path + 'binaryPairFiles/pairs-' + overlapID + '-cm.bin'

        #print('reading file:', filename)

        # read binary Pairs
        fileUsable = ri.readBinaryPairFile(filename)

        # apply dynmaic cut
        fileUsable = finder.dynamicCut(fileUsable, cut)

        # slice to separate vectors
        hit1 = fileUsable[:, :3]
        hit2 = fileUsable[:, 3:6]

        # Make C a homogeneous representation of A and B
        hit1H = np.ones((len(fileUsable), 4))
        hit1H[:, 0:3] = hit1
        hit2H = np.ones((len(fileUsable), 4))
        hit2H[:, 0:3] = hit2

        # make numpy matrix from JSON info
        toSen1 = np.array(self.__matrices[overlapID]['matrix1']).reshape(4, 4)

        # invert matrices
        toSen1Inv = np.linalg.inv(toSen1)

        # transform hit1 and hit2 to frame of reference of hit1
        hit1T = np.matmul(toSen1Inv, hit1H.T).T
        hit2T = np.matmul(toSen1Inv, hit2H.T).T

        # make difference hit array
        dHit = hit2T[:, :3] - hit1T[:, :3]

        sigX = np.std(dHit[:, 0])*1e4
        sigY = np.std(dHit[:, 1])*1e4
        muX = np.average(dHit[:, 0])*1e4
        muY = np.average(dHit[:, 1])*1e4

        textStr = 'µx={:1.2f}µm, σx={:1.2f}µm\nµy={:1.2f}µm, σy={:1.2f}µm'.format(
            muX, sigX, muY, sigY)

        axes.hist2d(dHit[:, 0], dHit[:, 1], bins=150,
                    norm=LogNorm(), range=[[-0.12, 0.12], [-0.12, 0.12]])
        axes.text(0.05, 0.95, textStr, transform=axes.transAxes,
                  fontsize=12, verticalalignment='top')

        # this is currently wrong, change this!
        axes.set_title('mis: dx: {:1.2f}µm, dy: {:1.2f}µm'.format(
            toSen1[0][3], toSen1[1][3]))
        axes.set_xlabel('dx [cm]')
        axes.set_ylabel('dy [cm]')

    def histBinaryPairFileSingle_x_dx(self, path, overlapID, cut, axes):

        filename = path + 'binaryPairFiles/pairs-' + overlapID + '-cm.bin'

        #print('reading file:', filename)

        # read binary Pairs
        fileUsable = ri.readBinaryPairFile(filename)

        # apply dynmaic cut
        fileUsable = finder.dynamicCut(fileUsable, cut)

        # slice to separate vectors
        hit1 = fileUsable[:, :3]
        hit2 = fileUsable[:, 3:6]

        # Make C a homogeneous representation of A and B
        hit1H = np.ones((len(fileUsable), 4))
        hit1H[:, 0:3] = hit1
        hit2H = np.ones((len(fileUsable), 4))
        hit2H[:, 0:3] = hit2

        # make numpy matrix from JSON info
        toSen1 = np.array(self.__matrices[overlapID]['matrix1']).reshape(4, 4)

        # invert matrices
        toSen1Inv = np.linalg.inv(toSen1)

        # transform hit1 and hit2 to frame of reference of hit1
        hit1T = np.matmul(toSen1Inv, hit1H.T).T
        hit2T = np.matmul(toSen1Inv, hit2H.T).T

        # make difference hit array
        dHit = hit2T[:, :3] - hit1T[:, :3]

        #sigX = np.std(dHit[:,0])*1e4
        #sigY = np.std(dHit[:,1])*1e4
        #muX = np.average(dHit[:,0])*1e4
        #muY = np.average(dHit[:,1])*1e4

        #textStr = 'µx={:1.2f}µm, σx={:1.2f}µm\nµy={:1.2f}µm, σy={:1.2f}µm'.format(muX, sigX, muY, sigY)

        axes.hist2d(hit1T[:, 0], dHit[:, 0]*dHit[:, 0]*1e4 + dHit[:, 1]*dHit[:, 1]
                    * 1e4, bins=250, norm=LogNorm())    # , range=[[-0.12, 0.12], [-0.12, 0.12]]
        #xmin, xmax = axes.get_xlim()
        #axes.set_xticks(np.round(np.linspace(xmin, xmax, 3), 0))
        #ymin, ymax = axes.get_ylim()
        #axes.set_yticks(np.round(np.linspace(ymin, ymax, 5), 0))

        #plt.locator_params(axis='y', nbins=5)
        #plt.locator_params(axis='x', nbins=3)

        # plt.show()

        #axes.text(0.05, 0.95, textStr, transform=axes.transAxes, fontsize=12, verticalalignment='top')

        # this is currently wrong, change this!
        axes.set_title('mis: dx: {:1.2f}µm, dy: {:1.2f}µm'.format(
            toSen1[0][3], toSen1[1][3]))
        axes.set_xlabel('x1 [cm]')
        axes.set_ylabel('dy [µm]')

    def plotAllhitsonCirlce(self):

        # get all overlap IDs
        # not neccessary, is in matrices

        #path = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-aligned/'
        #path = '/mnt/himster2/lmdData/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-1500_uncut_no_data_misalignment/Pairs/'
        path = '/mnt/himster2/lmdData/plab_15.0GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-1500_uncut_no_data_misalignment/Pairs/'

        matPandaToLMDdoubles = [0.999199, 0.000000, 0.040010, 25.378128,
                                0.000000, 1.000000, 0.000000, 0.000000,
                                -0.040010, 0.000000, 0.999199, 1109.130000,
                                0.0, 0.0, 0.0, 1.0
                                ]
        matPandaToLMD = np.array(matPandaToLMDdoubles).reshape(4, 4)
        matPandaToLMD = np.linalg.inv(matPandaToLMD)

        hitsAllOne = np.empty((0, 4))
        dHitsAllOne = np.empty((0, 4))

        for ID in self.__matrices:
            print(ID)

            # if ri.getHalf(int(ID)) != 0:
            #    continue
            if ri.getPlane(int(ID)) != 0:
                continue
            # if ri.getModule(int(ID)) != 2:
            #    continue
                # pass

            filename = path + 'binaryPairFiles/pairs-' + ID + '-cm.bin'
            # read binary Pairs
            fileUsable = ri.readBinaryPairFile(filename)

            # apply dynmaic cut
            fileUsable = finder.dynamicCut(fileUsable, 3)

            # slice to separate vectors
            hit1 = fileUsable[:, :3]
            hit2 = fileUsable[:, 3:6]

            # Make C a homogeneous representation of A and B
            hit1H = np.ones((len(fileUsable), 4))
            hit1H[:, 0:3] = hit1
            hit2H = np.ones((len(fileUsable), 4))
            hit2H[:, 0:3] = hit2

            # transform hit1 and hit2 to frame of reference of hit1
            hit1T = np.matmul(matPandaToLMD, hit1H.T).T
            hit2T = np.matmul(matPandaToLMD, hit2H.T).T
            # make numpy matrix from JSON info
            dHit = hit2T - hit1T

            hitsAllOne = np.concatenate((hitsAllOne, hit1T), axis=0)
            dHitsAllOne = np.concatenate((dHitsAllOne, dHit))

            # if int(ID) > 10:
        fig, axes = plt.subplots()
        #axes.hist2d(hitsAllOne[:,0], hitsAllOne[:,1], bins=1250, norm=LogNorm(), weights = dHitsAllOne[:,1]*dHitsAllOne[:,1]+dHitsAllOne[:,0]*dHitsAllOne[:,0])

        #fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        # plt.show()
        #hist = axes.hist2d(hitsAllOne[:,0], hitsAllOne[:,1], bins=500, weights = dHitsAllOne[:,1]*1e4, cmap=plt.get_cmap('viridis'))
        hist = axes.hist2d(hitsAllOne[:, 0], hitsAllOne[:, 1], bins=500, norm=LogNorm(
        ), cmap=plt.get_cmap('viridis'))
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.colorbar(hist[3])
        plt.show()

        return
