#include "../../json/single_include/nlohmann/json.hpp"

//* call with root -l -q convertRootTracks.C

// TODO: dump result to binary file with 6*3 values: trkOri, trkDir, reco1 - reco4, each having (x,y,z) 
// also, the python stuff must be able to read that

using nlohmann::json;

void convertRootTracks(std::string dataPath, std::string outJsonFile) {
    //*** output json
    json outJson;

    // filename
    TFile *trackFile = new TFile(dataPath.c_str() + "/Lumi_Track_100000.root");
    // TTree name, use TBrowser if the name is unknown
    TTree *trackTree = (TTree *)trackFile->Get("pndsim");
    // the TClonesArray needs to know the class of the objects you want to retrieve
    TClonesArray *trackArray = new TClonesArray("PndTrack");
    // and the TBranch name, use TBrowser if the name is unknown
    trackTree->SetBranchAddress("LMDPndTrack", &trackArray);

    // same for recoHits
    TFile *recoFile = new TFile(dataPath.c_str() + "/Lumi_recoMerged_100000.root");
    TTree *recoTree = (TTree *)recoFile->Get("pndsim");
    TClonesArray *recoArray = new TClonesArray("PndSdsMergedHit");
    recoTree->SetBranchAddress("LMDHitsMerged", &recoArray);

    // how many events are in the track file?
    Long64_t nEvents = trackTree->GetEntries();
    cout << "nEvents: " << nEvents << "\n";
    int runIndex = 0;

    // event loop
    for (Long64_t event = 0; event < nEvents; event++) {
        trackArray->Clear();
        recoArray->Clear();
        trackTree->GetEntry(event);
        recoTree->GetEntry(event);

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
    }
    //! dump to json here!
    std::ofstream o(outJsonFile);
    o << std::setw(2) << outJson << std::endl;
    cout << "all done!\n";
}