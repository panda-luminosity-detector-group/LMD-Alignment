/*
compare all matrices in the TGeoManager before and after misalignment and
corrections are applied.
 */

#ifndef __CLING__

#include <PndCave.h>
#include <PndDpmGenerator.h>
#include <PndLmdDetector.h>
#include <PndMagnet.h>
#include "PndMatrixUtil.h"
#include <PndMultiField.h>
#include <PndPipe.h>

#include <FairBoxGenerator.h>
#include <FairPrimaryGenerator.h>
#include <FairRunSim.h>
#include <PndLmdGeometryHelper.h>

#include <TGeant4.h>
#include <TString.h>

#include <iostream>
#include <string>

#endif

using nlohmann::json;
using std::cout;
using std::string;

int saveMatricesFromGeomanager()
{
  cout << "greetings, human.\n";

  //! ==========================================================================

  // output file name
  string outFileName = "config/detectorMatricesIdeal.json";

  // this specifies, at what step the matrices should be applied. when in doubt,
  // set only misalignSimStep = true, the others false!
  bool misalignSimStep = false;
  bool misalignRecoStep = false;
  bool alignRecoStep = false;

  //! ==========================================================================

  const int nEvents = 10;
  const int startEv = 0;
  TString storePath = "tmpOutput";

  const int verboseLevel = 0;
  const int particle = -2212;
  double mom = 15;
  const int trkNum = 1;
  const int seed = 0;
  const double dP = 0;
  const TString lmd_geometry_filename = "Luminosity-Detector.root";

  bool use_point_transform_misalignment = false;

  gSystem->Exec("mkdir " + storePath);

  // load lumi etc
  gDebug = 0;
  mom += dP;
  cout << "We start run for beam Mom = " << mom << "\n";
  // output1
  TString simOutput = storePath + "/Lumi_MC_";
  simOutput += startEv;
  simOutput += ".root";
  TString parOutput = storePath + "/Lumi_Params_";
  parOutput += startEv;
  parOutput += ".root";

  FairRunSim *fRun = new FairRunSim();
  cout << "All libraries succsesfully loaded!"
       << "\n";

  // set the MC version used
  fRun->SetName("TGeant4");
  // fRun->SetName("TGeant3");    //GEANE uses GEANT3!

  fRun->SetOutputFile(simOutput);

  // set material
  fRun->SetMaterials("media_pnd.geo");

  // create and add detectors
  FairModule *Cave = new PndCave("CAVE");
  // Cave->SetGeometryFileName("../macro/lmd/pndcaveVAC.geo");
  Cave->SetGeometryFileName("pndcave.geo");
  fRun->AddModule(Cave);

  FairModule *Pipe = new PndPipe("PIPE");
  //    Pipe->SetGeometryFileName("../macro/lmd/geo/beampipe_201303.root");
  Pipe->SetGeometryFileName("beampipe_201309.root");
  fRun->AddModule(Pipe);

  FairModule *Magnet = new PndMagnet("MAGNET");
  Magnet->SetGeometryFileName("FullSolenoid_V842.root");
  fRun->AddModule(Magnet);

  FairModule *Dipole = new PndMagnet("MAGNET");
  Dipole->SetGeometryFileName("dipole.geo");
  fRun->AddModule(Dipole);

  PndLmdDetector *Lum = new PndLmdDetector("LUM", kTRUE);
  Lum->SetExclusiveSensorType("LumActive"); // ignore MVD
  Lum->SetGeometryFileName(lmd_geometry_filename);
  Lum->SetVerboseLevel(verboseLevel);

  fRun->AddModule(Lum);

  // particle generator
  FairPrimaryGenerator *primGen = new FairPrimaryGenerator();

  fRun->SetGenerator(primGen);

  // Box Generator
  FairBoxGenerator *fBox = new FairBoxGenerator(particle, trkNum);
  fBox->SetPRange(mom, mom);
  fBox->SetThetaRange(0.13, 0.65); // 2... 11 mrad
  fBox->SetPhiRange(0, 360.);
  primGen->AddGenerator(fBox);

  // reading the new field map in the old format
  fRun->SetBeamMom(mom);

  PndMultiField *fField = new PndMultiField("AUTO");

  fRun->SetField(fField);

  // now finally, the init() call
  fRun->Init();

  std::map<std::string, TGeoHMatrix> totalmatrices;

  PndLmdGeometryHelper &helper = PndLmdGeometryHelper::getInstance();
  cout << "Generating all matrices...\n";
  auto allMatrices = helper.getAllAlignPaths(true, true, true, true, true);

  // save matrices to array and disk
  for (auto &i : allMatrices) {
    auto path = i;
    gGeoManager->cd(path.c_str());
    TGeoHMatrix currentmatrix = *(gGeoManager->GetCurrentMatrix());
    totalmatrices[path] = currentmatrix;
  }

  PndMatrixUtil::saveMatrices(&totalmatrices, outFileName);

  //* Generate moduleID to modulePath mappings
  cout << "Generating moduleID to modulePath mappings...\n";

  auto allOverlapInfos = helper.getOverlapInfos();
  json modulePaths;

  for (auto overlapInfo : allOverlapInfos) {
    modulePaths[std::to_string(overlapInfo.moduleID)] = overlapInfo.pathModule;
  }
  std::ofstream oMod("moduleIDtoModulePath.json");
  oMod << std::setw(2) << modulePaths << std::endl;

  //* Generate sensorID to sectorID and moduleID to sectorID mappings
  cout << "Generating sensorID to sectorID mappings...\n";
  json sensorToSector;
  json moduleToSector;
  for (int iSensor = 0; iSensor < 320; iSensor++) {
    moduleToSector[std::to_string(helper.getModuleIDFromSensorID(iSensor))] = helper.getSectorIDfromSensorID(iSensor);
    sensorToSector[std::to_string(iSensor)] = helper.getSectorIDfromSensorID(iSensor);
  }
  std::ofstream oSen("sensorIDtoSectorID.json");
  oSen << std::setw(2) << sensorToSector << std::endl;
  std::ofstream oSenToMod("moduleIDtoSectorID.json");
  oSenToMod << std::setw(2) << moduleToSector << std::endl;

  //* generate geometry paths sorted by subassembly to be aligned (box, modules and sensors)
  cout << "Generating geometry paths sorted by subassembly to be aligned (box, modules and sensors)...\n";
  auto boxPath = helper.getAllAlignPaths(false, false, false, false, true);
  auto modulesPaths = helper.getAllAlignPaths(false, true, false, false, false);
  auto sensorPaths = helper.getAllAlignPaths(true, false, false, false, false);

  json assemblyJson;

  // hot piss, nlohmann::json is awesome
  assemblyJson["box"] = boxPath;
  assemblyJson["modules"] = modulesPaths;
  assemblyJson["sensors"] = sensorPaths;

  std::ofstream oPaths("assemblyPaths.json");
  oPaths << std::setw(2) << assemblyJson << std::endl;
  cout << "all done.\n";

  return 0;
}
