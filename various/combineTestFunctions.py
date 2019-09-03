"""

This is a test bed for ways I combined matrices in the matrix combiner.
Most of the functions worked and were at one time useful to me,
but they no longer belong in the MatrixCombiner.

So I'll put them here as long as I need a reminder how certain things worked,
but in the future, these can be deleted.

"""

if False:
    # * This is still correct!
    msg = "Example: get perfect mat1to2 and apply misalignment onto it, compare with actual mat1to2"
    with open('input/detectorMatrices-sensors-1.00.json') as f:
        totalMatrices = json.load(f)

    p1 = self.modulePath + '/sensor_0'
    p2 = self.modulePath + '/sensor_5'

    m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
    m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
    m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
    m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
    m1misInPnd = m1 @ m1mis @ inv(m1)
    m2misInPnd = m2 @ m2mis @ inv(m2)

    matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

    # get actual matrix from GeoManager
    m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)
    m1misTo2misInMod = self.baseTransform(m1misTo2WithAddedMis, inv(matToModule))

    # method 1: use the perfect matrix, apply misalignments (which we don't actually know)
    # and compare with unknown actual misaligned mat
    mat1to2Perfect = self.getIdealMatrixP1ToP2(p1, p2)
    mat1to2Compute = m2misInPnd @ mat1to2Perfect @ inv(m1misInPnd)

    # transform to module, for ease of reading
    mat1to2ComputeInMod = self.baseTransform(mat1to2Compute, inv(matToModule))
    mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(matToModule))

    print(msg)
    print('Method 1:')
    self.dMat(m1misTo2misInMod, mat1to2ComputeInMod)

if False:
    # * This is still correct!
    msg = "Example: get ICP matrix and ideal matrix, compare with actual matrix. We can do this onlt if the actual matrix is transformed to MISALIGNED sensor A. After that, we can transform both to the module system."
    with open('input/detectorMatrices-sensors-1.00.json') as f:
        totalMatrices = json.load(f)

    p1 = self.modulePath + '/sensor_1'
    p2 = self.modulePath + '/sensor_3'

    m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
    m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
    m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
    m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
    m1misInPnd = m1 @ m1mis @ inv(m1)
    m2misInPnd = m2 @ m2mis @ inv(m2)

    matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

    # get actual matrix from GeoManager
    m1misTo2Actual = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

    # what does this matrix look like in the system of MISALIGNED sensor A?
    m1misTo2ActualInAstar = self.baseTransform(m1misTo2Actual, inv(m1misInPnd))

    # and now, what does it look like in the module?
    m1misTo2ActualInMod = self.baseTransform(m1misTo2ActualInAstar, inv(matToModule))

    # method 2: use ICP matrix and ideal m1, m2 to get misaligned mat
    Micp = self.getOverlapMisalignLikeICP(p1, p2)
    Mideal = self.getIdealMatrixP1ToP2(p1, p2)

    mat1to2fromICP = inv(Micp) @ Mideal
    mat1to2fromICPInModule = self.baseTransform(mat1to2fromICP, inv(matToModule))

    print(msg)
    print('Method 2:')
    self.dMat(m1misTo2ActualInMod, mat1to2fromICPInModule)

if False:
    # * This is still correct!
    """
    Example: we are sitting in MISALIGNED sensor 1 and want to know the matrix to misaligned sensor2.
    From that matrix, we remove the misalignment of sensor2 (because that is included in sensor2),
    and add the misalignment to sensor1 (because we're sitting in a misaligned spot).
    now compare with the ideal matrix1to2 (in ALIGNED sensor1)
    """

    with open('input/detectorMatrices-sensors-1.00.json') as f:
        totalMatrices = json.load(f)

    m1 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
    m2 = np.array(self.idealDetectorMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
    m1mis = np.array(misalignMatrices[self.modulePath + '/sensor_1']).reshape(4, 4)
    m2mis = np.array(misalignMatrices[self.modulePath + '/sensor_2']).reshape(4, 4)
    m1misInPnd = m1 @ m1mis @ inv(m1)
    m2misInPnd = m2 @ m2mis @ inv(m2)

    # matrix to MISALIGNED sensor1
    matPndTo1mis = m1misInPnd @ m1

    # get actual matrix from GeoManager
    m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2', totalMatrices)

    # remove misalign2 from and add misalign1 to this matrix
    m1misTo2NoMisalign = (m1misInPnd) @ inv(m2misInPnd) @ m1misTo2WithAddedMis  # this line is very useful, because we get "inv((m1misInPnd) @ inv(m2misInPnd))" from the ICP!

    # tansform to system of misaligned s1
    m1misTo2misInS1 = self.baseTransform(m1misTo2NoMisalign, inv(matPndTo1mis))

    # compare with perfect matrix
    mat1to2Perfect = self.getIdealMatrixP1ToP2(self.modulePath + '/sensor_1', self.modulePath + '/sensor_2')
    mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(m1))

    self.dMat(m1misTo2misInS1, mat1to2PerfectInMod)

    """
    so, this works and is interesting, because this way, I can find my misalignment to sen2 (if I know it for sen1)
    """

if False:
    # * This is still correct!
    msg = """
    Example: we sit at misaligned sensor 1, and want to know the matrix to misaligned sensor 2.
    We start with the total matrix from mis1 to mis2, substract mis2 and add mis1.
    We have the inverse ICP matrix and apply it to a misaligned total overlap, compare that with the ideal overlap
    """

    with open('input/detectorMatrices-sensors-1.00.json') as f:
        totalMatrices = json.load(f)

    p1 = self.modulePath + '/sensor_0'
    p2 = self.modulePath + '/sensor_5'

    m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
    m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
    m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
    m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)
    m1misInPnd = m1 @ m1mis @ inv(m1)
    m2misInPnd = m2 @ m2mis @ inv(m2)

    # matrix to MISALIGNED sensor1
    matPndTo1mis = m1misInPnd @ m1

    # get actual matrix from GeoManager
    m1misTo2WithAddedMis = self.getMatrixP1ToP2fromMatrixDict(p1, p2, totalMatrices)

    # remove misalign1 from and add misalign2 to this matrix
    m1misTo2MisRemoved = (m1misInPnd) @ inv(m2misInPnd) @ m1misTo2WithAddedMis

    # tansform to system of misaligned s1
    m1misTo2misInS1 = self.baseTransform(m1misTo2MisRemoved, inv(matPndTo1mis))

    # compare with perfect matrix
    mat1to2Perfect = self.getIdealMatrixP1ToP2(p1, p2)
    mat1to2PerfectInMod = self.baseTransform(mat1to2Perfect, inv(m1))

    print(msg)
    self.dMat(m1misTo2misInS1, mat1to2PerfectInMod)

    """
    so, this works and is interesting, because this way, I can find my misalignment to sen2 (if I know it for sen1)
    """

if False:
    msg = "I used math to get the ICP matrix. It was a work of art. And math."
    """
    # port this to the comparer! this is how you compare the overlap matrix to the simulation matrix
    ! DO NOT DELETE THIS BLOCK until you ported it to the comparer!
    """

    with open('input/detectorMatrices-sensors-1.00.json') as f:
        totalMatrices = json.load(f)

    m0t5misIcp = self.overlapMatrices['0']

    p1 = self.modulePath + '/sensor_0'
    p2 = self.modulePath + '/sensor_5'

    m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)
    m2 = np.array(self.idealDetectorMatrices[p2]).reshape(4, 4)
    m1mis = np.array(misalignMatrices[p1]).reshape(4, 4)
    m2mis = np.array(misalignMatrices[p2]).reshape(4, 4)

    matToModule = np.array(self.idealDetectorMatrices[self.modulePath]).reshape(4, 4)

    m1misInPnd = self.baseTransform(m1mis, m1)
    m2misInPnd = self.baseTransform(m2mis, m2)

    m1star = m1misInPnd @ m1
    m2star = m2misInPnd @ m2

    ICPmat = inv(m2misInPnd) @ (m1misInPnd)
    compareICP = self.getOverlapMisalignLikeICP(p1, p2)

    print(msg)
    self.dMat(ICPmat, m0t5misIcp)

if False:
    print('Which way goes the point trafo?')
    p1 = self.modulePath + '/sensor_0'
    m1 = np.array(self.idealDetectorMatrices[p1]).reshape(4, 4)

    point = np.array([0, 0, 0, 1]).reshape(4, 1)     # point in the center of A
    pointInPnd = (m1) @ point

    print(f'point in sensor:{point}')
    print(f'point in pnd:{pointInPnd}')
