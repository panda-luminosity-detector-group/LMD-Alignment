//* call with root -l -q convertRootTracks.C(dataPath, csvFile)

// TODO: dump result to binary file with 6*3 values: trkOri, trkDir, reco1 - reco4, each having (x,y,z)
// TODO: sometimes some values are null, and those are stored to json as well. Skip them!

int readRootTrackRecosNoTracks() {
    cout << "\n\nUsage: convertRootTracks.C(dataPath, outCSVfile)\n\n";
    return 1;
}

int readRootTrackRecosNoTracks(std::string dataPath, std::string outCSVfile) {
    cout << "reading tracks from this dir:\n"
         << dataPath << "\n";
    cout << "writing tracks to this file:\n"
         << outCSVfile << "\n";

    // std::stringstream result;
    std::ofstream result(outCSVfile);
    // set precision
    result << std::setprecision(6);

    TChain *recoChain = new TChain("pndsim");
    recoChain->Add((dataPath + "/Lumi_recoMerged_*.root").c_str());
    TClonesArray *recoArray = new TClonesArray("PndSdsMergedHit");
    recoChain->SetBranchAddress("LMDHitsMerged", &recoArray);

    // how many events are in the track file?
    Long64_t nEvents = recoChain->GetEntries();
    cout << "nEvents: " << nEvents << "\n";
    int runIndex = 0;

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        recoArray->Clear();
        recoChain->GetEntry(event);

        Int_t recosPerEvent = recoArray->GetEntriesFast();

        if (recosPerEvent != 4) {
            continue;
        }
        
        // purposefully unrolled reco hit loop - Iteration 0
        PndSdsMergedHit *thisReco0 = (PndSdsMergedHit *)recoArray->At(0);
        TVector3 addPos0 = thisReco0->GetPosition();
        double xhit0 = addPos0.X();
        double yhit0 = addPos0.Y();
        double zhit0 = addPos0.Z();
        int sensorID0 = thisReco0->GetSensorID();
        
        // Iteration 1
        PndSdsMergedHit *thisReco1 = (PndSdsMergedHit *)recoArray->At(1);
        TVector3 addPos1 = thisReco1->GetPosition();
        double xhit1 = addPos1.X();
        double yhit1 = addPos1.Y();
        double zhit1 = addPos1.Z();
        int sensorID1 = thisReco1->GetSensorID();
        
        // Iteration 2
        PndSdsMergedHit *thisReco2 = (PndSdsMergedHit *)recoArray->At(2);
        TVector3 addPos2 = thisReco2->GetPosition();
        double xhit2 = addPos2.X();
        double yhit2 = addPos2.Y();
        double zhit2 = addPos2.Z();
        int sensorID2 = thisReco2->GetSensorID();
        
        // Iteration 3
        PndSdsMergedHit *thisReco3 = (PndSdsMergedHit *)recoArray->At(3);
        TVector3 addPos3 = thisReco3->GetPosition();
        double xhit3 = addPos3.X();
        double yhit3 = addPos3.Y();
        double zhit3 = addPos3.Z();
        int sensorID3 = thisReco3->GetSensorID();

        // some are clearly outliers with abs(x) or abs(y) > 2000.
        // if that's the case, skip this event
        int limit = 2000;
        if( abs(xhit0) > limit || abs(yhit0) > limit )
            continue;
        if( abs(xhit1) > limit || abs(yhit1) > limit )
            continue;
        if( abs(xhit2) > limit || abs(yhit2) > limit )
            continue;
        if( abs(xhit3) > limit || abs(yhit3) > limit )
            continue;
            
        // check if the four hits are really on four different planes
        // by checking if their z coordinates are at least 5cm apart
        if( ! (zhit1 > zhit0 + 5) )
            continue;
        if( ! (zhit2 > zhit1 + 5) )
            continue;   
        if( ! (zhit3 > zhit2 + 5) )
            continue;

        // write to csv
        result << sensorID0 << "," << xhit0 << "," << yhit0 << "," << zhit0 << "\n";
        result << sensorID1 << "," << xhit1 << "," << yhit1 << "," << zhit1 << "\n";
        result << sensorID2 << "," << xhit2 << "," << yhit2 << "," << zhit2 << "\n";
        result << sensorID3 << "," << xhit3 << "," << yhit3 << "," << zhit3 << "\n";
        
    }
    //! dump to json here!
    // std::ofstream o(outCSVfile);
    // o << std::setw(4) << result.str() << std::endl;
    cout << "all done!\n";
    return 0;
}