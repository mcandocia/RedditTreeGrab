#CREATED BY MAX CANDOCIA
#MAY 2014
#THIS WILL SCRAPE A REDDIT PAGE AND THEN WRITE IT TO A READABLE FILE
#different types of imports will be used
#concatenations are also possible in the future

####options
#-ou: overwrite users; 1-hour delay before you can do this
#-ot: overwrite threads; 1-hour delay before you can do this
#-random: randomized selection
#-sub: followed by subreddits to scrape
#-fsub: followed by filename containing subreddits to scrape
#-date: followed by type of date to analyze (i.e., hour, day, week, month, year, all)
#-edate: followed by range in days that posts should be drawn from 
#-n: followed by numerical limit
#-u: followed by list of users to scrape
#-fu: followed by filename of line-separated users to scrape
#-ux: if -u or -fu is specified, will analyze each thread user is in
#-name: specify part of the name of the file; THIS IS IMPORTANT
#-depth: followed by how far back in someone's comment history you should go
#-type: followed by type of random post to get for subreddits (hot, new, top, rising, etc.); not every option works with every date combination (although some do)
#-tree: followed by integers representing how far in tree depth you want to go to view comments
#-mw: followed by minimum words for a comment
#-fi: followed by file containing ids of posts to scrape
#-top: for subreddit-based queries, the number following this will get one of the top [this number] posts from that subreddit for the type specified


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

filename_userdict='user_dictionary_custom04.dat'
filename_threaddict='thread_dictionary_custom04.dat'



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
	submission=bot.get_submission(submission_id=id)
	title=rmnl(submission.title)
	comment_tree=comtree(submission.comments,depth_maxima)
	post_created = submission.created
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
	ncomments=0
	comment_sums=0
	comment_ids=dict()#this will aid in comment-counting
	temp_thread_dict=dict()
	maxlen=0
	topcomlen=-1
	while comment_tree.direction <> 'T':
		current_comment=comment_tree.get_current_comment()
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			#print("HIT THIS")#hopefully it never gets hit
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
		current_time=current_comment.created
		#current_id=current_comment.id
		is_gilded=current_comment.gilded
		try:
			current_author_id=current_author.id
		except HTTPError:
			print('author ID not found.  set to void')
			current_author_id='NO_AUTHOR_ID'
		#list() will dereference the value
		#current_text is included because the comment histories of users may not go back far enough; this will double storage space, approximately
		temp_thread_dict[current_id]={'AUTHOR_ID':current_author_id,'AUTHOR_NAME':current_author_string,'SCORE':current_score,'TIME_CREATED':current_time,'TIME_AFTER_SUBMISSION':current_time-post_created,'COMMENT_LOCATION':list(comment_tree.location),'COMMENT_GILDED':is_gilded,'COMMENT_TEXT':current_text}
		if current_author_id=='NO_AUTHOR_ID':
			comment_tree.move()
			continue
		if not str(current_author_id) in user_dict or ropts.overwrite_users:
			continue_attempts=True
			if str(current_author_id) in user_dict:
				timediff=calendar.timegm(time.gmtime())-user_dict[str(current_author_id)][1]['RETRIEVED']
				if timediff<3600:#1 hour minimum between successive scrapes of same author
					comment_tree.move()
					continue
			while continue_attempts:
				continue_attempts=ravage_comment_history(current_author,minwords,user_comment_depth,user_dict)
		comment_tree.move()
	attris=dict()
	attris['THREAD_SCORE']=submission.score
	attris['SUBREDDIT']=str(submission.subreddit)
	attris['DATE_CREATED']=submission.created
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
	except HTTPError:
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
		self.depth_maxima = depth_maxima
		self.location=[-1]*len(depth_maxima)
		self.location[0]=0
		self.direction='D'
		self.current_tree = tree
		self.level=0
		if not self.can_move_down():
			if self.can_move_to_side():
				self.direction='S'
			else:
				self.direction='T'
	def move(self):
		#if self.depth_maxima[self.level]==self.location[self.level]:
		#print(self.direction)
		#print(self.location)
		#print(self.level)
		if str(type(self.get_current_comment()))=="<class 'praw.objects.MoreComments'>":
			self.invoke_morecomments()
		if self.direction=='D':
			self.current_tree=self.get_current_comment().replies
			self.level=self.level+1
			self.location[self.level]=0
			if not self.can_move_down():
				if not self.can_move_to_side():
					self.direction='U'
				else:
					self.direction='S'
			return()
		elif self.direction=='S':
			self.location[self.level]=self.location[self.level]+1
			if self.can_move_down():
				self.direction='D'
			elif not self.can_move_to_side():
				if self.level==0:
					self.direction='T'
				else:
					self.direction='U'
			return()
		elif self.direction=='U':
			self.location[self.level]=-1
			self.level=self.level-1
			self.set_current_tree()
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
		self.current_tree=self.tree
		temp_level=0
		#print('sl')
		#print(self.location)
		if str(type(self.current_tree[len(self.current_tree)-1]))=="<class 'praw.objects.MoreComments'>":
			#print("EXPANDING TREE")
			rmindex=len(self.current_tree)-1
			self.current_tree=self.current_tree+self.current_tree[rmindex].comments()
			del(self.current_tree[rmindex])
		while temp_level<self.level:
			try:
				if str(type(self.current_tree[self.location[temp_level]]))=="<class 'praw.objects.MoreComments'>":
					#print("DOING MORE EXPANDING")
					self.current_tree+=self.current_tree[self.location[temp_level]].comments()
					del(self.current_tree[self.location[temp_level]])
				self.current_tree=self.current_tree[self.location[temp_level]].replies
				temp_level=temp_level+1
			except IndexError:
				print('IndexError found...reforming tree')
				#print(self.location)
				#print(self.current_tree)
				lct=len(self.current_tree)
				self.current_tree+=self.current_tree[lct-1].comments()
				del(self.current_tree[lct-1])
				self.current_tree=self.current_tree[self.location[temp_level]].replies
				temp_level=temp_level+1
		if self.can_move_to_side():
			self.direction='S'
		elif self.level==0:
			self.direction='T'
		return()
	def get_current_comment(self):
		#print('LOCATION/LEVEL')
		#print(self.location)
		#print(self.level)
		try:
			return(self.current_tree[self.location[self.level]])
		except IndexError:
			#print(self.current_tree)
			#print('ctree')
			clnn=last_nn(self.location)
			try:
				self.location[clnn]-=1
				self.invoke_morecomments()
				self.location[clnn]+=1
			except AttributeError:
				print('attribute error found...continuing')
				self.move()
				return(self.current_tree[self.location[self.level]])
			return(self.current_tree[self.location[self.level]])
		
	def invoke_morecomments(self):
		#print('mc')
		selfcurrentcomment=self.get_current_comment()
		if selfcurrentcomment==None:
			return(False)
		try:
			if selfcurrentcomment.comments()==[]:
				return(False)
		except AttributeError:
			print('strange attribute error...continuing')
			return(False)
		self.current_tree=self.current_tree+self.get_current_comment().comments()
		del(self.current_tree[self.location[self.level]])
		current_comment=self.get_current_comment()
		if current_comment==[] or current_comment==None:
			return(False)
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			return(False)
		return(True)
		
		
		
	#used as a test function for tree navigation
	def move_loc(self):
		while self.direction <> 'T':
			print(self.location)
			print(self.direction)
			errbreak=self.get_current_comment()#just used to break code if it's wrong
			print(errbreak.body)
			self.move()
		return()
			
			
			

#this will write user comments
def ravage_comment_history(user,minwords,user_comment_depth,user_dict):
	if user==None:
		print("No User Found...continuing")
		return(False)
	#print('------Investigating: ' + str(user))
	user_subs=set()
	user_sub_dict=dict()
	comments=user.get_comments(limit=user_comment_depth)
	#comments=user.get_comments(limit=user_comment_depth)
	comment_dict=dict()
	ncomments=0
	ncomments_over=0
	average_comment_length=0
	try:
		for comment in comments:
			comment_text=comment.body
			average_comment_length+=nwords(comment_text)
			ncomments+=1
			if nwords(comment_text)<minwords:
				continue
			ncomments_over+=1
			#SUBREDDIT previously COMMENT_ID
			comment_dict[str(comment.id)]={'SUBREDDIT':str(comment.subreddit),'COMMENT_SCORE':comment.score,'COMMENT_CREATED':comment.created,'COMMENT_GILDED':comment.gilded,'COMMENT_DISTINGUISHED':comment.distinguished,'COMMENT_TEXT':comment_text,'POST_LINK':str(comment.link_id)[3:]}
			if str(comment.subreddit) not in user_subs:
				user_subs.add(str(comment.subreddit))
				user_sub_dict[str(comment.subreddit)]=1
			else:
				user_sub_dict[str(comment.subreddit)]+=1
	except (HTTPError,ConnectionError) as err:
		if type(err)==HTTPError:#err.errno==404:
			print('User is shadowbanned: '+ str(user))
			return(False)
		else:
			print('Connection Error...sleeping')
			time.sleep(10)
			return(True)
	#print(str(user))
	if (ncomments_over==0):
		#this can happen with old comments and the way that user history is archived
		#the original comment that was scraped will still exist, though
		print("USER " + str(user) + "HAS NO COMMENTS")
		return(False)
	average_comment_length=average_comment_length/ncomments_over
	utris=dict()
	utris['AUTHOR_AGE']=user.created
	utris['AUTHOR_NAME']=str(user)
	utris['AUTHOR_COMMENTKARMA']=user.comment_karma
	utris['AUTHOR_LINKKARMA']=user.link_karma
	utris['IS_MOD']=user.is_mod
	utris['IS_GOLD']=user.is_gold
	utris['VERIFIED']=user.has_verified_email
	utris['SUBREDDIT_LIST']=user_subs
	utris['SUBREDDIT_FREQUENCIES']=user_sub_dict
	utris['RETRIEVED']=calendar.timegm(time.gmtime())
	utris['NCOMMENTS']=ncomments
	utris['NCOMMENTS_OVER']=ncomments_over
	utris['AVERAGE_COMMENT_LENGTH']=average_comment_length
	user_dict[str(user.id)]=[comment_dict,utris]
	user_dict.sync()
	print("Got comment history for: " + str(user))
	return(False)
		

#will move up the tree, and then determine if it should move up or move to the side
def move_up_tree(tree,tree_navigation):
	lnn=last_nn(tree_navigation)
	tree_navigation[lnn]=-1

	return(tree_navigation)
	
def get_random_post(bot,minwords):
	end_loop=False
	while not end_loop:
		try:
			post=bot.get_random_submission()
			end_loop=check_post_for_comments(post,minwords)
		except UnicodeDecodeError:
			print('weird unicode issue found')
			continue
	return(post)
	
#currently same as get_random_post
def get_subreddit_post(bot,minwords,subreddit,ropts):
	end_loop=False
	subred=bot.get_subreddit(subreddit)
	comstring=construct_function(ropts)
	evalstring='subred.'+comstring+'(limit='+str(ropts.top)+')'
	while not end_loop:
		try:
			posts=eval(evalstring)
			i=0
			hit_i=random.randint(0,ropts.top-1)
			for item in posts:
				post=item
				if i==hit_i:
					break
				i+=1
			end_loop=check_time(post,ropts)
			end_loop=end_loop and check_post_for_comments(post,minwords)
		except UnicodeDecodeError:
			print('weird unicode issue found')
			continue
	print('Post was made '+str((gettime()-post.created)/3600/24)+' days ago')
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
	time=post.created
	if ropts.edate==None:
		return True
	else:
		if time<(gettime()-ropts.edate[0]*24*3600) and time>(gettime()-ropts.edate[1]*24*3600):
			return True
	return False


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

#-u: overwrite users
#-t: overwrite threads
#-r: randomized selection
#-s: followed by subreddits to scrape
#-date: followed by time range to analyze
#-n: followed by numerical limit
#-f: followed by file containing ids of posts to scrape
#-mw: followed by minimum number of words
#-prefix: followed by prefix of filename
#-tree: followed by integers representing depth_maxima
#-depth: user comment depth
def main(args):
	bot=praw.Reddit('thread analyzing test by /u/SymphMeta')
	if args==[]:
		args=['-random']
	ropts=rargs(args)
	n_max=ropts.n_max
	n_total=0
	if '-random' in ropts.args:
		while n_max<0 or n_total<n_max:
			post=get_random_post(bot,ropts.minwords)
			print('Scraping ' + str(removeNonAscii(post.title)) + ' from ' + str(post.subreddit))
			id=str(post.id)
			grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
			n_total+=1
	elif ropts.subreddits<>[]:
		nsubs=len(ropts.subreddits)
		while n_total<n_max or n_max<0:
			post=get_subreddit_post(bot,ropts.minwords,ropts.subreddits[n_total%nsubs],ropts)
			print('Scraping ' + str(removeNonAscii(post.title)) + ' from ' + str(post.subreddit))
			id=str(post.id)
			print('id = '+id)
			grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
			n_total+=1
	elif ropts.idlist<>[]:
		for id in ropts.idlist:
			grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
			print('++++++++Done with thread id: '+id)
	elif ropts.users<>[]:
		user_dict=shelve.open(ropts.filename_userdict)
		for user in ropts.users:
			ruser=bot.get_redditor(user)
			ravage_comment_history(ruser,ropts.minwords,ropts.depth,user_dict)
			if ropts.ux:
				for comment in user_dict[str(ruser.id)][0]:
					if user_dict[str(ruser.id)][0][comment]['POST_LINK'] not in ropts.idlist:
						ropts.idlist+=[user_dict[str(ruser.id)][0][comment]['POST_LINK']]
		user_dict.close()
		if ropts.idlist<>[]:
			print(ropts.idlist)
			for id in ropts.idlist:
				print(id)
				grab_page_depth(id,bot,ropts.depth_maxima,ropts.minwords,user_comment_depth=ropts.depth,ropts=ropts)
				print('++++++++Done with thread id: '+id)
	print("DONE WITH SCRAPING")

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
#-mw: followed by minimum number of words
#-name: followed by prefix of filename
#-tree: followed by integers representing depth_maxima	
#-ux: will go to threads for all comments of users if there are users defined; this is too slow to do in any other context
#-type: will allow you to specify what kinds of submissions to get (top, hot, controversial)
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
			self.idlist+=extract_lines(args[args.index('-f')+1])
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
			self.depth_maxima=[18,5,3,2]
		if '-edate' in args:
			di=args.index('-edate')
			self.edate =[args[di+1],args[di+2]]
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
		print('finished parsing options')
		#self.idlist=self.thread_ids
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
	
		
		
if __name__ == '__main__':
	main(sys.argv[1:])

	
#idlist=['23rt24','z1c9z','25hauk','14obcf','180yye','22m5op','1pd095','24zdnn','13vvzd','1cgo6n','1uw05k','18umza','18err8','16oyf4','13xqbr','1j17ir']
#idlist+=['25gicq','25bupu','25kesk','25ftb7','24m4yw','2558kd','25gl4u','ydtg5','25hm4s','220xfl','24d12b','24hjlx','22gse9']
#idlist+=['23vf6g','1wj4ec']
#idlist+=['vw47s','1cjtzx','25jbjx','25kkob','25j861','25iw22','23r1zu','25lgfn']
#idlist+=['25jawr','25lldd','25kddk']
#idlist+=['124ej8','1fwfhr','vktow','1gacat']	
#idlist+=['25j4zb','1fljyt','259gwy','172oqi','y681w','1zwhxf','25mg31','23uq5l','22lv1n','23fgax','1hzb78','1v0zxa','1eviwk','21r2mk','1hv1ut','1xcpe8']

#idlist+=['24rh62']
#idlist+=['1ursuy','1x5mxx','1xdhq8','25n2oe','25fren','20umlq','25n96t','xmfwg','1gh0fc','1l7skp']
#idlist+=['1wxxty','25mth6']

#for id in idlist: