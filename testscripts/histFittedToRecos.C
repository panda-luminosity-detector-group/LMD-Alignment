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

void histFittedToRecos() {
    //*** output json
    json outJson;

    // filename
    TFile *trackFile = new TFile("Lumi_Track_100000.root");
    // TTree name, use TBrowser if the name is unknown
    TTree *trackTree = (TTree *)trackFile->Get("pndsim");
    // the TClonesArray needs to know the class of the objects you want to retrieve
    TClonesArray *trackArray = new TClonesArray("PndTrack");
    // and the TBranch name, use TBrowser if the name is unknown
    trackTree->SetBranchAddress("LMDPndTrack", &trackArray);

    // same for recoHits
    TFile *recoFile = new TFile("Lumi_recoMerged_100000.root");
    TTree *recoTree = (TTree *)recoFile->Get("pndsim");
    TClonesArray *recoArray = new TClonesArray("PndSdsMergedHit");
    recoTree->SetBranchAddress("LMDHitsMerged", &recoArray);

    // how many events are in the track file?
    Long64_t nEvents = trackTree->GetEntries();
    cout << "nEvents: " << nEvents << "\n";
    int runIndex = 0;

    TH1D hist("distance LMDPoint - MC track", "distance LMDPoint - MC track", 100, -1, -1);

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        trackTree->GetEntry(event);
        recoTree->GetEntry(event);

        string evStr = std::to_string(event);

        Int_t tracksPerEvent = trackArray->GetEntriesFast();

        // create empty json object which will hold this event
        auto thisEvent = json({});

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

            // cout << "First Track in this event!\n";
            // cout << "Track: x,y,z: " << trackX << ", " << trackY << ", " << trackZ << "\n";
            // cout << "Track: Px,Py,Pz: " << trackPX << ", " << trackPY << ", " << trackPZ << "\n";

            // can also be done with GetPosition() and GetMomentum(), return TVector3!

            thisEvent.push_back({"trkPos", {trackX, trackY, trackZ}});
            thisEvent.push_back({"trkMom", {trackPX, trackPY, trackPZ}});
            
            TVector3 trkO(trackX, trackY, trackZ);
            TVector3 trkD(trackPX, trackPY, trackPZ);

            trkD *= 1.0 / trkD.Mag();

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

                TVector3 thisLMDPoint(xhit, yhit, zhit);

                double errxhit = addHit->GetDx();
                double erryhit = addHit->GetDy();
                double errzhit = addHit->GetDz();

                int sensorID = addHit->GetSensorID();

                // cout << "hitIndex: " << hitIndex << "\n";
                // cout << "Original RecoHit Positions: " << xhit << ", " << yhit << ", " << zhit << "\n";
                // cout << "-- Errors for this RecoHit: " << errxhit << ", " << erryhit << ", " << errzhit << "\n";

                thisEvent["recoHits"].push_back({{"index", hitIndex}, {"sensorID", sensorID}, {"pos", {xhit, yhit, zhit}}, {"err", {errxhit, erryhit, errzhit}}});
                
                // if(!(sensorID >= 150 && sensorID < 200)){
                // // if(sensorID != 140){
                //     continue;
                // }
                
                cout << "\n ------------ \nattention!\n";
                trkO.Print();
                trkD.Print();
                thisLMDPoint.Print();


                // cald distance
                auto tVec1 = trkO - thisLMDPoint;
                auto dVec = ( tVec1 ) - ((( tVec1 )*trkD ) * trkD);
                hist.Fill(dVec.Mag()*1e4);
                dVec.Print();

            }
            // outJson["events"].push_back(thisEvent);

            //*** skip remaining tracks, they are copies of the first
            break;
        }
        break;
        if (runIndex++ > 0) {
            break;
        }
    }
    //! dump to json here!

    // TODO: better target dir!
    // std::ofstream o("../../input/modulesAlTest/tracks_processed.json");
    // o << std::setw(2) << outJson << std::endl;

    TCanvas canvas;
    canvas.cd();
    // canvas.SetLogy();
    hist.GetXaxis()->SetTitle("d [#mum]");
    hist.GetYaxis()->SetTitle("count (log)");
    hist.Draw();
    canvas.SaveAs("dxdy.pdf");

    cout << "all done!\n";
}