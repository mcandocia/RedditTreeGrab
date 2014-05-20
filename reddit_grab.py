#THIS WILL SCRAPE A REDDIT PAGE AND THEN WRITE IT TO A READABLE FILE
#different types of imports will be used
#concatenations are also possible in the future

import re
import os
import praw
import time
import shelve
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ConnectionError
from exceptions import UnicodeDecodeError
import time
import calendar

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
def grab_page_depth(id,bot,depth_maxima,minwords=25,user_comment_depth=300):
	submission=bot.get_submission(submission_id=id)
	title=rmnl(submission.title)
	comment_tree=comtree(submission.comments,depth_maxima)
	post_created = submission.created
	user_dict=shelve.open(filename_userdict)
	thread_dict=shelve.open(filename_threaddict)
	if id in thread_dict:
		user_dict.close()
		thread_dict.close()
		print("Thread already analyzed")
		return(False)
	temp_thread_dict=dict()
	while comment_tree.direction <> 'T':
		current_comment=comment_tree.get_current_comment()
		if str(type(current_comment))=="<class 'praw.objects.MoreComments'>":
			print("HIT THIS")#hopefully it never gets hit
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
			#current_comment=comment_tree.get_current_comment()
			#comment_tree.move()
			#continue
		current_text=current_comment.body
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
		current_id=current_comment.id
		is_gilded=current_comment.gilded
		try:
			current_author_id=current_author.id
		except HTTPError:
			print('author ID not found.  set to void')
			current_author_id='NO_AUTHOR_ID'
		#list() will dereference the value
		temp_thread_dict[current_id]={'AUTHOR_ID':current_author_id,'AUTHOR_NAME':current_author_string,'SCORE':current_score,'TIME_CREATED':current_time,'TIME_AFTER_SUBMISSION':current_time-post_created,'COMMENT_LOCATION':list(comment_tree.location),'COMMENT_GILDED':is_gilded}
		if current_author_id=='NO_AUTHOR_ID':
			comment_tree.move()
			continue
		if not str(current_author_id) in user_dict:
			continue_attempts=True
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
		if str(type(self.current_tree[len(self.current_tree)-1]))=="<class 'praw.objects.MoreComments'>":
			rmindex=len(self.current_tree)-1
			self.current_tree=self.current_tree+self.current_tree[rmindex].comments()
			del(self.current_tree[rmindex])
		#print('current level: '+str(self.level))
		#print(str(self.location))
		#print(self.current_tree)
		while temp_level<self.level:
			#print('temp level: ' + str(temp_level))
			self.curent_tree=self.current_tree[self.location[temp_level]].replies
			temp_level=temp_level+1
		if self.can_move_to_side():
			self.direction='S'
		elif self.level==0:
			self.direction='T'
		return()
	def get_current_comment(self):
		return(self.current_tree[self.location[self.level]])
	def invoke_morecomments(self):#unstable atm	
		if self.get_current_comment().comments()==[]:
			return(False)
		self.current_tree=self.current_tree+self.get_current_comment().comments()
		#print(self.location)
		#print(self.level)
		
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
	comments=user.get_comments(limit=user_comment_depth)
	#comments=user.get_comments(limit=user_comment_depth)
	comment_dict=dict()
	try:
		for comment in comments:
			comment_text=comment.body
			if nwords(comment_text)<minwords:
				continue
			#SUBREDDIT previously COMMENT_ID
			comment_dict[str(comment.id)]={'SUBREDDIT':str(comment.subreddit),'COMMENT_SCORE':comment.score,'COMMENT_CREATED':comment.created,'COMMENT_GILDED':comment.gilded,'COMMENT_DISTINGUISHED':comment.distinguished,'COMMENT_TEXT':comment_text}
			if str(comment.subreddit) not in user_subs:
				user_subs.add(str(comment.subreddit))
	except (HTTPError,ConnectionError) as err:
		if type(err)==HTTPError:#err.errno==404:
			print('User is shadowbanned: '+ str(user))
			return(False)
		else:
			print('Connection Error...sleeping')
			time.sleep(10)
			return(True)
	utris=dict()
	utris['AUTHOR_AGE']=user.created
	utris['AUTHOR_NAME']=str(user)
	utris['AUTHOR_COMMENTKARMA']=user.comment_karma
	utris['AUTHOR_LINKKARMA']=user.link_karma
	utris['IS_MOD']=user.is_mod
	utris['IS_GOLD']=user.is_gold
	utris['VERIFIED']=user.has_verified_email
	utris['SUBREDDIT_LIST']=user_subs
	utris['RETRIEVED']=calendar.timegm(time.gmtime())
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

#note that number of users in each 
def main():
	#idlist=['23rt24','z1c9z','25hauk','14obcf','180yye','22m5op','1pd095','24zdnn','13vvzd','1cgo6n','1uw05k','18umza','18err8','16oyf4','13xqbr','1j17ir']
	#idlist+=['25gicq','25bupu','25kesk','25ftb7','24m4yw','2558kd','25gl4u','ydtg5','25hm4s','220xfl','24d12b','24hjlx','22gse9']
	#idlist+=['23vf6g','1wj4ec']
	#idlist+=['vw47s','1cjtzx','25jbjx','25kkob','25j861','25iw22','23r1zu','25lgfn']
	#idlist+=['25jawr','25lldd','25kddk']
	#idlist+=['124ej8','1fwfhr','vktow','1gacat']	
	#idlist+=['25j4zb','1fljyt','259gwy','172oqi','y681w','1zwhxf','25mg31','23uq5l','22lv1n','23fgax','1hzb78','1v0zxa','1eviwk','21r2mk','1hv1ut','1xcpe8']
	bot=praw.Reddit('thread analyzing test by /u/SymphMeta')
	#idlist+=['24rh62']
	#idlist+=['1ursuy','1x5mxx','1xdhq8','25n2oe','25fren','20umlq','25n96t','xmfwg','1gh0fc','1l7skp']
	#idlist+=['1wxxty','25mth6']
	
	#for id in idlist:
	while True:
		post=get_random_post(bot,13)
		print('Scraping ' + str(removeNonAscii(post.title)) + ' from ' + str(post.subreddit))
		id=str(post.id)
		grab_page_depth(id=id,bot=bot,depth_maxima=[18,5,3,2],minwords=13,user_comment_depth=500)
		print('++++++++Done with thread id: '+id)
	print("DONE WITH TEST")
	
	
	
if __name__ == '__main__':
	main()

	