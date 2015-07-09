#builds user-user links using thread data
#user ids should be extracted from the user dictionary prior
#later versions will have the option to exclude user_dict data from the start

import shelve
import csv
import os
import sys
import sqlite3
import time
import math


#child	parent	comment_id	thread_id	comment_score	top_level_comment	[sign]

def main(args):
	options = option(args)
	construct_thread_network(options)
	print "Fin"

#this will analyze a thread and 	
def construct_thread_network(options):
	print 'BEGINNING THREAD CONSTRUCTION'
	threaddict = shelve.open(options.filename_threaddict)
	tks = threaddict.keys()
	thread_id = 0
	sub_map = shelve.open(options.filename_sub_id)
	user_map = shelve.open(options.filename_user_id)
	thread_comment_map = open(options.filename_commentthread,'w')
	thread_sub_map = open(options.filename_threadsub,'w')
	comment_id = 0
	missingauthors = []
	self_responses = 0
	notfoundcounter=0
	thread_comment_map.write(options.header)
	negative_counter = 0
	for tk in tks:
		#first collect all user ids
		uids = set()
		author_id = str(threaddict[tk][1]['AUTHOR_ID'])
		if len(author_id)<9:
			uids.add(author_id)
		thread = threaddict[tk][0]
		subreddit = threaddict[tk][1]['SUBREDDIT']
		sid = sub_map[subreddit]
		#this should substantially reduce the time for processing
		for comment in thread:
			temp_uid = str(thread[comment]['AUTHOR_ID'])
			if temp_uid not in uids and temp_uid <> 'NO_AUTHOR_ID':
				uids.add(temp_uid)
		uid_map = []
		breakloop = False
		for uid in uids:
			try:
				uid_map.append((uid,user_map[uid]))
			except:
				print "ERROR"
				print threaddict[tk][1]
				for comment in thread:
					if uid == str(thread[comment]['AUTHOR_ID']):
						print 'hi'
						missingauthors.append(str(thread[comment]['AUTHOR_NAME']))
						print str(thread[comment])
						breakloop = True
				print ':('
		if breakloop:
			continue
		#this will store negative id's by index
		neglocations = dict()
		#go through comments
		for comment in thread:
			is_toplevel = 0
			raw_comment = thread[comment]
			parent = match_parent(raw_comment,thread)
			comment_score = (raw_comment['SCORE'])
			if comment_score == None:
				comment_score = 0
			if str(parent) == '-1':
				is_toplevel = 1
				if options.noauthor:
					parent_id = str(threaddict[tk][1]['SUBREDDIT'])
					#continue
				else:
					parent_id = author_id
					parent_id = map_match(parent_id,uid_map)
			elif parent <> -2:
				parent_comment = thread[parent]
				parent_id = map_match(parent_comment['AUTHOR_ID'],uid_map) 
			else:
				parent_id = '-2'
				notfoundcounter+=1#I don't think this should ever happen
			node_id = map_match(str(raw_comment['AUTHOR_ID']),uid_map)
			#assigns unique negative indices to unidentified nodes
			if parent_id in ['-2','-1',-1,-2]:
				if options.skipmissing:
					continue
				ploc = parent_location(raw_comment,thread)
				if ploc in neglocations:
					parent_id = neglocations[ploc]
				else:
					parent_id = str(-1-negative_counter)
					negative_counter+=1
					neglocations[ploc] = parent_id
			if node_id in ['-2','-1',-1,-2]:
				if options.skipmissing:
					continue
				loc = str(raw_comment['COMMENT_LOCATION'])			
				if loc in neglocations:
					node_id = neglocations[loc]
				else:
					node_id = str(-1-negative_counter)
					neglocations[loc] = node_id
					negative_counter+=1	
			#modifies comment score
			new_score = comment_score
			scoresign = -1 + 2*(new_score > 0)
			if options.writeSign:
				signstring = ',' + str(scoresign)
			else:
				signstring = ''
			new_score = max(new_score,options.floor)
			if options.usemag:
				new_score = abs(new_score)
			new_score = new_score + options.add
			if options.uselog:
				new_score = math.log(new_score)
			#writes
			thread_comment_map.write(','.join([str(node_id),str(parent_id),str(comment_id),str(thread_id),str(new_score),str(is_toplevel)])+','+subreddit+signstring+'\n')
			comment_id+=1
			if str(node_id)==str(parent_id):
				self_responses+=1
			if comment_id % 10000 == 0:
				print "Parsed " + str(comment_id) + ' comments'
		thread_sub_map.write(str(thread_id) + ',' + str(sid) + '\n')
		thread_id+=1
		if thread_id % 500 == 0:
			print "Parsed " + str(thread_id) + ' threads'
	print missingauthors
	print "Finished threads"
	print "TOTAL THREADS: " + str(thread_id)
	print "TOTAL COMMENTS: " + str(comment_id)
	print "SELF-RESPONSES: " + str(self_responses)
	print "TOTAL NOT FOUND: " + str(notfoundcounter)
	thread_comment_map.close()
	thread_sub_map.close()
	sub_map.close()
	user_map.close()
	threaddict.close()
	print "Closed files"
	
#matches a comment to its parent
def match_parent(comment,thread):
	comment_location = comment['COMMENT_LOCATION']
	parent_location = list(comment_location)#dereference
	lnn = last_nn(parent_location)
	try:
		parent_location[lnn] = -1
	except:
		print parent_location
		print lnn
		raise
	if parent_location[0] == -1:
		return -1#indicates root node
	for ocomment in thread:
		if thread[ocomment]['COMMENT_LOCATION']==parent_location:
			return ocomment
	#print 'No parent found'#may want to delete
	return -2
	
def parent_location(comment,thread):
	comment_location = comment['COMMENT_LOCATION']
	parent_location = list(comment_location)
	lnn = last_nn(parent_location)
	parent_location[lnn] = -1
	return str(parent_location)

def map_match(id,map):
	for element in map:
		if element[0]==id:
			return element[1]
	return -1
	
	
	
def last_nn(array):
	if not -1 in array:
		return len(array)-1
	return(array.index(-1)-1)

#-edate: selects date range for threads to be used
#-name: name of dataset
#-noauthor: does not designate an author of the post as a node, and instead 
##treats each post as a unique author
#-floor sets minimum value link weight can be
#-mag takes the magnitude of score values
#-add adds a raw value to a score values
#-uselog uses a log transformation to score values; recommend using floor and/or mag 
##in combination with this
#-sign creates another variable that records the sign of a comment's score
class option:
	def __init__(self,args):
		print 'Creating options'
		if '-edate' in args:
			self.edate = nargs('-edate',apply_float=True)
		else:
			self.edate=None
		if '-name' in args:
			name = args[args.index('-name')+1]
			self.filename_userdict='user_'+name+'.dat'
			self.me_userdict_filename = 'me_user_' + name + '.dat'
			self.ngram_prefix='ngrams_'+name+'_Neq'
			self.filename_threaddict = 'thread_' + name + '.dat'
			self.filename_grand = 'grandsum_' + name + '.dat'
			self.filename_user_id = 'user_'+name+'.id'
			self.filename_sub_id = 'sub_'+name+'.id'
			self.filename_term_id = 'term_'+name+'.id'
			self.filename_commentuser = 'commentuser_' + name + '.net'
			self.filename_commentsub = 'commentsub_' + name + '.net'
			self.filename_commentreplies = 'replies' + name + '.net'
			self.filename_commentthread = 'commentthread_' + name + '.net'
			self.filename_threadsub = 'filename_threadsub_' + name + '.net'
			self.filename_sql = 'relations_' + name +'.db'
		else:
			print "PLEASE ENTER NAME"
			sys.exit()
		if '-noauthor' in args:
			print 'Author of post not considered'
			self.noauthor = True
		else:
			print 'Author of post being used'
			self.noauthor = False
		#currently unused
		if '-cterm' in args:
			self.ngram_to_comment = True
		else:
			self.ngram_to_comment = False
		#currently unused
		if '-nothread' in args:
			print 'Skipping thread-analysis step'
			self.nothread = True
		else:
			self.nothread = False
		if '-floor' in args:
			print 'Modifying floor function'
			self.floor = float(args[args.index('-floor')+1])
		else:
			self.floor = -100
		if '-usemag' in args:
			print 'Using magnitude'
			self.usemag = True
		else:
			self.usemag = False
		if '-uselog' in args:
			self.uselog=True
		else:
			self.uselog = False
		if '-add' in args:
			self.add = float(args[args.index('-add')+1])
		else:
			self.add = 0
		self.writeSign = '-sign' in args
		if '-header' in args:
			headerargs=['Source','Target','comment_id','thread_id','score','toplevel','subreddit']
			if self.writeSign:
				headerargs+=['sign']
			self.header = ','.join(headerargs) + '\n'
		else:
			self.header = ''
		self.skipmissing = '-skip' in args
	

def nargs(name,args,apply_float):
	mindex=args.index(name)+1
	arglist=[]
	while(mindex<len(args) and re.search('^-',args[mindex])==None):
		if apply_int:
			arglist.append(float(args[mindex]))
		else:
			arglist.append(float(args[mindex]))
		mindex+=1
	return(arglist)
		
def extract_lines(filename):
	file=open(filename,'r')
	objs=[]
	while True:
		nextobj=re.sub('[\n\r]','',file.readline())
		if nextobj=='':
			break
		else:
			objs+=[nextobj]
	return(objs)		
	

if __name__=='__main__':
	main(sys.argv[1:])