#!/usr/bin/env python3

import uproot
import numpy as np
from pathlib import Path
import subprocess


def getTrkNo(filename):
    tracks = readTrackQA(filename)
    return count(tracks)


# removes all tracks with TrkRecStatus != 0
def cleanArray(arrayDict):

    recStatus = arrayDict[b'LMDTrackQ.fTrkRecStatus'].flatten()
    recX = arrayDict[b'LMDTrackQ.fXrec'].flatten()
    recY = arrayDict[b'LMDTrackQ.fYrec'].flatten()
    recZ = arrayDict[b'LMDTrackQ.fZrec'].flatten()

    retArray = np.array([recStatus, recX, recY, recZ]).T
    recStatusMask = (recStatus == 0)

    return retArray[recStatusMask]


def count(cleanedArray):
    return cleanedArray.shape[0]


def readTrackQA(filename):
    resArray = np.zeros((4)).T
    for array in uproot.iterate(filename, 'pndsim', [b'LMDTrackQ.fTrkRecStatus', b'LMDTrackQ.fXrec', b'LMDTrackQ.fYrec', b'LMDTrackQ.fZrec']):
        resArray = np.vstack((resArray, cleanArray(array)))
    return resArray


factors = ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']
momenta = ['1.5', '4.06', '8.9', '11.91', '15.0']

copy = False
singleCombi = False

print(f'Copying some shit')

shitfile = ''

for fac in factors:
    for mom in momenta:
        # copy file
        trkFile = 'Lumi_TrksQA_200000.root'
        # remotePath = Path(f'himster:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/backup_beamTiltEnabled/plab_{mom}GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-combi-{fac}/100000/1-100_xy_m_cut_real/no_alignment_correction')

        if singleCombi:
            #! this path is for the single combi simulations
            remotePath = Path(
                f'himster:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_{mom}GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-combi-{fac}/100000/1-100_xy_m_cut_real/aligned-alMat-combiSenMod-{fac}'
            )

            #! this path is for the single combi simulations
            localPath = Path(f'temp/p{mom}/f{fac}')

            localPath.mkdir(exist_ok=True, parents=True)

            if copy:
                subprocess.run(['rsync', remotePath / Path(trkFile), localPath / Path(trkFile)])

        else:
            for seedID in range(1, 11):
                #! this path is for the combiSeed shit
                remotePath = Path(
                    f'/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_{mom}GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-combiSeed{seedID}-{fac}/200000/1-100_xy_m_cut_real/aligned-alMat-combiSenMod-seed{seedID}-{fac}'
                )

                #! this path is for the combiSeed shit
                localPath = Path(f'/home/roklasen/temp/combiStuff/temp/p{mom}/f{fac}-seed{seedID}')

                # print to some file or some shit
                shitfile += f'mkdir -p {localPath}\n'
                shitfile += f'cp {remotePath}/{trkFile} {localPath}\n'

with open('shitlist.sh', 'w') as f:
    f.write(shitfile)

print(f'Copying some more shit for baseline')

# establish baseline
for mom in momenta:
    # copy file
    trkFile = 'Lumi_TrksQA_100000.root'
    remotePath = Path(
        f'himster:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/backup_beamTiltEnabled/plab_{mom}GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-100_xy_m_cut_real/no_alignment_correction'
    )
    localPath = Path(f'temp/p{mom}/no')

    localPath.mkdir(exist_ok=True, parents=True)

    if copy:
        subprocess.run(['rsync', remotePath / Path(trkFile), localPath / Path(trkFile)])

resArray = []

print(f'Calculating some shit for more shit')
for fac in factors:
    for mom in momenta:
        trkFile = 'Lumi_TrksQA_200000.root'
        trkFile1 = 'Lumi_TrksQA_100000.root'

        if singleCombi:
            localPath = Path(f'temp/p{mom}/f{fac}')
            baseLineFile = Path(f'temp/p{mom}/no/{trkFile1}')
            baseline = getTrkNo(str(baseLineFile))

            try:
                recTracks = getTrkNo(str(localPath / Path(trkFile)))
                # sometimes the reco tracks file is broken
                if recTracks < 1000:
                    continue
                ratio = recTracks / baseline
                #print(f'good track ratio: {ratio}')
                resArray.append([mom, fac, ratio])
            except:
                pass

        else:
            #
            for seedID in range(1, 11):
                localPath = Path(f'temp/p{mom}/f{fac}-seed{seedID}')
                baseLineFile = Path(f'temp/p{mom}/no/{trkFile1}')
                baseline = getTrkNo(str(baseLineFile))

                try:
                    recTracks = getTrkNo(str(localPath / Path(trkFile)))
                    # sometimes the reco tracks file is broken
                    if recTracks < 1000:
                        continue
                    ratio = recTracks / baseline
                    #print(f'good track ratio: {ratio}')
                    resArray.append([mom, fac, ratio, seedID])
                except:
                    pass

resArray = np.array(resArray)
print(f'I will save these values:\n{resArray}')
if singleCombi:
    np.save('input/effValues.npy', resArray)
else:
    np.save('input/effValuesNonAligned.npy', resArray)
    # np.save('input/effValuesAligned.npy', resArray)