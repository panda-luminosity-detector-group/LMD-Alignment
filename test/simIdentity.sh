#!/bin/bash

align=""
misalign=""

mismatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/"
almatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/"
matid="misMat-identity-1.00.root"

box025=${matpath}"misMat-box-0.25.root"
box050=${matpath}"misMat-box-0.50.root"
box100=${matpath}"misMat-box-1.00.root"
box200=${matpath}"misMat-box-2.00.root"
box300=${matpath}"misMat-box-3.00.root"
box500=${matpath}"misMat-box-5.00.root"
box1000=${matpath}"misMat-box-10.00.root"

combi050=${matpath}"misMat-combi-0.50.root"
combi100=${matpath}"misMat-combi-1.00.root"
combi200=${matpath}"misMat-combi-2.00.root"

mom="1.5"


run_sims() {
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign}
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --alignment_matrices_path ${align}
    echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign} --alignment_matrices_path ${align}
}

align=${box025}
misalign=${align}

run_sims

align=${box300}
misalign=${align}

run_sims

align=${box500}
misalign=${align}

run_sims

align=${box1000}
misalign=${align}

run_sims

mom="15.0"

align=${box025}
misalign=${align}

run_sims

align=${box300}
misalign=${align}

run_sims

align=${box500}
misalign=${align}

run_sims

align=${box1000}
misalign=${align}

run_sims

# align=${combi100}
# misalign=${align}

# run_sims

# align=${combi200}
# misalign=${align}

# run_sims