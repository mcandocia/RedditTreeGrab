FILE DESCRIPTIONS:

reddit_grab.py - This is the program that collects all the data.  It requires an updated version of PRAW.  
The Reddit API changes consistently, so there may be new bugs occasionally.  Note that large files
run very slowly due to the use of the shelve module.

extract_ngrams.py - This will create a data structure to determine which ngrams should be collected.  It allows both
manual input and frequency-based selection.

create_ngrams_fast.py - This puts the ngrams of data into a text file for analysis.

prepare_data4.py - This prepares data for use with gen.py

gen.py - This runs a supervised, unsupervised, or semi-supervised model based on the data and any classifications that
are provided.

genmod_params.py - This file contains parameters to be used for gen.py.

get_random_users.py - This creates a file with randomly selected users so that you can add classifications to them.
Microsoft Excel hyperlink URLs are available as an option if you want to check user post histories out while having
the file open.

stopwords.txt - These are words that are removed from a dictionary if frequency-based ngram detection is allowed.

joinwords.txt - These are exceptions to stopwords if the word is not the first or last word of an ngram.

bigramjoinwords.txt - These are exceptions to stopwords if the ngram is not a unigram.

construct_user_network.py - This will construct edgelists in plaintext for thread histories.

transfer_data_to_postgres.py - This will allow you to transfer shelve module data to a PostgreSQL server.
This is a big speed advantage over the shelve module, but it is not yet integrated seamlessly into the 
reddit_grab.py file.

database_options.py - This file contains parameters for transfer_data_to_postgres.py.  This file needs to be
created by the user, but it only takes 5 lines.  It is currently omitted in this directory because it contains password
information for logging into the database server.