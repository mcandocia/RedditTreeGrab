#performs final analysis on reddit data
#requires a tuning document

import csv
import os
import shelve
import math
import sqlite3
import sys
import random
import re
import copy
#this file you should configure manually
#import genmod_params

def main(argv):
	#create filenames 
	opts = options()
	name = opts.name
	k = opts.k
	if '-header' in argv:
		writeHeader = True
	else:
		writeHeader = False
	writeHistory = '-history' in argv
	
	if opts.clusterClasses <> None:
		unsupervised = False
		filelist = os.listdir(os.getcwd())
		assigned = []
		parsed_ids = set()
		filename_clusters = 'user_sample0_'+name + '.csv'
		counter = 0
		while filename_clusters in filelist:
			counter+=1
			file = open(filename_clusters,'rb')
			reader = csv.reader(file)
			for line in reader:
				if len(line)<5:
					continue
				number = line[0]
				cluster = line[4]
				if cluster not in opts.clusterClasses:
					continue
				if number in parsed_ids:
					continue
				assigned.append((int(number),opts.clusterClasses.index(cluster)))
				parsed_ids.add(int(number))
			file.close()
			filename_clusters = 'user_sample' + str(counter) + '_' + name + '.csv'
		if opts.clusterPriors in ['train','train2']:
			opts.clusterPriors = [0]*k
			for user in assigned:
				opts.clusterPriors[user[1]]+=1
			print "Training group sizes: " + str(opts.clusterPriors)
			opts.clusterPriors = divide(opts.clusterPriors,sum(opts.clusterPriors))
			print "Derived priors = " + str(opts.clusterPriors)
			opts.clusterPriors = [x*opts.priorConfidence+(1.-opts.priorConfidence)/k for x in opts.clusterPriors]
			if opts.priorConfidence <> 1:
				print "Smoothed priors = " + str(opts.clusterPriors)
	else:
		unsupervised = True
	print "Loaded labeled data"
	#temporary counting
	counters = [0]*k
	for item in assigned:
		counters[item[1]]+=1
	print counters
	#figure out number of users, terms, and subreddits
	#user
	userfile = open(opts.filename_uid,'r')
	usercount = 0
	while True:
		blank = userfile.readline()
		if blank == '':
			break
		usercount+=1
	userfile.close()
	#sub
	subfile = open(opts.filename_sid,'r')
	subcount = 0
	while True:
		blank = subfile.readline()
		if blank == '':
			break
		subcount+=1
	subfile.close()
	#term
	termfile = open(opts.filename_tid,'r')
	termcount = 0
	while True:
		blank = termfile.readline()
		if blank == '':
			break
		termcount+=1
	termfile.close()
	print "Established counts for data types"
	#now we will initialize the attributes for each point...they will be as follows
	#[cluster,[cluster_priors],[cluster_logscores],manually_labeled]
	clustcounts = [0]*k
	udata = [[-1,[1./k for _ in range(opts.nclasses)],[1./k for _ in range(opts.nclasses)],0] for _ in range(usercount) ]
	print [usercount,termcount,subcount]
	counts = [usercount,termcount,subcount]
	validSubs = [True] * subcount
	validTerms = [True] * termcount
	for sid in opts.ignoreSubs:
		validSubs[sid] = False
	for tid in opts.ignoreSubs:
		validTerms[tid] = False
	if not unsupervised:
		for user in assigned:
			#print user
			cluster = user[1]
			probs = [0]*k
			probs[cluster]=1
			uid = user[0]
			udata[uid][0] = cluster
			udata[uid][3] = 1
			udata[uid][1] = probs
			clustcounts[cluster]+=1
		print "Copied labeled clusters"
	clusrange = range(k)
	for uid in range(usercount):
		if udata[uid][0] == -1:
			cluster = random.choice(clusrange)
			clustcounts[cluster]+=1
			udata[uid][0]=cluster
			probs = [0]*k
			probs[cluster]=1
			udata[uid][1]=probs
	print "Assigned initial clusters"
	#these will change to raw count values briefly 
	#when estimating the parameters
	#each class gets its own subreddit probabilities
	#print "Initialized all constants. Beginning EM ALGORITHM"
	prior = divide(clustcounts,sum(clustcounts))
	traingroups = xv_groups(assigned,opts.nfolds,opts.k)
	#printmat(traingroups)
	errors=[0]*k
	classmat = [[0]*k for _ in range(k)]
	deviances = []
	qdata=list(udata)
	if opts.paramSelection:
		netTerms = validTerms
		netSubs = validSubs
		for l in range(opts.paramIter):
			errors=[0]*k
			impurities = [0]*k
			classmat = [[0]*k for _ in range(k)]
			deviances = []
			#print traingroups
			print '+++++++++++++++++++++++++++++'
			print 'Beginning round ' + str(l+1)
			for fold in range(opts.nfolds):
				oldprior = opts.clusterPriors
				newerrors = copy.deepcopy(generative_model(copy.deepcopy(udata),opts,fold,traingroups,list(prior),counts,copy.deepcopy(validSubs),copy.deepcopy(validTerms),writeHeader,writeHistory))
				deviances.append(newerrors[2])
				opts.clusterPriors = oldprior
				netTerms = bitand(netTerms,newerrors[3])
				netSubs = bitand(netSubs,newerrors[4])
				for i in range(opts.k):
					errors[i] += newerrors[0][i]
					impurities[i]+=colSum(newerrors[1],i)*newerrors[5][i]
					for j in range(opts.k):
						classmat[i][j] += newerrors[1][i][j]
				print "Done with fold #" + str(fold+1)
			errors = [x/opts.nfolds for x in errors]
			impurities = [impurities[i]/colSum(classmat,i) for i in range(k)]
			vsum = 0
			for uid in range(usercount):
				vsum+=udata[uid][3]
			for i in range(len(opts.forceSubs)):
				netTerms[opts.forceSubs[i]] = True
				validTerms[opts.forceSubs[i]] = True
			for i in range(len(opts.forceTerms)):
				netSubs[opts.forceTerms[i]] = True
				validSubs[opts.forceTerms[i]] = True
			#print vsum
			print [round(x,3) for x in errors]
			print [round(x,3) for x in impurities]
			printmat(classmat)
			udata=list(qdata)
			print "DEVIANCES"
			print "MEAN: " + str(mean(deviances))
			print "STDEV: " + str(sd(deviances))
			print "TOTAL SUBS " + str(sum(netSubs))
			print "TOTAL TERMS: " + str(sum(netTerms))
			if l <> opts.paramIter-1:
				validTerms = list(netTerms)
				validSubs = list(netSubs)
		filename_params = 'params_' + opts.name + '.dat'
		paramfile = shelve.open(filename_params)
		paramfile['TERM'] = validTerms
		paramfile['SUB'] = validSubs
		paramfile['DEVIANCES'] = deviances
		paramfile['ERRORS'] = errors
		paramfile['CLASSMAT'] = classmat
		paramfile.close()
	else:
		for fold in range(opts.nfolds):
			oldprior = list(opts.clusterPriors)
			newerrors = generative_model(copy.deepcopy(udata),opts,fold,traingroups,prior,counts,validSubs,validTerms,writeHeader,writeHistory)
			deviances.append(newerrors[2])
			opts.clusterPriors = oldprior
			for i in range(opts.k):
				errors[i] += newerrors[0][i]
				for j in range(opts.k):
					classmat[i][j] += newerrors[1][i][j]
			print "Done with fold #" + str(fold+1)
		errors = [x/k for x in errors]
		print errors
		printmat(classmat)
		print "DEVIANCES"
		print "MEAN: " + str(mean(deviances))
		print "STDEV: " + str(sd(deviances))
	
def mean(x):
	return float(sum(x))/len(x)

def var(x):
	mx = mean(x)
	return float(sum([(y-mx)**2 for y in x]))/len(x)
	
def sd(x):
	return math.sqrt(var(x))

def generative_model(udata,opts,fold,traingroups,prior,counts,validSubs,validTerms,writeHeader,writeHistory):
	k = opts.k
	fold_ids = []
	fold_clusts = []
	parsed_ids = []
	traincount=0
	usercount = counts[0]
	termcount = counts[1]
	subcount = counts[2]
	for clus in range(k):
		fold_ids += traingroups[clus][fold]
		for fol in range(len(traingroups[clus])):
			parsed_ids+=traingroups[clus][fol]
		#print len(fold_ids)
	for id in fold_ids:
		traincount-=1
		fold_clusts.append(udata[id][0])
		udata[id][3] = 0
	#print fold_ids
	for id in parsed_ids:
		traincount+=1
	#print traincount
	#print 'Beginning EM Algorithm'
	for iter in range(opts.niter):
		phiSub = [[opts.lambdaSub]*subcount for _ in range(k)]
		phiTerm = [[opts.lambdaTerm]*termcount for _ in range(k)]
		userTermWeight = (1+(usercount)*opts.weightInitialTerm*max(math.exp(-iter*opts.decayTerm),opts.weightMinTerm)/traincount)
		userSubWeight = (1+(usercount)*opts.weightInitialSub*max(math.exp(-iter*opts.decaySub),opts.weightMinSub)/traincount)
		if opts.useTerms:
			#print "Estimating: Term"
			userterm = open(opts.filename_userterm,'rb')
			reader = csv.reader(userterm)
			for row in reader:
				uid = int(row[0])
				tid = int(row[1])
				if opts.supervised_mode:
					if udata[uid][3] <> 1:
						continue
				if uid in fold_ids:
					continue
				if not validTerms[tid]:
					continue
				value = float(row[2])
				cluster = udata[uid][0]
				if udata[uid][3]:
					phiTerm[cluster][tid]+=userTermWeight*value
				else:
					phiTerm[cluster][tid]+=value
			userterm.close()
			termSums = [0]*k
			for cluster in range(k):
				termSums[cluster] = sum(phiTerm[cluster])
				phiTerm[cluster] = divide(phiTerm[cluster],termSums[cluster])
			
		if opts.useSubs:
			#print "Estimating: Subreddit"
			usersub = open(opts.filename_usersub,'rb')
			reader = csv.reader(usersub)
			for row in reader:
				uid = int(row[0])
				if opts.supervised_mode:
					if udata[uid][3] <> 1:
						continue
				if uid in fold_ids:
					continue
				sid = int(row[1])
				if not validSubs[sid]:
					continue
				value = float(row[2])
				cluster = udata[uid][0]
				if udata[uid][3]:
					phiSub[cluster][sid]+=userSubWeight*value
				else:
					phiSub[cluster][sid]+=value
			usersub.close()	
			subSums = [0]*k
			for cluster in range(k):
				subSums[cluster] = sum(phiSub[cluster])
				phiSub[cluster] = divide(phiSub[cluster],subSums[cluster])
		#print "Maximization Step"
		#discovers components
		if opts.useTerms:
			#print "term step"
			userterm = open(opts.filename_userterm,'rb')
			reader = csv.reader(userterm)
			for row in reader:
				uid = int(row[0])
				tid = int(row[1])
				if not validTerms[tid]:
					continue
				value = float(row[2])
				for cluster in range(k):
					try:
						udata[uid][2][cluster]+=math.log(value*phiTerm[cluster][tid])*opts.termMultiplier
					except:
						print phiTerm[cluster][tid]
						print value
						print uid
						raise
			userterm.close()		
		if opts.useSubs:
			#print "sub step"
			usersub = open(opts.filename_usersub,'rb')
			reader = csv.reader(usersub)
			for row in reader:
				uid = int(row[0])
				sid = int(row[1])
				if not validSubs[sid]:
					continue
				value = float(row[2])
				for cluster in range(k):
					udata[uid][2][cluster]+=math.log(value*phiSub[cluster][sid])
			usersub.close()
		#calculates	probabilities and assigns values
		newPrior = [0]*k
		similarity = 0
		for uid in range(usercount):
			if uid in parsed_ids and uid not in fold_ids:
				newPrior[udata[uid][0]]+=1
				continue
			for cluster in range(k):
				if opts.clusterPriors == None:
					udata[uid][2][cluster]+=math.log(prior[cluster])
				else:
					udata[uid][2][cluster]+=math.log(opts.clusterPriors[cluster])
			udata[uid][2] = add(udata[uid][2],-max(udata[uid][2]))
			denominator = sum([math.exp(x) for x in udata[uid][2]])
			for cluster in range(k):
				udata[uid][1][cluster] = math.exp(udata[uid][2][cluster])/denominator
			
			newclus = whichmax(udata[uid][1])
			if udata[uid][0]==newclus:
				similarity+=1
			udata[uid][0]=newclus
			newPrior[newclus]+=1
		#resets counter for next iteration
		priors = divide(newPrior,sum(newPrior))
		if opts.changePriors:
			opts.clusterPriors = priors
		prettypriors = [round(x,4) for x in priors]
		#print "+++++++++++++++++++++++++++++"
		#print "Priors: " + str(prettypriors)
		#print "Similarity: " + str(round(float(similarity)/usercount,3))
		if iter <> opts.niter - 1:
			#each class gets its own subreddit probabilities
			phiSub = [[0]*subcount for _ in range(k)]
			phiTerm = [[0]*subcount for _ in range(k)]
			for uid in range(usercount):
				udata[uid][2] = [0]*k		
		#print "+++++Done with " + str(iter+1) + " iterations+++++"
	print "-----------------------------"
	#calculate cross-validation error
	ts = len(fold_clusts)
	deviances = [0]*ts
	for i in range(ts):
		deviances[i] = -2.*math.log(max((udata[i][1][fold_clusts[i]]),0.01))
	deviance = sum(deviances)/ts
	errors = [0]*k
	impurities = [0]*k
	predsizes = [0]*k
	sizes = [len(x[fold]) for x in traingroups]
	classmat = [[0]*k for i in range(k)]
	for i in range(len(fold_clusts)):
		classmat[fold_clusts[i]][udata[fold_ids[i]][0]]+=1
		predsizes[udata[fold_ids[i]][0]]+=1
		if fold_clusts[i]<>udata[fold_ids[i]][0]:
			errors[fold_clusts[i]]+=1
			impurities[udata[fold_ids[i]][0]]+=1
	#avoids divide by zero issues
	sizes = [max(0.01,x) for x in sizes]
	predsizes = [max(0.01,x) for x in predsizes]
	#print fold_clusts
	try:
		errors = [float(errors[i])/sizes[i] for i in range(len(errors))]
		impurities = [float(impurities[i])/predsizes[i] for i in range(k)]
	except:
		print sizes
		print predsizes
		raise
	print [round(x,3) for x in errors]
	print [round(x,3) for x in impurities]
	printmat(classmat)
	if opts.paramSelection:
		if opts.useTerms:
			try:
				newTermSigs = find_lowest_contrasts(rotate_mat(phiTerm),math.log(opts.paramFactor))
				for i in range(len(opts.forceTerms)):
					newTermSigs[opts.forceTerms[i]]=True
				validTerms = bitand(validTerms,newTermSigs)
			except:
				print len(validTerms)
				print len(newTermSigs)		
		if opts.useSubs:
			newSubSigs = find_lowest_contrasts(rotate_mat(phiSub),math.log(opts.paramFactor))
			for i in range(len(opts.forceSubs)):
				newSubSigs[opts.forceSubs[i]]=True
			validSubs = bitand(validSubs,newSubSigs)
	if opts.writefolds:
		filename_gs = opts.filename_fgs + str(fold)
		filename_gu = opts.filename_fgu + str(fold)
		filename_gt = opts.filename_fgt + str(fold)
		userout = open(filename_gu,'w')
		userids = open(opts.filename_uid,'r')
		userdict = shelve.open(opts.filename_userdict)
		if writeHeader:
			toprow = ['Id','Username','Clus']+pstrvec(range(k),'Prob')
			if writeHistory:
				toprow+=pstrvec(range(o.niter+1),'Step')
			userout.write(','.join(toprow)+'\n')
		print "OPENED USER INFO"
		for uid in range(usercount):
			user_rid = extract_row(userids.readline())
			username = str(userdict[user_rid][1]['AUTHOR_NAME'])
			line = [str(uid),username,str(udata[uid][0])]
			line = line + mstr(udata[uid][1])
			if writeHistory:
				line = line + stringvec(userHistory[uid])
			userout.write(','.join(line) + '\n')
		userdict.close()
		userout.close()
		userids.close()
		print "CLOSED USER INFO"
		#term
		if opts.useTerms:
			termout=open(filename_gt,'w')
			termids = open(opts.filename_tid,'r')
			if writeHeader:
				toprow = ['TermId']+pstrvec(range(k),'Prob')
				if writeHistory:
					toprow+=pstrvec(range(o.niter + 1),'Step')
				termout.write(','.join(toprow) + '\n')
			for tid in range(termcount):
				line = [str(tid)]
				line.append(extract_row(termids.readline()))
				if opts.paramSelection:
					if not validTerms[tid]:
						continue
				for cluster in range(k):
					line = line + [str(phiTerm[cluster][tid])]
				if writeHistory:
					line = line + stringvec(termHistory[tid])
				termout.write(','.join(line) + '\n')
			termout.close()
			termids.close()
			
		#sub
		if opts.useSubs:
			subout = open(filename_gs,'w')
			subids = open(opts.filename_sid,'r')
			if writeHeader:
				toprow = ['SubId'] + pstrvec(range(k),'Prob')
				if writeHistory:
					toprow+=pstrvec(range(o.niter + 1),'Step')
				subout.write(','.join(toprow) + '\n')
			for sid in range(subcount):
				line = [str(sid)]
				line.append(extract_row(subids.readline()))
				if opts.paramSelection:
					if not validSubs[sid]:
						continue
				for cluster in range(k):
					line = line + [str(phiSub[cluster][sid])]
				if writeHistory:
					line = line + stringvec(subHistory[sid])
				subout.write(','.join(line) + '\n')
			subout.close()
			subids.close()
	return [errors,classmat,deviance,list(validTerms),list(validSubs),impurities]

def find_lowest_contrasts(x,mindiff=math.log(2)):
	vec = [maxdiff(v)>mindiff for v in x]
	return vec
	
def rotate_mat(x):
	lx = len(x)
	ly = len(x[0])
	res = [[0]*lx for _ in range(ly)]
	for i in range(ly):
		for j in range(lx):
			res[i][j] = x[j][i]
	return res
	
	
def bitand(x,y):
	z = []
	for i in range(len(x)):
		z.append(x[i]&y[i])
	return z
	
def maxdiff(x,uselog=True):
	if not uselog:
		return max(x) - min(x)
	else:
		return math.log(max(x)) - math.log(min(x))

def mstr(x):
	return [str(y) for y in x]
		
def divide(vec,value):
	return [float(x)/value for x in vec]
	
def whichmax(vals):
	maximum = max(vals)
	return vals.index(maximum)
	
def add(vec,value):
	return [x + value for x in vec]

def rmnl(text):
	text=re.sub('\t',' ',text)
	return(re.sub('\n',' ',text))
	
def extract_row(line):
	element = line.split(',')[1]
	element = rmnl(element)
	return element
	
class options:
	def __init__(self):
		import genmod_params as o
		self.useTerms = o.useTerms
		self.useSubs = o.useSubs
		self.name = o.name
		self.termMultiplier = o.termMultiplier
		self.lambdaTerm = o.lambdaTerm
		self.lambdaSub = o.lambdaSub
		self.clusterClasses = o.clusterClasses
		self.nullClasses = o.nullClasses
		self.nclasses = o.nclasses
		self.nfolds = o.nfolds
		self.niter = o.niter
		self.weightInitialTerm = o.weightInitialTerm
		self.weightInitialSub = o.weightInitialSub
		self.decayTerm = o.decayTerm
		self.decaySub = o.decaySub
		self.weightMinTerm = o.weightMinTerm
		self.weightMinSub = o.weightMinSub
		self.clusterPriors = o.clusterPriors
		self.priorConfidence = o.priorConfidence
		self.k = self.nclasses
		#self.gridlength = len(o.weightInitialTerm)*len(o.weightInitialSub)*len(o.decayTerm)*len(o.decaySub)*len(o.lambdaTerm)*len(o.lambdaSub)*len(o.termMultiplier)*len(self.useTerms)*len(self.useSubs)*len(self.nfolds)
		name = o.name
		self.filename_userdict='user_'+name+'.dat'
		self.me_userdict_filename = 'me_user_' + name + '.dat'
		self.ngram_prefix='ngrams_'+name+'_Neq'
		self.filename_grand = 'grandsum_' + name + '.dat'
		self.filename_user_id = 'user_'+name+'.id'
		self.filename_sub_id = 'sub_'+name+'.id'
		self.filename_term_id = 'term_'+name+'.id'
		self.filename_sql = 'relations_'+name+'.db'
		self.filename_userdict = 'user_' + name + '.dat'
		#these are text files
		self.filename_uid = 'user_id_' + name + '.txt'
		self.filename_sid = 'sub_id_' + name + '.txt'
		self.filename_tid = 'term_id_' + name + '.txt'
		self.filename_gu = 'genmod_user_'+name+'.csv'
		self.filename_gs = 'genmod_sub_'+name+'.csv'
		self.filename_gt = 'genmod_term_'+name+'.csv'
		#for the n-fold results
		self.filename_fgu = 'genmod_user_'+name+'.fold'
		self.filename_fgs = 'genmod_sub_'+name+'.fold'
		self.filename_fgt = 'genmod_term_'+name+'.fold'
		self.writefolds = o.writefolds
		
		self.filename_usersub = 'usersub_' + name + '.txt'
		self.filename_userterm = 'userterm_' + name +'.txt'
		self.paramIter = o.paramIter
		self.paramFactor = o.paramFactor
		self.paramSelection = o.paramSelection
		self.changePriors = (o.clusterPriors=='train2')
		self.supervised_mode = o.supervised_mode
		self.ignoreSubs = o.ignoreSubs
		self.ignoreTerms = o.ignoreTerms
		self.forceSubs = o.forceSubs
		self.forceTerms = o.forceTerms
	def shift_self(self):
		pass
	def recursive_check(self,varname):
		pass

#cross-validation		
def xv_groups(assigned,nfolds,k):
		groups = [[[] for _ in range(nfolds)] for _ in range(k)]
		counters = [0]*k
		for i in range(len(assigned)):
			groups[assigned[i][1]][counters[assigned[i][1]] % nfolds].append(assigned[i][0])
			counters[assigned[i][1]]+=1
		return groups
	
def printmat(mat):
	for element in mat:
		print element

def colSum(mat,i):
	return sum([mat[j][i] for j in range(len(mat))])

#will be used to give idea of how well current classifiers work for dataset
def calculate_train_error(train_ids,user_data,phiTerm,phiSub,term_multiplier,filename_usersub,filename_userterm,useTerm,useSub):
	pass

#will be used to give idea of what an unsupervised estimation would give with
#the final partitions
def calculate_train_error_unweighted(train_ids,user_data,phiTerm,phiSub,term_multiplier,filename_usersub,filename_userterm,useTerm,useSub):
	pass

if __name__=='__main__':
	main(sys.argv[1:])
