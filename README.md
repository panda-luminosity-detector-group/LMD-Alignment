# LMD-python-scripts

This is my collection of useful python scripts I wrote for the development of the LMD alignment. More info will come.

# Usage

The align scripts are in `align`. They can be called with command line arguments in interactive fashion, or can be called object-oriented from the `simWrapper` python script.

# Requirements

These scripts work only with python3. The requirements can be installed with:

```
pip3 install -r requirements.txt
```

# Files in `input/`

The most important files are `detectorMatricesIdeal.json` and `detectorOverlapsIdeal.json`. The former contains a mapping of all geometry paths to their ideal position matrices. The latter contains a mapping of `(ID1, ID2, path1, path2, matrix1, matrix2) -> overlapID`. They can be generated with PandaROOT (TODO: include details). **Without them, this alignment framework can not work.**

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