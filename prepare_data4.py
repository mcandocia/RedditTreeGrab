# This file is part of RedditTreeGrab
#
#    RedditTreeGrab is free software: you can redistribute it and/or modify
#    it under the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RedditTreeGrab is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with RedditTreeGrab.  If not, see <http://www.gnu.org/licenses/>
#    and <http://www.gnu.org/licenses/lgpl.txt>.

#constructs necessary data files to begin EM algorithm
#requires running ngram analysis beforehand

#removed sql databases
#this version uses sql databases to solve memory issues

import math
import shelve
import sys
import numpy
import re
import time
import os
import sqlite3

LOG10 = math.log(10)

#-name [name of dataset]
#-age [maximum difference between grab date and comment]
#-select [filename of subreddit list]
#-skip {currently unused}
#-usepercent [scales numbers used for adding]

def main(argv):
	argvn=nargs('-N',argv,True)
	if '-name' in argv:
		name=argv[argv.index('-name')+1]
		filename_userdict='user_'+name+'.dat'
		me_userdict_filename = 'me_user_' + name + '.dat'
		ngram_prefix='ngrams_'+name+'_Neq'
		filename_grand = 'grandsum_' + name + '.dat'
		filename_user_id = 'user_'+name+'.id'
		filename_sub_id = 'sub_'+name+'.id'
		filename_term_id = 'term_'+name+'.id'
		#filename_sql = 'relations_'+name+'.db'
		#try just using a text file so that entries can be read a line at a time
		filename_usersub = 'usersub_' + name + '.txt'
		filename_userterm = 'userterm_' + name +'.txt'
		#these are text files
		filename_uid = 'user_id_' + name + '.txt'
		filename_sid = 'sub_id_' + name + '.txt'
		filename_tid = 'term_id_' + name + '.txt'
	usePercent = '-usePercent' in argv	
	if '-select' in argv:
		select_name = argv[argv.index('-select')+1]
		selection = import_wordlist(select_name)
	else:
		selection = None
	if '-negatives' in argv:
		useSign = True
	else:
		useSign = False
	print 'loaded options'
	userdict = shelve.open(filename_userdict)
	print 'opened userdict'
	me_userdict = dict()#shelve.open(me_useridict_filename)
	#open up ngram files to analyze
	ngram_names = []
	usernames = userdict.keys()
	usercount = 0
	cumsum=0
	usersub = open(filename_usersub,'w')
	userterm = open(filename_userterm,'w')
	print 'First round of processing'
	for user in userdict:
		me_userdict[user] = dict()
	for i in argvn:
		usercount=0
		print('Processing N='+str(i))
		ngf = open(ngram_prefix + str(i) +'.csv','r')
		line = ngf.readline()
		#print(line)
		line = re.sub('\n','',line)
		sline = line.split(',')
		for j in range(1,len(sline)):
			ngram_names.append(sline[j])	
		for user in usernames:
			#user count is same, but user is changed
			usercount+=1
			ukey = []
			line = ngf.readline()
			line = re.sub('\n','',line)
			sline = line.split(',')
			user = sline.pop(0)
			if 'ngram' not in me_userdict[user]:
				me_userdict[user]['ngram'] = dict()
			for j in range(0,len(sline)):
				if float(sline[j]) <> 0:
					me_userdict[user]['ngram'][ngram_names[j+cumsum]] = float(sline[j])
			if usercount % 5000 ==0:
				print("Preprocessed "+str(usercount) + ' users')
		cumsum=len(ngram_names)
		ngf.close()
	rm_if_exists(me_userdict_filename)
	mu = shelve.open(me_userdict_filename)
	mu['main']=me_userdict
	mu.close()
	print 'finished extracting all raw ngram values from users'
	#begin processing
	V = len(ngram_names)
	#print ngram_names
	subreddit_counts = dict()
	ngram_counts = dict()
	print 'Mapping user ids'
	usercount = 0
	rm_if_exists(filename_user_id)
	user_id = shelve.open(filename_user_id)
	user_ida = userdict.keys()
	user_text_id = open(filename_uid,'w')
	for user in userdict:
		user_id[user]=usercount
		user_text_id.write(str(usercount) + ',' + str(user) + ',' + str(userdict[user][1]['AUTHOR_NAME']) + '\n')
		usercount+=1
	user_text_id.close()
	print 'Mapping sub ids'
	rm_if_exists(filename_sub_id)
	sub_id = shelve.open(filename_sub_id)
	sub_ida = selection
	subcount = 0
	#modified 11-19-2014 to include negative scores as a separate subreddit
	if selection <> None:
		sub_text_id = open(filename_sid,'w')
		for sub in selection:
			sub_id[sub] = subcount
			if useSign:
				sub_id[sub+'?'] = subcount + 1
			sub_text_id.write(str(subcount) +',' +  sub + '\n')
			if useSign:
				sub_text_id.write(str(subcount+1) +',' + sub + '?' + '\n')
			subcount+=(1+useSign)
		sub_text_id.close()
	else:
		print 'Please limit subreddit selection!!!'
		time.sleep(1)
		sys.exit()
	print 'Mapping terms'
	rm_if_exists(filename_term_id)
	term_id = shelve.open(filename_term_id)
	term_ida = ngram_names
	term_text_id = open(filename_tid,'w')
	termcount=0
	for term in ngram_names:
		term_id[term]=termcount
		term_text_id.write(str(termcount) + ',' + term + '\n')
		termcount+=1
	term_text_id.close()
	print 'Finished mappings'
	UC = usercount
	SC = subcount
	TC = termcount
	usercount=0
	subcount=0
	termcount=0
	
	for uid in range(UC):
		#subreddit mapping
		subsum=0
		user = user_ida[uid]
		comments = userdict[user][0]
		subdict=dict()
		#raw processing
		for comment in comments:
			subreddit = comments[comment]['SUBREDDIT']
			if subreddit not in selection:
				continue
			#11-19-2014 made score linear and now included option to include sign of comment as a separate subreddit
			adder = math.log(abs(comments[comment]['COMMENT_SCORE'])+2)
			if comments[comment]['COMMENT_SCORE'] < 1 and useSign:
				subreddit =  subreddit + '?'
			if subreddit not in subdict:
				subdict[subreddit]=adder
			else:
				subdict[subreddit]+=adder
			subsum+=adder
		#final processing
		for sub in subdict:
			adder = subdict[sub]/max(subsum*usePercent,1)
			sid = sub_id[sub]
			usersub.write(','.join([str(uid),str(sid),str(adder)])+'\n')
		#term mapping
		termdict = dict()
		termsum = 0
		for term in me_userdict[user]['ngram']:
			adder = me_userdict[user]['ngram'][term]
			if term not in termdict:
				termdict[term]=adder
			else:
				termdict[term]+=adder
			termsum+=adder
		#final processing
		for term in me_userdict[user]['ngram']:
			adder = float(termdict[term])/max(termsum*usePercent,1)
			tid = term_id[term]
			userterm.write(','.join([str(uid),str(tid),str(adder)])+'\n')
		if (uid+1)%2500==0:
			print 'Processed '+str(uid+1)+' users'
	print 'Finished processing'
	userterm.close()
	usersub.close()

	#user_id['id'] = user_ida
	user_id.close()
	#sub_id['id'] = sub_ida
	sub_id.close()
	#term_id['id'] = term_ida
	term_id.close()
	#database.commit()
	#d.close()
	#database.close()
	print "COMPLETE"
	
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

#debugged
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

def rm_if_exists(file):
	if os.path.isfile(file):
		print 'Overwriting '+file
		os.remove(file)
if __name__=='__main__':
	main(sys.argv[1:])
