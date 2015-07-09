import sys
import os

filename_stopwords='stopwords.txt'
filename_joinwords='joinwords.txt'
filename_bijoinwords='bigramjoinwords.txt'

def main(argv):
	print "INITIALIZING LAZINESS"
	#extract arguments
	if '-select' in argv:
		select = argv[argv.index('-select')+1]
	else:
		print "INCLUDE SELECTION TO LIMIT CONSIDERED SUBREDDITS"
		sys.exit()
	if '-name' in argv:
		name = argv[argv.index('-name')+1]
	else:
		print "INCLUDE NAME!!!"
		sys.exit()
	if '-force' in argv:
		string_forcelist = '-force ' + argv[argv.index('-force') + 1]
	else:
		string_forcelist = ''
		
	if '-suppress' in argv:
		suppress_search_string = ' -suppress '
	else:
		suppress_search_string = ''
		
	if '-negatives' in argv:
		negativestring = ' -negatives '
	else:
		negativestring = ''
	if '-header' in argv:
		headerstring = ' -header '
	else:
		headerstring = ''

	step1 = 'python create_ngrams_fast.py -name '+name+' -select '+ select + ' -N 1 2 3 4 -cutoff 800 500 250 100 -age 136 ' + string_forcelist+suppress_search_string
	
	step2 = 'python extract_ngrams.py -name '+name+' -select ' + select + ' -N 1 2 3 4 -age 136'
	
	step3 = 'python prepare_data4.py -name ' + name + ' -select ' + select + ' -N 1 2 3 4 ' + negativestring

	step4 = 'python construct_user_network.py -header -name ' + name + ' -select ' + select + headerstring
	#1st ngram sweep
	os.system(step1)
	print "FINISHED STEP 1"
	#2nd ngram sweep
	os.system(step2)
	print "FINISHED STEP 2"
	#user, sub, term id mapping
	os.system(step3)
	print 'FINISHED STEP 3'
	os.system(step4)
	print "FINISHED STEP 4"
	#thread id mapping
	
	
if __name__=='__main__':
	main(sys.argv[1:])