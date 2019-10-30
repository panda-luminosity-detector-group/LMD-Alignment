#include "../json/single_include/nlohmann/json.hpp"

// call with root -l -q convertRootTracks.C

using nlohmann::json;

struct recoPoint {
    int hitIndex;
    double x, y, z;
    double ex, ey, ez;
};

struct track3Dinfo {
    double tx, ty, tz;
    double px, py, pz;
    std::vector<int> hitIndices;

    // this info is only for cross checks if the python library can read the correct reco points
    std::vector<recoPoint> recoPoints;
};

void histTrackToRecoDist() {

    cout << "Hi!\n";

    //*** output json
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
    // int runIndex = 0;

    TH1D hist("distance LMDPoint - MC track", "distance LMDPoint - MC track", 100, -1, -1);

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        trackTree->GetEntry(event);

        string evStr = std::to_string(event);

        Int_t tracksPerEvent = trackArray->GetEntriesFast();

        std::vector<TVector3> posVectors;
        std::vector<TVector3> dirVectors;
        std::vector<int> sensorIDs;

        if(tracksPerEvent < 2 || tracksPerEvent > 8){
            continue;
        }

        // LMDPoint loop per event
        for (int iTrack = 0; iTrack < tracksPerEvent; iTrack++) {
            
            PndSdsMCPoint *thisPoint = (PndSdsMCPoint *)trackArray->At(iTrack);
            
            if(!thisPoint){
                continue;
            }

            int eventID = thisPoint->GetEventID();
            int trackID = thisPoint->GetTrackID();
                
            // cout << "IDs: " << eventID << ", " << trackID << "\n";

            if(eventID > 0 || trackID > 0){
                continue;
            }

            auto sensorID = thisPoint->GetSensorID();
            // if( !(sensorID >= 0 && sensorID < 50) ){
            //     continue;
            // }

            TVector3 position = thisPoint->GetPosition();
            // TVector3 outDirection = thisPoint -> GetPositionOut();
            Double_t px = thisPoint->GetPxOut();
            Double_t py = thisPoint->GetPyOut();
            Double_t pz = thisPoint->GetPzOut();
            TVector3 momentumOut(px, py, pz); 

            // if(pz < 14){
            //     continue;
            // }

            momentumOut *= 1.0/momentumOut.Mag();   // no /= available
            
            posVectors.push_back(position);
            dirVectors.push_back(momentumOut);
            sensorIDs.push_back(sensorID);
        }

        // filter again for at least 2 lmdpoints, some may have been skipped because of their trackID
        if( dirVectors.size() > 1){
            //create "track":
            auto trkO = posVectors[0];
            auto trkD = dirVectors[0];

            for(int i=1; i<posVectors.size(); i++){
                auto thisLMDpoint = posVectors[i];

                auto sensorID = sensorIDs[i];

                if( !(sensorID >= 150 && sensorID < 200) ){
                    continue;
                }

                // cald distance
                auto tVec1 = trkO - thisLMDpoint;
                auto dVec = ( tVec1 ) - ((( tVec1 )*trkD ) * trkD);
                // cout << "distance: " << dVec.Mag()*1e4 << "\n";
                hist.Fill(dVec.Mag()*1e4);
            }
        }

    }
    // //! dump to json here!
    // // TODO: better target dir!
    // std::ofstream o("LMDPoints_processed.json");
    // o << std::setw(2) << outJson << std::endl;

    if(false){


    TCanvas canvas;
    canvas.cd();
    // canvas.SetLogy();
    hist.GetXaxis()->SetTitle("d [#mum]");
    hist.GetYaxis()->SetTitle("count (log)");
    hist.Draw();
    canvas.SaveAs("dxdy.pdf");

    }


    cout << "all done!\n";
}