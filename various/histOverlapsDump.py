def histCompareResults(self):

    with open(self.idealDetectorMatrixPath) as ideasF:
        idealDetectorMatrices = json.load(ideasF)

    with open(self.config.pathMisMatrix()) as f:
        misMatrices = json.load(f)

    comparator = overlapComparator()
    
    # set ideal and misalignment matrices
    comparator.idealDetectorMatrices = idealDetectorMatrices
    comparator.misalignMatrices = misMatrices

    comparator.setOverlapMatrices(self.overlapMatrices)
    comparator.loadPerfectDetectorOverlaps(self.idealOverlapsPath)
    
    histogramFileName = Path('output') / Path(self.config.misalignType)
    comparator.saveHistogram(histogramFileName)