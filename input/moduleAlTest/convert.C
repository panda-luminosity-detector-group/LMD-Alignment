#include <PndTrack.h>
#include <TClonesArray.h>
#include <TFile.h>
#include <TTree.h>
#include <TVector3.h>
#include <iostream>

struct recoPoint {
    int hitIndex;
    double x, y, z;
    double ex, ey, ez;
};

struct track3Dinfo : public TObject {
    double tx, ty, tz;
    double px, py, pz;
    std::vector<int> hitIndices;

    // this info is only for cross checks if the python library can read the correct reco points
    std::vector<recoPoint> recoPoints;
};

void convert() {
    cout << "Hi!\n";

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

    // event loop
    for (Long64_t ev = 0; ev < nEvents; ev++) {
        trackArray->Clear();
        trackTree->GetEntry(ev);
        recoTree->GetEntry(ev);

        Int_t tracksPerEvent = trackArray->GetEntriesFast();

        if (tracksPerEvent > 0) {
            cout << "\n\n==== Next Event\n";
            cout << "for this event, there are " << recoArray->GetEntriesFast() << " reco hits\n";
        }

        // tracks loop per event
        for (Int_t iTrack = 0; iTrack < tracksPerEvent; iTrack++) {
            PndTrack *thisTrack = (PndTrack *)trackArray->At(iTrack);

            PndTrackCand thisCandidate = thisTrack->GetTrackCand();

            // cout << "\n---- Next Track\n";

            // get all hits for this track candidate
            const int numPts = thisCandidate.GetNHits();

            //* Okay, now I have the track and all RecoHits that led to it. Now, all I need is the residuals from the track to the reco position on each plane!

            cout << "Event summary: " << tracksPerEvent << " tracks in this event and this track had " << numPts << " merged hits.\n";

            FairTrackParP paramFirst = thisTrack->GetParamFirst();

            double trackX = paramFirst.GetX();
            double trackY = paramFirst.GetY();
            double trackZ = paramFirst.GetZ();

            double trackPX = paramFirst.GetPx();
            double trackPY = paramFirst.GetPy();
            double trackPZ = paramFirst.GetPz();

            cout << "First Track in this event!\n";
            cout << "Track: x,y,z: " << trackX << ", " << trackY << ", " << trackZ << "\n";
            cout << "Track: Px,Py,Pz: " << trackPX << ", " << trackPY << ", " << trackPZ << "\n";

            // can also be done with GetPosition() and GetMomentum(), return TVector3!

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

                cout << "hitIndex: " << hitIndex << "\n";
                cout << "Original RecoHit Positions: " << xhit << ", " << yhit << ", " << zhit << "\n";
                cout << "-- Errors for this RecoHit: " << errxhit << ", " << erryhit << ", " << errzhit << "\n";
            }

            //*** skip remaining tracks
            break;
        }

        if (runIndex++ > 4) {
            break;
        }
    }
    //! dump to json here!
}