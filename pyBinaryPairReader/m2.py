#!/usr/bin/env python3

import subprocess
import sys
import os

"""

1.5:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/box_theta_2.0-12.0mrad_recoil_corrected/misalign_

15:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_15.0GeV/box_theta_2.0-12.0mrad_recoil_corrected/misalign_

data:
data/100000/1-1500_uncut_aligned/Pairs
data/100000/1-1500_uncut_misalignMatrices-SensorsOnly-10/Pairs

geometry:
geometry/aligned/100000/1-1500_uncut/Pairs
geometry/misalignMatrices-SensorsOnly-10/100000/1-1500_uncut/Pairs

copy (if not there):
cp ../../mc_data/Lumi_MC_1000000.root ../../mc_data/Lumi_Params_1000000.root .
"""


def findMatrices():

    #all = input('enter "all" to start all matrix finders (1.5 / 15 GeV, all misalignments), [enter] for individual selection:')

    mom = menuSelect(['Select Momentum:', '1.5', '15.0'], 2)
    misalignType = menuSelect(['Shift geometry or data?', 'geometry', 'data'], 1)
    misalign = menuSelect(['Select Misalignment:', 'aligned', 'misalignMatrices-SensorsOnly-10', 'misalignMatrices-SensorsOnly-50',
                           'misalignMatrices-SensorsOnly-100', 'misalignMatrices-SensorsOnly-200'], 1)
    thetaRange = menuSelect(['Select Theta Range:', '2.0-9.0mrad', '2.0-12.0mrad'], 2)

    lmdDataPath = os.environ['LMDFIT_DATA_DIR']
    pathTotal = lmdDataPath + '/plab_' + mom + 'GeV/box_theta_' + thetaRange + '_recoil_corrected/misalign_' + misalignType

    if misalignType == 'data':
        # prepare data
        pathTotal += '/100000/1-1500_uncut_' + misalign + '/Pairs/'

    elif misalignType == 'geometry':
        # prepare geometry
        pathTotal += '/' + misalign + '/100000/1-1500_uncut/Pairs/'

    rootMacroDir = "/home/roklasen/PandaRoot/macro/detectors/lmd/"

    pairPath = pathTotal
    binaryPath = pathTotal+'binaryPairFiles/'
    matrixPath = pathTotal+'LMDmatrices/'

    # copy mc and param files
    subprocess.call(['rsync', pathTotal + '../../mc_data/Lumi_MC_1000000.root', pathTotal + '../../mc_data/Lumi_Params_1000000.root', pathTotal])
    macroArg = rootMacroDir+'runLumiPixel2fMatrixFinder.C("' + pairPath + '","' + binaryPath + '","' + matrixPath + '",true,0)'
    print(macroArg)
    # subprocess.call(['root','-q','-l',macroArg])

    print('all done!')


def menuSelect(options, default=0):
    print(options[0])
    print('[0]: exit')

    # print menu
    for i in range(1, len(options)):
        print('[{}]:'.format(i), options[i], end='')
        if default == i:
            print(' <-default->')
        else:
            print('')

    # get user input
    try:
        choice = input('Selection: ')
        if choice == '' and default != 0:
            return options[default]
        else:
            choice = int(choice)
    except:
        print('invalid entry, somehow!')
        sys.exit()

    # return user selection
    if choice == 0:
        print('exiting!')
        sys.exit()
    if choice < 0 or choice > len(options)-1:
        print('invalid entry!')
        sys.exit()
    return options[choice]


if __name__ == '__main__':
    #options = ['select something','one', 'two', 'tree','four','gandalf']
    #print(menuSelect(options, 5))

    findMatrices()
