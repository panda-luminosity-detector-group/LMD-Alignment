# TODO: deprecate, use vectorized version in trasnformRecos
    def transformRecoHit(self, point, matrix):
        # vector must be row-major 3 vector
        assert len(point) == 3

        # homogenize
        vecH = np.ones(4)
        vecH[:3] = point

        # make 2D array, reshape and transpose
        vecH = vecH.reshape((1,4)).T

        # perform actual transform
        vecH = matrix @ vecH

        # de-homogenize
        vecNew = vecH[:3] / vecH[3]
        
        # and re-transpose
        vecNew = vecNew.T.reshape(3)

        return vecNew

    def getTracksOnModule(self, allTracks, modulePath):

        filteredTracks = []

        # TODO: express the outer loop as list comprehension as well, for speedup
        for track in allTracks:
            # filter relevant recos
            # track['recoHits'] = [x for x in track['recoHits'] if ( self.getPathModuleFromSensorID(x['sensorID']) == modulePath) ]
            newtrack = copy.deepcopy(track)
            goodRecos = [x for x in track['recoHits'] if ( self.reader.getPathModuleFromSensorID(x['sensorID']) == modulePath) ]
            
            if len(goodRecos) == 1:
                newtrack['recoPos'] = goodRecos[0]['pos']
                # this info is not needed anymore
                newtrack.pop('recoHits', None)
                filteredTracks.append(newtrack)
        
        # return just the newTracks list of dicts, the mouleAligner will take it from here
        return filteredTracks

    # oen way function, the results go to track fitter and are then discarded
    def getAllRecosFromAllTracks(self, allTracks):
        nTrks = len(allTracks)

        # this array has nTrks entries, each entry has 4 reco hits, each reco hit has 3 values
        recoPosArr = np.zeros((nTrks, 4, 3))

        for i in range(nTrks):
            nRecos = len(allTracks[i]['recoHits'])
            if nRecos != 4:
                print('listen. you fucked up.')
                continue

            for j in range(nRecos):
                recoPosArr[i, j] = allTracks[i]['recoHits'][j]['pos']
        
        return recoPosArr

    #* this function modifies the resident data! be careful!
    # allTracks is all data
    # matrices is a dict modulePath->np.array() 
    def transformRecos(self, allTracks, matrices, inverse=False):

        # TODO: this can be vectorized by:
        # first writing all reco points to 4 arrays
        # then transforming the arrays vectorized
        # then reassigning the new reco values

        for track in allTracks:

            # loop over reco hits
            for reco in track['recoHits']:

                # for every reco hit, find path from sensorID
                thisPath = self.reader.getPathModuleFromSensorID(reco['sensorID'])

                # transform reco hit using matrix from matrices
                if inverse:
                    reco['pos'] = self.transformRecoHit( reco['pos'], np.linalg.inv(matrices[thisPath]) )
                else:
                    reco['pos'] = self.transformRecoHit( reco['pos'], matrices[thisPath] )

        return allTracks

    #* this function modifies the resident data! be careful!
    # allTracks is (reference to) all data
    # matrices is a dict modulePath->np.array() 
    def updateTracks(self, allTracks, newTracks):
        assert len(newTracks) == len(allTracks)
        nTrks = len(newTracks)

        for i in range(nTrks):
            allTracks[i]['trkPos'] = newTracks[i][0]
            allTracks[i]['trkMom'] = newTracks[i][1]
        
        return allTracks

    def getRecosFromAlltracks(self, filteredTracks):
        
        nTrks = len(filteredTracks)
        recoPosArr = np.zeros((nTrks, 3))
        for i in range(nTrks):
            recoPosArr[i] = filteredTracks[i]['recoPos']
        return recoPosArr
    
    def baseTransformMatrix(self, matrix, basisMatrix, inverse=False):
        if inverse:
            return basisMatrix @ matrix @ np.linalg.inv(basisMatrix)
        else: 
            return np.linalg.inv(basisMatrix) @ matrix @ basisMatrix
    
    # one way function, the results are only important for matrix finder and are then discarded
    # filteredTracks are the tracks for a single module with a single reco hit!
    def getTrackPosFromTracksAndRecos(self, filteredTracks):
        
        nTrks = len(filteredTracks)
                
        trackPosArr = np.zeros((nTrks, 3))
        trackDirArr = np.zeros((nTrks, 3))
        recoPosArr = np.zeros((nTrks, 3))
        # dVecTest = np.zeros((nTrks, 3))

        for i in range(nTrks):
            trackPosArr[i] = filteredTracks[i]['trkPos']
            trackDirArr[i] = filteredTracks[i]['trkMom']
            recoPosArr[i] = filteredTracks[i]['recoPos']

        # optionally, transform the track to a different frame of reference

        # compare this with the vectorized version
        # for i in range(nTrks):
        #     # normalize fukn direction here, again
        #     trackDirArr[i] /= np.linalg.norm(trackDirArr[i])
        #     dVecTest[i] = ((trackPosArr[i] - recoPosArr[i]) - np.dot((trackPosArr[i] - recoPosArr[i]), trackDirArr[i]) * trackDirArr[i])

        # norm momentum vectors, this is important for the distance formula!
        trackDirArr = trackDirArr / np.linalg.norm(trackDirArr, axis=1)[np.newaxis].T

        # vectorized version, much faster
        tempV1 = (trackPosArr - recoPosArr)
        tempV2 = (tempV1 * trackDirArr ).sum(axis=1)
        dVec = (tempV1 - tempV2[np.newaxis].T * trackDirArr)
        
        # the vector thisReco+dVec now points from the reco hit to the intersection of the track and the sensor
        pIntersection = recoPosArr+dVec
        # pIntersection = recoPosArr+dVecTest
        return pIntersection, recoPosArr

    def applyNoiseToRecos(self, allTracks, sigma, multipleScattering):
        
        mu = 0
        for track in allTracks:
            for reco in track['recoHits']:
                dx = random.gauss(mu, sigma)
                dy = random.gauss(mu, sigma)

                if multipleScattering:
                    # get plane
                    thisRecoPath = self.reader.getPathModuleFromSensorID(reco['sensorID'])
                    _, plane, _, _ = self.reader.getParamsFromModulePath(thisRecoPath)

                    MSsigma = plane * 25.0*1e-4
                    dx += random.gauss(mu, MSsigma)
                    dy += random.gauss(mu, MSsigma)

                # generate matrix
                matrix = np.identity(4)
                matrix[0,3] = dx
                matrix[1,3] = dy

                # transform reco hit using matrix from matrices
                reco['pos'] = self.transformRecoHit( reco['pos'], matrix)

        return allTracks
    
    def prepareSynthDataOLD(self, sector):
        
        synthData = self.reader.readSyntheticDate('testscripts/LMDPoints_processed.json')
        nMCtrks = len(synthData)

        # filter by sector 0
        sector0 = []
        # sector = 0
        print(f'starting to sort {nMCtrks} tracks...')

        # for sector in range(10):

        # select only corridor 0
        for event in synthData:
            tempPoints = []
            for point in event:
                path = self.reader.getPathModuleFromSensorID( point[3] )
                _, _, _, thissector = self.reader.getParamsFromModulePath(path)
                
                if thissector == sector:
                    tempPoints.append(point)
            
            if len(tempPoints) == 4:
                temparray = np.array(tempPoints)
                # print(temparray)
                sector0.append(temparray)

        print(f'done, {len(sector0)} left.')

        # prepare empty allTracks list
        allTracks = []
        for i in range(len(sector0)):
            thisTrack = {}
            thisTrack['recoHits'] = []

            for point in sector0[i]:
                recoPoint = {}
                recoPoint['pos'] = point[:3]
                recoPoint['sensorID'] = int(point[3])
                thisTrack['recoHits'].append(recoPoint)

            allTracks.append(thisTrack)

        print(f'=== allTracks is now {len(allTracks)} entries long.')

        modulePaths = self.reader.getModulePathsInSector(sector)
        misMatPath = '/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-modulesNoRot-1.00.json'

        #! cheat hard here for now:
        with open(misMatPath) as f:
            misalignmatrices = json.load(f)
            
        with open(misMatPath) as f:
            misalignmatricesOriginal = json.load(f)
        
        # make 4x4 matrices
        moduleMatrices = {}
        for path in misalignmatrices:
            moduleMatrices[path] = np.array(self.reader.detectorMatrices[path]).reshape(4,4)
            misalignmatrices[path] = np.array(misalignmatrices[path]).reshape((4,4))
            misalignmatricesOriginal[path] = np.array(misalignmatricesOriginal[path]).reshape((4,4))

        # transform accoring to calculations
        for path in misalignmatrices:
            mis = misalignmatrices[path]
            modMat = moduleMatrices[path]
            mis = modMat @ mis @ np.linalg.inv(modMat)
            misalignmatrices[path] = mis

        #! ====================  apply misalignment
        allTracks = self.transformRecos(allTracks, (misalignmatrices))

        print(f'recos "misaligned". performing first track fit.')

        mat = np.zeros((4,4))
        for path in modulePaths:
            thisMat = misalignmatricesOriginal[path]
            mat = mat + thisMat
        
        print(f'average shift of first four modules:')
        averageShift = mat/4.0
        print(averageShift*1e4)
        
        #! apply 23mu noise and multiple scattering
        # this works only if the points are transformed to LMD local!
        # allTracks = self.applyNoiseToRecos(allTracks, 23.0*1e-4, True)
        use2D = False

        #! define anchor point
        print(f'performing first track fit.')
        anchorPoint = [-18.93251088, 0.0, 2.51678065]
        
        recos = self.getAllRecosFromAllTracks(allTracks)
        corrFitter = CorridorFitter(recos)
        # corrFitter.useAnchorPoint(anchorPoint)
        resultTracks = corrFitter.fitTracksSVD()
        allTracks = self.updateTracks(allTracks, resultTracks)
    
        #* allTracks now look just like real data
        print(f'track fit complete.')
       
        print('\n\n')
        print(f'===================================================================')
        print(f'Inital misalignment:')
        print(f'===================================================================')
        print('\n\n')

        # np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
        np.set_printoptions(precision=6)
        np.set_printoptions(suppress=True)

        for path in modulePaths:
            filteredTracks = self.getTracksOnModule(allTracks, path)
            trackPos, recoPos = self.getTrackPosFromTracksAndRecos(filteredTracks)
            trackPos, recoPos = self.dynamicCut(trackPos, recoPos, 5)

            #? 1: get initial align matrices for 4 modules
            T0 = self.getMatrix(trackPos, recoPos, use2D)

            print('after transform:')
            matrix1 = T0
            toModMat = moduleMatrices[path]

            # transform matrix to module?
            matrix10 = np.linalg.inv(toModMat) @ matrix1 @ (toModMat)
            matrix10  = matrix10 + averageShift
            print(f'transformed normal:\n{matrix10*1e4}')
            print(f'actual:\n{misalignmatricesOriginal[path]*1e4}')
            print(f'\nDIFF:\n{(matrix10-misalignmatricesOriginal[path])*1e4}\n\n')
            print(f' ------------- next -------------')

        #* okay, fantastic, the matrices are identiy matrices. that means at least distance LMDPoint to mc track works 

        print(f'\n\n\n')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'===================================================================')
        print(f'\n\n\n')
        return