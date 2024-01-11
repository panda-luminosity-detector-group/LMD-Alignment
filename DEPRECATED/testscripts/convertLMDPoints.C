#include "../json/single_include/nlohmann/json.hpp"

// call with root -l -q convertRootTracks.C

using nlohmann::json;

void convertLMDPoints() {

    //*** output json, contains events
    json outJson;

    // filename
    TFile *trackFile = new TFile("Lumi_MC_100000.root");
    
    // TTree name, use TBrowser if the name is unknown
    TTree *trackTree = (TTree *)trackFile->Get("pndsim");
    
    // the TClonesArray needs to know the class of the objects you want to retrieve
    TClonesArray *trackArray = new TClonesArray("PndSdsMCPoint");
    
    // and the TBranch name, use TBrowser if the name is unknown
    trackTree->SetBranchAddress("LMDPoint", &trackArray);

    // how many events are in the track file?
    Long64_t nEvents = trackTree->GetEntries();
    cout << "nEvents: " << nEvents << "\n";

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        trackTree->GetEntry(event);

        Int_t pointsPerEvent = trackArray->GetEntriesFast();

        // first filter 
        if(pointsPerEvent < 2 || pointsPerEvent > 8){
            continue;
        }

        json thisevent;

        // LMDPoint loop per event
        for (int iPoint = 0; iPoint < pointsPerEvent; iPoint++) {

            // contains all lmdpoints for this event
            json lmdpointsJson;

            PndSdsMCPoint *thisPoint = (PndSdsMCPoint *)trackArray->At(iPoint);
            
            if(!thisPoint){
                continue;
            }

            int eventID = thisPoint->GetEventID();
            int trackID = thisPoint->GetTrackID();
                
            if(eventID > 0 || trackID > 0){
                continue;
            }

            auto sensorID = thisPoint->GetSensorID();

            TVector3 position = thisPoint->GetPosition();

            double fx = position.x();
            double fy = position.y();
            double fz = position.z();

            lmdpointsJson.push_back(fx);
            lmdpointsJson.push_back(fy);
            lmdpointsJson.push_back(fz);
            lmdpointsJson.push_back(sensorID);

            thisevent.push_back(lmdpointsJson);
        }

        if(thisevent.size() > 0){
            outJson.push_back(thisevent);
        }
    }

    //! dump to json here!
    // TODO: better target dir!
    std::ofstream o("LMDPoints_processed.json");
    o << std::setw(2) << outJson << std::endl;

    cout << "all done!\n";
}