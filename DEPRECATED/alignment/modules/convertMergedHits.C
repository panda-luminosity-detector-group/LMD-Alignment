#include "../../json/single_include/nlohmann/json.hpp"

// call with root -l -q convertRootTracks.C

using nlohmann::json;

void convertMergedHits() {
    //*** output json
    json outJson;

    // TChain Version
    TChain *chain = new TChain("pndsim");
    chain->Add("../../input/modulesAlTest/Lumi_recoMerged_*.root");

    TClonesArray *recoArray = new TClonesArray("PndSdsMergedHit");
    // recoTree->SetBranchAddress("LMDHitsMerged", &recoArray);
    chain->SetBranchAddress("LMDHitsMerged", &recoArray);

    // how many events are in the track file?
    Long64_t nEvents = chain->GetEntries();
    cout << "nEvents: " << nEvents << "\n";

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        recoArray->Clear();
        chain->GetEntry(event);

        int mergedHitsPerEvent = recoArray->GetEntriesFast();

        // I'm only interested in these, for now
        if(mergedHitsPerEvent != 4){
            continue;
        }

        auto thisEvent = json({});

        // add dummy data for now
        thisEvent.push_back({"trkPos", {0.0, 0.0, 0.0}});
        thisEvent.push_back({"trkMom", {0, 0, 15.0}});

        // mergedHits loop per event
        for (int iMergedHit = 0; iMergedHit < mergedHitsPerEvent; iMergedHit++) {
            PndSdsMergedHit *thisMergedHit = (PndSdsMergedHit *)recoArray->At(iMergedHit);

            //* I need x, y, z and sensorID
            auto thisPos = thisMergedHit->GetPosition();
            int sensorID = thisMergedHit->GetSensorID();
            double fx, fy, fz;
            fx = thisPos.x();
            fy = thisPos.y();
            fz = thisPos.z();

            json thisHit = json({});
            thisEvent["recoHits"].push_back({{"sensorID", sensorID}, {"pos", {fx, fy, fz}}});
        }
        outJson["events"].push_back(thisEvent);
    }
    //! dump to json here!
    // TODO: better target dir!
    std::ofstream o("../../input/modulesAlTest/tracks_processed-noTrks-chain.json");
    // std::ofstream o("../../input/modulesAlTest/tracks_processed-modulesNoRot-1.00.json");
    o << std::setw(2) << outJson << std::endl;

    cout << "all done!\n";
}