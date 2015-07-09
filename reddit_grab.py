#CREATED BY MAX CANDOCIA
#Copyright 2014, 2015

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








#UPDATED JULY 2015
#THIS WILL SCRAPE A REDDIT PAGE AND THEN WRITE IT TO A READABLE FILE
#SHELVE FILES ARE THE CURRENT IMPLEMENTATION, AS SQL DATABASES
#MAY NOT BE OPTIMAL DEPENDING ON THE LEVEL OF DETAIL YOU DESIRE
#IT CAN ALSO TRACK DIFFERENT USERS AND SUBREDDITS
#WITH CUSTOMIZED OPTIONS AVAILABLE 
#(ALTHOUGH NOT FULLY IMPLEMENTED FOR EACH OPTION)
#different types of imports will be used

####options
#-ou: overwrite users; 1-hour delay before you can do this
#-ot: overwrite threads; 1-hour delay before you can do this
#-overshoot: goes past comments for already-scraped users; useful if
##doing final run with large history collection
#-random: randomized selection
#-sub: followed by subreddits to scrape
#-fsub: followed by filename containing subreddits to scrape
#-date: followed by type of date to analyze (i.e., hour, day, week, month, year, all)
#-edate: followed by range in days that posts should be drawn from 
#-n: followed by integer limit for how many posts to grab; if excluded, will scrape indefinitely
#-u: followed by list of users to scrape
#-fu: followed by filename of line-separated users to scrape
#-ux: if -u or -fu is specified, will analyze each thread user is in; takes a long time to run, usually
#-name: specify part of the name of the file; THIS IS IMPORTANT
#-depth: followed by how far back in someone's comment history you should go
#-nouser: use this if you do not want to gather any user data (a shelve file is still made, but it will be empty)
#-type: followed by type of random post to get for subreddits (hot, new, top, rising, etc.); not every option works with every date combination (although some do)
#-tree: followed by integers representing how far in tree depth you want to go to view comments
#-mw: followed by minimum words for a comment
#-fi: followed by file containing ids of posts to scrape
#-top: for subreddit-based queries, the number following this will get one of the top [this number] posts from that subreddit for the type specified
#-norandom: This option significantly speeds up data gathering by always scraping the earliest post that fits the criteria instead of choosing one randomly
#-mergetime: this precedes a float value indicating how many days must pass before an author's history is regathered, and new comments are added to the old
#-grabauthors: In case you forgot to use -getauthor before, you can specify this argument to regather all author data (provided it still exists)
#-getauthor:  This will get the authors for each post grabbed
#-rescrapeposts: This will load all existing post ids into ids of submissions to scrape.  This is useful if you want to continuously monitor
#-rescrapeusers: This will load all existing users from the dictionary and regather information.  This is somewhat expensive to do, so it is not recommended unless something like follow-up data is needed
#-queue: This will store all users in a set file before scraping in order to avoid
#-timefloor: This is a parameter used when you are rescraping all previous users.  It is a
##boundary used for user retrieval times so that you do not have to redo all users
##if you need to stop the scraper (forseeable with very large files

##issues with constantly changing threads (which cause errors with infinite recursion);
##note: issues with recursion currently fixed
VERSION = 'JUL 06 2015, 19:26'

import re
import os
import praw
import time
import shelve
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ConnectionError
from exceptions import UnicodeDecodeError
from exceptions import IndexError
from exceptions import AttributeError
import time
import calendar
import sys
import random
import socket
from socket import AF_INET, SOCK_DGRAM

#default names if none specified
filename_userdict='user_dictionary_custom04.dat'
filename_threaddict='thread_dictionary_custom04.dat'

infinite_loop_catcher=0



def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def nwords(text):
	return(len(re.split(' ',text)))

#removes tabs and newlines so that data files can be easily written
def rmnl(text):
	text=re.sub('\t',' ',text)
	return(re.sub('\n',' ',text))
	

	

#id = page id
#filename = desired filename for object
#bot = praw bot used to grab information
def grab_page(id,filename,bot):
	pass#submission=bot.get_submission()
	

	
#index = reference to thread
#n_maxima is an array indicating how many top n comments of each tree level will be considered
#k=maximum depth of comment tree to navigate
#d=maximum 

def grab_page_depth(id,bot,depth_maxima,minwords=25,user_comment_depth=300,ropts=None):
	if ropts==None:
		ropts=rargs(['nada'])
	#makes algorithm more efficient for when the post itself is passed instead of the id
	if type(id)==type('hi'):
		submission=bot.get_submission(submission_id=id)
		print('Now grabbing: ' + submission.title + ' from ' + str(submission.subreddit))
		print('Post was made '+str((gettime()-submission.created_utc)/3600/24)+' days ago')
		print('TOTAL COMMENTS: ' + str(submission.num_comments))
	else:
		submission=id
	id = str(submission.id)#added 10-11-2014
	title=rmnl(submission.title)
	comment_tree=comtree(submission.comments,depth_maxima)
	post_created = submission.created_utc
	user_dict=shelve.open(ropts.filename_userdict)
	thread_dict=shelve.open(ropts.filename_threaddict)
	if id in thread_dict and ropts.overwrite_threads == False:
		user_dict.close()
		thread_dict.close()
		print("Thread already analyzed")
		return(False)
	elif ropts.overwrite_threads==True and id in thread_dict:#############
		timediff=calendar.timegm(time.gmtime())-thread_dict[id][1]['RETRIEVED']
		if timediff<3600:
			user_dict.close()
			thread_dict.close()
			print("Thread already analyzed recently")
			return(False)
	if ropts.getauthor:
		try:
			if str(submission.author.id) not in user_dict:
				print 'ADDING AUTHOR TO DICTIONARY'
				ravage_comment_history(submission.author,minwords,user_comment_depth,user_dict,ropts)
			else:
				print "AUTHOR ALREADY IN DICTIONARY"
		except (HTTPError, AttributeError, praw.errors.NotFound):
			print "AUTHOR NOT FOUND FOR POST...NOT ADDING AUTHOR"
	ncomments=0
	comment_sums=0
	comment_ids=dict()#this will aid in comment-counting
	temp_thread_dict=dict()
	maxlen=0
	topcomlen=-1
	user_queue = set()
	while (comment_tree.direction <> 'T' or comment_tree.override) and depth_maxima[0] <> 0:
		comment_tree.override=False
		current_comment=comment_tree.get_current_comment()
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			if comment_tree.location[0] == 0 and comment_tree.level==0:
				print 'Expanding Initial Top-level MoreComments (should not happen)'
			dontskip=comment_tree.invoke_morecomments()
			if not dontskip:
				if comment_tree.can_move_to_side():
					comment_tree.direction='S'
					comment_tree.move()
					continue
				elif comment_tree.level <> 0:
					comment_tree.direction='U'
					comment_tree.move()
					continue
				else:
					print 'Terminating Tree due to failed MoreComments expansion'
					comment_tree.direction='T'
					continue		
			current_comment=comment_tree.get_current_comment()
			#comment_tree.move()
			#continue
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			print('is this working?')
			comment_tree.invoke_morecomments()
			#comment_tree.move()
			#continue
		current_text=current_comment.body
		#print(current_text)
		current_id=str(current_comment.id)
		if current_id not in comment_ids:
			comment_ids[current_id]=1
			ncomments+=1
			comment_sums+=nwords(current_text)
		maxlen=max(maxlen,nwords(current_text))
		if topcomlen==-1:
			topcomlen=nwords(current_text)
		if nwords(current_text)<minwords:
			comment_tree.move()
			continue
		current_author=current_comment.author
		if current_author==None:
			print('No author available')
			comment_tree.move()
			continue
		#print(current_author)
		current_author_string=str(current_author)
		current_score=current_comment.score
		current_time=current_comment.created_utc
		#current_id=current_comment.id
		is_gilded=current_comment.gilded
		try:
			current_author_id=current_author.id
		except (HTTPError,praw.errors.NotFound):
			print('author ID not found.  set to void')
			current_author_id='NO_AUTHOR_ID'
			print comment_tree.location
		#list() will dereference the value
		#current_text is included because the comment histories of users may not go back far enough; this will double storage space, approximately
		temp_thread_dict[current_id]={'AUTHOR_ID':current_author_id,'AUTHOR_NAME':current_author_string,'SCORE':current_score,'TIME_CREATED':current_time,'TIME_AFTER_SUBMISSION':current_time-post_created,'COMMENT_LOCATION':list(comment_tree.location),'COMMENT_GILDED':is_gilded,'COMMENT_TEXT':current_text,'COMMENT_ID':current_comment.id,'PARENT_ID' : current_comment.parent_id,'NCHILDREN':get_number_of_replies(current_comment)}
		if current_author_id=='NO_AUTHOR_ID':
			comment_tree.move()
			continue
		#print current_author_string
		if ropts.usequeue:
			user_queue.add((current_author,current_author_id))
		elif not str(current_author_id) in user_dict or ropts.overwrite_users:
			#changed March 25th to allow for skipping author creation
			continue_attempts=(not ropts.nouser)
			if str(current_author_id) in user_dict:
				timediff=calendar.timegm(time.gmtime())-user_dict[str(current_author_id)][1]['RETRIEVED']
				if timediff<24.*ropts.mergetime*3600.:#3 day minimum between successive scrapes of same author
					comment_tree.move()
					continue
			while continue_attempts:
				continue_attempts=ravage_comment_history(current_author,minwords,user_comment_depth,user_dict,ropts)
		comment_tree.move()
		#comment_tree.remove_override()
	if ropts.usequeue:
		print "ANALYZING USERS FROM QUEUE"
		for current_author, current_author_id in user_queue:
			if not str(current_author_id) in user_dict or ropts.overwrite_users:
				#changed March 25th to allow for skipping author creation
				continue_attempts=(not ropts.nouser)
				if str(current_author_id) in user_dict:
					timediff=calendar.timegm(time.gmtime())-user_dict[str(current_author_id)][1]['RETRIEVED']
					if timediff<24.*ropts.mergetime*3600.:#3 day minimum between successive scrapes of same author
						continue
				while continue_attempts:
					continue_attempts=ravage_comment_history(current_author,minwords,user_comment_depth,user_dict)
		print "WROTE NEW AUTHORS"	
	attris=dict()
	attris['THREAD_SCORE']=submission.score
	attris['SUBREDDIT']=str(submission.subreddit)
	attris['DATE_CREATED']=submission.created_utc
	attris['TITLE']=title
	attris['TEXT']=submission.selftext
	attris['RETRIEVED']=calendar.timegm(time.gmtime())
	attris['NCOMMENTS']=ncomments
	attris['TOTAL_COMMENTS']=submission.num_comments
	attris['COMMENT_WORDCOUNT']=comment_sums
	attris['URL']=str(submission.short_link)
	attris['LONGEST_COMMENT']=maxlen
	attris['TOP_COMMENT_LENGTH']=topcomlen
	print('Got '+str(ncomments) +' from this thread')
	print('Total of '+str(comment_sums)+' words in this thread')
	try:
		if submission.author == None:
			attris['AUTHOR'] = "DELETED_999"
			attris['AUTHOR_ID']='UNAVAILABLE'
		else:
			attris['AUTHOR']=str(submission.author)
			attris['AUTHOR_ID']=submission.author.id
	except (praw.errors.NotFound,HTTPError):
		print("Author of post is shadowbanned")
		attris['AUTHOR']=str(submission.author)
		attris['AUTHOR_ID']='AUTHOR_SHADOWBANNED'
	try:
		thread_dict[str(submission.id)]=[temp_thread_dict,attris]
	except HTTPError:
		print("strange submission error...continuing anyway")
		thread_dict[id]=[temp_thread_dict,attris]
	user_dict.close()
	thread_dict.close()
	return(True)
		
#these functions mainly exist so recursion can be used to move up and down easily		
def last_nn(array):
	if not -1 in array:
		return len(array)
	return(array.index(-1)-1)

#better way of navigating a comment
#Directions: 'D' = down, 'U' = up, 'S' = side, 'T' = no more movement
class comtree:
	def __init__(self,tree,depth_maxima):
		self.tree = tree
		self.treelist = [[] for _ in range(len(depth_maxima))]
		self.treelist[0] = self.tree
		self.depth_maxima = depth_maxima
		self.location=[-1]*len(depth_maxima)
		self.location[0]=0
		self.direction='D'
		self.infinite_loop_catcher=0
		self.current_tree = tree
		self.level=0
		self.override=False
		self.maxlen = len(self.tree)
		if not self.can_move_down():
			if self.can_move_to_side():
				self.direction='S'
			else:
				print 'This tree contains a single node. Gathering one'
				self.override=True
				self.direction='T'
	def remove_override(self):
		self.override=False
	def move(self):
		#print self.direction
		#print self.location
		if self.infinite_loop_catcher>8:
			if self.can_move_to_side():
				self.direction='S'
			else:
				self.direction='U'
		#adjusted infinite loop catcher 10-10-2014
		if str(type(self.get_current_comment()))=="<class 'praw.objects.MoreComments'>":
			#time.sleep(0.5)
			if self.infinite_loop_catcher >9:
				print self.location
				print "Infinite Loop Impending ERROR"
				self.direction = 'T'
				time.sleep(5)
				return()
			truth = self.invoke_morecomments()
			#if not truth:
			#	del(self.current_tree[self.location[self.level]])
		#	else:
		#		if self.can_move_to_side():
		#			self.direction='S'
		#		else:
		#			self.direction='U'
		#self.infinite_loop_catcher=0
		if self.direction=='D':
			self.current_tree=self.get_current_comment().replies
			self.level=self.level+1
			self.location[self.level]=0
			self.treelist[self.level] = self.current_tree
			if not self.can_move_down():
				if not self.can_move_to_side():
					self.direction='U'
				else:
					self.direction='S'
			self.infinite_loop_catcher = 0
			return()
		elif self.direction=='S':
			self.location[self.level]=self.location[self.level]+1
			if self.can_move_down() and not self.override:
				self.infinite_loop_catcher=0
				self.direction='D'
			elif not self.can_move_to_side():
				if self.level==0:
					print 'Terminating tree naturally'
					self.direction='T'
				else:
					self.direction='U'
			self.infinite_loop_catcher = 0
			return()
		elif self.direction=='U':
			self.location[self.level]=-1
			self.level=self.level-1
			self.set_current_tree()
			self.infinite_loop_catcher=0
		else:#this is direction='T'
			return()
	#nsiblings includes itself, so it's guaranteed to be at least 1	
	def nsiblings(self):
		return(len(self.current_tree))
	def can_move_to_side(self):
		if min(len(self.current_tree),self.depth_maxima[self.level])>self.location[self.level]+1:
			return True
		else:
			return False
	def can_move_down(self):
		if self.override:
			self.override=False
			return False
		if str(type(self.get_current_comment()))=="<class 'praw.objects.MoreComments'>":
			dontskip=self.invoke_morecomments()
			if not dontskip:
				return False
		if self.nchilds()==0:
			return False
		if self.level+1==len(self.depth_maxima):
			return False
		return True
	def nchilds(self):
		return(len(self.current_tree[self.location[self.level]].replies))
	#needed since can't derive parent comments from child comments
	def set_current_tree(self):
		#method greatly shortened 10-26-2014; works much faster and fewer bugs
		self.current_tree = self.treelist[self.level]
		if self.can_move_to_side():
			self.direction='S'
		elif self.level==0:
			print 'Terminating tree while moving upwards'
			self.direction='T'
		return()
		
	def get_current_comment(self):
		#print('LOCATION/LEVEL')
		#print(self.location)
		#print(self.level)
		try:
			return(self.current_tree[self.location[self.level]])
		except IndexError:
			if len(self.treelist) < self.level+1:
				print 'overshot level'
				self.level-= self.level - len(self.treelist) + 1
				self.set_current_tree()
				return(self.current_tree[self.location[self.level]])
			elif len(self.treelist[self.level]) == 0 and self.level <> 0:
				print 'on empty branch'
				self.level-=1
				self.set_current_tree()
				return(self.current_tree[self.location[self.level]])
			print(self.location)
			print self.level
			print len(self.current_tree)
			print self.direction
			print self.infinite_loop_catcher
			#print('ctree')
			print 'IndexError ;-;'
			time.sleep(0.1)
			clnn=last_nn(self.location)
			#self.direction = 'U'
			#self.move()
			#return
			
			try:
				#temporarily disabled for debugging
				if True and self.backwards_counter<1:
					self.location[clnn]-=1
					self.backwards_counter +=1
					self.invoke_morecomments()
					print 'ATTENTION'
				else:
					print self.level
					print self.current_tree
					print self.direction
					print self.location
					self.backwards_count=0
					self.location[clnn]+=1
					
			except AttributeError:
				print('attribute error found...continuing')
				#time.sleep(0.5)
				if self.location[self.level]==-1 and self.level <> 0:
					print self.level
					#try:
					#	del(self.current_tree[self.location[self.level]])
					#except IndexError:
					#	print 'new solution does nothing'
					#	time.sleep(0.1)
					self.level-=1
				#added June 2015
				self.infinite_loop_catcher+=1
				try:
					pass#del(self.current_tree[self.location[self.level]])
				except IndexError:
					print 'new solution really doesn\'t do anything'
				#print self.direction
				print self.treelist
				self.move()
				return(self.current_tree[self.location[self.level]])
			self.backwards_counter=0
			return(self.current_tree[self.location[self.level]])
		
	def invoke_morecomments(self):
		#print('mc')
		self.infinite_loop_catcher+=1
		#added to deal with ininite loops
		#temporarily disabled
		if False and self.infinite_loop_catcher>6 and self.infinite_loop_catcher<10:
			print("avoiding infinite loop")
			self.move()
			return(False)
		elif self.infinite_loop_catcher>6:
			print 'mayday'
			if self.can_move_to_side():
				self.direction='S'
			else:
				print 'Terminating tree to avoid infinite loop'
				if self.level ==0:
					self.direction = 'T'
				else:
					print "TEMPORARILY MOVING UP INSTEAD"					
					self.direction='U'
			return(False)
		selfcurrentcomment=self.get_current_comment()
		if selfcurrentcomment==None:
			print 'current comment type is None'
			return(False)
		try:
			if selfcurrentcomment.comments()==[]:
				print 'expanded comments are []'
				return(False)
		except (AttributeError, AssertionError):
			print('strange attribute/assertion error...continuing')
			return(False)
		#added 10-10-2014 to address a bug
		temp_coms = self.get_current_comment().comments()
		if type(temp_coms) == type(None):
			print('nonetype found here')
			self.direction = 'S'
			self.override=True
			self.move()
		else:
			self.current_tree=self.current_tree+temp_coms
		del(self.current_tree[self.location[self.level]])
		current_comment=self.get_current_comment()
		self.treelist[self.level] = self.current_tree
		if current_comment==[] or current_comment==None:
			print 'no comments'
			return(False)
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			print 'HIT MORECOMMENTS ODDLY'
			return(False)
		#print 'expanding'
		return(True)
		
		
		
	#used as a test function for tree navigation
	#very useful for debugging
	def move_loc(self):
		while self.direction <> 'T':
			print(self.location)
			print(self.direction)
			errbreak=self.get_current_comment()#just used to break code if it's wrong
			try:
				print(errbreak.body)
			except:
				print type(errbreak)
			self.move()
		return()
			
			
			

#this will write user comments
def ravage_comment_history(user,minwords,user_comment_depth,user_dict,ropts,uid = None):
	if user==None:
		print("No User Found...continuing")
		return(False)
	is_shadowbanned = False
	try:
		UID = str(user.id)
	except praw.errors.NotFound:
		print 'notfound'
		is_shadowbanned = True
		UID = uid
	user_subs=set()
	user_sub_dict=dict()
	comment_dict=dict()
	#variables will remain 0 unless a previous entry is in the dictionary
	average_comment_length_old=0.
	ncomments_over_old=0.
	ncomments_old = 0.
	overwrite_aware=False
	subdict = dict()
	nsubmissions = 0
	if UID in user_dict:
		#print 'going back'
		overwrite_aware =True
		entry = user_dict[UID]
		if len(entry) ==3:
			subdict = entry[2]
			nsubmissions = len(subdict.keys())
		user_subs = entry[1]['SUBREDDIT_LIST']
		user_sub_dict=entry[1]['SUBREDDIT_FREQUENCIES']
		ncomments_old = entry[1]['NCOMMENTS']
		average_comment_length_old = entry[1]['AVERAGE_COMMENT_LENGTH']
		ncomments_over_old = entry[1]['NCOMMENTS_OVER']
		comment_dict=entry[0]
		old_utris = entry[1]
	if not is_shadowbanned:
		comments=user.get_comments(limit=user_comment_depth)
		submissions = user.get_submitted(limit = user_comment_depth)
	#comments=user.get_comments(limit=user_comment_depth)
	ncomments=0
	ncomments_over=0
	average_comment_length=0
	#raise#prevent active program from rerunning file
	try:
		if is_shadowbanned:
			raise praw.errors.NotFound("Shadowbanned")
		for submission in submissions:
			if str(submission.id) in subdict and not ropts.overshoot:
				break
			subdict[str(submission.id)] = {'SUBREDDIT':str(submission.subreddit),'TITLE':submission.title,
				  'SCORE':submission.score,'CREATED':submission.created_utc,'NUM_COMMENTS':submission.num_comments,'EDITED':submission.edited,
				  'TEXT':submission.selftext,'RETRIEVED':gettime(),'IS_SELF':submission.is_self,'GILDED':submission.gilded,'DISTINGUISHED':submission.distinguished,
				  'NSFW':submission.over_18,'URL':submission.url,'FLAIR':submission.author_flair_css_class}
			nsubmissions+=1
			
		for comment in comments:
			#prevents same comments from being rewritten
			if overwrite_aware:
				if str(comment.id) in comment_dict and not ropts.overshoot:
					break#may change to continue if errors arise
			comment_text=comment.body
			average_comment_length+=nwords(comment_text)
			ncomments+=1
			if nwords(comment_text)<minwords:
				continue
			ncomments_over+=1
			#SUBREDDIT previously COMMENT_ID
			comment_dict[str(comment.id)]={'SUBREDDIT':str(comment.subreddit),'COMMENT_SCORE':comment.score,'COMMENT_CREATED':comment.created_utc,'COMMENT_GILDED':comment.gilded,'COMMENT_DISTINGUISHED':comment.distinguished,'COMMENT_TEXT':comment_text,'POST_LINK':str(comment.link_id)[3:],'COMMENT_ID':comment.id,'COMMENT_RETRIEVED':gettime()}
			if str(comment.subreddit) not in user_subs:
				user_subs.add(str(comment.subreddit))
				user_sub_dict[str(comment.subreddit)]=1
			else:
				user_sub_dict[str(comment.subreddit)]+=1
	except (HTTPError,ConnectionError,socket.timeout,praw.errors.NotFound) as err:
		if str(type(err)) in ("<class 'HTTPError'>","<class 'praw.errors.NotFound'>"):#err.errno==404:
			print('User is shadowbanned: '+ str(user))
			#implementing shadowban detection for users that were previously not shadowbanned while their data was collected
			if overwrite_aware:
				print "RECORDING INCIDENT OF SHADOWBANNING..."
				average_comment_length=average_comment_length_old
				utris=dict()
				e1 = entry[1]
				utris = e1
				if not 'SHADOWBANNED' in e1:
					utris['SHADOWBANNED'] = True
					utris['SHADOWBANNED_DATE'] = gettime()
				elif not e1['SHADOWBANNED']:
					utris['SHADOWBANNED'] = True
					utris['SHADOWBANNED_DATE'] = gettime()
				else:
					return(False)
				user_dict[UID]=[comment_dict,utris,subdict]
				user_dict.sync()
			return(False)
		else:
			print('Connection Error...sleeping')
			time.sleep(20)
			return(True)
	#print(str(user))I'd beI'd beI'd be
	if (ncomments_over+ncomments_over_old==0):
		#this can happen with old comments and the way that user history is archived
		#the original comment that was scraped will still exist, though
		print("USER " + str(user) + "HAS NO COMMENTS")
		#return(False)
	#updated 10-30-2014 to allow expansion of dictionaries with new users
	average_comment_length=average_comment_length/max(1,ncomments_over)
	average_comment_length=(average_comment_length*ncomments+average_comment_length_old*ncomments_over_old)/max(ncomments_over+ncomments_over_old,1)
	utris=dict()
	utris['AUTHOR_AGE']=user.created_utc
	utris['AUTHOR_NAME']=str(user)
	utris['AUTHOR_COMMENTKARMA']=user.comment_karma
	utris['AUTHOR_LINKKARMA']=user.link_karma
	utris['IS_MOD']=user.is_mod
	utris['IS_GOLD']=user.is_gold
	utris['VERIFIED']=user.has_verified_email
	utris['SUBREDDIT_LIST']=user_subs
	utris['SUBREDDIT_FREQUENCIES']=user_sub_dict
	#antiquated, but easy fix due to date-time differences
	if overwrite_aware:
		if 'FIRST_RETRIEVED' not in old_utris:
			print 'using older date as first retrieval date'
			utris['FIRST_RETRIEVED'] = old_utris['RETRIEVED']
		else:
			utris['FIRST_RETRIEVED'] = old_utris['FIRST_RETRIEVED']
	else:
		utris['FIRST_RETRIEVED'] = gettime()
	utris['RETRIEVED']=calendar.timegm(time.gmtime())
	utris['NCOMMENTS']=ncomments
	utris['NCOMMENTS_OVER']=ncomments_over
	utris['AVERAGE_COMMENT_LENGTH']=average_comment_length
	utris['SHADOWBANNED'] = False
	utris['SHADOWBAN_DATE'] = None
	utris['NSUBMISSIONS'] = nsubmissions
	user_dict[str(user.id)]=[comment_dict,utris,subdict]
	user_dict.sync()
	if not overwrite_aware:
		print("Got comment history for: " + str(user))
	else:
		print("Updated comment history for: " + str(user))
	return(False)
		

#will move up the tree, and then determine if it should move up or move to the side
def move_up_tree(tree,tree_navigation):
	lnn=last_nn(tree_navigation)
	tree_navigation[lnn]=-1

	return(tree_navigation)
	
def get_random_post(bot,minwords,ropts):
	end_loop=False
	while not end_loop:
		try:
			post=bot.get_random_submission()
			end_loop=check_post_for_comments(post,minwords)
			good_time = check_time(post,ropts)
			#currently disabled notifying when posts aren't selected
			if True and not good_time:
				print "BAD_TIMING"
				print '(ncomments:)' + str(post.num_comments)
			end_loop = end_loop and good_time
		except (UnicodeDecodeError, HTTPError):
			print('weird unicode/http issue found')
			time.sleep(0.1)
			continue
	print('Post was made '+str((gettime()-post.created_utc)/3600/24)+' days ago')
	return(post)
	
#currently same as get_random_post
def get_subreddit_post(bot,minwords,subreddit,ropts):
	end_loop=False
	subred=bot.get_subreddit(subreddit)
	comstring=construct_function(ropts)
	#added these to allow for faster searching through posts
	threaddict = shelve.open(ropts.filename_threaddict)
	post_keys = threaddict.keys()
	threaddict.close()
	print comstring
	evalstring='subred.'+comstring+'(limit='+str(ropts.top)+')'
	#need to improve to be less random
	if not ropts.norandom:
		while not end_loop:
			try:
				hit_i=random.randint(0,ropts.top-1)
				i=0
				posts=eval(evalstring)
				print evalstring
				for item in posts:
					post=item
					#print i
					if i==hit_i:
						#print item.title
						#print 'actually got something'
						end_loop=check_time(post,ropts)
						print end_loop
						end_loop=end_loop and check_post_for_comments(post,minwords)
						print end_loop
						break
					i+=1
				#end_loop=check_time(post,ropts)
				#end_loop=end_loop and check_post_for_comments(post,minwords)
			except UnicodeDecodeError:
				print('weird unicode issue found')
				continue
		print 'got something'
	else:
		i = 0
		while not end_loop:
			try:
				i+=1
				posts = eval(evalstring)
				n=0
				for item in posts:
					n+=1
					post = item
					if not check_time_lower(post,ropts):
						continue
					if item.id in post_keys:
						continue
					if not check_time_lower(post,ropts):
						continue
					if not check_time_upper(post,ropts):
						print 'Time boundary reached'
						return None
					end_loop = check_time(post,ropts)
					end_loop = end_loop and check_post_for_comments(post,minwords)
					if end_loop:
						print('Post was made '+str((gettime()-post.created_utc)/3600/24)+' days ago')
						return(post)
				if n==0:
					print "Nothing could be found"
					return None
				print "Went through all items"
				return None
			except UnicodeDecodeError:
				print('weird unicode issue found')
				post_keys.append(post.title)
				continue
			if i>1000:
				print "UNABLE TO FIND A POST WITHIN 1000 LOOPS"
				return None
	print('Post was made '+str(round((gettime()-post.created_utc)/3600./24.,4))+' days ago')
	return(post)

#types= hot top controversial new rising
#times = hour day week month year all
#not all combinations are actually valid
def construct_function(ropts):
	comstring=''
	if ropts.ctype <> None:
		comstring+='get_'+ropts.ctype
		if ropts.date <> None:
			comstring+='_from_'+ropts.date
	else:
		comstring+='get_random_submission'
	return comstring
	
def check_time(post,ropts):
	time=post.created_utc
	if ropts.edate==None:
		return True
	else:
		if time<(gettime()-ropts.edate[0]*24*3600) and time>(gettime()-ropts.edate[1]*24*3600):
			return True
	return False

#checks time to see if no valid posts are available
def check_time_upper(post,ropts):
	time = post.created_utc
	if ropts.edate==None:
		return True
	else:
		if time<=(gettime()-ropts.edate[1]*24*3600):
			return False
	return True

#checks lower bound to hasten process for -norandom
def check_time_lower(post,ropts):
	time=post.created_utc
	if ropts.edate==None:
		return True
	else:
		if time>=(gettime()-ropts.edate[0]*24*3600):
			return False
	return True

def gettime():
	return calendar.timegm(time.gmtime())

#checks root tree
def check_post_for_comments(post,minwords):
	coms=post.comments
	if coms==[]:
		return False
	for comment in coms:
		if str(type(comment))=="<class 'praw.objects.MoreComments'>":
			return False
		if nwords(comment.body)>=minwords:
			return True
	return False

#main
def main(args):
	bot=praw.Reddit('thread analyzing test by /u/SymphMeta')
	if args==[]:
		args=['-random']
	ropts=rargs(args)
	n_max=ropts.n_max
	n_total=0
	print "BEGINNING"
	if ropts.grabauthors:
		print 'GRABBING POST AUTHORS\' COMMENT HISTORIES'
		threaddict = shelve.open(ropts.filename_threaddict)
		userdict = shelve.open(ropts.filename_userdict)
		for thread in threaddict:
			author = threaddict[thread][1]['AUTHOR']
			authorid = threaddict[thread][1]['AUTHOR_ID']
			if str(author) <> "DELETED_999" and str(authorid) not in userdict:
				try:
					user = bot.get_redditor(author)
					id = str(user.id)
				except (praw.errors.NotFound,HTTPError):
					print "POST AUTHOR COULD NOT BE FOUND"
					continue
				if id not in userdict:
					ravage_comment_history(user,ropts.minwords,ropts.depth,userdict,ropts)
					userdict.sync()
		print 'FINISHED REGRABBING AUTHOR IDS'
		threaddict.close()
		userdict.close()
	if '-random' in ropts.args:
		while n_max<0 or n_total<n_max:
			post=get_random_post(bot,ropts.minwords,ropts)
			print('Scraping ' + str(removeNonAscii(post.title)) + ' from ' + str(post.subreddit))
			id=str(post.id)
			print('id = '+id)
			score = str(post.score)
			print('score = ' + score)
			ncomments = str(post.num_comments)
			print('ncomments = ' + ncomments)
			print "TOTAL COMMENTS: " + str(post.num_comments)
			grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
			n_total+=1
	elif ropts.subreddits<>[]:
		nsubs=len(ropts.subreddits)
		while n_total<n_max or n_max<0:
			try:
				print 'searching for post...'
				post=get_subreddit_post(bot,ropts.minwords,ropts.subreddits[n_total%nsubs],ropts)
				if post==None:
					print("NO POSTS FOUND")
					n_total+=1
					continue
			except:
				'CONNECTION ERROR WHILE TRYING TO GET POST...SLEEPING'
				time.sleep(25)
				continue
			print('Scraping ' + str(removeNonAscii(post.title)) + ' from ' + str(post.subreddit))
			id=str(post.id)
			print('id = '+id)
			score = str(post.score)
			print('score = ' + score)
			ncomments = str(post.num_comments)
			print('ncomments = ' + ncomments)
			grab_page_depth(post,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
			n_total+=1
			print 'TOTAL DONE = ' + str(n_total)
	elif ropts.idlist<>[] or ropts.rescrapeposts:
		if ropts.rescrapeposts:
			threaddict = shelve.open(ropts.filename_threaddict)
			thkeys = threaddict.keys()
			for key in thkeys:
				if key not in ropts.idlist:
					ropts.idlist.append(key)
			threaddict.close()
		for id in ropts.idlist:
			print('SCRAPING '+id)
			grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
	elif ropts.users<>[] or ropts.rescrapeusers:
		ropts.idlist = []
		kcounter = 0
		if ropts.rescrapeusers:
			
			print "WARNING: THIS WILL TAKE A LONG TIME"
			userdict = shelve.open(ropts.filename_userdict)
			print 'opened shelve file...'
			if not os.path.isfile('./' + ropts.filename_keys):
				ukeys = userdict.keys()
				keyfile = shelve.open(ropts.filename_keys)
				keyfile['entry'] = ukeys
				keyfile.close()
			else:
				keyfile = shelve.open(ropts.filename_keys)
				ukeys = keyfile['entry']
				keyfile.close()
			lkeys = len(ukeys) + len(ropts.users)
			ukeys_copy = ukeys
			print "LOADED KEYS"
			kcounter = 0
			keyfile = shelve.open(ropts.filename_keys)
			for i, key in enumerate(ukeys):
				if i % 20 == 0:
					print 'TOTAL DONE = ' + str(i) + '/' + str(lkeys)
					print to_percent(float(i)/lkeys) + ' done'
				keyfile.sync()
				uname = userdict[key][1]['AUTHOR_NAME']
				#if i % 500 == 0:
				#	print 'prepped ' + str(i) + '/' + str(lkeys)
				#	print to_percent(float(i)/lkeys) + ' done'
				if ropts.timefloor <> None:
					if 'SHADOWBANNED' in userdict[key][1]:
						if userdict[key][1]['SHADOWBANNED'] == True:
							kcounter +=1
							ukeys_copy.pop(ukeys_copy.index(key))
							keyfile['entry'] = ukeys_copy
							next
					if userdict[key][1]['RETRIEVED'] > ropts.timefloor:
						kcounter+=1
						ukeys_copy.pop(ukeys_copy.index(key))
						keyfile['entry'] = ukeys_copy
						next
				ruser=bot.get_redditor(userdict[key][1]['AUTHOR_NAME'])
				ravage_comment_history(ruser,ropts.minwords,ropts.depth,userdict,ropts,ukeys[i])					
				ukeys_copy.pop(ukeys_copy.index(key))
				keyfile['entry'] = ukeys_copy
			userdict.close()
			print "DONE"
			return None
		print 'BEGINNING SCRAPING FOR REAL'
		user_dict=shelve.open(ropts.filename_userdict)
		if ropts.rescrapeusers:
			keyfile = shelve.open(ropts.filename_keys)
		for i, user in enumerate(ropts.users):
			ruser=bot.get_redditor(user)
			ravage_comment_history(ruser,ropts.minwords,ropts.depth,user_dict,ropts,ukeys[i])
			kcounter+=1
			if ropts.rescrapeusers:
					ukeys_copy.pop(i)
			if kcounter % 100 == 0:
				keyfile['entry'] = ukeys_copy
				keyfile.sync()
				print 'TOTAL DONE = ' + str(kcounter) + '/' + str(lkeys)
				print to_percent(float(kcounter)/lkeys) + ' done'
			if ropts.ux:
				print 'oh why?'
				for comment in user_dict[str(ruser.id)][0]:
					if user_dict[str(ruser.id)][0][comment]['POST_LINK'] not in ropts.idlist:
						ropts.idlist+=[user_dict[str(ruser.id)][0][comment]['POST_LINK']]
		user_dict.close()
		if ropts.rescrapeusers:
			keyfile.close()
		if ropts.idlist<>[]:
			nids=float(len(ropts.idlist))
			i=0.
			print(ropts.idlist)
			print('total posts: ' + str(nids))
			for id in ropts.idlist:
				print(str(round(i/nids*100.,2))+r'% of the way done')
				print(id)
				post=bot.get_submission(submission_id=id)
				print('Scraping '+ str(removeNonAscii(post.title)) +' from ' + removeNonAscii(str(post.subreddit)))
				grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
				print('++++++++Done with thread id: '+id)
				i+=1.
	print("DONE WITH SCRAPING")

##go to top of file for more comprehensive explanations
#-ou: overwrite users
#-u tells bot to track users followed by this term
#-fu tells bot to track users in a file
#-ot: overwrite threads
#-random: randomized selection
#-sub: followed by subreddits to scrape
#-fsub: followed by filename containing subreddits
#-date: specifies general time period to go through
#-edate: followed by two arguments to indicate acceptable time range; this will trigger some interesting code to get stuff exactly right; these values will be in terms of days (so transformed by factors of 3600*24); only applicable in randomized subreddit selection
#-n: followed by numerical limit
#-i: ids of posts to analyze
#-fi: followed by file containing ids of posts to scrape
#-mw: followed by minimum number of words per comment
#-name: followed by prefix of filename
#-tree: followed by integers representing depth_maxima	
#-ux: will go to threads for all comments of users if there are users defined; this is too slow to do in any other context
#-type: will allow you to specify what kinds of submissions to get (top, hot, controversial)
#-norandom: when a list of subreddits is provided, this will remove the normally random selection from the process. This is more methodological and (usually) faster
#-getauthor: Adds author of posts to user dictionary in case they are persons of interest
#-grabauthors: Retroactively grabs authors of posts already made if they are not in the user dictionary already
#-mergetime: Determines amount of time (in days) before an author can be rescraped; default is 3 days
class rargs:
	def __init__(self,args):
		print('creating options')
		self.args=args
		self.subreddits=[]
		self.idlist=[]
		self.users=[]
		if '-ou' in args:
			self.overwrite_users=True
		else:
			self.overwrite_users=False
		if '-ot' in args:
			self.overwrite_threads=True
		else:
			self.overwrite_threads=False
		if '-n' in args:
			self.n_max=int(args[args.index('-n')+1])
		else:
			self.n_max=-1
		if '-mw' in args:
			self.minwords=int(args[args.index('-mw')+1])
		else:
			self.minwords=13
		if '-fi' in args:
			self.idlist+=extract_lines(args[args.index('-fi')+1])
		if '-i' in args:
			self.idlist+=nargs('-i',args,False)
			#print(self.idlist)
		if '-u' in args:
			self.users+=nargs('-u',args,False)
		if '-fu' in args:
			self.users+=extract_lines(args[args.index('-fu')+1])
		if '-fsub' in args:
			self.subreddits+=extract_lines(args[args.index('-fsub')+1])
		if '-sub' in args:
			self.subreddits+=nargs('-sub',args,False)
		if '-tree' in args:
			self.depth_maxima=nargs('-tree',args,True)
		else:
			self.depth_maxima=[300,125,80,45,18,8,4,3,3,3,2,2,1]
		if '-edate' in args:
			di=args.index('-edate')
			self.edate =[float(args[di+1]),float(args[di+2])]
			print 'TIME RANGE: ' + str(self.edate)
		else:
			self.edate=None
		if '-date' in args:
			self.date=args[args.index('-date')+1]
		else:
			self.date=None
		if '-name' in args:
			px=args[args.index('-name')+1]
			self.filename_userdict='user_'+px+'.dat'
			self.filename_threaddict='thread_'+px+'.dat'
			#used for scraping large files
			self.filename_keys = 'ukeys_' + px + '.dat'
		else:
			self.filename_userdict=filename_userdict
			self.filename_threaddict=filename_threaddict
		if '-depth' in args:
			self.depth=int(args[args.index('-depth')+1])
		else:
			self.depth=500
		if '-type' in args:
			self.ctype=args[args.index('-type')+1]
		else:
			self.ctype=None
		if '-ux' in args:
			self.ux=True
		else:
			self.ux=False
		if '-top' in args:
			self.top = int(args[args.index('-top')+1])
		else:
			self.top=25
		if '-norandom' in args:
			self.norandom = True
		else:
			self.norandom = False
		#getauthor will add authors of posts to the thread dictionary if applicable
		if '-getauthor' in args:
			self.getauthor=True
		else:
			self.getauthor=False
		#grabauthors will get comment histories for all authors previously from posts in the thread dictionary
		if '-grabauthors' in args:
			self.grabauthors =True
		else:
			self.grabauthors = False
		if '-mergetime' in args:
			self.mergetime = float(args[args.index('-mergetime')+1])
		else:
			self.mergetime=3.0
		if '-nouser' in args:
			self.nouser = True
		else:
			self.nouser = False
		if '-timefloor' in args:
			self.timefloor = int(args[args.index('-timefloor')+1])
		else:
			self.timefloor = None
		self.overshoot = '-overshoot' in args
		self.rescrapeposts = '-rescrapeposts' in args
		self.rescrapeusers = '-rescrapeusers' in args
		self.usequeue = '-queue' in args
		self.top_level_index = 0
		self.backwards_counter = 0
		print('finished parsing options')
		#self.idlist=self.thread_ids
		print(self.idlist)
		#return(self)
		
	
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

#added March 25, 2015
def get_number_of_replies(comment):
	replies = comment.replies
	nreplies = len(replies)
	if nreplies==0:
		#print "ERROR: NO REPLIES"
		return 0
	while str(type(replies[nreplies-1]))=="<class 'praw.objects.MoreComments'>":
		try:
			new_replies = replies[nreplies-1].comments()
		except AssertionError:
			return(0)
		nreplies = nreplies - 1
		if len(new_replies)==0:
			break
		replies.pop()
		replies = replies + new_replies
		nreplies += len(new_replies)
	return(nreplies)

def to_percent(num,ndigits = 6):
	return str(round(num,ndigits)*100) + r'%'
		
if __name__ == '__main__':
	print 'VERSION: '+VERSION
	main(sys.argv[1:])

	

