int convert() {
    cout << "Hi!\n";

    TFile *f = new TFile("Lumi_Track_100000.root");
    TTree *T = (TTree *)f->Get("pndsim");

    // T->Print();

    TClonesArray *arr = new TClonesArray("Double_t");
    T->GetBranch("LMDPndTrack.fTrackParamFirst.fX")->SetAutoDelete(kFALSE);
    T->SetBranchAddress("LMDPndTrack", &arr);
    Long64_t nEvents = T->GetEntries();

    cout << "nEvents: " << nEvents << "\n";

    // i want:
    // LMDPndTrack.fTrackParamFirst.fX

    for (Long64_t ev = 0; ev < nEvents; ev++) {
        
        arr->Clear();
        T->GetEntry(ev);

        Int_t entriesPerEvent = arr->GetEntriesFast();
        cout << "this entries: " << entriesPerEvent << "\n";
        // for (Int_t i = 0; i < entriesPerEvent; i++) {
        //     Double_t* value = (Double_t*)arr->At(i);
        //     cout << "value is: " << *value << "\n";
        // }
    }

    return 0;
}