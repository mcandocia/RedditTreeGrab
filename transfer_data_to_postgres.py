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


import shelve
import psycopg2
import os
import re
import sys
import praw#in order to work with praw-like objects in case they exist
from datetime import datetime, timedelta

import database_options

directory = database_options.directory

#these are makeshift file names; actual names should be input via command lines
udict_filename = 'user_sqltest.dat'
tdict_filename = 'thread_sqltest.dat'

#these are default table names; please use -target [tablename] for a different prefix
t_dbname = 't_thread'
tc_dbname = 't_threadcomments'
u_dbname = 't_user'
uc_dbname = 't_usercomments'

#used to determine how much of a file 
user_blocksize = 200
thread_blocksize = 200

###new arguments will be added as functionality needs to be diversified
#-name: followed by name of source file
#-target: followed by prefix of desired table names

def main(args):
	print "WARNING: TEST MODE"
	os.chdir(directory)
	if '-name' in args:
		name = args[args.index('-name')+1]
		udict_filename = 'user_' + name + '.dat'
		tdict_filename = 'thread_' + name + '.dat'
	##skip for now
	if '-target' in args:
		target = args[args.index('-target') + 1]
		global t_dbname
		global tc_dbname
		global u_dbname
		global uc_dbname
		t_dbname = target + '_thread'
		tc_dbname = target + '_threadcomments'
		u_dbname = target + '_user'
		uc_dbname = target + '_usercomments'
	#load server
	conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (database_options.dbname, database_options.username, database_options.host, database_options.password))
	cur = conn.cursor()
	cur.execute("""DROP TABLE IF EXISTS %s;
		DROP TABLE IF EXISTS %s;
		DROP TABLE IF EXISTS %s;
		DROP TABLE IF EXISTS %s;""" % (t_dbname,tc_dbname,u_dbname,uc_dbname))
	cur.execute('''CREATE TABLE IF NOT EXISTS %s(
		thread_id text PRIMARY KEY, 
		thread_score int,
		thread_subreddit text,
		thread_date_created date,
		thread_title text,
		thread_retrieved date,
		thread_ncomments int,
		thread_totalcomments int,
		thread_wordcount int,
		thread_url text,
		thread_longestcomment int,
		thread_topcommentlength int)
		;''' % (t_dbname))
	cur.execute('''CREATE TABLE IF NOT EXISTS %s(
		tc_id text PRIMARY KEY,
		tc_authorid text,
		tc_authorname text,
		tc_score int,
		tc_created date,
		tc_timeaftersubmission int,
		tc_location integer ARRAY[12],
		tc_gilded int,
		tc_text text,
		tc_parentID text,
		tc_nchildren int,
		tc_threadid text,
		tc_subreddit text)
		;''' % (tc_dbname))
	cur.execute('''CREATE TABLE IF NOT EXISTS %s(
		user_id text PRIMARY KEY,
		user_name text,
		user_age int,
		user_commentkarma int,
		user_linkkarma int,
		user_ismod bool,
		user_isgold bool,
		user_verified bool,
		user_firstretrieved date,
		user_lastretrieved date,
		user_shadowbanned bool,
		user_shadowbandate date
		);''' % (u_dbname))
	cur.execute('''CREATE TABLE IF NOT EXISTS %s(
		uc_id text PRIMARY KEY,
		uc_score int,
		uc_subreddit text,
		uc_created date,
		uc_gilded int,
		uc_distinguished text,
		uc_text text,
		uc_postlink text,
		uc_retrieved date,
		uc_authorid text,
		uc_authorname text)
		;''' % (uc_dbname))
	print "CREATED NEW TABLES"
	#input thread and thread comment data
	threaddict = shelve.open(tdict_filename)
	threads = []
	thread_keys = []
	counter = 0
	overcounter = 0
	#ltks = len(threaddict.keys())
	print "PROCESSING THREADS..."
	for key in threaddict:
		thread_keys.append(key)
		threads.append(threaddict[key])
		counter += 1
		if counter == thread_blocksize:
			insert_thread_data(cur,threads,thread_keys)
			counter = 0
			overcounter+=thread_blocksize
			print "PROCESSED " + str(overcounter) + " THREADS"
			threads = []
			thread_keys = []
	#manages very large size of dictionary
	if counter <> 0:
		insert_thread_data(cur,threads,thread_keys)
		counter = 0
		overcounter+=thread_blocksize
		print "PROCESSED " + str(overcounter) + " THREADS"
	
	threaddict.close()
	print "PROCESSED THREADS"
	#input user and comment data
	userdict = shelve.open(udict_filename)
	users = []
	print 'opened file...'
	user_keys = []
	counter = 0
	overcounter = 0
	#luks = len(userdict.keys())
	print "PROCESSING USERS..."
	for key, entry in userdict.iteritems():
		user_keys.append(key)
		users.append(entry)
		counter += 1
		if counter == 1:
			print 1+overcounter
		if counter == user_blocksize:
			insert_user_data(cur,users,user_keys)
			counter = 0
			overcounter += thread_blocksize
			print "PROCESSED " + str(overcounter) + " USERS"
			users = []
			user_keys = []
	if counter <> 0:
		insert_user_data(cur,users,user_keys)
		counter = 0
		overcounter += thread_blocksize
		print "PROCESSED " + str(overcounter) + " USERS"
		users = []
		user_keys = []
	
	userdict.close()
	print "PROCESSED USERS"
	conn.commit()
	cur.close()
	conn.close()
	print "FINISHED"
	


def insert_thread_data(cursor,threads,thread_keys):
	thread_data = []
	thread_comment_data = []
	for i, thread in enumerate(threads):
		attris = thread[1]
		thread_data.append((
			thread_keys[i],
			attris['THREAD_SCORE'],
			attris['SUBREDDIT'],
			convert_time(attris['DATE_CREATED']),
			attris['TITLE'],
			convert_time(attris['RETRIEVED']),
			attris['NCOMMENTS'],
			attris['TOTAL_COMMENTS'],
			attris['COMMENT_WORDCOUNT'],
			attris['URL'],
			attris['LONGEST_COMMENT'],
			attris['TOP_COMMENT_LENGTH']))
		comments = thread[0]
		comment_keys = comments.keys()
		for j, comment_k in enumerate(comments):
			comment = comments[comment_k]
			thread_comment_data.append((
				comment_keys[j],
				comment['AUTHOR_ID'],
				comment['AUTHOR_NAME'],
				comment['SCORE'],
				convert_time(comment['TIME_CREATED']),
				comment['TIME_AFTER_SUBMISSION'],
				comment['COMMENT_LOCATION'],
				comment['COMMENT_GILDED'],
				comment['COMMENT_TEXT'],
				comment['PARENT_ID'],
				comment['NCHILDREN'],
				thread_keys[i],
				attris['SUBREDDIT']))		
	exmany(cursor,t_dbname,thread_data)
	exmany(cursor,tc_dbname,thread_comment_data)
		
def insert_user_data(cursor, users,user_keys):
	user_data = []
	user_comment_data = []
	for i, user in enumerate(users):
		utris = user[1]
		comments = user[0]
		comment_keys = comments.keys()
		if 'FIRST_RETRIEVED' not in utris:
			utris['FIRST_RETRIEVED'] = None
		if 'SHADOWBANNED' not in utris:
			utris['SHADOWBANNED'] = None
			utris['SHADOWBAN_DATE'] = None
		user_data.append((
			user_keys[i],
			utris['AUTHOR_NAME'],
			utris['AUTHOR_AGE'],
			utris['AUTHOR_COMMENTKARMA'],
			utris['AUTHOR_LINKKARMA'],
			utris['IS_MOD'],
			utris['IS_GOLD'],
			utris['VERIFIED'],
			convert_time(utris['FIRST_RETRIEVED']),
			convert_time(utris['RETRIEVED']),
			utris['SHADOWBANNED'],
			convert_time(utris['SHADOWBAN_DATE'])))
		for j, comment_k in enumerate(comments):
			comment = comments[comment_k]
			if 'COMMENT_RETRIEVED' not in comment:
				comment['COMMENT_RETRIEVED'] = None
			user_comment_data.append((
				comment_keys[j],
				comment['COMMENT_SCORE'],
				comment['SUBREDDIT'],
				convert_time(comment['COMMENT_CREATED']),
				comment['COMMENT_GILDED'],
				comment['COMMENT_DISTINGUISHED'],
				comment['COMMENT_TEXT'],
				comment['POST_LINK'],
				convert_time(comment['COMMENT_RETRIEVED']),
				user_keys[i],
				utris['AUTHOR_NAME']))
	exmany(cursor,u_dbname,user_data)
	exmany(cursor,uc_dbname,user_comment_data)		
				
def exmany(cursor,table_name,tup):
	"""executes many functions more efficiently than normal"""
	tlen = len(tup[0])
	#print tup
	inner_string = "(" +','.join([r'%s' for _ in range(tlen)])+')'
	#print inner_string
	argstring = ','.join(cursor.mogrify( inner_string,x) for x in tup)
	#print argstring
	try:
		cursor.execute("INSERT INTO " + table_name + " VALUES " + argstring)
	except psycopg2.DataError as err:
		raise
def convert_time(inttime):
	if inttime <> None:
		return datetime.fromtimestamp(inttime).strftime('%x %X')
	else:
		return None
	
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

if __name__ == '__main__':
	main(sys.argv[1:])