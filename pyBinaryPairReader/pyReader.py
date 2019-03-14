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
    cut = int(N*0.1)
    fileUsable = fileUsable[fileUsable[:,6].argsort()]
    fileUsable = fileUsable[cut:-cut]
    N = N - 2*cut
    
    # slice to separate vectors
    A = fileUsable[:, :3]
    B = fileUsable[:, 3:6]

    # create matrix panda->lmd
    toLmd = np.array([  [0.999199,  0.0,    0.040010,  25.378128], 
                        [0.0,       1.0,    0.0,       0.0],
                        [-0.040010, 0.0,    0.999199,  1109.130000],
                        [0.0,       0.0,    0.0,       1.0]])

    # create matrix panda->module
    toMod = np.array([  [0.999199,  0.0,    0.040010,  24.902014], 
                        [0.0,       1.0,    0.0,       0.0],
                        [-0.040010, 0.0,    0.999199,  1097.239528],
                        [0.0,       0.0,    0.0,       1.0]])


    # create matrix panda->sensor0
    toMod = np.array([  [0.999199,  0.0,    0.040010,  24.902014], 
                        [0.0,       1.0,    0.0,       0.0],
                        [-0.040010, 0.0,    0.999199,  1097.239528],
                        [0.0,       0.0,    0.0,       1.0]])

    # create matrix panda->sensor1
    toMod = np.array([  [0.999199,  0.0,    0.040010,  24.902014], 
                        [0.0,       1.0,    0.0,       0.0],
                        [-0.040010, 0.0,    0.999199,  1097.239528],
                        [0.0,       0.0,    0.0,       1.0]])

    # and inverse
    toLmdInv = np.linalg.inv(toLmd)
    toModInv = np.linalg.inv(toMod)

    # Make C a homogeneous representation of A and B
    C = np.ones((N, 4))
    C[:,0:3] = A

    D = np.ones((N, 4))
    D[:,0:3] = B

    # Transform C and D
    C = np.matmul(toModInv, C.T).T
    D = np.matmul(toModInv, D.T).T

    # make 2D versions for ICP
    A = C[:, :2]
    B = D[:, :2]

    # find ideal transformation
    T, R1, t1 = icp.best_fit_transform(B, A)

    print('\nfor', filename, ':')
    print('rotation:\n', R1)
    print('translation:\n', t1)

if __name__ == "__main__":
    test('/home/arbeit/RedPro3TB/simulationData/himster2misaligned-move-data/Pairs/binaryPairFiles/pairs-0-cm.bin')

