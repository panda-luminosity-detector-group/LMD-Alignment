#!/usr/bin/env python3

import numpy as np
import uproot

"""

Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

read TrksQA.root files
find apparent IP position
compare with actual IP position from PANDA upstream
create matrix that accounts for box rotations
save matrix to json file
rerun Reco and Lumi steps

TODO: mmaybe use scipy and/or quaternion implementations


"""

def getEulerAnglesFromRotationMatrix(R):
    rx = np.arctan2(R[2][1], R[2][2])
    ry = np.arctan2(-R[2][0], np.sqrt(R[2][1]*R[2][1] + R[2][2] * R[2][2] ))
    rz = np.arctan2(R[1][0], R[0][0])
    return (rx, ry, rz)

#! this is the simplest I could find, seems to work just fine
def getRot(A, B):

    #! see https://math.stackexchange.com/a/476311

    # assert shapes
    assert A.shape == B.shape

    # normalize vectors
    A = A / np.linalg.norm(A)
    B = B / np.linalg.norm(B)

    # calc rot axis by cross product
    # v = np.cross(A, B)

    # calc rot angle by dot product
    cosine = np.dot(A, B)  # cosine

    
    # v_x = np.array( [   [0, -v[2], v[1]],
    #                     [v[2], 0, -v[0]], 
    #                     [-v[1], v[0], 0]   ])

    # https://en.wikipedia.org/wiki/Cross_product#Conversion_to_matrix_multiplication
    # a = c x d 

    # make 2D vectors so that transposing works
    cw = A[np.newaxis].T
    dw = B[np.newaxis].T

    # compute skew symmetric cross product matrix
    a_x = np.matmul(dw, cw.T) - np.matmul(cw, dw.T)

    # print('==========================')
    # print(f'a_x:\n{a_x}\nv_x:\n{v_x}')
    # print('==========================')

    # compute rotation matrix
    R = np.identity(3) + a_x + np.dot(a_x, a_x) * (1/(1+cosine)) 

    return R

def testTwo():

    lumiPos = np.array([0.0, 0.0, 10.0])

    # np vectors must be 2d
    ipApparent = np.array([1.0, 0.0, 0.0])
    ipActual = np.array([0.0, 0.0, 0.0])

    ipApparent -= lumiPos
    ipActual -= lumiPos


    #! ======== test calssical variant
    R1 = getRot(ipActual, ipApparent)

    print(f'classic R1:\n{R1}')

    rx1, ry1, rz1 = getEulerAnglesFromRotationMatrix(R1)

    print(f'angle x1: {rx1 * 1e3} mrad')
    print(f'angle y1: {ry1 * 1e3} mrad')
    print(f'angle z1: {rz1 * 1e3} mrad')

    
if __name__ == "__main__":
    print('greetings, human.')
    testTwo()
    print('all done!')
