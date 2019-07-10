#!/usr/bin/env python3

import numpy as np
from numpy import array,mat,sin,cos,dot,eye
from numpy.linalg import norm
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


def getRot(A, B):

    # calc rot axis by cross product
    rotAx = np.cross(A, B)

    # calc rot angle by dot product
    angle = np.dot(A, B.T)

    # rotate around arbitrary axis

    pass


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
    # we can probably omit this
    # if np.linalg.det(R) < 0:
    #     print(f'is reflected!')
    #     Vt[m-1, :] *= -1
    #     R = np.dot(Vt.T, U.T)

    return R

def getBoxRotationMatrix(interactionPointFromLumi, interactionPointFromPanda, lumiPosition):

    # TODO: maybe don't hard code Lumi Position and read it from some config file instead
    # TODO: to account for survey!

    # all values are in centimeters, (x, y, z)
    # lumiPosition = (10.0, 0.0, 1100.0)      # TODO: get actual values!
    # lumiPosition = (0.0, 0.0, 100.0)      # TODO: remove after testing

    LMDpos = np.array(lumiPosition, ndmin=2)
    IPwrong = np.array(interactionPointFromLumi, ndmin=2)
    IPactual = np.array(interactionPointFromPanda, ndmin=2)

    # shift IPs so that LMD is at (0,0,0)
    IPwrong -= LMDpos
    IPactual -= LMDpos

    print(f'IP wrong: {IPwrong}')
    print(f'IP actual: {IPactual}')

    # then ICP that shizzle
    R = icpRot(IPwrong, IPactual)
    # T, R, t = best_fit_transform(IPa, IPb)

    print(f'R is:\n{R}')
    print(f'R inv is:\n{np.linalg.inv(R)}')

    # and see if matrix actually works
    result = R.T@IPwrong.T - IPactual.T
    print(f'R@IPwrong - IPactual =\n{result}')
    print(f'angle: {np.arccos(R[0][0]) * 180 / np.pi}')

def icpRotNew(fromVec, toVec):

    # v = a x b

    # c = a dot b

    # R = I + v_x + v_x^2 * (1/(1+c))

    a = fromVec.T
    b = toVec.T

    n = 2 * np.matmul((a+b),(a+b).T )
    d = np.dot( (a+b).T, (a+b) )

    print(f'n:{n}\nd:{d}')

    R = (n/d) - np.identity(3)

    return R

def fuckMe():

    # np vectors must be 2d
    fromVec = np.array([1.0, 0.0, 0.0])[np.newaxis]
    toVec = np.array([0.0, 1.0, 0.0])[np.newaxis]

    R = icpRotNew(fromVec, toVec)
    print(f'fukken R:\n{R}')

if __name__ == "__main__":
    print('greetings, human.')
    #getBoxRotationMatrix((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 10.0))
    fuckMe()
    print('all done!')
