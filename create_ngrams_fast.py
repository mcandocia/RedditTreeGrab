#ngram algorithm

filename_stopwords='stopwords.txt'
#currently disabled inner stopwords, so this file has no effect
filename_joinwords='joinwords.txt'
filename_bijoinwords='bigramjoinwords.txt'
filename_userdict='user_dictionary_custom04.dat'
ngram_prefix='ngrams_ZMOD_Neq'
stdev_cutoff=1.4
MAX_WORD_LENGTH=22
#adds this value to the cutoff value for minimum required ngram counts
cutoff_raw_adder=3
cutoff_size_factor=0.00001#per-comment - 10/M currently

#MAX_WORD_LENGTH=30s

import re
import os
import shelve
import math
import sys

def removeNonAscii(s): 
	return "".join(i for i in s if ord(i)<128)

def nwords(text):
	return(len(re.split(' ',text)))

#removes tabs and newlines so that data files can be easily written
def rmnl(text):
	text=re.sub('\t',' ',text)
	return(re.sub('\n',' ',text))
	
def AlphaOnly(text):
	text=re.sub('[^a-zA-Z \-]','',text)
	return(text)

def AlphaNumericOnly(text):
	text=re.sub('[^0-9a-zA-Z \-]','',text)
	return(text)

def remove_long_spaces(text):
	text=re.sub('[ ]{2,}',' ',text)
	return(text)
	
def cleanse_text(text):
	text=removeNonAscii(text)
	text=rmnl(text)
	text=AlphaNumericOnly(text)
	text=remove_long_spaces(text)
	return(text)

def import_wordlist(filename_stopwords):
	stopwords_file=open(filename_stopwords,'r')
	stopwords=[]
	while True:
		current_word=re.sub('\n','',stopwords_file.readline())
		current_word=re.sub('[^a-zA-Z_]','',current_word)
		if current_word=='':
			break
		if current_word not in stopwords:
			stopwords.append(current_word)
	stopwords_file.close()
	return(stopwords)
	
	
#forcelist added so that fringe phrases may be forced in for 
#purposes of giving certain groups proper chances for having significant
#terms	
def main(argv):
	argvn=nargs('-N',argv,True)
	if '-cutoff' in argv:
		cutoffs = nargs('-cutoff',argv,True)
	else:
		cutoffs = None
	#for arg in argv:
	#	if re.search('[^0-9]',arg)==None:
	#		argvn.append(int(arg))
	if '-name' in argv:
		name=argv[argv.index('-name')+1]
		filename_userdict='user_'+name+'.dat'
		ngram_prefix='ngrams_'+name+'_Neq'
	if '-select' in argv:
		select_name = argv[argv.index('-select')+1]
		selection = import_wordlist(select_name)
	else:
		selection = []
	if '-age' in argv:
		age = int(argv[argv.index('-age')+1])
	else:
		age = None
	if '-force' in argv:
		filename_forcelist = argv[argv.index('-force') + 1]
		forcelist = create_forcelist(filename_forcelist,argvn)
	else:
		forcelist = None
	suppress_search = '-suppress' in argv
	print filename_userdict
	stopwords=import_wordlist(filename_stopwords)
	#print stopwords
	#raise
	joinwords=import_wordlist(filename_joinwords)
	bijoinwords=import_wordlist(filename_bijoinwords)
	user_dict=shelve.open(filename_userdict)
	for arg in argvn:
		create_ngrams(int(arg),user_dict,stopwords,joinwords,bijoinwords,ngram_prefix,selection,cutoffs,age,forcelist,suppress_search)
	user_dict.close()
	print("FINISHED WITH ALL NGRAMS")
	
	
	
def create_ngrams(N,user_dict,stopwords,joinwords,bijoinwords,ngram_prefix,selection,cutoffs,age,forcelist,suppress_search):
	if N==1:
		create_unigrams(user_dict,stopwords,ngram_prefix,selection,cutoffs,age,forcelist,suppress_search)
		return()
	print("STARTING WITH N="+str(N))
	ngram_dict=dict()
	outer_stopwords=[]
	inner_stopwords=[]
	nusers=0
	ncomments=0
	reductcount=0
	if not suppress_search:
		for word in stopwords:
			if word not in bijoinwords:
				outer_stopwords.append(word)
			if word not in joinwords:
				inner_stopwords.append(word)
		outer_stopwords.append(' ')
		inner_stopwords.append(' ')
		outer_stopwords.append('')
		inner_stopwords.append('')
		for user in user_dict:
			nusers+=1
			comments=user_dict[user][0]
			user_retrieved = user_dict[user][1]['RETRIEVED']
			for comment in comments:
				if selection <> []:
					if comments[comment]['SUBREDDIT'] not in selection:
						continue
				if age <> None:
					if float(user_retrieved-comments[comment]['COMMENT_CREATED'])/(3600*24)>age:
						continue
				comment_text=comments[comment]['COMMENT_TEXT']
				comment_text=cleanse_text(comment_text)
				comment_text=str(comment_text.lower())
				words=re.split(' ',comment_text)
				comment_dict=dict()#used to filter out replicates within a comment
				ncomments+=1
				nwords=len(words)
				for i in range(0,nwords-N+1):
					current_ngram=[]
					skip_ngram=False
					for u in range(i,i+N):
						current_word=words[u]
						if (len(current_word)>MAX_WORD_LENGTH):
							skip_ngram=True
							break
						current_ngram.append(current_word)
						if u in [i,i+N-1] and current_word in outer_stopwords:
							skip_ngram=True
							break
					if skip_ngram:
						continue
					ngram_string=' '.join(current_ngram)
					if ngram_string in comment_dict:
						continue
					comment_dict[ngram_string]=1
					if ngram_string in ngram_dict:
						ngram_dict[ngram_string]+=1
					else:
						ngram_dict[ngram_string]=1
			if nusers%1000==0:
				print('Users parsed: '+str(nusers))
			#this will prevent memory issues
			if len(ngram_dict) > 100000:
				ngram_dict = reduce_dict(ngram_dict,2)
				reductcount+=1
	ngf = ngram_prefix+str(N)+'.ngram'
	if os.path.isfile(ngf):
		print 'Overwriting old file'
		os.remove(ngf)
	ngram_file=shelve.open(ngram_prefix+str(N)+'.ngram')
	n_ngrams=0
	sum_ngrams=0
	sumsquared_ngrams=0
	#gets rid of annoying repeated ngrams; currently disabled
	if False:
		for ngram in ngram_dict:
			ngram_words=re.split(' ',ngram)
			all_same=True
			first_word=ngram_words[0]
			for i in range(1,N-1):
				if ngram_words[i] <> first_word:
					all_same=False
					break
			if all_same:
				ngram_dict.pop(ngram,None)
	dictsave = shelve.open(ngram_prefix+str(N)+'.ngramB')
	dictsave['dict'] = ngram_dict
	dictsave.close()
	if cutoffs==None and not suppress_search:
		for ngram in ngram_dict:
			n_ngrams+=1
			val=ngram_dict[ngram]
			sum_ngrams+=val
			sumsquared_ngrams+=pow(val,3)
		standard_deviation=math.sqrt(sumsquared_ngrams/n_ngrams-pow(sum_ngrams/n_ngrams,2))
		cutoff_value=sum_ngrams/n_ngrams+standard_deviation*stdev_cutoff+cutoff_raw_adder+cutoff_size_factor*ncomments/pow(N-1,3)
		print('mean: '+str(sum_ngrams/n_ngrams))
		print('standard deviation: '+str(standard_deviation))
		print('cutoff value: '+str(cutoff_value))
		for ngram in ngram_dict:
			if ngram_dict[ngram]>cutoff_value:
				ngram_file[ngram]=ngram_dict[ngram]
	elif not suppress_search:
		ngramvals = []
		for gram in ngram_dict:
			ngramvals.append(ngram_dict[gram])
		ngramvals.sort()
		ngramvals[:] = ngramvals[::-1]
		cutoff_val = ngramvals[cutoffs[N-1]]-1
		for gram in ngram_dict:
			if ngram_dict[gram] > cutoff_val:
				ngram_file[gram] = ngram_dict[gram]
	#adds forced entries
	forcecount = 0
	if forcelist <> None:
		elements = forcelist[N-1]
		for gram in elements:
			if gram not in ngram_file:
				ngram_file[gram] = 1
				forcecount+=1
	print("TOTAL ENTRIES: "+str(len(ngram_file)))
	print("FINISHED WITH N="+str(N))
	print "TRUNCATED DICTIONARY " + str(reductcount) + " times"
	print "Forced " + str(forcecount) + " ngrams into dictionary"
	ngram_file.close()
	return()
					
#this method will remove entries with too few hits and also
#reduce the count for all elements to avoid bias in data position			
def reduce_dict(dictionary, nmin):
	newdict = dict()
	dk = dictionary.keys()
	dkl = len(dk)
	for item in dk:
		if dictionary[item] >= nmin:
			newdict[item] = dictionary[item]-1
	newl = len(newdict)
	#print('reduce dict from '+str(dkl)+' to '+str(newl))
	return newdict
	
def create_unigrams(user_dict,stopwords,ngram_prefix,selection,cutoffs,age,forcelist,suppress_search):
	#stopwords=import_stopwords(filename_stopwords)
	print("STARTING UNIGRAM-DETECTING")
	ngf = ngram_prefix+str(1)+'.ngram'
	if os.path.isfile(ngf):
		print 'Overwriting old file'
		os.remove(ngf)
	worddict=shelve.open(ngram_prefix+'1.ngram')
	nusers=0
	ncomments=0
	temp_ngram_dict=dict()
	reductcount=0
	if not suppress_search:
		if ' ' not in stopwords:
			stopwords.append(' ')
		for user in user_dict:
			nusers+=1
			comments=user_dict[user][0]
			user_retrieved = user_dict[user][1]['RETRIEVED']
			for comment in comments:
				if selection <> []:
					if comments[comment]['SUBREDDIT'] not in selection:
						continue
				if age <> None:
					if float(user_retrieved-comments[comment]['COMMENT_CREATED'])/(3600*24)>age:
						continue
				comment_text=comments[comment]['COMMENT_TEXT']
				comment_text=cleanse_text(comment_text)
				comment_text=str(comment_text.lower())
				comment_dict=dict()
				words=re.split(' ',comment_text)
				ncomments+=1
				for word in words:
					word=str(word)
					if word in comment_dict:
						continue
					if len(word)>MAX_WORD_LENGTH:
						continue
					comment_dict[word]=1
					if str(word) not in temp_ngram_dict:
						temp_ngram_dict[word]=1
					else:
						temp_ngram_dict[word]+=1
			if nusers%1000==0:
				print('users parsed: ' + str(nusers))
			if len(temp_ngram_dict)>125000:
				temp_ngram_dict = reduce_dict(temp_ngram_dict,5)
				reductcount+=1
	#user_dict.close()
	print('Number of users: ' + str(nusers))
	print('Number of comments: ' + str(ncomments))
	nwords=0
	sumfreq=0
	sumsquarefreq=0
	temp_ngram_dict.pop('',None)#there is probably '' in the dictionary
	#this might be a faster way of parsing through this
	if cutoffs==None and not suppress_search:
		for word in stopwords:
			temp_ngram_dict.pop(word,None)
		for word in temp_ngram_dict:
			val=temp_ngram_dict[word]
			nwords+=1
			sumfreq+=val
			sumsquarefreq+=pow(val,2)
		print('nwords: '+str(nwords))
		print('total: ' + str(sumfreq))
		print('sum square: ' + str(sumsquarefreq))
		standard_deviation=math.sqrt(sumsquarefreq/nwords-pow(sumfreq/nwords,2))
		cutoff_value=sumfreq/nwords+standard_deviation*stdev_cutoff+cutoff_raw_adder
		print('mean: '+str(sumfreq/nwords))
		print('standard deviation: '+str(standard_deviation))
		print('cutoff value: ' + str(cutoff_value))
		#super_high_value=cutoff_value*2+math.sqrt(sumsquarefreq/nwords)*3
		ncuts=0
		for word in temp_ngram_dict:
			if temp_ngram_dict[word]>cutoff_value:
				worddict[word]=temp_ngram_dict[word]
	elif not suppress_search:
		for word in stopwords:
			temp_ngram_dict.pop(word,None)
		ngramvals = []
		for gram in temp_ngram_dict:
			ngramvals.append(temp_ngram_dict[gram])
		ngramvals.sort()
		ngramvals[:] = ngramvals[::-1]
		cutoff_val = ngramvals[cutoffs[0]]-1
		for gram in temp_ngram_dict:
			if temp_ngram_dict[gram] > cutoff_val:
				worddict[gram] = temp_ngram_dict[gram]
	forcecount = 0
	if forcelist <> None:
		elements = forcelist[0]
		for gram in elements:
			if gram not in worddict:
				worddict[gram] = 1
				forcecount+=1
	print "Forced " + str(forcecount) + " unigrams into dictionary"
	print("TOTAL UNIGRAMS: "+str(len(worddict)))
	print "REDUCED DICTIONARY " + str(reductcount) + " times"
	worddict.close()
	print("FINISHED CREATING WORDLIST")
	
def nargs(name,args,apply_int):
	mindex=args.index(name)+1
	arglist=[]
	while(mindex<len(args) and re.search('^-',args[mindex])==None):
		if apply_int:
			arglist.append(int(args[mindex]))
		else:
			arglist.append(str(args[mindex]))
		mindex+=1
	return(arglist)

def create_forcelist(filename_forcelist,argvn):
	forcelist = [[] for _ in range(max(argvn))]
	nmax = len(forcelist)
	with open(filename_forcelist,'r') as f:
		for line in f:
			line = AlphaOnly(line)
			n = nwords(line)
			if n<=nmax:
				forcelist[n-1].append(line)
	return forcelist

if __name__=='__main__':
	main(sys.argv[1:])
