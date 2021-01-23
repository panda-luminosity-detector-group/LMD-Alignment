#!/usr/bin/env python3

from pathlib import Path
from alignment.alignerModules import alignerModules

trackFile = Path('input/trackResiduals/processedTracks-1.5-GeV-aligned.json')
# trackFile = Path('input/trackResiduals/processedTracks-1.5-GeV-aligned-mini.json')

alignerMod = alignerModules()
alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
alignerMod.readTracks(trackFile)
alignerMod.alignModules()




