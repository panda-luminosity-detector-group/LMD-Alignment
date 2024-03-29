# TODO

We need scripts / jupyter notebooks:

- [ ] generate ideal detector matrices from current geometry
- [ ] generate a run config file (for LumiFit) that actually uses the misliagnment matrices
- [ ] scripts to do the actual alignment

# Docs

Document:

- [ ] how this software should be used (e.g. how to run the scripts, venv and all)
- [ ] what the other repo (Lumi Fit) is for and must do (here, we don't generate any data at all, only extract params and make alignment)
- [ ] how an alignment campaign is run (run LumiFit for data, then scripts here)


# Start Here

## Generatre ideal detector matrices

## Generate expConfig File that can be used by the Lumifit

The Lumifit Software takes care of almost all the simulation stuff. Therefore the only config generator is there, and I won't write another one here.

Instead, you can use the existing config generator:

```bash
 ./create_sim_reco_pars.py -mp ../../LMD-Alignment/matrices/100u-case-1/misMat-sensors.json
```

Or whatever misalignment matrix you want to use.

## runSimulationReconstruction

## Perform Alignment

## Delete now obsolete files

```
rm -rf resacc/ recoIP.json lumi-values.json data/reco_* experiment.config 
```

## Run Lumifit

```bash
./determineLuminosity.py
```

# Details

# Sensor Alignment

# Module Alignment

## Recos from Root Files

```
[[[   4.        21.5248     2.02203 1097.36   ]
  [   4.        22.2404     2.06879 1117.35   ]
  [   4.        22.6504     2.0961  1127.34   ]
  [   4.        23.0254     2.11596 1137.33   ]]

  ...

  [[   0.        29.6018     2.26185 1097.06   ]
  [   0.        30.4964     2.26132 1117.04   ]
  [   0.        30.9581     2.31261 1127.03   ]
  [   0.        31.3922     2.33388 1137.02   ]]]
```

## Sector Recos

The structure is a 3D numpy array with shape (nEvents, 6, 4)

for each event, we have 6 4-vecors:

- trackPoint
- trackDirection
- recoPoint 1
- recoPoint 2
- recoPoint 3
- recoPoint 4


so for example:



# Box Alignment