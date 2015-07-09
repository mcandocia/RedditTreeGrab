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

#grabs random users and puts them into a csv to fill out

import shelve
import sys
import os
import random
import csv



def main(argv):
	if '-name' in argv:
		name = argv[argv.index('-name')+1]
		filename_idlist = 'user_id_' + name +'.txt'
		outfile = 'user_sample0_' + name + '.csv'
		filelist = os.listdir(os.getcwd())
		counter = 0
		while outfile in filelist:
			counter+=1
			outfile = 'user_sample' + str(counter) + '_' + name + '.csv'
		print "Making random file #" + str(counter+1)
	else:
		print 'PLEASE PROVIDE NAME'
		sys.exit()
	if '-n' in argv:
		n = int(argv[argv.index('-n')+1])
	else:
		n = 150
	if '-excel' in argv:
		excel_hyper = True
	else:
		excel_hyper = False
	uid_file_ = open(filename_idlist)
	uid_file = csv.reader(uid_file_)
	uids = []
	for row in uid_file:
		uids.append(row)
	uid_file_.close()
	sample = random.sample(uids,n)
	out = open(outfile,'wb')
	writer = csv.writer(out)
	for uid in sample:
		uid.append(make_url(uid[2],excel_hyper))
		writer.writerow(uid)
	out.close()
	print "MADE RANDOM LIST"

def make_url(x,excel_hyper):
	if not excel_hyper:
		return 'http://reddit.com/user/' + str(x) + '/'
	return '=HYPERLINK("http://reddit.com/user/' + str(x) + '/")'

if __name__=='__main__':
	main(sys.argv[1:])