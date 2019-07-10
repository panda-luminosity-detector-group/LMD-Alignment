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
"""

#! this is the simplest I could find, seems to work just fine
def getRot(A, B):

    #! see https://math.stackexchange.com/a/476311

    # assert shapes
    assert A.shape == B.shape

    # normalize vectors
    A = A / np.linalg.norm(A)
    B = B / np.linalg.norm(B)

    # calc rot axis by cross product
    v = np.cross(A, B)

    # calc rot angle by dot product
    c = np.dot(A, B.T)  # cosine

    # TODO: maybe there is a function in np for this
    # compute skew symmetric cross product
    v_x = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])

    # compute rotation matrix
    R = np.identity(3) + v_x + np.dot(v_x, v_x) * (1/(1+c)) 

    return R

# TODO: cleanup, fix or remove!
def icpRot(A, B):
    '''
    Gets Rotation from A to B, light version of ICP, without translation
    Might not strictly be correct
    Input:  TODO: update this
      A: Nxm numpy array of corresponding points
      B: Nxm numpy array of corresponding points
    Returns:
      R: mxm rotation matrix
    '''

    assert A.shape == B.shape

    # get number of dimensions
    m = A.shape[1]
    if m != 2 and m != 3:
        print('error! must be either 2D or 3D!')

    # rotation matrix, see ICP
    H = np.dot(A.T, B)
    U, _, Vt = np.linalg.svd(H)
    #R = np.dot(Vt.T, U.T)
    R = Vt.T@U.T

    # this is covered by Wikipedia!
    # https://de.wikipedia.org/wiki/Drehmatrix

    # special reflection case
    if np.linalg.det(R) < 0:
        Vt[m-1, :] *= -1
        R = Vt.T@U.T

    return R

def testTwo():

    # np vectors must be 2d
    fromVec = np.array([1.0, 0.0, 0.0])
    toVec = np.array([1.0, 1.0, 0.0])

    R1 = getRot(fromVec, toVec)

    print(f'blimey R1:\n{R1}')
    print(f'angle: {np.arcsin(R1[0][1]) * 180 / np.pi}')

    # test ICP varian

    fromVec = np.array(fromVec)[np.newaxis]
    toVec = np.array(toVec)[np.newaxis]

    R2 = icpRot(fromVec, toVec)

    print(f'blimey R2:\n{R2}')
    print(f'angle: {np.arcsin(R2[0][1]) * 180 / np.pi}')

    print(f'bloody difference:\n{R2-R1}')


if __name__ == "__main__":
    print('greetings, human.')
    testTwo()
    print('all done!')
