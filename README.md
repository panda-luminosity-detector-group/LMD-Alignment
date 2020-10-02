# LMD-python-scripts

This is my collection of useful python scripts I wrote for the development of the LMD alignment. Their main purpose is a quick and easy way to run lots of simualtion on the Himster II, but it also contains all the alignment stuff.

# Usage

The align scripts are in `align`. They can be called with command line arguments in interactive fashion, or can be called object-oriented from the `simWrapper` python script. Actually, for now they can *only* be called from the simWrapper, but I will add some basic wrapping scripts.

The main idea is that every set of run parameters (beam momentum, misalingnment of geometry etc) is stored in a `LMDrunConfig` object, and the simWrapper can read these objects (for example from a json file, see the folder `runConfigs`) and execute every needed step to create monte carlo data, find pairs for sensor alignment, determine box rotation, cumpute alignment matrices, apply them to a new simulation and determine the luminosity.
 
# Requirements

These scripts work only with python3. The requirements can be installed with:

```
pip3 install -r requirements.txt
```

# Files in `input/`

The most important files are `detectorMatricesIdeal.json` and `detectorOverlapsIdeal.json`. The former contains a mapping of all geometry paths to their ideal position matrices. The latter contains a mapping of `(ID1, ID2, path1, path2, matrix1, matrix2, module path) -> overlapID`. They can be generated with PandaROOT (TODO: include details). **Without them, this alignment framework can not work.**

## Generating `detectorMatricesIdeal.json`

The macro to do that is `Pandaroot/macro/detectors/lmd/geo/saveMatricesFromGeomanager.C`, so just run:

```
root -l -q saveMatricesFromGeomanager.C
```

You can optionally specify the output file name and apply misalignment matrices to the working geometry before saving. This way, you can create a set of detector matrices with misalignment just like the alignment framework does, and compare them with your alignment matrices that you obtained through software alignment.

## Generating `detectorOverlapsIdeal.json`

The macro to do that is `Pandaroot/macro/detectors/lmd/geo/saveOverlapsToJSON.C`, so run:

```
root -l -q saveOverlapsToJSON.C
```

# RunConfigs

These are the main configuration files for a run. You can create a default run config with no misalignment using `./runSimulations.py -d`. You can create multiple default run configs (multiple momenta, misalignment factors, types) with the `-D` flag:

```
./runSimulations.py -D
```

You can also create them by hand, which might be useful if you want to add misalignments/factors/beam momenta. They need to have **at least** these fields:

```
{
  "_LMDRunConfig__misalignType": "identity",
  "_LMDRunConfig__misalignFactor": "1.00",
  "_LMDRunConfig__momentum": "1.5"
}
```

All other neccessary field *should* get be generaterd automatically, but only at run-time. After that, you can read them using any simulation type. Note however that some important values will only reside in memory and are not stored to the run config, like paths for (mis)alignment matrices. If you wnt to store them to the run config as well, execute `./runSimulations.py --updateRunConfigs`.

## Special Case: combi misalignment

Combi misalignment incorporates all three previous misalignments, sensors, modules and box rotation. Software alignment of each individual misalignment type works rathe well, but combinations (such as they will occur on the final detector) are more complicated. The alignment process always performs all three and saves all three matrices. But the order is important: if the sensors are misaligned, module alignment will produce incorrect matrices. Sensor alignment must therefore be done separately, and the sensor alignment matrices must already be in use during module alignment. I don't yet know how IP alignment plays into this, that's why I'm trying all combinations.

They are then merged in various combinations:

- alMat-merged.json | All alignment matrices. After the first run with misaligned sensors AND misaligned modules, only the sensor alignment will have worked.
- combi0 | this is only the sensor alignment matrices. a second run must be done to perform module alignment.
- combi1 | sensor + module alignment matrices. 
- combi2 | sensor + box rot alignment matrices. 
- combi3 | all matrices, just like alMat-merged. this is for verbosity, to see if the order (after sensor alignment) matters.

So, the runConfigs for those are not created automatically but must be created with `helperScripts/makeCombiRunConfigs.py` for now.

They must also be called in sequence, the combi0 configs *must* be run before any other. I think SLURM supports job dependencies, but I don't know how yet.

# Multiple Samples for Combined Misalignment

Combi misalignment can be corrected if the individual methods are done in the right order. To get more statistics, each scenario (every misalign factor at every beam momentum) is done ten times with randomized misalignment matrices. This is called MultiSeed. The runConfigs for that are in the "special" sub directory.

# TODO: Add parameters to runConfig

- Add tracks/event to runConfig and simulation, should work with 1 - 10!
- add dynamic cut value to runConfig!
- add separate runConfigs for multiple dynamic cut values! 