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