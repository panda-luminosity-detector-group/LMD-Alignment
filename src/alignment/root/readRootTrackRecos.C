//* call with root -l -q convertRootTracks.C(dataPath, csvFile)

// TODO: dump result to binary file with 6*3 values: trkOri, trkDir, reco1 - reco4, each having (x,y,z)
// TODO: sometimes some values are null, and those are stored to json as well. Skip them!

int readRootTrackRecos() {
    cout << "\n\nUsage: convertRootTracks.C(dataPath, outCSVfile)\n\n";
    return 1;
}

int readRootTrackRecos(std::string dataPath, std::string outCSVfile) {
    cout << "reading tracks from this dir:\n"
         << dataPath << "\n";
    cout << "writing tracks to this file:\n"
         << outCSVfile << "\n";

    // std::stringstream result;
    std::ofstream result(outCSVfile);
    // set precision
    result << std::setprecision(6);

    // TChain Version
    TChain *trackChain = new TChain("pndsim");
    trackChain->Add((dataPath + "/Lumi_Track_*.root").c_str());
    TClonesArray *trackArray = new TClonesArray("PndTrack");
    trackChain->SetBranchAddress("LMDPndTrack", &trackArray);

    TChain *recoChain = new TChain("pndsim");
    recoChain->Add((dataPath + "/Lumi_recoMerged_*.root").c_str());
    TClonesArray *recoArray = new TClonesArray("PndSdsMergedHit");
    recoChain->SetBranchAddress("LMDHitsMerged", &recoArray);

    // how many events are in the track file?
    Long64_t nEvents = trackChain->GetEntries();
    cout << "nEvents: " << nEvents << "\n";
    int runIndex = 0;

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        recoArray->Clear();
        trackChain->GetEntry(event);
        recoChain->GetEntry(event);

        Int_t tracksPerEvent = trackArray->GetEntriesFast();

        // tracks loop per event
        for (Int_t iTrack = 0; iTrack < tracksPerEvent; iTrack++) {
            PndTrack *thisTrack = (PndTrack *)trackArray->At(iTrack);

            PndTrackCand thisCandidate = thisTrack->GetTrackCand();

            // get all hits for this track candidate
            const int numPts = thisCandidate.GetNHits();

            //* Okay, now I have the track and all RecoHits that led to it. Now, all I need is the residuals from the track to the reco position on each plane!

            FairTrackParP paramFirst = thisTrack->GetParamFirst();

            // makes it easier for later
            if (numPts != 4) {
                continue;
            }
            std::vector<int> sensorIDs;
            bool skipThis = false;

            // hit loop per candidate
            for (int iHit = 0; iHit < numPts; iHit++) {
                // check that all sensorIDs are different
                PndTrackCandHit theHit = thisCandidate.GetSortedHit(iHit);  // get hit
                int hitIndex = theHit.GetHitId();

                // get mergedHit
                PndSdsMergedHit *addHit = (PndSdsMergedHit *)recoArray->At(hitIndex);
                TVector3 addPos = addHit->GetPosition();
                double xhit = addPos.X();
                double yhit = addPos.Y();
                double zhit = addPos.Z();

                int sensorID = addHit->GetSensorID();

                for (auto id : sensorIDs) {
                    if (id == sensorID) {
                        cout << "double sensor hit\n";
                        skipThis = true;
                    }
                }

                if (skipThis) {
                    continue;
                }
                sensorIDs.push_back(sensorID);

                // thisEvent["recoHits"].push_back({{"index", hitIndex}, {"sensorID", sensorID}, {"pos", {xhit, yhit, zhit}}});
                result << sensorID << "," << xhit << "," << yhit << "," << zhit << "\n";
            }

            // outJson["events"].push_back(thisEvent);

            //*** skip remaining tracks, they are copies of the first
            break;
        }
        // if (event == 2000000) {
            // break;
        // }
    }
    //! dump to json here!
    // std::ofstream o(outCSVfile);
    // o << std::setw(4) << result.str() << std::endl;
    cout << "all done!\n";
    return 0;
}