#!/usr/bin/env python3

import numpy as np
import uproot

trackFile = uproot.open('Lumi_Track_100000.root')
print(f'Your file looks like this:\n')
trackFile[b"pndsim"].show()
print(f'\n\n')
print(f'Access some sub branch:\n { trackFile[b"pndsim"].array("LMDPndTrack.fTrackParamLast.fiver") }\n\n')
print(f'Access the important sub branch:\n { trackFile[b"pndsim"].array("LMDPndTrack.fTrackCand.fHitId") }\n\n')
