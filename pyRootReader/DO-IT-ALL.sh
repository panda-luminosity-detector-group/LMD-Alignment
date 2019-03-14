#!/bin/bash

cd /home/roklasen/LuminosityFit/scripts

./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-10.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-50.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-100.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-150.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-200.root
./doSimulationReconstruction.py 100000 500 1.5 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-250.root

./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-10.root
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-50.root
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-100.root
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-150.root
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-200.root
./doSimulationReconstruction.py 100000 500 4.09 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-250.root

./doSimulationReconstruction.py 100000 500 15 dpm_elastic
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-10.root
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-50.root
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-100.root
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-150.root
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-200.root
./doSimulationReconstruction.py 100000 500 15 dpm_elastic --misalignment_matrices_path /home/roklasen/PandaRoot/macro/detectors/lmd/geo/misalignMatrices-SensorsOnly-250.root





