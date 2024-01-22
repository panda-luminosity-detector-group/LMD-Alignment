Table of Contents

- [Introduction and TL;DR](#introduction-and-tldr)
- [Installation](#installation)
  - [Bare Metal Installation](#bare-metal-installation)
  - [In a Virtual Environment](#in-a-virtual-environment)
  - [Using the LumiFit Docker/Singularity Container](#using-the-lumifit-dockersingularity-container)
- [Required Config Files](#required-config-files)
  - [Anchor Points](#anchor-points)
  - [assemblyPaths](#assemblypaths)
  - [detectorMaticesIdeal](#detectormaticesideal)
  - [moduleIDtoModulePath](#moduleidtomodulepath)
  - [moduleIDtoSectorID](#moduleidtosectorid)
  - [sectorPahts](#sectorpahts)
  - [sensorIDtoSectorID](#sensoridtosectorid)
- [Deprecated Stuff](#deprecated-stuff)
- [Matrices](#matrices)
- [Jupyter Notebooks](#jupyter-notebooks)
  - [alignCampaing{Box,Modules,Sensors}](#aligncampaingboxmodulessensors)
  - [calculateAnchorPoints](#calculateanchorpoints)
  - [checkExternalMatrices](#checkexternalmatrices)
  - [compareAlignmentMatricesWithMisalignmentMatrices](#comparealignmentmatriceswithmisalignmentmatrices)
  - [Interpreting the residuals matrix](#interpreting-the-residuals-matrix)
  - [generateMisalignmentMatrices](#generatemisalignmentmatrices)
  - [genSenToSectorLut](#gensentosectorlut)
- [Alignment Modules](#alignment-modules)
  - [Data Readers](#data-readers)
  - [Sensor Alignment](#sensor-alignment)
    - [Sensor External Matrices](#sensor-external-matrices)
  - [Module Alignment](#module-alignment)
    - [Module External Matrices](#module-external-matrices)
  - [Box Rotation Alignment](#box-rotation-alignment)

# Introduction and TL;DR

This repo contains all that you need to perform software alignment of the Luminosity Detector. It is written in pure python, although for legacy reasons there are also some ROOT macros that are used to generate the input files for the module alignment. Those must be run with PanadaROOT's `root -l -q myMacro.C`.

Once you have the Lumi\_\*.root files, you can run the alignment with the following command:

```bash
./runAlignment.py -p <pathToData> -t <type> [options]
```

for example, a module alignment campaign could look like this:

```bash
./runAlignment.py \
-t modules \
-p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-jPzRgtxO/data/reco_uncut/no_alignment_correction" \
--externalMatrices "matrices/100u-case-1/externalMatrices-modules.json" \
--anchorPoints "config/anchorPoints/anchorPoints-15.00-aligned.json"
```

# Installation

The software requires python 3.7 or higher and only three packages:

- awkward (part of the uproot package)
- numpy
- uproot

## Bare Metal Installation

To install these packages, you can use pip:

```bash
pip install -r requirements.txt
```

## In a Virtual Environment

```bash
python3 -m venv alignment-venv
source alignment-venv/bin/activate
pip install -r requirements.txt
```

## Using the LumiFit Docker/Singularity Container

The container image needed to run the [LumiFit Software](https://github.com/panda-luminosity-detector-group/LuminosityFit) already contains the needed packages, so the alignment can also be run in the same container.

```bash
docker run -u $(id -u):$(id -g) \
--net=host -it --rm \
--mount type=bind,source=/path/to/LMD-Alignment,target=/mnt/work/LMD-Alignment \ # this repo
--mount type=bind,source=/path/to/LumiData,target=/mnt/work/LumiData \ # the path where the Lumi_*.root files are
rklasen/lmdfit:miniNov22p1
```

This is a reduced version of the call for LumiFit docker call [described here](https://github.com/panda-luminosity-detector-group/LuminosityFit#new-version-with-docker) (omitting stuff for that's needed for ROOT and ROOTs TBrowser).

Inside, you can then run the alignment as described below.

# Required Config Files

All config files are located in the `config` folder and are pre-generated for the Luminosity Defector as it was in 2023. They provide mapping between geometry paths used by ROOT and sensorID, moduleID and sectorID numbers.

If the geometry changes, these files need to be updated. It is advisable to keep the current ones as blueprints.

## Anchor Points

The anchor points are an extrapolated virtual interaction point if the dipole magnet wasn't there. For details, please find the documentation in [my thesis](https://hss-opus.ub.ruhr-uni-bochum.de/opus4/frontdoor/index/index/year/2022/docId/8586) in chapter 8.6. If the distance of the LMD to the interaction point changes, these anchor points must be updated.

For that you need recoHits files from an _ideal_ geometry (i.e. no misalignments) and the `calculateAnchorPoints.ipynb` notebook. The recoHits files can be generated with the `readRootTrackRecos.C` macro in the `src/ROOT` folder. I'm not entirely sure if this still works, but it should serve as a good starting point.

Alternatively, the `lumiRecoReader.py` in `src/alignment/readers` should work as well.

## assemblyPaths

A dictionary that shows which geometry paths belong to which assembly:

````json

```json
"box": [
    "/cave_1/lmd_root_0"
  ],
  "modules": [
    "/cave_1/lmd_root_0/half_0/plane_0/module_0",
    "/cave_1/lmd_root_0/half_0/plane_0/module_1",
    "/cave_1/lmd_root_0/half_0/plane_0/module_2",
...
````

## detectorMaticesIdeal

The ideal geometry matrices for LMD _without_ misalignment. For details how geometry matrices work, please find chapter 6.2 in [my thesis](https://hss-opus.ub.ruhr-uni-bochum.de/opus4/frontdoor/index/index/year/2022/docId/8586). These matrices are in the `TGeoManager` in PandaROOT once all geometries are added to an `FairRunSim` or `FairRunAna`. They can be written to a json file with the ROOT macro `saveMatricesFromGeomanager.C` in `src/ROOT`. I've written it ages ago and God only knows if it still works. Again, when in doubt, it should provide a good starting point.

**Important**: The matrices are **absolute** matrices from the global coordinate system to the component, i.e. the matrices are not relative to the parent of a component. That means to transform from PandaGlobal to sensor 4 on module 4 on plane 2 on the top half (`"/cave_1/lmd_root_0/half_0/plane_2/module_4/sensor_4"`), you don't need the matrices for the parent components, but only the one matrix for the sensor itself:

```json
"/cave_1/lmd_root_0/half_0/plane_2/module_4/sensor_4": [
    0.9991992951284931,
    -4.899763657267719e-18,
    -0.04000960653046352,
    21.372093283940952,
    0.0,
    -1.0,
    1.2246467991473532e-16,
    1.1615000000000006,
    -0.04000960653046352,
    -1.2236662184894007e-16,
    -0.9991992951284931,
    1127.4174227151334,
    0.0,
    0.0,
    0.0,
    1.0
  ],
```

## moduleIDtoModulePath

Mapping between moduleID and geometry path:

```json
"0": "/cave_1/lmd_root_0/half_0/plane_0/module_0",
"1": "/cave_1/lmd_root_0/half_0/plane_0/module_1",
...
```

## moduleIDtoSectorID

Mapping between moduleID and which sectorID this module is in:

```json
0": 0,
"1": 1,
"10": 0,
"11": 1,
"12": 2,
"13": 3,
"14": 4,
...
```

There are (or at least there should be) 4 modules in each sector.

## sectorPahts

Mapping between sectorID and _all_ geometry paths of the modules in this sector (so closely related to `moduleIDtoModulePath`):

```json
"0": [
"/cave_1/lmd_root_0/half_0/plane_0/module_0",
"/cave_1/lmd_root_0/half_0/plane_1/module_0",
"/cave_1/lmd_root_0/half_0/plane_2/module_0",
"/cave_1/lmd_root_0/half_0/plane_3/module_0"
],
"1": [
"/cave_1/lmd_root_0/half_0/plane_0/module_1",
"/cave_1/lmd_root_0/half_0/plane_1/module_1",
"/cave_1/lmd_root_0/half_0/plane_2/module_1",
"/cave_1/lmd_root_0/half_0/plane_3/module_1"
],
...
```

## sensorIDtoSectorID

Mapping between sensorID and which sectorID the corresponding sensor is in:

```json
"0": 0,
"1": 0,
"10": 1,
"100": 2,
"101": 2,
"102": 2,
"103": 2,
"104": 3,
...
```

# Deprecated Stuff

The folder `DEPRECATED` contains the old alignment code that was used for my thesis to run > 500 misalignment case studies. It is not maintained or even working anymore because of significant changes in the LumiFit software. It is only kept for reference.

# Matrices

To get started quickly, I've provided one set of misalignment matrices for the LMD (geometry as of 2023) with 100 microns average shift. To see how the numbers were chosen in these matrices, please find chapters 7.1 and 7.2 in [my thesis](https://hss-opus.ub.ruhr-uni-bochum.de/opus4/frontdoor/index/index/year/2022/docId/8586) for the sensors, and chapters 8.1 and 9.1 for modules and the entire box.

They include external matrices (see [Sensor External Matrices](#sensor-external-matrices) and [Module External Matrices](#module-external-matrices)) and the resultant alignment matrices if the PandaROOT simulation used the misaligned geometry and software alignment was performed at 1.5 GeV and 15 GeV.

# Jupyter Notebooks

In the folder `jupyter` there are several Jupiter notebooks that help you to understand the software alignment, generate a set of misalignment matrices, generate anchor points and - most importantly - to compare the found alignment matrices with the misalignment matrices used in the simulation.

## alignCampaing{Box,Modules,Sensors}

The "manual" version of an alignment campaign. While it is not recommended to use this for the actual alignment (rather use the `runAlignment.py` script for that), these are still useful to understand the alignment process for each case.

## calculateAnchorPoints

See [Anchor Points](#anchor-points).

## checkExternalMatrices

Obsolete, external matrices should be generated together with the misalignment matrices.

## compareAlignmentMatricesWithMisalignmentMatrices

Pretty much what it says on the tin. This notebook compares the alignment matrices found by the software alignment with the misalignment matrices used in the simulation. This is done by calculating the residuals matrix for each aligned component (sensor and module alignment) or the Euler angles (box rotation alignment) and printing. For details about residuals matrices, please check chapter 6.5 or 7.10.1 in ... [you know where](https://hss-opus.ub.ruhr-uni-bochum.de/opus4/frontdoor/index/index/year/2022/docId/8586).

## Interpreting the residuals matrix

The results will look something like this (here for sensor 3 on module 0 on plane 0 on the top half):

```text
--------------------------------------------------------:
Path: /cave_1/lmd_root_0/half_0/plane_0/module_0/sensor_3
Residuals Matrix:

[[ 9999.999701    -2.445756    -0.           0.137858]
 [    2.445756  9999.999701     0.          -5.056183]
 [   -0.           0.       10000.          -0.      ]
 [    0.           0.           0.       10000.      ]]
--------------------------------------------------------:
```

This is the homogeneous $4 \times 4$ residuals matrix (see chapter 5.3). Basically, the most important parameters will be the the entries at $m_{14}$ and $m_{24}$, so $0.137858$ and $-5.056183$. The usual units in ROOT are centimeters, but the resultant difference after alignment will be in the order of *micro*meters, so the entire matrix is scaled by `1e4` (thats $10 ^4$ in lazy). That means, the alignment of this specific sensor was off by $0.137858 \cdot 10^{-4} = 1.37858 \cdot 10^{-3} = 1.37858 \mu m$ in $x$ and $-5.056183 \cdot 10^{-4} = -5.056183 \mu m$ in $y$.

The rotation is encoded in the upper left $3 \times 3$ portion of the matix. Usually, ROOT uses degrees for all rotations, but in this case the matrix comes from the software alignment, which uses radians. So the rotation values are always $sin(\alpha), cos(\beta)$ etc with $\alpha, \beta$ being the rotation angles around the Euler angles. These values are also totally important to see if the alignment found the correct rotation, but chances are that the rotation is correct when the translation is correct.

## generateMisalignmentMatrices

Generates sets of misalignment matrices (see chapters 7.1, 8.1 and 9.1 for example numbers). It's very important to generate _sensible_ misalignment matrices, that means matrices that are rigid transformations. You can't just throw random numbers in each entry $m_{11}$ to $m_{44}$ and expect a sensible result. Instead you have to generate real rotation matrices and real translation matrices and combine them to one total rigid transformation matrix. Because $A \cdot B \neq B \cdot A$ for matrices $A$ and $B$, the _order_ matters. You can of course choose any order of rotations and translations that you like, but you should be consistent.

For example, I've always used *first translation, then rotation* (remember, matrix multiplication order is right to left):

```python
# module matrices follow the same reasoning as sensors, 
# but we need also the 1/4th of every transformation for the avg misalign (external matrix)
def genModuleMatrix(avgShift, avgRot):
    shiftVals = np.random.normal(0, avgShift, 2)
    rotVals = np.random.normal(0, avgRot, 1)
    totalTrans = genTransY(shiftVals[1]) @ genTransX(shiftVals[0])
    totalTransQ = genTransY(shiftVals[1]/4) @ genTransX(shiftVals[0]/4)
    totalRot = genRotZ(rotVals[0])
    totalRotQ = genRotZ(rotVals[0]/4)
    return totalRot @ totalTrans, totalRotQ @ totalTransQ
```

The matrices `totalRotQ` and `totalTransQ` are quarter matrices, see [Module External Matrices](#module-external-matrices) for details.

## genSenToSectorLut

Generates some of the config files in the `config` folder. This is valid only for the current geometry, if the geometry changes, you have to write a new version of this notebook. See it as a blueprint.

# Alignment Modules

ALright, this is the real meat of the alignment (or the real tofu if you're vegetarian). The alignment is split into three parts: box, modules and sensors.

## Data Readers

## Sensor Alignment

### Sensor External Matrices

## Module Alignment

### Module External Matrices

## Box Rotation Alignment
