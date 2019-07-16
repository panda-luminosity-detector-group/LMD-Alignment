#!/bin/bash

align=""
misalign=""

mismatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-"
almatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/alMatrices/alMat-"
matid="misMat-identity-1.00.root"

box025="box-0.25.root"
box050="box-0.50.root"
box100="box-1.00.root"
box200="box-2.00.root"
box300="box-3.00.root"
box500="box-5.00.root"
box1000="box-10.00.root"

combi050="combi-0.50.root"
combi100="combi-1.00.root"
combi200="combi-2.00.root"

mom="1.5"


run_sims() {
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign}
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --alignment_matrices_path ${align}
    echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign} --alignment_matrices_path ${align}
}

align=${almatpath}${box025}
misalign=${mismatpath}${box025}

run_sims

align=${almatpath}${box050}
misalign=${mismatpath}${box050}

run_sims

align=${almatpath}${box100}
misalign=${mismatpath}${box100}

run_sims

align=${almatpath}${box200}
misalign=${mismatpath}${box200}

run_sims

align=${almatpath}${box300}
misalign=${mismatpath}${box300}

run_sims

align=${almatpath}${box500}
misalign=${mismatpath}${box500}

run_sims

align=${almatpath}${box1000}
misalign=${mismatpath}${box1000}

run_sims

mom="15.0"

align=${almatpath}${box025}
misalign=${mismatpath}${box025}

run_sims

align=${almatpath}${box050}
misalign=${mismatpath}${box050}

run_sims

align=${almatpath}${box100}
misalign=${mismatpath}${box100}

run_sims

align=${almatpath}${box200}
misalign=${mismatpath}${box200}

run_sims

align=${almatpath}${box300}
misalign=${mismatpath}${box300}

run_sims

align=${almatpath}${box500}
misalign=${mismatpath}${box500}

run_sims

align=${almatpath}${box1000}
misalign=${mismatpath}${box1000}

run_sims
