#!/bin/bash

align=""
misalign=""

mismatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-"
almatpath="/home/roklasen/PandaRoot/macro/detectors/lmd/geo/alMatrices/alMat-"

matid="misMat-identity-1.00"

box025="box-0.25"
box050="box-0.50"
box100="box-1.00"
box200="box-2.00"
box300="box-3.00"
box500="box-5.00"
box1000="box-10.00"

combi050="combi-0.50"
combi100="combi-1.00"
combi200="combi-2.00"

dotroot=".root"
dotjson=".json"

mom="1.5"


run_sims() {
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign}
    #echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --alignment_matrices_path ${align}
    echo ./doSimulationReconstruction.py 100000 500 ${mom} dpm_elastic --misalignment_matrices_path ${misalign} --alignment_matrices_path ${align} \&
}

align=${almatpath}${box025}${dotjson}
misalign=${mismatpath}${box025}${dotroot}

run_sims

align=${almatpath}${box050}${dotjson}
misalign=${mismatpath}${box050}${dotroot}

run_sims

align=${almatpath}${box100}${dotjson}
misalign=${mismatpath}${box100}${dotroot}

run_sims

align=${almatpath}${box200}${dotjson}
misalign=${mismatpath}${box200}${dotroot}

run_sims

align=${almatpath}${box300}${dotjson}
misalign=${mismatpath}${box300}${dotroot}

run_sims

align=${almatpath}${box500}${dotjson}
misalign=${mismatpath}${box500}${dotroot}

run_sims

align=${almatpath}${box1000}${dotjson}
misalign=${mismatpath}${box1000}${dotroot}

run_sims

mom="15.0"

align=${almatpath}${box025}${dotjson}
misalign=${mismatpath}${box025}${dotroot}

run_sims

align=${almatpath}${box050}${dotjson}
misalign=${mismatpath}${box050}${dotroot}

run_sims

align=${almatpath}${box100}${dotjson}
misalign=${mismatpath}${box100}${dotroot}

run_sims

align=${almatpath}${box200}${dotjson}
misalign=${mismatpath}${box200}${dotroot}

run_sims

align=${almatpath}${box300}${dotjson}
misalign=${mismatpath}${box300}${dotroot}

run_sims

align=${almatpath}${box500}${dotjson}
misalign=${mismatpath}${box500}${dotroot}

run_sims

align=${almatpath}${box1000}${dotjson}
misalign=${mismatpath}${box1000}${dotroot}

run_sims
