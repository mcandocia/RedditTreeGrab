#this document contains the specific parameters for the generative model
#alter this prior to running code [genmod.py]

print "IMPORTING PARAMETERS"

useTerms = True
useSubs = True
name = 'apoptosis'
#this weights the terms more than the subreddits; this does nothing if subs is turned
#off
termMultiplier = 0.4#
#lambda terms are factors for the smoothing terms
#essentially, the higher they are, the greater the shrinkage
lambdaTerm = 2
lambdaSub = 1
#these are pre-defined groups
#replace this with None if unsupervised learning is used
clusterClasses = ['GG','SJW','O']
#these will make sure unlabeled classes are properly defined as so when
#reading in manually labeled data
nullClasses = ['NA','?']
#this is important for unsupervised learning
nclasses = 3
k=nclasses#just for quick reference
#if greater than 1, n-fold cross-validation is used to determine accuracy of algorithm 
#with already-sorted data...this will make the algorithm run nfolds times longer
nfolds = 5
#defines number of iterations for convergence
niter = 9
#this defines the initial weight for labeled terms and subreddits
#true_weight = (2 + sample_size*weight* 
#exp(-iter*decayRate)/training_size)/(2*sample_size)
#use decay = 0 to keep the terms fixed
#use weight = 0 to not use any weighting for labeled data
weightInitialTerm = 100
weightInitialSub = 100
decayTerm = 3.
decaySub = 3.
#sets lower bound for what the weight can decay to
weightMinTerm = 2.0/1
weightMinSub = 2.0/1

supervised_mode = False
#this can be used to define priors for clusters.  If unchecked, then they will be 
#calculated each loop
#it can also be adjusted to the initial value from the training set ("train")
clusterPriors = [0.05,0.01,0.94]
#this will smooth the priors slightly based on one's confidence in the training
#higher values are preferred
priorConfidence = 0.8

#use manually defined weights for each node
useManualWeights=False

#used for backwards parameter selection
paramSelection = True
paramIter = 2
paramFactor = 10

#used to pre-ignore certain variables manually; use this when results are counterintuitive for certain variables
ignoreSubs = []
ignoreTerms = []#[275,285,292]
#used for large subreddits that are frequent enough to warrant utilizing
forceSubs = []
forceTerms = []
#used to determine if fold results should be written
writefolds = True
