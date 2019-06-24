#!/bin/bash
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-identity-1.00.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --alignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-identity-1.00.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-identity-1.00.root --alignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misMatrices/misMat-identity-1.00.root
