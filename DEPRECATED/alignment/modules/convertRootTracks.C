#include "../../json/single_include/nlohmann/json.hpp"

//* call with root -l -q convertRootTracks.C(dataPath, jsonFile)

// TODO: dump result to binary file with 6*3 values: trkOri, trkDir, reco1 - reco4, each having (x,y,z)
// TODO: sometimes some values are null, and those are stored to json as well. Skip them!
// also, the python stuff must be able to read that

using nlohmann::json;

int convertRootTracks() {
    cout << "\n\nUsage: convertRootTracks.C(dataPath, outJsonFile)\n\n";
    return 1;
}

int convertRootTracks(std::string dataPath, std::string outJsonFile) {
    //*** output json
    json outJson;

    cout << "reading tracks from this dir:\n"
         << dataPath << "\n";
    cout << "writing tracks to this file:\n"
         << outJsonFile << "\n";

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

            double trackX = paramFirst.GetX();
            double trackY = paramFirst.GetY();
            double trackZ = paramFirst.GetZ();

            double trackPX = paramFirst.GetPx();
            double trackPY = paramFirst.GetPy();
            double trackPZ = paramFirst.GetPz();

            // can also be done with GetPosition() and GetMomentum(), return TVector3!
            auto thisEvent = json({});

            thisEvent.push_back({"trkPos", {trackX, trackY, trackZ}});
            thisEvent.push_back({"trkMom", {trackPX, trackPY, trackPZ}});

            // hit loop per candidate
            for (int iHit = 0; iHit < numPts; iHit++) {
                PndTrackCandHit theHit = thisCandidate.GetSortedHit(iHit);  // get hit
                int hitIndex = theHit.GetHitId();

                // get mergedHit
                PndSdsMergedHit *addHit = (PndSdsMergedHit *)recoArray->At(hitIndex);
                TVector3 addPos = addHit->GetPosition();
                double xhit = addPos.X();
                double yhit = addPos.Y();
                double zhit = addPos.Z();
                int sensorID = addHit->GetSensorID();

                thisEvent["recoHits"].push_back({{"index", hitIndex}, {"sensorID", sensorID}, {"pos", {xhit, yhit, zhit}}});
            }

            outJson["events"].push_back(thisEvent);

            //*** skip remaining tracks, they are copies of the first
            break;
        }
        if (event == 2000000) {
            break;
        }
    }
    //! dump to json here!
    std::ofstream o(outJsonFile);
    o << std::setw(2) << outJson << std::endl;
    cout << "all done!\n";
    return 0;
}