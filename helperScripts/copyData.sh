#!/bin/bash

# setup old and new data paths

oldDataPath=backup_beamTiltEnabled
newDataPath=backup_LumiFitOnUNcut

# -------------------------------------
#          copy non-misaligned data
# -------------------------------------

#!/bin/bash
for srcDir in ../${newDataPath}/plab*/dpm*/no*/100000/1-100_x*/no*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# -------------------------------------
#          copy boxRot100 data
# -------------------------------------

#! check if this is the right directory!
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*box100*/100000/1-100_x*/aligned*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

for srcDir in ../${oldDataPath}/plab*/dpm*/geo*box100*/100000/1-100_x*/no_alignment_corr*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# copy alignment matrices
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*box100*/100000/alignmentMatrices; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/alMat*.json ./$target/
done

# -------------------------------------
#          copy modules data
# -------------------------------------

for srcDir in ../${oldDataPath}/plab*/dpm*/geo*modules*/100000/1-100_x*/aligned*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

for srcDir in ../${oldDataPath}/plab*/dpm*/geo*modules*/100000/1-100_x*/no_alignment_corr*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# copy alignment matrices
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*modules*/100000/alignmentMatrices; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/alMat*.json ./$target/
done

# -------------------------------------
#          copy sensors data
# -------------------------------------

# copy aligned lumi fit
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*sensors*/100000/1-100_x*/aligned*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# copy non-aligned lumi fit
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*sensors*/100000/1-100_x*/no_alignment_corr*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# copy alignment matrices
for srcDir in ../${oldDataPath}/plab*/dpm*/geo*sensors*/100000/alignmentMatrices; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/alMat*.json ./$target/
done


# -------------------------------------
#          copy combi data
# -------------------------------------

for srcDir in ../${newDataPath}/plab*/dpm*/geo*combi-*/*0000/1-100_x*/aligned*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

for srcDir in ../${oldDataPath}/plab*/dpm*/geo*combi-*/*0000/1-100_x*/no_alignment_corr*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

# -------------------------------------
#          copy combiMultiSeed data
# -------------------------------------

for srcDir in ../${newDataPath}/plab*/dpm*/geo*combiSeed*/*0000/1-100_x*/aligned*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done

for srcDir in ../${newDataPath}/plab*/dpm*/geo*combiSeed*/*0000/1-100_un*/no_alignment_corr*/bunches*/binning*/merge*; do
  target=$(echo $srcDir | cut -d'/' -f3-)
  mkdir -p $target
  cp $srcDir/lumi-values.json ./$target/lumi-values.json
done
