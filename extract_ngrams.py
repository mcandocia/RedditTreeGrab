#ngram algorithm

filename_stopwords='stopwords.txt'
#currently disabled inner stopwords, so this file has no effect
filename_joinwords='joinwords.txt'
filename_bijoinwords='bigramjoinwords.txt'
filename_userdict='user_dictionary_custom03.dat'
filename_userout_prefix='ngram_user_Neq'
ngram_prefix='ngrams_01_Neq'
stdev_cutoff=1.3
MAX_WORD_LENGTH=30
#adds this value to the cutoff value for minimum required ngram counts
cutoff_raw_adder=25
#adjust this so that you don't need to repeat the process of remaking certain levels of ngrams over and over again
#N_values_to_skip=[1]

#currently set to unigrams, bigrams, and trigrams
n_max=2

#MAX_WORD_LENGTH=30



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
	text=re.sub('[^a-zA-Z ]','',text)
	return(text)

def remove_long_spaces(text):
	text=re.sub('[ ]{2,}',' ',text)
	return(text)
	
def cleanse_text(text):
	text=removeNonAscii(text)
	text=rmnl(text)
	text=AlphaOnly(text)
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
	
	
	
def main(argv):
	argvn = nargs('-N',argv,True)
	if '-name' in argv:
		name=argv[argv.index('-name')+1]
		filename_userdict='user_'+name+'.dat'
		ngram_prefix='ngrams_'+name+'_Neq'
	if '-select' in argv:
		select_name = argv[argv.index('-select')+1]
		selection = import_wordlist(select_name)
	if '-age' in argv:
		age = int(argv[argv.index('-age')+1])
	else:
		age = None
	stopwords=import_wordlist(filename_stopwords)
	joinwords=import_wordlist(filename_joinwords)
	bijoinwords=import_wordlist(filename_bijoinwords)
	user_dict=shelve.open(filename_userdict)
	for arg in argvn:
		analyze_ngrams(int(arg),user_dict,stopwords,joinwords,bijoinwords,selection,ngram_prefix,age)
	user_dict.close()
	print("FINISHED WITH ALL NGRAMS")
	
	
	
def analyze_ngrams(N,user_dict,stopwords,joinwords,bijoinwords,selection,ngram_prefix,age):
	if N==1:
		analyze_unigrams(user_dict,stopwords,selection,ngram_prefix,age)
		return()
	print("STARTING WITH N="+str(N))
	#ngram_dict=dict()
	outer_stopwords=[]
	inner_stopwords=[]
	for word in stopwords:
		if word not in bijoinwords:
			outer_stopwords.append(word)
		if word not in joinwords:
			inner_stopwords.append(word)
	outer_stopwords.append(' ')
	inner_stopwords.append(' ')
	outer_stopwords.append('')
	inner_stopwords.append('')
	nusers=0
	new_userdict=dict()##
	ngram_file=shelve.open(ngram_prefix+str(N)+'.ngram')
	print("loaded ngram list")
	ngk = ngram_file.keys()
	ngram_file.close()
	#ncomments=0
	for user in user_dict:
		nusers+=1
		comments=user_dict[user][0]
		new_userdict[user] = dict()##
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
			#ncomments+=1
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
					#elif current_word in inner_stopwords:
						#skip_ngram=True
						#break
				if skip_ngram:
					continue
				ngram_string=' '.join(current_ngram)
				if ngram_string not in ngk:
					continue
				if ngram_string in comment_dict:
					new_userdict[user][ngram_string] +=1##
					continue
				comment_dict[ngram_string]=1
				new_userdict[user][ngram_string] = 1##
				#if ngram_string in ngram_dict:
				#	ngram_dict[ngram_string]+=1
				#else:
				#	ngram_dict[ngram_string]=1
		if nusers%100==0:
			print('Users parsed: '+str(nusers))
	ngram_file=shelve.open(ngram_prefix+str(N)+'.ngram')
	print("WRITING NGRAM CSV")
	ngk = ngram_file.keys()
	ngram_file.close()
	csv_filename = ngram_prefix + str(N) + '.csv'
	csvf = open(csv_filename,'w')
	csvf.write('REDDIT_USERNAME,' + str(ngk)[1:(len(str(ngk))-1)]+'\n')
	ustring = ngram_prefix[7:-4]
	print(ustring)
	old_userdict = shelve.open('user_'+ustring+'.dat')
	for user in new_userdict:
		uf = new_userdict[user]
		if False:#this can be changed depending on the purpose
			csvf.write(old_userdict[user][1]['AUTHOR_NAME'])
		else:#this is preferred when usernames are displayed in a more formal environment
			csvf.write(user)
		for gram in ngk:
			if gram in uf:
				csvf.write(',' + str(uf[gram]))
			else:
				csvf.write(',0')
		csvf.write('\n')
	old_userdict.close()
	csvf.close()
	print("WROTE CSV")
	return()
					
			
	
	
def analyze_unigrams(user_dict,stopwords,selection,ngram_prefix,age):
	#stopwords=import_stopwords(filename_stopwords)
	print("STARTING UNIGRAM-DETECTING")
	#worddict=shelve.open(ngram_prefix+'1.ngram')
	if ' ' not in stopwords:
		stopwords.append(' ')
	nusers=0
	ncomments=0
	temp_ngram_dict=dict()
	new_userdict=dict()##
	for user in user_dict:
		nusers+=1
		new_userdict[user] = dict()##
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
					new_userdict[user][word] +=1
					continue
				if len(word)>MAX_WORD_LENGTH:
					continue
				comment_dict[word]=1
				if str(word) not in new_userdict[user]:
					new_userdict[user][str(word)] =1
					#temp_ngram_dict[word]=1
				else:
					new_userdict[user][str(word)]+=1
		if nusers%100==0:
			print('users parsed: ' + str(nusers))
	#user_dict.close()
	print('Number of users: ' + str(nusers))
	print('Number of comments: ' + str(ncomments))
	print("Writing NGRAM CSV")
	ngram_file = shelve.open(ngram_prefix + '1.ngram')
	ngk = ngram_file.keys()
	ngram_file.close()
	csv_filename = ngram_prefix+'1.csv'
	csvf = open(csv_filename,'w')
	csvf.write('REDDIT_USERNAME,' + str(ngk)[1:(len(str(ngk))-1)]+'\n')
	ustring = ngram_prefix[7:-4]
	print(ustring)
	old_userdict = shelve.open('user_'+ustring+'.dat')
	for user in new_userdict:
		uf = new_userdict[user]
		if False:
			csvf.write(old_userdict[user][1]['AUTHOR_NAME'])
		else:
			csvf.write(user)
		for gram in ngk:
			if gram in uf:
				csvf.write(',' + str(uf[gram]))
			else:
				csvf.write(',0')
		csvf.write('\n')
	csvf.close()
	old_userdict.close()
	print("WROTE CSV")
	#worddict.close()
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


if __name__=='__main__':
	main(sys.argv[1:])
