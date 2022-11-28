#!/usr/bin/env python3

import numpy as np
import icp

def test(filename):
    # read file
    f = open(filename, "r")
    fileRaw = np.fromfile(f, dtype=np.double)

    # copy without header
    fileUsable =  fileRaw[6:]
    N = int(len(fileUsable)/7)

    # reshape to array with one pair each line
    fileUsable = fileUsable.reshape(N,7)

    # sort by distance and cut 10% from start and end (discard outliers)
    cut = int(N*0.05)
    fileUsable = fileUsable[fileUsable[:,6].argsort()]
    fileUsable = fileUsable[cut:-cut]
    N = N - 2*cut
    
    # slice to separate vectors
    A = fileUsable[:, :3]
    B = fileUsable[:, 3:6]

    #print('vector A:\n', A)
    #print('vector B:\n', B)

    # create matrix panda->sensor0
    toSen0 = np.array([ [0.999199, 0.0, 0.040010, 29.397911],
                        [0.0, 1.000000, 0.000000, 1.0],
                        [-0.040010, 0.0, 0.999199, 1097.657930],
                        [0.0,       0.0,    0.0,       1.0]])

    # create matrix panda->sensor10
    toSen0 = np.array([ [0.808369, -0.587315, 0.040010, 27.971866],
                        [0.587785, 0.809017, 0.000000,  3.454051],
                        [-0.032368, 0.023517, 0.999199, 1097.604497],
                        [0.0,       0.0,    0.0,       1.0]])

    # create matrix panda->sensor5
    toSen5 = np.array([ [0.808369,    0.587315,   -0.040010, 29.127490],
                        [ 0.587785,  -0.809017,   -0.000000, 1.836017],
                        [-0.032368,   -0.023517,   -0.999199, 1097.082843],
                        [0.0,       0.0,    0.0,       1.0]])

    # and inverse
    toSen0Inv = np.linalg.inv(toSen0)
    toSen5Inv = np.linalg.inv(toSen5)

    # Make C a homogeneous representation of A and B
    C = np.ones((N, 4))
    C[:,0:3] = A

    D = np.ones((N, 4))
    D[:,0:3] = B

    # Transform C and D
    C = np.matmul(toSen0Inv, C.T).T
    D = np.matmul(toSen0Inv, D.T).T

    #print('vec C:\n', C)
    #print('vec D:\n', D)

    # make 2D versions for ICP
    A = C[:, :3]
    B = D[:, :3]

    # find ideal transformation
    T, R1, t1 = icp.best_fit_transform(B, A)

    print('\nfor', filename, ':')
    print('rotation:\n', R1)
    print('translation:\n', t1)

def histPairDistances(path):
    test('/home/arbeit/RedPro3TB/simulationData/himster2misaligned-move-data/Pairs/binaryPairFiles/pairs-0-cm.bin')

def run():
    #path10 = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-misalign-10u/binaryPairFiles/'
    #path100 = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-misalign-100u/binaryPairFiles/'
    #path200 = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-misalign-200u/binaryPairFiles/'
    pass
    #histPairDistances(path10)

if __name__ == "__main__":
    print("Running...")
    histPairDistances('')
    print("All done!")
