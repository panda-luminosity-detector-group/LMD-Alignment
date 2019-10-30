#include "../../json/single_include/nlohmann/json.hpp"

// call with root -l -q convertRootTracks.C

using nlohmann::json;

void histRecoMCrtakDist() {
    //*** output json
    // json outJson;

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

    // and for MC tracks
    TFile *mcFile = new TFile("Lumi_MC_100000.root");
    TTree *mcTree = (TTree *)mcFile->Get("pndsim");
    TClonesArray *mcArray = new TClonesArray("PndSdsMCPoint");
    recoTree->SetBranchAddress("LMDPoint", &mcArray);

    // how many events are in the track file?
    Long64_t nEvents = trackTree->GetEntries();
    cout << "nEvents: " << nEvents << "\n";
    int runIndex = 0;

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        recoArray->Clear();
        mcArray->Clear();
        trackTree->GetEntry(event);
        recoTree->GetEntry(event);
        mcTree->GetEntry(event);

        Int_t fittedTracksPerEvent = trackArray->GetEntriesFast();
        Int_t recosPerEvent = recoArray->GetEntriesFast();
        Int_t mctracksPerEvent = mcTree->GetEntriesFast();

        for(int i=0; i<mctracksPerEvent; i++){
            cout << "feck oi \n";
        }
        break;

        // tracks loop per event
        for (Int_t iTrack = 0; iTrack < fittedTracksPerEvent; iTrack++) {
            PndTrack *thisTrack = (PndTrack *)trackArray->At(iTrack);

            PndTrackCand thisCandidate = thisTrack->GetTrackCand();

            // get all hits for this track candidate
            const int numPts = thisCandidate.GetNHits();

            //* Okay, now I have the track and all RecoHits that led to it. Now, all I need is the residuals from the track to the reco position on each plane!

            FairTrackParP paramFirst = thisTrack->GetParamFirst();
            // FairTrackParP paramLast = thisTrack->GetParamLast();

            //* fitted track
            double trackX = paramFirst.GetX();
            double trackY = paramFirst.GetY();
            double trackZ = paramFirst.GetZ();

            double trackPX = paramFirst.GetPx();
            double trackPY = paramFirst.GetPy();
            double trackPZ = paramFirst.GetPz();
            
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

                double errxhit = addHit->GetDx();
                double erryhit = addHit->GetDy();
                double errzhit = addHit->GetDz();

                int sensorID = addHit->GetSensorID();

                thisEvent["recoHits"].push_back({{"index", hitIndex}, {"sensorID", sensorID}, {"pos", {xhit, yhit, zhit}}, {"err", {errxhit, erryhit, errzhit}}});
            }

            //*** skip remaining tracks, they are copies of the first
            break;
        }
        if (runIndex++ > 20) {
            break;
        }
    }
    //! dump to json here!

    // TODO: better target dir!
    // std::ofstream o("../../input/modulesAlTest/tracks_processed.json");
    // std::ofstream o("../../input/modulesAlTest/tracks_processed-modulesNoRot-1.00.json");
    // o << std::setw(2) << outJson << std::endl;


    cout << "all done!\n";
}