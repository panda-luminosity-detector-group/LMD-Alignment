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